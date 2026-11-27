"""Metis · EDA automático dentro del actor.

Genera, para cualquier rubro:
- EDA_RESUMEN (JSON): estadísticas, frecuencias, correlaciones, selección de features y métrica de negocio.
- EDA_REPORTE (PDF de 2 páginas): los mismos gráficos listos para subir a Drive con Make.
"""
from __future__ import annotations

import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

AZUL, NARANJA, TINTA, GRIS, GRILLA, PANEL = "#2F5D8C", "#D9822B", "#1F2933", "#5F6B7A", "#E3E7EC", "#F6F7F9"
NUMERICAS = ["precio", "precio_anterior", "descuento_pct", "cuotas_sin_interes", "envio_gratis",
             "tienda_oficial", "es_combo", "rating", "cantidad_resenas"]
LINEALES = ["cantidad_resenas", "rating", "tienda_oficial", "precio", "descuento_pct"]
NO_LINEALES = ["categoria", "marca", "precio_anterior", "cuotas_sin_interes", "es_combo"]


def _fmt(v, d=0):
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _brecha(grupo: pd.Series, y: pd.Series) -> float:
    g = pd.DataFrame({"g": grupo, "y": y}).groupby("g")["y"].agg(["mean", "size"])
    g = g[g["size"] >= 10]
    return round(float((g["mean"].max() - g["mean"].min()) * 100), 1) if len(g) > 1 else 0.0


def seleccion_features(df: pd.DataFrame, target: str = "vende_mucho") -> list[dict]:
    y = df[target]
    filas = [{"feature": f, "tipo": "lineal", "medida": "correlación con el target",
              "valor": round(float(df[f].corr(y)), 3)} for f in LINEALES]
    quint = pd.qcut(df["precio_anterior"], 5, labels=False, duplicates="drop")
    grupos = {"categoria": df["categoria"], "marca": df["marca"], "precio_anterior": quint,
              "cuotas_sin_interes": df["cuotas_sin_interes"], "es_combo": df["es_combo"]}
    filas += [{"feature": f, "tipo": "no lineal", "medida": "brecha de alta rotación entre grupos (pp)",
               "valor": _brecha(grupos[f], y)} for f in NO_LINEALES]
    return filas


def eda_resumen(df: pd.DataFrame, etl_log: dict, target: str = "vende_mucho") -> dict:
    p = df["precio"]
    bandas = (df.groupby("banda_precio")
              .agg(publicaciones=("precio", "size"), alta_rotacion=(target, "mean"))
              .reindex(["abajo", "dentro", "arriba"]).fillna(0))
    return {
        "rubro": str(df["rubro"].iloc[0]),
        "etl": etl_log,
        "precio": {"media": round(float(p.mean())), "mediana": round(float(p.median())), "min": round(float(p.min())),
                   "max": round(float(p.max())), "desvio": round(float(p.std())), "asimetria": round(float(p.skew()), 2)},
        "nulos_rating_completados": int((df["tiene_rating"] == 0).sum()),
        "frecuencia_categoria": df["categoria"].value_counts().to_dict(),
        "top_marcas": df["marca"].value_counts().head(10).to_dict(),
        "pct_alta_rotacion": round(float(df[target].mean() * 100), 1),
        "correlacion": df[NUMERICAS + ["vendidos", target]].corr().round(3).fillna(0).to_dict(),
        "seleccion_features": seleccion_features(df, target),
        "metrica_negocio": {
            "nombre": "distancia del precio al promedio de su categoría (%)",
            "pct_dentro_10": round(float((df["banda_precio"] == "dentro").mean() * 100), 1),
            "bandas": {b: {"pct_publicaciones": round(float(r["publicaciones"] / len(df) * 100), 1),
                           "pct_alta_rotacion": round(float(r["alta_rotacion"] * 100), 1)} for b, r in bandas.iterrows()},
        },
    }


def _estilo():
    plt.rcParams.update({"font.family": "DejaVu Sans", "axes.edgecolor": GRILLA, "axes.labelcolor": GRIS,
                         "xtick.color": GRIS, "ytick.color": GRIS, "axes.titleweight": "bold", "axes.titlesize": 12,
                         "axes.titlecolor": TINTA, "axes.grid": True, "grid.color": GRILLA, "axes.axisbelow": True})


def eda_pdf(df: pd.DataFrame, resumen: dict, target: str = "vende_mucho") -> bytes:
    """Reporte de EDA en PDF (2 páginas) para el rubro analizado."""
    _estilo()
    rubro, n, p = resumen["rubro"], len(df), df["precio"]
    dentro = resumen["metrica_negocio"]["pct_dentro_10"]
    alta = resumen["pct_alta_rotacion"]
    buf = io.BytesIO()
    with PdfPages(buf) as pdf:
        fig = plt.figure(figsize=(16.5, 11.7))
        fig.text(0.06, 0.955, f"Metis · EDA · {rubro}", fontsize=20, fontweight="bold", color=TINTA)
        fig.text(0.06, 0.93, f"De {_fmt(n)} publicaciones, el {_fmt(dentro, 1)} % tiene un precio dentro de ±10 % del "
                 f"promedio de su categoría y el {_fmt(alta, 1)} % tiene alta rotación.", fontsize=11.5, color=GRIS)
        kpis = [("Publicaciones", _fmt(n)), ("Precio promedio", "$ " + _fmt(p.mean())),
                ("Precio mediano", "$ " + _fmt(p.median())), ("Alta rotación", _fmt(alta, 1) + " %"),
                ("Dentro de ±10 % del promedio", _fmt(dentro, 1) + " %")]
        w = 0.88 / 5
        for i, (lab, val) in enumerate(kpis):
            x = 0.06 + i * w
            fig.patches.append(plt.Rectangle((x, 0.835), w - 0.01, 0.07, transform=fig.transFigure, facecolor=PANEL, edgecolor=GRILLA))
            fig.text(x + 0.01, 0.883, lab, fontsize=8.5, color=GRIS)
            fig.text(x + 0.01, 0.849, val, fontsize=15, color=TINTA, fontweight="bold")
        gs = fig.add_gridspec(2, 2, left=0.13, right=0.97, top=0.79, bottom=0.06, hspace=0.38, wspace=0.3)
        ax = fig.add_subplot(gs[0, 0])
        ax.hist(p, bins=40, color=AZUL, edgecolor="white")
        ax.axvline(p.mean(), color=NARANJA, lw=2, ls="--", label=f"media $ {_fmt(p.mean())}")
        ax.axvline(p.median(), color=TINTA, lw=2, label=f"mediana $ {_fmt(p.median())}")
        ax.set_title(f"Distribución del precio · asimetría {_fmt(p.skew(), 2)}", loc="left")
        ax.set_xlabel("precio ($)"); ax.set_ylabel("publicaciones"); ax.legend(frameon=False)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: "$ " + _fmt(v)))
        ax = fig.add_subplot(gs[0, 1])
        ax.hist(df["distancia_precio_prom_pct"].clip(upper=200), bins=np.arange(-100, 220, 20), color=AZUL, edgecolor="white")
        ax.axvspan(-10, 10, color=NARANJA, alpha=0.25, label="±10 % del promedio")
        ax.set_title("Distancia al precio promedio de su categoría (%)", loc="left")
        ax.set_xlabel("distancia % (200 = 200 o más)"); ax.legend(frameon=False)
        for pos, serie, titulo in [(gs[1, 0], df["categoria"].value_counts(), "Publicaciones por categoría"),
                                   (gs[1, 1], df["marca"].value_counts().head(10), "Top 10 marcas")]:
            ax = fig.add_subplot(pos)
            s = serie.sort_values()
            ax.barh([str(i)[:28] for i in s.index], s.values, color=AZUL)
            ax.bar_label(ax.containers[0], labels=[f" {v}" for v in s.values], fontsize=9, color=TINTA)
            ax.set_title(titulo, loc="left"); ax.grid(axis="y", visible=False)
        pdf.savefig(fig); plt.close(fig)

        fig = plt.figure(figsize=(16.5, 11.7))
        fig.text(0.06, 0.955, f"Correlaciones, features y métrica de negocio · {rubro}", fontsize=20, fontweight="bold", color=TINTA)
        gs = fig.add_gridspec(2, 2, left=0.08, right=0.97, top=0.9, bottom=0.08, hspace=0.42, wspace=0.32)
        cols = NUMERICAS + ["vendidos", target]
        corr = df[cols].corr().fillna(0)
        ax = fig.add_subplot(gs[0, 0])
        ax.imshow(corr, cmap=LinearSegmentedColormap.from_list("bo", [NARANJA, "#FFFFFF", AZUL]), vmin=-1, vmax=1)
        ax.set_xticks(range(len(cols))); ax.set_xticklabels(cols, rotation=60, ha="right", fontsize=8)
        ax.set_yticks(range(len(cols))); ax.set_yticklabels(cols, fontsize=8); ax.grid(False)
        for (i, j), v in np.ndenumerate(corr.to_numpy()):
            ax.text(j, i, _fmt(v, 2), ha="center", va="center", fontsize=6.5, color=TINTA)
        ax.set_title("Matriz de correlación (Pearson)", loc="left")
        ax = fig.add_subplot(gs[0, 1]); ax.axis("off")
        ax.set_title("Selección de 10 features (5 lineales y 5 no lineales)", loc="left")
        filas = [[r["feature"], r["tipo"], "correlación" if r["tipo"] == "lineal" else "brecha (pp)",
                  _fmt(r["valor"], 2 if r["tipo"] == "lineal" else 1)] for r in resumen["seleccion_features"]]
        tb = ax.table(cellText=filas, colLabels=["Variable", "Tipo", "Medida", "Valor"], loc="upper left",
                      cellLoc="left", colWidths=[0.36, 0.2, 0.26, 0.14])
        tb.auto_set_font_size(False); tb.set_fontsize(10); tb.scale(1, 1.6)
        for (r, _), cell in tb.get_celld().items():
            cell.set_edgecolor(GRILLA)
            if r == 0:
                cell.set_facecolor(PANEL); cell.set_text_props(fontweight="bold", color=TINTA)
        b = resumen["metrica_negocio"]["bandas"]
        orden = [("abajo", "Más de 10 % abajo"), ("dentro", "Dentro de ±10 %"), ("arriba", "Más de 10 % arriba")]
        ax = fig.add_subplot(gs[1, 0]); x = np.arange(3); w = 0.38
        v1 = [b[k]["pct_publicaciones"] for k, _ in orden]; v2 = [b[k]["pct_alta_rotacion"] for k, _ in orden]
        for vals, off, col, lab in [(v1, -w / 2, GRIS, "% de publicaciones"), (v2, w / 2, AZUL, "% con alta rotación")]:
            bars = ax.bar(x + off, vals, w, color=col, label=lab)
            ax.bar_label(bars, labels=[_fmt(v, 1) + " %" for v in vals], padding=3, fontsize=9, color=TINTA)
        ax.set_xticks(x); ax.set_xticklabels([t for _, t in orden]); ax.legend(frameon=False)
        ax.set_ylim(0, max(v1 + v2) + 12)
        ax.set_title("Métrica de negocio: distancia al precio promedio", loc="left")
        ax = fig.add_subplot(gs[1, 1]); ax.axis("off"); ax.set_title("ETL aplicado", loc="left")
        e = resumen["etl"]
        lineas = [("Filas crudas", _fmt(e["filas_crudas"])), ("Duplicados eliminados", _fmt(e["duplicados"])),
                  ("Sin precio o precio absurdo", _fmt(e["descartadas_precio"])), ("Filas finales", _fmt(e["filas_finales"])),
                  ("Ratings faltantes completados", _fmt(resumen["nulos_rating_completados"])),
                  ("Categorías", _fmt(df["categoria"].nunique()))]
        for i, (k, v) in enumerate(lineas):
            ax.text(0, 0.88 - i * 0.12, k, fontsize=11, color=GRIS, transform=ax.transAxes)
            ax.text(0.55, 0.88 - i * 0.12, v, fontsize=11, color=TINTA, fontweight="bold", transform=ax.transAxes)
        fig.text(0.06, 0.02, "Generado automáticamente por el actor Metis (Apify) · Equipo Metis · SIC 2026", fontsize=8, color=GRIS)
        pdf.savefig(fig); plt.close(fig)
    return buf.getvalue()
