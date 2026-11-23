"""Metis · Actor de inferencia (seguridad electrónica).

Flujo de una corrida:
    1. Lee el input: `csv_url`, el CSV crudo del scraper de Mercado Libre (llega desde Drive vía Make).
    2. ETL: limpia y transforma las columnas crudas a las variables del modelo.
    3. EDA: arma un resumen del mercado y lo guarda como EDA_RESUMEN.json.
    4. Inferencia: carga el modelo ya entrenado en el Colab (pickle) y predice `vende_mucho`.
    5. Salida: filas en el dataset del run y OUTPUT.csv en el key-value store (Make lo descarga y lo envía).

El actor NO entrena el modelo: solo lo carga y predice. Tampoco guarda datos propios.
"""
import os
import pickle
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from apify import Actor

MODELO_LOCAL = Path(__file__).resolve().parents[1] / "model" / "modelo_seguridad_capstone.pickle"

MAPA_CATEGORIAS = {
    "MLA-SURVEILLANCE_CAMERAS": "Cámara / Kit CCTV",
    "MLA-HOME_ALARMS_AND_SENSORS": "Alarma Inteligente",
    "MLA-ELECTRIC_LOCKS": "Cerradura Digital",
    "MLA-DOOR_AND_WINDOW_LOCKS": "Cerradura Digital",
    "MLA-ELECTRIC_ENTRANCE_INTERCOMS": "Portero Visor",
    "MLA-ELECTRONIC_ACCESSORIES_AND_REPLACEMENTS": "Accesorios CCTV",
    "MLA-ALARM_REMOTE_CONTROLS": "Accesorios Alarma",
    "MLA-GAS_DETECTORS": "Alarma Inteligente",
}
PATRON_COMBO = r"\b(?:combo|kit|pack|piezas|pzas|set)\b|\bx\s?\d+\b|\b\d+\s?x\b"
PRECIO_MIN, PRECIO_MAX = 5_000, 2_000_000
# Mismas marcas "genéricas" que se unificaron en el Colab al entrenar
MARCAS_GENERICAS = {
    "", "nan", "none", ",", "! ! !", "no", "na", "other", "general", "generic", "generica", "genérica",
    "generico", "genérico", "generel", "nobrand", "neutral", "full", "kit", "camara", "cámaras",
    "cerradura electrónica inteligente", "smart lock",
}


def _a_binario(serie: pd.Series) -> pd.Series:
    return serie.astype(str).str.lower().isin(["true", "1", "1.0"]).astype(int)


def preparar_para_modelo(df_raw: pd.DataFrame) -> pd.DataFrame:
    """ETL: transforma el CSV crudo del scraper a las columnas que usa el modelo."""
    df = df_raw.drop_duplicates("itemId" if "itemId" in df_raw else None).copy()

    # Si ya viene limpio (ej. dataset_seguridad_limpio.csv), no se vuelve a mapear
    if "price" not in df.columns and "precio" in df.columns:
        return df

    df["precio"] = pd.to_numeric(df["price"], errors="coerce")
    df["precio_anterior"] = pd.to_numeric(df["originalPrice"], errors="coerce").fillna(df["precio"])
    df["precio_anterior"] = np.maximum(df["precio_anterior"], df["precio"])
    df["descuento_pct"] = np.where(
        df["precio_anterior"] > df["precio"],
        np.round((df["precio_anterior"] - df["precio"]) / df["precio_anterior"] * 100, 2),
        0.0,
    )
    df["cuotas_sin_interes"] = _a_binario(df.get("installments/interestFree", pd.Series(False, index=df.index)))
    df["envio_gratis"] = _a_binario(df["freeShipping"])
    df["tienda_oficial"] = _a_binario(df["isOfficialStore"])
    df["es_combo"] = df["title"].astype(str).str.lower().str.contains(PATRON_COMBO, regex=True, na=False).astype(int)
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(4.7)
    df["cantidad_resenas"] = pd.to_numeric(df["ratingCount"], errors="coerce").fillna(0).astype(int)
    df["categoria"] = df["domainId"].map(MAPA_CATEGORIAS).fillna("Otros")
    marca = df["brand"].fillna("Genérica").astype(str).str.strip()
    df["marca"] = np.where(marca.str.lower().isin(MARCAS_GENERICAS), "Genérica", marca.str.title())
    return df


def resumen_eda(df: pd.DataFrame) -> dict:
    """EDA encapsulado: las preguntas de negocio que responde la presentación."""
    return {
        "total_productos_limpios": int(len(df)),
        "precio_promedio_por_marca": df.groupby("marca")["precio"].mean().round(2).to_dict(),
        "publicaciones_por_categoria": df["categoria"].value_counts().to_dict(),
        "precio_y_rating_promedio_por_categoria": df.groupby("categoria")[["precio", "rating"]].mean().round(2).to_dict(),
    }


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


async def main() -> None:
    async with Actor:
        # 1. Input
        actor_input = await Actor.get_input() or {}
        csv_url = actor_input.get("csv_url")
        if not csv_url:
            raise ValueError("Falta pasar 'csv_url' en el input del actor.")

        # 2. ETL
        df_raw = pd.read_csv(csv_url)
        df = preparar_para_modelo(df_raw)
        df = df.dropna(subset=["precio"])
        df = df[(df["precio"] >= PRECIO_MIN) & (df["precio"] <= PRECIO_MAX)].copy()
        Actor.log.info(f"ETL: {len(df_raw)} filas crudas → {len(df)} filas limpias")

        # 3. EDA
        await Actor.set_value("EDA_RESUMEN.json", resumen_eda(df))

        # 4. Inferencia con el modelo ya entrenado
        artefacto = cargar_modelo()
        df["prediccion"] = artefacto["pipeline"].predict(df[artefacto["features"]])

        # 5. Salida
        await Actor.push_data(df.where(df.notna(), None).to_dict(orient="records"))
        await Actor.set_value("OUTPUT.csv", df.to_csv(index=False), content_type="text/csv")
        Actor.log.info(f"Listo: {int(df['prediccion'].sum())} de {len(df)} productos con alta rotación predicha")
