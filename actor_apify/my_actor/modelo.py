"""Modelo: carga el pickle entrenado en el Colab y predice. El actor no entrena."""
import os
import pickle
import urllib.request
from pathlib import Path

import pandas as pd

MODELO_LOCAL = Path(__file__).resolve().parents[1] / "model" / "modelo_seguridad_capstone.pickle"


def cargar_modelo() -> dict:
    """Carga el modelo entrenado en el Colab. Por defecto usa el pickle incluido en model/.
    Si se define la variable de entorno MODEL_URL, lo descarga de ahí (ej. key-value store de Apify)."""
    url = os.environ.get("MODEL_URL")
    ruta = MODELO_LOCAL
    if url:
        ruta = Path("modelo.pickle")
        urllib.request.urlretrieve(url, ruta)
    with open(ruta, "rb") as f:
        return pickle.load(f)


def predecir(df: pd.DataFrame, artefacto: dict) -> pd.Series:
    """Devuelve 1 si el producto tiene alta rotación predicha, 0 si no."""
    return pd.Series(artefacto["pipeline"].predict(df[artefacto["features"]]), index=df.index)
