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

import json
import pickle
from pathlib import Path

from apify import Actor

from .eda import eda_pdf, eda_resumen
from .fuentes import datos_por_archivo, datos_por_busqueda
from .metis_core import FEATURES, aplanar, metricas_negocio, preparar, resumen, target_vende_mucho

MODELO = Path(__file__).resolve().parents[1] / "model" / "modelo_general.pickle"

COLUMNAS_SALIDA = [
    "rubro", "busqueda", "categoria", "item_id", "titulo", "marca", "precio", "precio_anterior",
    "descuento_pct", "cuotas_sin_interes", "envio_gratis", "tienda_oficial", "es_combo", "rating",
    "cantidad_resenas", "vendidos", "precio_prom_categoria", "distancia_precio_prom_pct", "banda_precio",
    "score_costo_beneficio", "es_competitivo", "prob_vende_mucho", "pred_vende_mucho", "url",
]


async def main() -> None:
    async with Actor:
        cfg = await Actor.get_input() or {}
        rubro = (cfg.get("rubro") or "Sin rubro").strip()
        rubro = rubro[:-4].strip() if rubro.lower().endswith(".csv") else rubro  # Make manda el nombre del archivo
        modo = cfg.get("modo") or ("archivo" if cfg.get("archivo_csv_url") else "busqueda")
        Actor.log.info(f"Rubro: {rubro} · modo: {modo}")

        crudo = datos_por_archivo(cfg["archivo_csv_url"]) if modo == "archivo" else await datos_por_busqueda(cfg)

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
