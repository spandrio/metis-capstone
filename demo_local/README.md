# Metis · Demo local

Página en Streamlit que corre en tu compu todo lo que hace el proyecto, importando el mismo código de los actores:

| Sección | Qué hace |
|---|---|
| Metis | Problema, arquitectura y flujo de Make |
| Actor de seguridad | Input `csv_url` → ETL (`etl.py`) → EDA (`eda.py`) → inferencia con el pickle del Colab (`modelo.py`). Descarga OUTPUT.csv, EDA_RESUMEN.json y el dataset limpio |
| Actor general | Input `rubro` + CSV → ETL general, métrica de negocio, score y modelo general. Descarga DATASET_LIMPIO, RESULTADOS_CSV, EDA_REPORTE.pdf y RESUMEN.json |
| Modelo y métricas | Métrica de negocio sobre el dataset limpio, comparación de 6 modelos, importancias y modelo general |
| Costos y precio | Costos de Apify y Make y calculadora de margen |

Los datos de entrada pueden ser los 4 CSV crudos de `data/raw/`, un CSV que subas o un link de Drive o GitHub.

## Cómo correrla

**Windows:** doble clic en `demo_local/iniciar_demo.bat`. La primera vez crea el entorno `.venv` e instala todo, tarda unos minutos. Después abre el navegador en `http://localhost:8501`.

**Manual:**

```
python -m venv .venv
.venv\Scripts\activate
pip install -r demo_local/requirements.txt
streamlit run demo_local/app.py
```

Se corre desde la raíz del repo. Necesita Python 3.10 a 3.13. `scikit-learn` queda fijo en 1.6.1 porque es la versión con la que se guardaron los modelos.
