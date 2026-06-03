# Carga de dataset y guardado de resultados

import pandas as pd
from app.core.config import DATA_CSV, OUTPUT_CSV


def cargar_dataset(csv_path=None):
    path = csv_path or DATA_CSV
    return pd.read_csv(
        path,
        sep=None,
        engine="python",
        on_bad_lines="skip",
        encoding="utf-8",
        keep_default_na=False,
    )


def guardar_dataset(df, output_path=None):
    path = output_path or OUTPUT_CSV
    df.to_csv(path, index=False, encoding='utf-8-sig')
    return path

# backward-compatible aliases
load_dataset = cargar_dataset
save_dataset = guardar_dataset
