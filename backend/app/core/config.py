from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_CSV = BASE_DIR / "data" / "job_applicant_dataset.csv"
OUTPUT_CSV = BASE_DIR / "data" / "job_applicant_dataset_final.csv"
RANDOM_STATE = 42

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "")
ADZUNA_COUNTRY = os.getenv("ADZUNA_COUNTRY", "us")
ADZUNA_LOCATION = os.getenv("ADZUNA_LOCATION", "")
ADZUNA_TIMEOUT_SECONDS = float(os.getenv("ADZUNA_TIMEOUT_SECONDS", "8"))
