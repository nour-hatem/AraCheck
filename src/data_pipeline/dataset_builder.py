"""
DatasetBuilder
==============
Reads a clean medical Q&A dataset (CSV or XLSX), validates its schema,
and converts it into HuggingFace Datasets formatted with the Qwen2.5
chat template — ready to be fed directly into the Trainer.

Expected input schema
---------------------
  Column     Type    Description
  --------   ------  ----------------------------
  Question   str     Patient question (user turn)
  Answer     str     Doctor answer (assistant turn)

Any additional columns are silently ignored.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pandas as pd
from datasets import Dataset, DatasetDict

if TYPE_CHECKING:
    from configs import Config
    from transformers import PreTrainedTokenizerBase

logger = logging.getLogger(__name__)

_REQUIRED_COLUMNS = {"Question", "Answer"}


class DatasetBuilder:
    """
    Converts a clean tabular data file into a pair of HuggingFace Datasets.

    Parameters
    ----------
    config:
        The centralised :class:`~configs.Config` instance.
    tokenizer:
        A HuggingFace tokenizer that supports ``apply_chat_template``.
        Must be loaded *before* building the dataset so the chat template
        is applied consistently.
    """

    def __init__(self, config: Config, tokenizer: PreTrainedTokenizerBase) -> None:
        self.config = config
        self.tokenizer = tokenizer

    # ── Public API ────────────────────────────────────────────────────────────

    def build(self) -> tuple[Dataset, Dataset]:
        """
        Execute the full build pipeline:

        1. Load data from disk (CSV or XLSX).
        2. Validate schema and drop incomplete rows.
        3. Apply the Qwen chat template to each row.
        4. Split into train / eval sets.

        Returns
        -------
        (train_dataset, eval_dataset)
        """
        df = self._load()
        df = self._validate(df)
        split = self._split(df)
        train_ds = self._apply_template(split["train"])
        eval_ds  = self._apply_template(split["test"])

        logger.info(
            "Dataset ready — train: %d samples | eval: %d samples",
            len(train_ds),
            len(eval_ds),
        )
        return train_ds, eval_ds

    # ── Private helpers ───────────────────────────────────────────────────────

    def _load(self) -> pd.DataFrame:
        path = self.config.data_path
        suffix = path.suffix.lower()

        logger.info("Loading dataset from: %s", path)

        if suffix == ".csv":
            df = pd.read_csv(path)
        elif suffix in {".xlsx", ".xls"}:
            df = pd.read_excel(path)
        else:
            raise ValueError(
                f"Unsupported file format '{suffix}'. "
                "Place a .csv or .xlsx file in the data/ directory."
            )

        logger.info("Loaded %d rows, %d columns.", len(df), df.shape[1])
        return df

    def _validate(self, df: pd.DataFrame) -> pd.DataFrame:
        missing_cols = _REQUIRED_COLUMNS - set(df.columns)
        if missing_cols:
            raise ValueError(
                f"Dataset is missing required columns: {missing_cols}. "
                f"Found columns: {list(df.columns)}"
            )

        before = len(df)
        # Only drop rows where the columns we actually use are null
        df = df.dropna(subset=list(_REQUIRED_COLUMNS)).reset_index(drop=True)
        dropped = before - len(df)

        if dropped:
            logger.warning(
                "Dropped %d rows with missing Question/Answer values.", dropped
            )

        if len(df) == 0:
            raise ValueError(
                "Dataset is empty after dropping rows with null values."
            )

        return df[list(_REQUIRED_COLUMNS)]  # keep only what we need

    def _split(self, df: pd.DataFrame) -> DatasetDict:
        dataset = Dataset.from_pandas(df, preserve_index=False)
        return dataset.train_test_split(
            test_size=self.config.eval_split,
            seed=self.config.seed,
        )

    def _apply_template(self, dataset: Dataset) -> Dataset:
        """Formats each row as a Qwen chat-template string."""
        return dataset.map(
            self._format_row,
            remove_columns=dataset.column_names,
            desc="Applying chat template",
        )

    def _format_row(self, row: dict) -> dict:
        messages = [
            {"role": "user",      "content": str(row["Question"]).strip()},
            {"role": "assistant", "content": str(row["Answer"]).strip()},
        ]
        return {
            "text": self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=False,
            )
        }
