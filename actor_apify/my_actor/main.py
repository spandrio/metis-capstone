"""Metis · Actor de inferencia (seguridad electrónica).

Flujo de una corrida:
    1. Lee el input: `csv_url`, el CSV crudo del scraper de Mercado Libre (llega desde Drive vía Make).
    2. ETL: limpia y transforma las columnas crudas a las variables del modelo.
    3. EDA: arma un resumen del mercado y lo guarda como EDA_RESUMEN.json.
    4. Inferencia: carga el modelo ya entrenado en el Colab (pickle) y predice `vende_mucho`.
    5. Salida: filas en el dataset del run y OUTPUT.csv en el key-value store (Make lo descarga y lo envía).

El actor NO entrena el modelo: solo lo carga y predice. Tampoco guarda datos propios.
"""
import pandas as pd
from apify import Actor

from .eda import resumen_eda
from .etl import filtrar_precios, preparar_para_modelo
from .modelo import cargar_modelo, predecir


async def main() -> None:
    async with Actor:
        # 1. Input
        actor_input = await Actor.get_input() or {}
        csv_url = actor_input.get("csv_url")
        if not csv_url:
            raise ValueError("Falta pasar 'csv_url' en el input del actor.")

        # 2. ETL
        df_raw = pd.read_csv(csv_url)
        df = filtrar_precios(preparar_para_modelo(df_raw))
        Actor.log.info(f"ETL: {len(df_raw)} filas crudas → {len(df)} filas limpias")

        # 3. EDA
        await Actor.set_value("EDA_RESUMEN.json", resumen_eda(df))

        # 4. Inferencia con el modelo ya entrenado
        df["prediccion"] = predecir(df, cargar_modelo())

        # 5. Salida
        await Actor.push_data(df.where(df.notna(), None).to_dict(orient="records"))
        await Actor.set_value("OUTPUT.csv", df.to_csv(index=False), content_type="text/csv")
        Actor.log.info(f"Listo: {int(df['prediccion'].sum())} de {len(df)} productos con alta rotación predicha")
