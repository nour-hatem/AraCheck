"""
Handles class distribution inspection and stratified sampling/balancing.
"""

import pandas as pd
from sklearn.model_selection import train_test_split

from configs.config import CATEGORY_COLUMN, SAMPLE_SIZE, RANDOM_STATE


def inspect_distribution(df: pd.DataFrame) -> None:
    """
    Print basic statistics about the class (category) distribution.
    """
    counts = df[CATEGORY_COLUMN].value_counts()
    print("Class distribution:")
    print(counts)
    print(f"Mean samples per category: {counts.mean():.2f}")


def stratified_sample(
    df: pd.DataFrame,
    sample_size: int = SAMPLE_SIZE,
    random_state: int = RANDOM_STATE,
) -> pd.DataFrame:
    """
    Draw a stratified sample of `sample_size` rows from the dataset,
    preserving the relative proportion of each category.

    Parameters
    ----------
    df : pd.DataFrame
        The cleaned dataset.
    sample_size : int
        Total number of rows to sample.
    random_state : int
        Random seed for reproducibility.

    Returns
    -------
    pd.DataFrame
        A stratified sample with `sample_size` rows.
    """
    df_sampled, _ = train_test_split(
        df,
        train_size=sample_size,
        stratify=df[CATEGORY_COLUMN],
        random_state=random_state,
    )
    print(f"Sampled {len(df_sampled):,} rows (stratified by '{CATEGORY_COLUMN}').")
    return df_sampled
