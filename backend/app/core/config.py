from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_CSV = BASE_DIR / "data" / "job_applicant_dataset.csv"
OUTPUT_CSV = BASE_DIR / "data" / "job_applicant_dataset_final.csv"
RANDOM_STATE = 42
