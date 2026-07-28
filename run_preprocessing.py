"""
Main entry point to execute the full preprocessing pipeline:

1. Load raw data
2. Clean data (merge categories, filter rare ones, dedupe, strip text)
3. Inspect class distribution
4. Draw a stratified sample
5. Save the resulting dataset to CSV
"""

from configs.config import OUTPUT_DATA_PATH
from src.data_loader import load_data
from src.cleaner import clean_data
from src.balancer import inspect_distribution, stratified_sample


def main():
    # 1. Load
    df = load_data()

    # 2. Clean
    df = clean_data(df)

    # 3. Inspect distribution
    inspect_distribution(df)

    # 4. Stratified sample
    df_sampled = stratified_sample(df)

    # 5. Save
    df_sampled.to_csv(OUTPUT_DATA_PATH, index=False)
    print(f"Saved final dataset to: {OUTPUT_DATA_PATH}")


if __name__ == "__main__":
    main()
