"""
feature_engineering.py — Features demográficas desde archivo local.
No depende de censoargentino ni duckdb.
"""

import json
from pathlib import Path
import pandas as pd


def cargar_datos_demograficos() -> dict:
    path = Path(__file__).parent / "features_patino.json"
    with open(path) as f:
        return json.load(f)


def agregar_features_demograficas(df: pd.DataFrame, features: dict) -> pd.DataFrame:
    for nombre, valor in features.items():
        df[nombre] = valor
    return df
