"""ETL: del CSV crudo del scraper de Mercado Libre a las variables que usa el modelo."""
import numpy as np
import pandas as pd


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


def filtrar_precios(df: pd.DataFrame) -> pd.DataFrame:
    """Descarta precios vacíos o fuera del rango razonable del rubro."""
    df = df.dropna(subset=["precio"])
    return df[(df["precio"] >= PRECIO_MIN) & (df["precio"] <= PRECIO_MAX)].copy()
