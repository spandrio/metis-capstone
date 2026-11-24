"""Metis · actor general de inteligencia competitiva para Mercado Libre.

Le decís el rubro y las búsquedas (o le pasás un CSV crudo) y devuelve cada
publicación con la métrica de negocio, el score de costo-beneficio y la
probabilidad de alta rotación que predice el modelo.

Todo el ETL y el EDA corren adentro del actor (requisito para el flujo con Make):
- DATASET_LIMPIO (CSV): datos después del ETL, con métricas y target.
- EDA_RESUMEN (JSON) y EDA_REPORTE (PDF): análisis exploratorio del rubro.
- RESUMEN (JSON) y RESULTADOS_CSV (CSV): KPIs y predicciones del modelo.
"""
from __future__ import annotations

import io
import json
import pickle
from pathlib import Path

import pandas as pd
import requests
from apify import Actor

from .eda import eda_pdf, eda_resumen
from .metis_core import FEATURES, aplanar, metricas_negocio, preparar, resumen, target_vende_mucho

MODELO = Path(__file__).resolve().parents[1] / "model" / "modelo_general.pickle"

COLUMNAS_SALIDA = [
    "rubro", "busqueda", "categoria", "item_id", "titulo", "marca", "precio", "precio_anterior",
    "descuento_pct", "cuotas_sin_interes", "envio_gratis", "tienda_oficial", "es_combo", "rating",
    "cantidad_resenas", "vendidos", "precio_prom_categoria", "distancia_precio_prom_pct", "banda_precio",
    "score_costo_beneficio", "es_competitivo", "prob_vende_mucho", "pred_vende_mucho", "url",
]


def _drive_directo(url: str) -> str:
    """Convierte un link de Google Drive en link de descarga directa."""
    if "drive.google.com" in url and "/d/" in url:
        file_id = url.split("/d/")[1].split("/")[0]
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return url


async def _datos_por_busqueda(rubro_input: dict) -> pd.DataFrame:
    scraper = rubro_input.get("scraper_actor") or "sourabhbgp/mercadolibre-scraper"
    base = dict(rubro_input.get("scraper_input") or {"mode": "search", "country": "AR"})
    campo = rubro_input.get("campo_busqueda") or "searchQuery"
    maximo = int(rubro_input.get("max_por_busqueda") or 300)
    partes = []
    for q in rubro_input.get("busquedas") or []:
        run_input = {**base, campo: q, "maxItems": maximo}
        Actor.log.info(f"Buscando '{q}' con {scraper} (máx. {maximo})")
        run = await Actor.call(scraper, run_input=run_input)
        if run is None:
            Actor.log.warning(f"La búsqueda '{q}' no devolvió resultados")
            continue
        items = (await Actor.apify_client.dataset(run.default_dataset_id).list_items()).items
        Actor.log.info(f"'{q}': {len(items)} publicaciones")
        partes.append(pd.json_normalize(items, sep="/"))
    if not partes:
        raise ValueError("Ninguna búsqueda devolvió publicaciones")
    return pd.concat(partes, ignore_index=True)


def _datos_por_archivo(url: str) -> pd.DataFrame:
    r = requests.get(_drive_directo(url), timeout=120)
    r.raise_for_status()
    return pd.read_csv(io.BytesIO(r.content), low_memory=False)


async def main() -> None:
    async with Actor:
        cfg = await Actor.get_input() or {}
        rubro = (cfg.get("rubro") or "Sin rubro").strip()
        rubro = rubro[:-4].strip() if rubro.lower().endswith(".csv") else rubro  # Make manda el nombre del archivo
        modo = cfg.get("modo") or ("archivo" if cfg.get("archivo_csv_url") else "busqueda")
        Actor.log.info(f"Rubro: {rubro} · modo: {modo}")

        crudo = _datos_por_archivo(cfg["archivo_csv_url"]) if modo == "archivo" else await _datos_por_busqueda(cfg)

        # ---------- ETL ----------
        plano = aplanar(crudo)
        sin_dup = plano.drop_duplicates("itemId") if "itemId" in plano else plano
        df = metricas_negocio(preparar(crudo, rubro))
        etl_log = {"filas_crudas": int(len(plano)), "duplicados": int(len(plano) - len(sin_dup)),
                   "descartadas_precio": int(len(sin_dup) - len(df)), "filas_finales": int(len(df))}
        Actor.log.info(f"ETL: {etl_log}")

        # ---------- Modelo ----------
        with open(MODELO, "rb") as f:
            artefacto = pickle.load(f)
        prob = artefacto["modelo"].predict_proba(df[FEATURES])[:, 1]
        df["prob_vende_mucho"] = prob.round(4)
        df["pred_vende_mucho"] = (prob >= 0.5).astype(int)

        # ---------- EDA ----------
        # Si el scraper trae vendidos, el target es real; si no, se usa la predicción.
        tiene_vendidos = df["vendidos"].notna().mean() > 0.5
        df["vende_mucho"] = target_vende_mucho(df) if tiene_vendidos else df["pred_vende_mucho"]
        eda = eda_resumen(df, etl_log)
        eda["target"] = "real (vendidos)" if tiene_vendidos else "predicho por el modelo"
        await Actor.set_value("EDA_RESUMEN", eda)
        await Actor.set_value("EDA_REPORTE", eda_pdf(df, eda), content_type="application/pdf")
        await Actor.set_value("DATASET_LIMPIO", df.to_csv(index=False), content_type="text/csv")
        Actor.log.info("EDA listo: EDA_RESUMEN, EDA_REPORTE y DATASET_LIMPIO")

        # ---------- Salida ----------
        salida = df[COLUMNAS_SALIDA]
        await Actor.push_data(json.loads(salida.to_json(orient="records", force_ascii=False)))  # NaN → null
        kpis = resumen(df)
        await Actor.set_value("RESUMEN", kpis)
        await Actor.set_value("RESULTADOS_CSV", salida.to_csv(index=False), content_type="text/csv")
        Actor.log.info(f"Listo: {kpis}")
