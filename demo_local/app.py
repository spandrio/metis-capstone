"""Metis · Demo local.

Corre en tu compu todo lo que hace el proyecto, con el mismo código del repo:
- Actor de seguridad (el que usa Make): ETL, EDA e inferencia con el modelo del Colab.
- Actor general (multirrubro): ETL, métrica de negocio, score, modelo general y EDA en PDF.
- Modelo y métricas, costos y precio.

Uso:  streamlit run demo_local/app.py   (o doble clic en demo_local/iniciar_demo.bat)
"""
from __future__ import annotations

import importlib.util
import io
import json
import pickle
import sys
import time
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

import ui

RAIZ = Path(__file__).resolve().parents[1]
RAW = RAIZ / "data" / "raw"
PROCESADO = RAIZ / "data" / "processed" / "dataset_seguridad_limpio.csv"
DOCS = RAIZ / "docs"
AZUL, NARANJA, GRIS = "#2F5D8C", "#F28C28", "#8A94A3"

# ---------- Código de los actores, importado tal cual está en el repo ----------
sys.path.insert(0, str(RAIZ / "actor_apify"))
from my_actor import eda as eda_seg  # noqa: E402
from my_actor import etl as etl_seg  # noqa: E402
from my_actor import modelo as modelo_seg  # noqa: E402


def _cargar(nombre: str, ruta: Path):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = mod
    spec.loader.exec_module(mod)
    return mod


core = _cargar("metis_core", RAIZ / "actor_general" / "src" / "metis_core.py")
eda_gen = _cargar("metis_eda_general", RAIZ / "actor_general" / "src" / "eda.py")
MODELO_GENERAL = RAIZ / "actor_general" / "model" / "modelo_general.pickle"
COLUMNAS_SALIDA_GENERAL = [
    "rubro", "busqueda", "categoria", "item_id", "titulo", "marca", "precio", "precio_anterior",
    "descuento_pct", "cuotas_sin_interes", "envio_gratis", "tienda_oficial", "es_combo", "rating",
    "cantidad_resenas", "vendidos", "precio_prom_categoria", "distancia_precio_prom_pct", "banda_precio",
    "score_costo_beneficio", "es_competitivo", "prob_vende_mucho", "pred_vende_mucho", "url",
]

st.set_page_config(page_title="Metis · Demo local", layout="wide")
ui.inject_css()


def fmt(v, d=0):
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pesos(v):
    return "$ " + fmt(v)


# ---------- Datos de entrada ----------
@st.cache_data
def leer_raw(nombres: tuple[str, ...]) -> pd.DataFrame:
    partes = []
    for n in nombres:
        df = pd.read_csv(RAW / n, low_memory=False)
        if "searchQuery" not in df:
            df["searchQuery"] = n.replace(".csv", "").replace("_", " ")
        partes.append(df)
    return pd.concat(partes, ignore_index=True)


def elegir_datos(key: str) -> tuple[pd.DataFrame | None, str]:
    """Selector de input: los CSV crudos del repo, un CSV subido o un link."""
    origen = st.radio("Datos de entrada", ["CSV crudos del repo", "Subir un CSV", "Link a un CSV"],
                      horizontal=True, key=f"origen_{key}")
    if origen == "CSV crudos del repo":
        archivos = sorted(p.name for p in RAW.glob("*.csv"))
        elegidos = st.multiselect("Búsquedas del 18/11/2026", archivos, default=archivos, key=f"raw_{key}")
        if not elegidos:
            return None, ""
        return leer_raw(tuple(elegidos)), "data/raw/" + (elegidos[0] if len(elegidos) == 1 else "*.csv")
    if origen == "Subir un CSV":
        f = st.file_uploader("CSV crudo del scraper de Mercado Libre", type="csv", key=f"up_{key}")
        return (pd.read_csv(f, low_memory=False), f.name) if f else (None, "")
    url = st.text_input("Link de descarga directa del CSV (Drive compartido o raw de GitHub)", key=f"url_{key}",
                        value="https://raw.githubusercontent.com/spandrio/metis-capstone/main/data/raw/cerraduras_inteligentes.csv")
    if not url:
        return None, ""
    if "drive.google.com" in url and "/d/" in url:
        url = f"https://drive.google.com/uc?export=download&id={url.split('/d/')[1].split('/')[0]}"
    try:
        return pd.read_csv(url, low_memory=False), url
    except Exception as e:  # noqa: BLE001
        st.error(f"No se pudo leer el CSV: {e}")
        return None, ""


def bandas_tabla(df: pd.DataFrame, col_rot: str) -> pd.DataFrame:
    t = (df.groupby("banda_precio").agg(publicaciones=("precio", "size"), rot=(col_rot, "mean"))
         .reindex(["abajo", "dentro", "arriba"]).fillna(0))
    t["% de publicaciones"] = (t["publicaciones"] / len(df) * 100).round(1)
    t["% con alta rotación"] = (t["rot"] * 100).round(1)
    t.index = ["Más de 10 % abajo", "Dentro de ±10 %", "Más de 10 % arriba"]
    return t[["publicaciones", "% de publicaciones", "% con alta rotación"]]


# ---------- Navegación ----------
with st.sidebar:
    st.markdown('<div style="font-family:Space Grotesk,Inter,sans-serif;font-size:34px;font-weight:700;'
                'letter-spacing:-.5px">Metis<span style="color:#F28C28">.</span></div>', unsafe_allow_html=True)
    st.caption("Inteligencia competitiva en Mercado Libre")
    seccion = st.radio("Sección", ["Metis", "Actor de seguridad", "Actor general", "Modelo y métricas", "Costos y precio"],
                       label_visibility="collapsed")
    st.divider()
    st.caption("Ramiro Spandrio · Business\n\nHelen Garcia · Solution Engineer\n\nYamila Jordan · Data Scientist")
    st.caption("Capstone · Samsung Innovation Campus 2026")


# =====================================================================
if seccion == "Metis":
    ui.hero()
    st.markdown("""
<div class="m-grid" style="margin-top:6px">
 <div class="m-card"><div class="cat">El problema</div><div class="tit">Precios a ojo y datos que se vencen</div>
  <div style="color:#5F6673;font-size:14px">Relevar a mano cientos de publicaciones lleva horas y cuando terminás los precios ya cambiaron.</div></div>
 <div class="m-card" style="animation-delay:.08s"><div class="cat">Qué hace Metis</div><div class="tit">Mira el mercado todas las semanas</div>
  <div style="color:#5F6673;font-size:14px">Extrae las publicaciones de Mercado Libre, las limpia, las analiza y predice qué productos van a rotar.</div></div>
 <div class="m-card" style="animation-delay:.16s"><div class="cat">Para quién</div><div class="tit">Seguridad hoy, cualquier rubro mañana</div>
  <div style="color:#5F6673;font-size:14px">Cámaras WiFi, alarmas y cerraduras. Con el actor general, el mismo modelo sirve en otros rubros.</div></div>
</div>""", unsafe_allow_html=True)
    st.write("")
    t1, t2, t3 = st.tabs(["Arquitectura", "Flujo de Make", "Qué hay en el repo"])
    with t1:
        st.image(str(DOCS / "arquitectura.png"), width="stretch")
    with t2:
        st.image(str(DOCS / "flujo_make.png"), width="stretch")
        st.caption("Apify · Run an Actor → HTTP · Download a file → Gmail · Send an email. "
                   "El ETL y el EDA están dentro del actor; Make solo lo dispara y mueve los archivos.")
    with t3:
        st.markdown("""
| Carpeta | Qué tiene |
|---|---|
| `actor_apify/` | Actor de seguridad que usa Make: `etl.py`, `eda.py`, `modelo.py` y el pickle del Colab |
| `actor_general/` | Actor multirrubro: ETL general, métrica de negocio, score, modelo general y EDA en PDF |
| `colabs/` | Notebook de Yami: ETL, EDA, score, comparación de 6 modelos y exportación |
| `data/raw/` | Los 4 CSV crudos del scraper |
| `data/processed/` | Dataset limpio de 1.077 productos |
| `dashboard/` | Dashboard en Streamlit |
| `demo_local/` | Esta demo |
""")
    st.info("Empezá por **Actor de seguridad** o **Actor general** en el menú de la izquierda: elegís los datos, "
            "apretás correr y ves el resultado.")


# =====================================================================
elif seccion == "Actor de seguridad":
    ui.header("Actor de Apify · el que usa Make", "Actor de seguridad",
              "Mismo código que <code>actor_apify/my_actor/</code>: limpia el CSV crudo, arma el EDA y predice con el modelo del Colab.",
              ["Elegí los datos", "Corré el actor", "Mirá y descargá el resultado"])

    with st.expander("Contrato del actor: input y output", expanded=False):
        st.markdown("""
**Input:** `csv_url`, el link al CSV crudo del scraper.

**Output:**
- Filas del dataset: cada producto con sus variables limpias y `prediccion` (1 = alta rotación).
- `OUTPUT.csv`: las mismas filas, es el archivo que Make descarga y manda por Gmail.
- `EDA_RESUMEN.json`: resumen del mercado.
""")

    df_raw, origen = elegir_datos("seg")
    if df_raw is not None:
        st.code(json.dumps({"csv_url": origen}, ensure_ascii=False), language="json")

    if df_raw is not None and st.button("Correr actor", type="primary", key="run_seg"):
        t0 = time.perf_counter()
        with st.spinner("Corriendo el actor..."):
            df = etl_seg.filtrar_precios(etl_seg.preparar_para_modelo(df_raw))
            eda = eda_seg.resumen_eda(df)
            artefacto = modelo_seg.cargar_modelo()
            df["prediccion"] = modelo_seg.predecir(df, artefacto)
        st.session_state["seg"] = {"raw": len(df_raw), "df": df, "eda": eda, "seg": time.perf_counter() - t0}

    if "seg" in st.session_state:
        r = st.session_state["seg"]
        df, eda = r["df"], r["eda"]
        neg = core.metricas_negocio(df)
        ui.pipeline([("Input", "csv_url"), ("ETL", f"{fmt(r['raw'])} → {fmt(len(df))} filas"),
                     ("EDA", "EDA_RESUMEN.json"), ("Modelo", f"{fmt(int(df['prediccion'].sum()))} con alta rotación"),
                     ("Output", "OUTPUT.csv para Make")], r["seg"])
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Filas crudas", fmt(r["raw"]))
        c2.metric("Filas limpias", fmt(len(df)))
        c3.metric("Alta rotación predicha", fmt(int(df["prediccion"].sum())))
        c4.metric("Dentro de ±10 % del promedio", f"{fmt((neg['banda_precio'] == 'dentro').mean() * 100, 1)} %")

        t1, t2, t3, t4 = st.tabs(["Output del actor", "EDA", "Métrica de negocio", "EDA_RESUMEN.json"])
        with t1:
            cols = ["title", "marca", "categoria", "precio", "descuento_pct", "cuotas_sin_interes", "envio_gratis",
                    "tienda_oficial", "es_combo", "rating", "cantidad_resenas", "prediccion"]
            cols = [c for c in cols if c in df]
            st.dataframe(df[cols].sort_values("prediccion", ascending=False), width="stretch", height=420)
        with t2:
            a, b = st.columns(2)
            cat = pd.Series(eda["publicaciones_por_categoria"]).rename_axis("categoria").reset_index(name="publicaciones")
            a.plotly_chart(px.bar(cat, x="publicaciones", y="categoria", orientation="h", title="Publicaciones por categoría",
                                  color_discrete_sequence=[AZUL]), width="stretch")
            pr = pd.DataFrame(eda["precio_y_rating_promedio_por_categoria"]).reset_index(names="categoria")
            b.plotly_chart(px.bar(pr, x="precio", y="categoria", orientation="h", title="Precio promedio por categoría",
                                  color_discrete_sequence=[NARANJA]), width="stretch")
            marcas = df["marca"].value_counts().head(10).index
            pm = (df[df["marca"].isin(marcas)].groupby("marca")["precio"].mean().sort_values()
                  .reset_index())
            st.plotly_chart(px.bar(pm, x="precio", y="marca", orientation="h",
                                   title="Precio promedio de las 10 marcas con más publicaciones",
                                   color_discrete_sequence=[AZUL]), width="stretch")
        with t3:
            st.write("**Distancia del precio al promedio de su categoría.** Le dice al comercio si está caro o barato "
                     "frente a su competencia directa.")
            tb = bandas_tabla(neg.assign(rot=df["prediccion"].values), "rot")
            ui.banda_visual(dict(zip(["abajo", "dentro", "arriba"], tb["% de publicaciones"])),
                            dict(zip(["abajo", "dentro", "arriba"], tb["% con alta rotación"])))
            st.caption("En esta tabla la alta rotación es la que predice el modelo.")
        with t4:
            st.json(eda, expanded=False)

        d1, d2, d3 = st.columns(3)
        d1.download_button("Descargar OUTPUT.csv", df.to_csv(index=False).encode("utf-8"), "OUTPUT.csv", "text/csv")
        d2.download_button("Descargar EDA_RESUMEN.json", json.dumps(eda, ensure_ascii=False, indent=2).encode("utf-8"),
                           "EDA_RESUMEN.json", "application/json")
        d3.download_button("Descargar dataset limpio", df.drop(columns="prediccion").to_csv(index=False).encode("utf-8"),
                           "dataset_limpio.csv", "text/csv")


# =====================================================================
elif seccion == "Actor general":
    ui.header("Versión multirrubro", "Actor general",
              "Mismo código que <code>actor_general/src/</code>: compara cada producto con su propia categoría, "
              "así el modelo sirve en cualquier rubro sin reentrenar.",
              ["Escribí el rubro", "Elegí los datos", "Corré y mirá las oportunidades"])

    with st.expander("Contrato del actor: input y output", expanded=False):
        st.markdown("""
**Input:** `rubro` (obligatorio), `modo` (búsqueda o archivo), `busquedas`, `max_por_busqueda`, `archivo_csv_url`.
En esta demo se usa el modo archivo; el modo búsqueda llama al scraper y corre en Apify.

**Output:**
- Dataset con resultados por producto: distancia al promedio, banda de precio, score, probabilidad y predicción.
- `DATASET_LIMPIO` (CSV), `RESULTADOS_CSV` (CSV), `EDA_REPORTE` (PDF), `EDA_RESUMEN` y `RESUMEN` (JSON).
""")

    rubro = st.text_input("Rubro", value="Seguridad electrónica")
    df_raw, origen = elegir_datos("gen")
    if df_raw is not None:
        st.code(json.dumps({"rubro": rubro, "modo": "archivo", "archivo_csv_url": origen}, ensure_ascii=False),
                language="json")

    if df_raw is not None and st.button("Correr actor general", type="primary", key="run_gen"):
        t0 = time.perf_counter()
        with st.spinner("Corriendo el actor general..."):
            plano = core.aplanar(df_raw)
            sin_dup = plano.drop_duplicates("itemId") if "itemId" in plano else plano
            df = core.metricas_negocio(core.preparar(df_raw, rubro))
            etl_log = {"filas_crudas": int(len(plano)), "duplicados": int(len(plano) - len(sin_dup)),
                       "descartadas_precio": int(len(sin_dup) - len(df)), "filas_finales": int(len(df))}
            with open(MODELO_GENERAL, "rb") as f:
                art = pickle.load(f)
            prob = art["modelo"].predict_proba(df[core.FEATURES])[:, 1]
            df["prob_vende_mucho"] = prob.round(4)
            df["pred_vende_mucho"] = (prob >= 0.5).astype(int)
            tiene_vendidos = df["vendidos"].notna().mean() > 0.5
            df["vende_mucho"] = core.target_vende_mucho(df) if tiene_vendidos else df["pred_vende_mucho"]
            eda = eda_gen.eda_resumen(df, etl_log)
            eda["target"] = "real (vendidos)" if tiene_vendidos else "predicho por el modelo"
            pdf = eda_gen.eda_pdf(df, eda)
        st.session_state["gen"] = {"df": df, "eda": eda, "pdf": pdf, "kpis": core.resumen(df), "etl": etl_log,
                                   "seg": time.perf_counter() - t0}

    if "gen" in st.session_state:
        g = st.session_state["gen"]
        df, eda, k = g["df"], g["eda"], g["kpis"]
        ui.pipeline([("Input", f"rubro: {df['rubro'].iloc[0]}"), ("ETL", f"{fmt(g['etl']['filas_crudas'])} → {fmt(len(df))} filas"),
                     ("Métrica y score", "distancia al promedio"), ("Modelo general", f"{fmt(int(df['pred_vende_mucho'].sum()))} con alta rotación"),
                     ("EDA", "reporte en PDF"), ("Output", "CSV, PDF y JSON")], g["seg"])
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Publicaciones", fmt(k["publicaciones"]))
        c2.metric("Precio mediano", pesos(k["precio_mediano"]))
        c3.metric("Dentro de ±10 %", f"{fmt(k['pct_dentro_10'], 1)} %")
        c4.metric("Alta rotación predicha", f"{fmt(k['pct_alta_rotacion_predicha'], 1)} %")
        c5.metric("Competitivos (score ≥ 65)", f"{fmt(k['pct_competitivos'], 1)} %")

        t1, t2, t3, t4 = st.tabs(["Oportunidades", "Métrica de negocio", "EDA", "Resultados completos"])
        with t1:
            st.write("Productos con alta rotación predicha y precio por debajo o dentro del promedio de su categoría.")
            op = df[(df["pred_vende_mucho"] == 1) & (df["banda_precio"] != "arriba")]
            op = op.sort_values(["prob_vende_mucho", "score_costo_beneficio"], ascending=False)
            cats = ["Todas"] + sorted(op["categoria"].unique())
            cat_sel = st.pills("Categoría", cats, default="Todas", key="cat_op") or "Todas"
            vista = op if cat_sel == "Todas" else op[op["categoria"] == cat_sel]
            ui.tarjetas_productos(vista, 9)
            with st.expander(f"Ver las {fmt(len(vista))} oportunidades en tabla"):
                st.dataframe(vista[["categoria", "titulo", "marca", "precio", "distancia_precio_prom_pct",
                                    "score_costo_beneficio", "prob_vende_mucho", "url"]], width="stretch", height=380,
                             column_config={"url": st.column_config.LinkColumn("publicación", display_text="ver")})
        with t2:
            mn = eda["metrica_negocio"]["bandas"]
            ui.banda_visual({b: v["pct_publicaciones"] for b, v in mn.items()},
                            {b: v["pct_alta_rotacion"] for b, v in mn.items()})
            st.caption(f"Target del EDA: {eda['target']}.")
            fig = px.scatter(df, x="distancia_precio_prom_pct", y="score_costo_beneficio", color="banda_precio",
                             hover_data=["titulo", "marca", "precio"], range_x=[-100, 150],
                             color_discrete_map={"abajo": AZUL, "dentro": NARANJA, "arriba": GRIS},
                             title="Distancia al promedio de la categoría vs score de costo-beneficio")
            st.plotly_chart(fig, width="stretch")
        with t3:
            a, b = st.columns(2)
            fc = pd.Series(eda["frecuencia_categoria"]).rename_axis("categoria").reset_index(name="publicaciones")
            a.plotly_chart(px.bar(fc, x="publicaciones", y="categoria", orientation="h", title="Publicaciones por categoría",
                                  color_discrete_sequence=[AZUL]), width="stretch")
            b.plotly_chart(px.histogram(df, x="precio", nbins=40, title="Distribución de precios",
                                        color_discrete_sequence=[NARANJA]), width="stretch")
            st.write("**Selección de features**")
            st.dataframe(pd.DataFrame(eda["seleccion_features"]), width="stretch", hide_index=True)
            st.json({k2: v for k2, v in eda.items() if k2 not in ("correlacion", "seleccion_features")}, expanded=False)
        with t4:
            st.dataframe(df[COLUMNAS_SALIDA_GENERAL], width="stretch", height=420)

        d1, d2, d3, d4 = st.columns(4)
        d1.download_button("DATASET_LIMPIO.csv", df.to_csv(index=False).encode("utf-8"), "DATASET_LIMPIO.csv", "text/csv")
        d2.download_button("RESULTADOS_CSV.csv", df[COLUMNAS_SALIDA_GENERAL].to_csv(index=False).encode("utf-8"),
                           "RESULTADOS_CSV.csv", "text/csv")
        d3.download_button("EDA_REPORTE.pdf", g["pdf"], "EDA_REPORTE.pdf", "application/pdf")
        d4.download_button("RESUMEN.json", json.dumps(k, ensure_ascii=False, indent=2).encode("utf-8"),
                           "RESUMEN.json", "application/json")


# =====================================================================
elif seccion == "Modelo y métricas":
    ui.header("Cómo sabemos que funciona", "Modelo y métricas",
              "Primero la métrica de negocio, después la del modelo.")

    st.subheader("Métrica de negocio")
    st.write("Distancia del precio al promedio de su categoría, calculada sobre el dataset limpio del Colab "
             "(`data/processed/dataset_seguridad_limpio.csv`).")
    dp = pd.read_csv(PROCESADO)
    prom = dp.groupby("categoria")["precio"].transform("mean")
    dist = (dp["precio"] - prom) / prom * 100
    dp["banda_precio"] = pd.cut(dist, [-1e9, -10, 10, 1e9], labels=["abajo", "dentro", "arriba"]).astype(str)
    c1, c2 = st.columns([1, 2])
    c1.metric("Dentro de ±10 % del promedio", f"{fmt((dp['banda_precio'] == 'dentro').mean() * 100, 1)} %")
    c1.caption("KPI para el cliente: el porcentaje de sus productos dentro de esa banda.")
    with c2:
        tb = bandas_tabla(dp, "vende_mucho")
        ui.banda_visual(dict(zip(["abajo", "dentro", "arriba"], tb["% de publicaciones"])),
                        dict(zip(["abajo", "dentro", "arriba"], tb["% con alta rotación"])))

    st.subheader("Modelo de seguridad (Colab)")
    st.write("Target `vende_mucho`: 1 si los vendidos superan la mediana de su categoría. "
             "Balance 27,6 % alta rotación. Los vendidos no entran al modelo para evitar leakage.")
    comp = pd.DataFrame({
        "Modelo": ["Random Forest", "Gradient Boosting", "MLP", "Regresión logística", "KNN", "SVM"],
        "Familia": ["Ensamble", "Ensamble", "Red neuronal", "Clásico", "Clásico", "Clásico"],
        "CV accuracy": [0.918, 0.911, 0.875, 0.830, 0.830, 0.804],
        "Test accuracy": [0.917, 0.917, 0.847, 0.843, 0.824, 0.810],
        "Test F1": [0.830, 0.830, 0.697, 0.691, 0.635, 0.602],
    })
    largo = comp.melt(id_vars=["Modelo", "Familia"], value_vars=["Test accuracy", "Test F1"],
                      var_name="Métrica", value_name="Valor")
    fig = px.bar(largo, x="Valor", y="Modelo", color="Métrica", barmode="group", orientation="h",
                 title="Comparación de los 6 modelos en test", range_x=[0.5, 1],
                 color_discrete_sequence=[NARANJA, AZUL], text="Valor")
    fig.update_yaxes(categoryorder="array", categoryarray=comp["Modelo"][::-1].tolist(), title="")
    fig.update_traces(texttemplate="%{x:.3f}", textposition="outside")
    st.plotly_chart(fig, width="stretch")
    with st.expander("Ver la tabla"):
        st.dataframe(comp, width="stretch", hide_index=True)
    a, b, c, d = st.columns(4)
    a.metric("Accuracy test", "0,917")
    b.metric("F1", "0,83")
    c.metric("Precisión", "0,957")
    d.metric("Recall", "0,733")
    st.caption("Train 0,940 vs CV 0,918: diferencia de 0,022, sin overfitting.")

    art = modelo_seg.cargar_modelo()
    rf = art["pipeline"].named_steps["modelo"]
    imp = pd.Series(rf.feature_importances_, index=art["features"]).sort_values()
    st.plotly_chart(px.bar(imp, orientation="h", title="Importancia de las variables, modelo de seguridad",
                           color_discrete_sequence=[AZUL]).update_layout(showlegend=False, yaxis_title="", xaxis_title=""),
                    width="stretch")

    st.subheader("Modelo general (multirrubro)")
    with open(MODELO_GENERAL, "rb") as f:
        mg = pickle.load(f)["metricas"]
    a, b, c, d = st.columns(4)
    a.metric("Accuracy test", fmt(mg["accuracy_test"], 3))
    b.metric("F1", fmt(mg["f1"], 3))
    c.metric("Precisión", fmt(mg["precision"], 3))
    d.metric("Recall", fmt(mg["recall"], 3))
    st.caption(f"Train {fmt(mg['accuracy_train'], 3)} vs CV {fmt(mg['accuracy_cv'], 3)}. "
               "Usa variables relativas a la categoría, por eso sirve en otros rubros sin reentrenar.")
    imp_g = pd.Series(mg["importancias"]).sort_values()
    st.plotly_chart(px.bar(imp_g, orientation="h", title="Importancia de las variables, modelo general",
                           color_discrete_sequence=[NARANJA]).update_layout(showlegend=False, yaxis_title="", xaxis_title=""),
                    width="stretch")

    st.subheader("Score de costo-beneficio")
    st.write("Es un dato más del análisis competitivo, no la métrica de negocio. Va de 0 a 100 y pondera "
             "precio relativo a la categoría 35 %, rating 30 %, cantidad de reseñas 20 % y promociones 15 %. "
             "Con 65 o más el producto se marca como competitivo.")


# =====================================================================
elif seccion == "Costos y precio":
    ui.header("Negocio", "Costos y precio", "Lo que cuesta correrlo y lo que se cobra.")
    st.dataframe(pd.DataFrame({
        "Concepto": ["Scraping de 1.078 productos", "Costo por 1.000 productos", "Una corrida del actor",
                     "ETL + EDA + inferencia, 1.100 filas", "Make por corrida"],
        "Valor": ["US$ 0,49", "~US$ 0,45", "US$ 0,006", "~6 s", "5 créditos"],
    }), width="stretch", hide_index=True)

    st.subheader("Calculadora")
    a, b, c = st.columns(3)
    rubros = a.number_input("Rubros", 1, 20, 1)
    corridas = b.number_input("Corridas por mes", 1, 31, 4)
    precio = c.number_input("Precio por rubro por mes (US$)", 1, 500, 30)
    costo = rubros * corridas * (0.49 + 0.006)
    ingreso = rubros * precio
    x, y, z = st.columns(3)
    x.metric("Costo mensual", f"US$ {fmt(costo, 2)}")
    y.metric("Ingreso mensual", f"US$ {fmt(ingreso, 0)}")
    z.metric("Margen bruto", f"{fmt((ingreso - costo) / ingreso * 100, 1)} %")
