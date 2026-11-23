"""Metis · Dashboard de inteligencia competitiva (Streamlit).

Lee los resultados del actor de Apify (uno o varios rubros) y muestra el EDA,
la métrica de negocio y el modelo. Se puede subir el CSV de un rubro nuevo
desde la barra lateral.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).parent / "data"
AZUL, NARANJA, GRIS, TINTA = "#2F5D8C", "#D9822B", "#8A94A3", "#1F2933"
FEATURES_NUM = ["precio", "precio_anterior", "descuento_pct", "cuotas_sin_interes", "envio_gratis",
                "tienda_oficial", "es_combo", "rating", "cantidad_resenas"]

st.set_page_config(page_title="Metis · Inteligencia competitiva", page_icon="📊", layout="wide")
st.markdown("""
<style>
[data-testid="stMetricValue"] { font-size: 1.7rem; }
.block-container { padding-top: 1.6rem; }
.metis-sub { color: #5F6B7A; margin-top: -0.6rem; }
</style>
""", unsafe_allow_html=True)


def fmt(v, d=0):
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


@st.cache_data
def cargar_base() -> pd.DataFrame:
    partes = [pd.read_csv(p) for p in sorted(DATA.glob("resultados_*.csv"))]
    return pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()


@st.cache_data
def metricas_modelo() -> dict:
    p = DATA / "metricas_modelo.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def alta_rotacion_real(df: pd.DataFrame) -> pd.Series:
    """Misma regla que el actor: vendidos por encima del percentil 75 de su categoría."""
    vend = df["vendidos"].fillna(0)
    umbral = vend.groupby([df["rubro"], df["categoria"]]).transform(lambda s: s.quantile(0.75))
    return ((vend > umbral) | ((vend >= umbral) & (vend > 0) & (umbral > 0))).astype(int)


# ---------- Datos ----------
base = cargar_base()
with st.sidebar:
    st.markdown("## Metis")
    st.caption("Inteligencia competitiva para cualquier rubro de Mercado Libre")
    subido = st.file_uploader("Analizar otro rubro (CSV del actor)", type="csv")
    if subido is not None:
        nuevo = pd.read_csv(subido)
        if "rubro" in nuevo:
            base = pd.concat([base, nuevo], ignore_index=True)
            st.success(f"Agregado: {', '.join(nuevo['rubro'].unique())}")
        else:
            st.error("El CSV no tiene la columna 'rubro'. Usá la salida del actor de Metis.")

if base.empty:
    st.warning("No hay datos. Corré el actor y subí su CSV.")
    st.stop()

base["vende_mucho"] = alta_rotacion_real(base)
with st.sidebar:
    rubros = sorted(base["rubro"].unique())
    rubro = st.selectbox("Rubro", rubros)
    df_r = base[base["rubro"] == rubro]
    cats = sorted(df_r["categoria"].unique())
    sel_cats = st.multiselect("Categorías", cats, default=cats)
    st.divider()
    st.caption("Fuente: publicaciones de Mercado Libre Argentina relevadas con Apify. Equipo Metis · SIC 2026.")

df = df_r[df_r["categoria"].isin(sel_cats)].copy()
if df.empty:
    st.info("Elegí al menos una categoría.")
    st.stop()

# ---------- Encabezado ----------
dentro = (df["banda_precio"] == "dentro").mean() * 100
alta = df["vende_mucho"].mean() * 100
st.title(f"Metis · {rubro}")
st.markdown(
    f"<p class='metis-sub'>De {fmt(len(df))} publicaciones, solo el {fmt(dentro, 1)} % tiene un precio dentro de "
    f"±10 % del promedio de su categoría y el {fmt(alta, 1)} % tiene alta rotación.</p>", unsafe_allow_html=True)

k = st.columns(5)
k[0].metric("Publicaciones", fmt(len(df)))
k[1].metric("Precio promedio", "$ " + fmt(df["precio"].mean()))
k[2].metric("Precio mediano", "$ " + fmt(df["precio"].median()))
k[3].metric("Alta rotación", fmt(alta, 1) + " %")
k[4].metric("En ±10 % del promedio", fmt(dentro, 1) + " %")

t1, t2, t3, t4 = st.tabs(["Mercado", "EDA y features", "Métrica de negocio", "Modelo"])

# ---------- Mercado ----------
with t1:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Distribución del precio")
        fig = px.histogram(df, x="precio", nbins=40, color_discrete_sequence=[AZUL])
        fig.add_vline(df["precio"].mean(), line_dash="dash", line_color=NARANJA,
                      annotation_text=f"media $ {fmt(df['precio'].mean())}")
        fig.add_vline(df["precio"].median(), line_color=TINTA,
                      annotation_text=f"mediana $ {fmt(df['precio'].median())}", annotation_position="bottom right")
        fig.update_layout(xaxis_title="precio ($)", yaxis_title="publicaciones", bargap=0.05, margin=dict(t=10))
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"Asimetría {fmt(df['precio'].skew(), 2)}: pocos productos muy caros suben el promedio.")
    with c2:
        st.subheader("Distancia al precio promedio de su categoría")
        fig = px.histogram(df, x=df["distancia_precio_prom_pct"].clip(upper=200), nbins=30, color_discrete_sequence=[AZUL])
        fig.add_vrect(x0=-10, x1=10, fillcolor=NARANJA, opacity=0.25, line_width=0, annotation_text="±10 %")
        fig.update_layout(xaxis_title="distancia % (200 = 200 o más)", yaxis_title="publicaciones", bargap=0.05, margin=dict(t=10))
        st.plotly_chart(fig, use_container_width=True)
    c3, c4 = st.columns(2)
    with c3:
        st.subheader("Publicaciones por categoría")
        cat = df["categoria"].value_counts().sort_values()
        fig = px.bar(x=cat.values, y=cat.index, orientation="h", text=cat.values, color_discrete_sequence=[AZUL])
        fig.update_layout(xaxis_title="publicaciones", yaxis_title="", margin=dict(t=10))
        st.plotly_chart(fig, use_container_width=True)
    with c4:
        st.subheader("Top 10 marcas")
        mar = df["marca"].value_counts().head(10).sort_values()
        fig = px.bar(x=mar.values, y=mar.index, orientation="h", text=mar.values, color_discrete_sequence=[AZUL])
        fig.update_layout(xaxis_title="publicaciones", yaxis_title="", margin=dict(t=10))
        st.plotly_chart(fig, use_container_width=True)
    st.subheader("Precio por categoría")
    fig = px.box(df, x="categoria", y="precio", color_discrete_sequence=[AZUL], points=False)
    fig.update_layout(xaxis_title="", yaxis_title="precio ($)", margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)

# ---------- EDA y features ----------
with t2:
    st.subheader("Matriz de correlación")
    cols = FEATURES_NUM + ["vendidos", "vende_mucho"]
    corr = df[cols].corr().round(2)
    fig = px.imshow(corr, text_auto=True, color_continuous_scale=[NARANJA, "#FFFFFF", AZUL], zmin=-1, zmax=1, aspect="auto")
    fig.update_layout(margin=dict(t=10), height=560)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Vendidos se muestra como referencia: no entra al modelo porque de ahí sale el target.")

    st.subheader("Selección de 10 features (5 lineales y 5 no lineales)")
    y = df["vende_mucho"]
    lin = (df[["cantidad_resenas", "rating", "tienda_oficial", "precio", "descuento_pct"]]
           .corrwith(y).rename("valor").reset_index().rename(columns={"index": "feature"}))
    lin["tipo"], lin["cómo se midió"] = "lineal", "correlación con el target"

    def brecha(s):
        g = pd.DataFrame({"g": s, "y": y}).groupby("g")["y"].agg(["mean", "size"])
        g = g[g["size"] >= 10]
        return (g["mean"].max() - g["mean"].min()) * 100 if len(g) > 1 else 0.0

    q = pd.qcut(df["precio_anterior"], 5, labels=False, duplicates="drop")
    nol = pd.DataFrame({
        "feature": ["categoria", "marca", "precio_anterior", "cuotas_sin_interes", "es_combo"],
        "valor": [brecha(df["categoria"]), brecha(df["marca"]), brecha(q), brecha(df["cuotas_sin_interes"]), brecha(df["es_combo"])],
    })
    nol["tipo"], nol["cómo se midió"] = "no lineal", "brecha de alta rotación entre grupos (pp)"
    tabla = pd.concat([lin, nol])[["feature", "tipo", "cómo se midió", "valor"]]
    tabla["valor"] = tabla["valor"].round(2)
    st.dataframe(tabla, hide_index=True, use_container_width=True)

# ---------- Métrica de negocio ----------
with t3:
    st.subheader("Distancia al precio promedio de la categoría")
    orden = {"abajo": "Más de 10 % abajo", "dentro": "Dentro de ±10 %", "arriba": "Más de 10 % arriba"}
    b = (df.groupby("banda_precio").agg(publicaciones=("precio", "size"), alta=("vende_mucho", "mean"))
         .reindex(list(orden)).fillna(0))
    b["% publicaciones"] = b["publicaciones"] / len(df) * 100
    b["% con alta rotación"] = b["alta"] * 100
    b.index = [orden[i] for i in b.index]
    fig = go.Figure([
        go.Bar(name="% de publicaciones", x=b.index, y=b["% publicaciones"], marker_color=GRIS,
               text=[fmt(v, 1) + " %" for v in b["% publicaciones"]], textposition="outside"),
        go.Bar(name="% con alta rotación", x=b.index, y=b["% con alta rotación"], marker_color=AZUL,
               text=[fmt(v, 1) + " %" for v in b["% con alta rotación"]], textposition="outside"),
    ])
    fig.update_layout(barmode="group", yaxis_title="%", margin=dict(t=10), legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("**KPI para el cliente:** % de sus productos dentro de ±10 % del promedio del mercado y % de productos con alta rotación.")

    st.subheader("Qué vender: mejores oportunidades")
    st.caption("Productos con alta probabilidad de rotación y buen costo-beneficio. Sirve para armar el surtido y los precios de referencia.")
    top = (df.sort_values(["prob_vende_mucho", "score_costo_beneficio"], ascending=False)
           [["categoria", "titulo", "marca", "precio", "distancia_precio_prom_pct", "score_costo_beneficio", "prob_vende_mucho", "url"]]
           .head(15))
    st.dataframe(top, hide_index=True, use_container_width=True,
                 column_config={"url": st.column_config.LinkColumn("publicación", display_text="ver"),
                                "prob_vende_mucho": st.column_config.ProgressColumn("prob. alta rotación", min_value=0, max_value=1),
                                "precio": st.column_config.NumberColumn("precio", format="$ %d"),
                                "distancia_precio_prom_pct": st.column_config.NumberColumn("distancia al promedio %", format="%.1f"),
                                "score_costo_beneficio": st.column_config.NumberColumn("score", format="%.1f")})

    st.subheader("Precio relativo vs. score de costo-beneficio")
    fig = px.scatter(df, x="distancia_precio_prom_pct", y="score_costo_beneficio", color="categoria",
                     hover_data=["titulo", "precio"], opacity=0.7)
    fig.update_layout(xaxis_title="distancia al promedio de la categoría (%)", yaxis_title="score (0-100)", margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)

# ---------- Modelo ----------
with t4:
    m = metricas_modelo()
    st.subheader("Modelo general: Random Forest")
    st.caption("Usa variables relativas a cada categoría, por eso sirve para cualquier rubro. "
               f"Entrenado con: {', '.join(m.get('rubros', []))}.")
    if m:
        c = st.columns(6)
        c[0].metric("Accuracy train", fmt(m["accuracy_train"] * 100, 2) + " %")
        c[1].metric("Accuracy CV", fmt(m["accuracy_cv"] * 100, 2) + " %")
        c[2].metric("Dif. train − CV", fmt(m["dif_train_cv"], 3))
        c[3].metric("Accuracy test", fmt(m["accuracy_test"] * 100, 2) + " %")
        c[4].metric("Precisión", fmt(m["precision"] * 100, 2) + " %")
        c[5].metric("Recall", fmt(m["recall"] * 100, 2) + " %")
        st.caption("Regla de la clase: diferencia train − CV menor a 0,05, sin overfitting.")
        c1, c2 = st.columns(2)
        with c1:
            cm = np.array(m["matriz_confusion"])
            fig = px.imshow(cm, text_auto=True, x=["pred. no", "pred. sí"], y=["real no", "real sí"],
                            color_continuous_scale=["#FFFFFF", AZUL])
            fig.update_layout(title="Matriz de confusión (test)", coloraxis_showscale=False, margin=dict(t=40))
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            imp = pd.Series(m["importancias"]).sort_values()
            fig = px.bar(x=imp.values, y=imp.index, orientation="h", color_discrete_sequence=[AZUL])
            fig.update_layout(title="Importancia de las variables", xaxis_title="", yaxis_title="", margin=dict(t=40))
            st.plotly_chart(fig, use_container_width=True)
