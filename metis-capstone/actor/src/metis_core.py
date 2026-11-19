"""Metis · núcleo general de ETL, métricas de negocio y modelo.

Funciona para cualquier rubro de Mercado Libre: no depende de categorías fijas,
usa la categoría que trae la publicación (domainId) y compara cada producto
contra su propia categoría.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

# Nombres en español para las categorías que ya conocemos (opcional).
# Si una categoría no está acá, se usa su domainId en formato legible.
NOMBRES_CATEGORIA = {
    "MLA-SURVEILLANCE_CAMERAS": "Cámaras / Kits CCTV",
    "MLA-HOME_ALARMS_AND_SENSORS": "Alarmas inteligentes",
    "MLA-GAS_DETECTORS": "Alarmas inteligentes",
    "MLA-ELECTRIC_LOCKS": "Cerraduras digitales",
    "MLA-DOOR_AND_WINDOW_LOCKS": "Cerraduras digitales",
    "MLA-ELECTRIC_ENTRANCE_INTERCOMS": "Porteros visores",
    "MLA-ELECTRONIC_ACCESSORIES_AND_REPLACEMENTS": "Accesorios",
    "MLA-ALARM_REMOTE_CONTROLS": "Accesorios",
}

# Variables del modelo: todas relativas o binarias, así sirven en cualquier rubro.
FEATURES = [
    "precio_rel",            # precio / mediana de su categoría
    "descuento_pct",
    "cuotas_sin_interes",
    "envio_gratis",
    "tienda_oficial",
    "es_combo",
    "rating",
    "tiene_rating",
    "resenas_log",           # log(1 + cantidad de reseñas)
    "resenas_rel",           # reseñas / mediana de reseñas de su categoría
]

MIN_POR_CATEGORIA = 5  # categorías con menos publicaciones se juntan en "Otras"

_COMBO = re.compile(r"\b(?:combo|kit|pack|set|piezas|pzas)\b|\bx\s?\d+\b|\b\d+\s?x\b", re.I)


def _bool(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.lower().isin(["true", "1", "1.0", "yes", "si", "sí"]).astype(int)


def _num(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df:
        return pd.Series(np.nan, index=df.index)
    return pd.to_numeric(df[col], errors="coerce")


def _nombre_categoria(domain: str) -> str:
    if not isinstance(domain, str) or not domain:
        return "Otras"
    if domain in NOMBRES_CATEGORIA:
        return NOMBRES_CATEGORIA[domain]
    return re.sub(r"^ML[A-Z]-", "", domain).replace("_", " ").capitalize()


def aplanar(items: list[dict] | pd.DataFrame) -> pd.DataFrame:
    """Convierte la salida del scraper (JSON anidado o CSV) en una tabla plana."""
    if isinstance(items, pd.DataFrame):
        return items
    return pd.json_normalize(items, sep="/")


def preparar(df_raw: pd.DataFrame, rubro: str) -> pd.DataFrame:
    """ETL general: de las columnas crudas del scraper a las columnas de Metis."""
    raw = aplanar(df_raw).copy()
    if "itemId" in raw:
        raw = raw.drop_duplicates("itemId")
    out = pd.DataFrame(index=raw.index)
    out["item_id"] = raw.get("itemId")
    out["titulo"] = raw.get("title", pd.Series("", index=raw.index)).fillna("").astype(str)
    out["rubro"] = rubro
    out["busqueda"] = raw.get("searchQuery", pd.Series(rubro, index=raw.index))
    out["categoria"] = raw.get("domainId", pd.Series("", index=raw.index)).map(_nombre_categoria)
    marca = raw.get("brand", pd.Series(np.nan, index=raw.index)).fillna("Genérica").astype(str).str.strip().str.title()
    out["marca"] = marca.replace({"": "Genérica", "No": "Genérica", "Nan": "Genérica"})

    precio = _num(raw, "price")
    anterior = _num(raw, "originalPrice").fillna(precio)
    out["precio"] = precio
    out["precio_anterior"] = np.maximum(anterior, precio)
    out["descuento_pct"] = np.where(out["precio_anterior"] > precio,
                                    (out["precio_anterior"] - precio) / out["precio_anterior"] * 100, 0.0).round(2)
    out["cuotas_sin_interes"] = _bool(raw.get("installments/interestFree", pd.Series(False, index=raw.index)))
    out["envio_gratis"] = _bool(raw.get("freeShipping", pd.Series(False, index=raw.index)))
    out["tienda_oficial"] = _bool(raw.get("isOfficialStore", pd.Series(False, index=raw.index)))
    out["es_combo"] = out["titulo"].str.contains(_COMBO, na=False).astype(int)
    rating = _num(raw, "rating")
    out["tiene_rating"] = rating.notna().astype(int)
    out["rating"] = rating
    out["cantidad_resenas"] = _num(raw, "ratingCount").fillna(0).astype(int)
    out["vendidos"] = _num(raw, "soldQuantity")
    out["url"] = raw.get("url")

    out = out[out["precio"].notna() & (out["precio"] > 0)]
    # Precios absurdos: fuera de 1/50 y 50 veces la mediana del rubro
    med = out["precio"].median()
    out = out[(out["precio"] >= med / 50) & (out["precio"] <= med * 50)]
    # Categorías chicas se juntan
    cuenta = out["categoria"].value_counts()
    out.loc[out["categoria"].isin(cuenta[cuenta < MIN_POR_CATEGORIA].index), "categoria"] = "Otras"
    # Rating faltante: mediana de su categoría (la falta queda en tiene_rating)
    out["rating"] = out["rating"].fillna(out.groupby("categoria")["rating"].transform("median")).fillna(out["rating"].median()).fillna(0)
    return out.reset_index(drop=True)


def metricas_negocio(df: pd.DataFrame) -> pd.DataFrame:
    """Métrica de negocio, score de costo-beneficio y variables relativas a la categoría."""
    df = df.copy()
    g = df.groupby("categoria")
    df["precio_prom_categoria"] = g["precio"].transform("mean").round(0)
    df["distancia_precio_prom_pct"] = ((df["precio"] - df["precio_prom_categoria"]) / df["precio_prom_categoria"] * 100).round(2)
    df["banda_precio"] = np.select(
        [df["distancia_precio_prom_pct"] < -10, df["distancia_precio_prom_pct"] > 10],
        ["abajo", "arriba"], default="dentro")
    df["precio_rel"] = (df["precio"] / g["precio"].transform("median")).round(4)
    df["resenas_log"] = np.log1p(df["cantidad_resenas"]).round(4)
    med_res = g["cantidad_resenas"].transform("median").replace(0, 1)
    df["resenas_rel"] = (df["cantidad_resenas"] / med_res).round(4)

    # Score de costo-beneficio 0-100, dentro de cada categoría
    rank_precio = 1 - g["precio"].rank(pct=True)
    rank_res = g["cantidad_resenas"].rank(pct=True)
    promos = (df["cuotas_sin_interes"] + df["envio_gratis"]) / 2
    df["score_costo_beneficio"] = (100 * (0.35 * rank_precio + 0.30 * (df["rating"] / 5) + 0.20 * rank_res + 0.15 * promos)).round(1)
    df["es_competitivo"] = (df["score_costo_beneficio"] >= 65).astype(int)
    return df


def target_vende_mucho(df: pd.DataFrame, q: float = 0.75) -> pd.Series:
    """1 si los vendidos superan el percentil q de su categoría (y son más de 0)."""
    vend = df["vendidos"].fillna(0)
    umbral = vend.groupby(df["categoria"]).transform(lambda s: s.quantile(q))
    return ((vend > umbral) | ((vend >= umbral) & (vend > 0) & (umbral > 0))).astype(int)


def resumen(df: pd.DataFrame) -> dict:
    """KPIs del relevamiento para el dashboard y el cliente."""
    return {
        "rubro": str(df["rubro"].iloc[0]) if len(df) else "",
        "publicaciones": int(len(df)),
        "categorias": int(df["categoria"].nunique()),
        "precio_promedio": float(round(df["precio"].mean(), 0)),
        "precio_mediano": float(round(df["precio"].median(), 0)),
        "pct_dentro_10": float(round((df["banda_precio"] == "dentro").mean() * 100, 1)),
        "pct_alta_rotacion_predicha": float(round(df["prob_vende_mucho"].ge(0.5).mean() * 100, 1)) if "prob_vende_mucho" in df else None,
        "pct_competitivos": float(round(df["es_competitivo"].mean() * 100, 1)),
    }
