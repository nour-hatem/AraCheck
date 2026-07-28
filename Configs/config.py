"""
Configuration file for the preprocessing pipeline.
Contains file paths and preprocessing parameters.
"""

import os

# ------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

RAW_DATA_PATH = os.path.join(DATA_DIR, "AHD_english.xlsx")
OUTPUT_DATA_PATH = os.path.join(DATA_DIR, "dataset_20k.csv")

# ------------------------------------------------------------------
# Preprocessing parameters
# ------------------------------------------------------------------

# Minimum number of samples a category must have to be kept
MIN_CATEGORY_COUNT = 1000

# Number of samples to extract for the final balanced dataset
SAMPLE_SIZE = 20000

# Random seed for reproducibility
RANDOM_STATE = 42

# Columns expected in the raw dataset
TEXT_COLUMNS = ["Question", "Answer"]
CATEGORY_COLUMN = "Category"

# ------------------------------------------------------------------
# Category mapping: merges the many raw/noisy category labels found
# in the original dataset into a smaller set of consistent categories
# ------------------------------------------------------------------
CATEGORY_MAPPING = {
    # Women's Health
    "Gynecological diseases": "Women's Health",
    "Women's health": "Women's Health",
    "Pregnancy and Birth": "Women's Health",
    "Infertility": "Women's Health",
    "Gynecological surgery": "Women's Health",
    "Embryology": "Women's Health",
    "Carry tubes": "Women's Health",

    # Sexual & Reproductive Health
    "Sexual health": "Sexual & Reproductive Health",
    "Sexual diseases": "Sexual & Reproductive Health",
    "Men's health": "Sexual & Reproductive Health",
    "Urinary and reproductive tract diseases": "Sexual & Reproductive Health",
    "Urology": "Sexual & Reproductive Health",
    "Urology and Genitourinary Tract Diseases": "Sexual & Reproductive Health",

    # Dermatology
    "skin diseases": "Dermatology",
    "Skin diseases": "Dermatology",
    "Skin and beauty": "Dermatology",
    "Allergic allergy": "Dermatology",

    # Dentistry & Oral Health
    "Dental diseases": "Dentistry & Oral Health",
    "Oral diseases": "Dentistry & Oral Health",
    "Teeth health": "Dentistry & Oral Health",
    "Dental health": "Dentistry & Oral Health",
    "Dentistry": "Dentistry & Oral Health",
    "dentist": "Dentistry & Oral Health",
    "Jaw and dental surgery": "Dentistry & Oral Health",

    # Musculoskeletal & Orthopedics
    "Musculoskeletal and joint diseases": "Musculoskeletal & Orthopedics",
    "Orthopaedic Surgery": "Musculoskeletal & Orthopedics",
    "physical therapy": "Musculoskeletal & Orthopedics",
    "Rheumatic diseases": "Musculoskeletal & Orthopedics",

    # Pediatrics
    "Pediatric": "Pediatrics",
    "Child health": "Pediatrics",
    "Children's diseases": "Pediatrics",
    "Pediatric surgery": "Pediatrics",

    # Mental Health
    "Psychiatric illness": "Mental Health",
    "Psychological health": "Mental Health",
    "Psychological illnesses": "Mental Health",
    "Mental health": "Mental Health",
    "psychology": "Mental Health",
    "addiction": "Mental Health",

    # Cardiovascular
    "Cardiovascular disease": "Cardiovascular",
    "Hypertension": "Cardiovascular",
    "Heart and arterial diseases": "Cardiovascular",
    "Cardiovascular surgery": "Cardiovascular",
    "Vascular surgery": "Cardiovascular",

    # Surgery
    "General Surgery": "Surgery",
    "Plastic surgery": "Surgery",
    "Neurosurgery": "Surgery",

    # Endocrinology & Diabetes
    "Endocrine diseases": "Endocrinology & Diabetes",
    "diabetes": "Endocrinology & Diabetes",
    "Hormones": "Endocrinology & Diabetes",
    "Metabolic diseases": "Endocrinology & Diabetes",

    # Respiratory
    "respiratory system diseases": "Respiratory Diseases",
    "Respiratory diseases": "Respiratory Diseases",

    # Ophthalmology
    "eyes illnesses": "Ophthalmology",
    "Eye diseases": "Ophthalmology",
    "optics": "Ophthalmology",

    # ENT
    "Nose, ear and throat": "ENT",
    "Nose, Ear and Throat": "ENT",

    # Infectious Diseases
    "Infectious diseases": "Infectious Diseases",
    "Vaccines and vaccinations": "Infectious Diseases",
    "Preventive Medicine": "Infectious Diseases",
    "Immunology": "Infectious Diseases",

    # Diagnostics & Laboratory
    "Diagnosis": "Diagnostics & Laboratory",
    "laboratory": "Diagnostics & Laboratory",
    "Radiology": "Diagnostics & Laboratory",
    "Pathology": "Diagnostics & Laboratory",
    "Microbiology": "Diagnostics & Laboratory",
    "Histology": "Diagnostics & Laboratory",
    "Anatomy": "Diagnostics & Laboratory",
    "Physiology": "Diagnostics & Laboratory",
    "Biochemistry": "Diagnostics & Laboratory",
    "biology": "Diagnostics & Laboratory",
    "chemistry": "Diagnostics & Laboratory",
    "physics": "Diagnostics & Laboratory",
    "organic chemistry": "Diagnostics & Laboratory",

    # Genetics
    "Genetic Disease": "Genetics",
    "Genetics": "Genetics",
    "Birth Defect": "Genetics",

    # Pharmacology
    "Pharmacology": "Pharmacology",
    "to drug": "Pharmacology",
    "toxicology": "Pharmacology",
    "Herbalists": "Pharmacology",
    "Alternative medicine": "Pharmacology",
    "Vitamins and minerals": "Pharmacology",

    # General Medicine
    "General medicine": "General Medicine",
    "Esoteric diseases": "General Medicine",
    "medical services": "General Medicine",
    "Medical equipment": "General Medicine",
    "Medical News": "General Medicine",
    "History of medicine": "General Medicine",
    "First aid": "General Medicine",
    "public health": "General Medicine",
    "Health and sports": "General Medicine",
    "Ramadan": "General Medicine",
    "Nutrition": "General Medicine",
    "feed": "General Medicine",
}
