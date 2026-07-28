"""
Handles text cleaning and category mapping/merging.
"""

import pandas as pd

from configs.config import (
    CATEGORY_MAPPING,
    CATEGORY_COLUMN,
    MIN_CATEGORY_COUNT,
    TEXT_COLUMNS,
)


def merge_categories(df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge the many raw/noisy category labels into a smaller,
    consistent set of categories using CATEGORY_MAPPING.
    """
    df = df.copy()
    df[CATEGORY_COLUMN] = df[CATEGORY_COLUMN].replace(CATEGORY_MAPPING)
    print("Category distribution after merging:")
    print(df[CATEGORY_COLUMN].value_counts())
    return df


def filter_rare_categories(
    df: pd.DataFrame, min_count: int = MIN_CATEGORY_COUNT
) -> pd.DataFrame:
    """
    Keep only categories that appear at least `min_count` times.
    """
    counts = df[CATEGORY_COLUMN].value_counts()
    categories_to_keep = counts[counts >= min_count].index
    df = df[df[CATEGORY_COLUMN].isin(categories_to_keep)]
    print(f"Categories kept (count >= {min_count}):")
    print(df[CATEGORY_COLUMN].value_counts())
    return df


def clean_text_columns(df: pd.DataFrame, columns=TEXT_COLUMNS) -> pd.DataFrame:
    """
    Drop rows with missing values and strip whitespace from text columns.
    """
    df = df.copy()
    df.dropna(inplace=True)
    for col in columns:
        df[col] = df[col].str.strip()
    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove duplicate rows from the dataset.
    """
    n_duplicates = df.duplicated().sum()
    print(f"Found {n_duplicates} duplicate rows. Removing them...")
    df = df.drop_duplicates()
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Full cleaning pipeline:
    1. Merge noisy categories into consistent labels
    2. Filter out categories with too few samples
    3. Remove duplicate rows
    4. Drop missing values and strip text columns
    """
    df = merge_categories(df)
    df = filter_rare_categories(df)
    df = remove_duplicates(df)
    df = clean_text_columns(df)
    return df
