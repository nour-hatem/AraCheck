"""
Handles reading the raw Excel file into a pandas DataFrame.
"""

import os
import pandas as pd

from configs.config import RAW_DATA_PATH


def load_data(path: str = RAW_DATA_PATH) -> pd.DataFrame:
    """
    Load the raw dataset from an Excel file.

    Parameters
    ----------
    path : str
        Path to the raw .xlsx file. Defaults to RAW_DATA_PATH from config.

    Returns
    -------
    pd.DataFrame
        The raw dataset as loaded from disk.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Raw data file not found at '{path}'. "
            "Please place the AHD_english.xlsx file in the data/ directory."
        )

    print(f"Loading raw data from: {path}")
    df = pd.read_excel(path)
    print(f"Loaded {len(df):,} rows and {df.shape[1]} columns.")
    return df
