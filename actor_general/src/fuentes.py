"""Metis · lectura de datos para el actor general.

Los datos siempre entran por el input del actor, de dos formas:
- modo "busqueda": llama al scraper de Mercado Libre en Apify con las búsquedas del rubro.
- modo "archivo": descarga el CSV crudo desde un link (por ejemplo, el de Drive que manda Make).
"""
from __future__ import annotations

import io

import pandas as pd
import requests
from apify import Actor


def _drive_directo(url: str) -> str:
    """Convierte un link de Google Drive en link de descarga directa."""
    if "drive.google.com" in url and "/d/" in url:
        file_id = url.split("/d/")[1].split("/")[0]
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return url


async def datos_por_busqueda(rubro_input: dict) -> pd.DataFrame:
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


def datos_por_archivo(url: str) -> pd.DataFrame:
    r = requests.get(_drive_directo(url), timeout=120)
    r.raise_for_status()
    return pd.read_csv(io.BytesIO(r.content), low_memory=False)
