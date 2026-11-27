"""Metis · Demo local: estilos, animaciones y componentes visuales.

Todo es HTML, CSS y SVG local: no depende de librerías externas, así que anda sin conexión
(si hay internet carga las fuentes de Google; si no, usa las del sistema).
"""
from __future__ import annotations

import html
import json

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
import streamlit.components.v1 as components

NAVY, NAVY2, NARANJA, NARANJA2 = "#14213D", "#1F3060", "#F28C28", "#B45309"
CREMA, TINTA, GRIS, AZUL = "#F5F4EF", "#14213D", "#5F6673", "#2F5D8C"
FUENTES = ('<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700'
           '&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">')
BASE_IFRAME = f"""{FUENTES}<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:Inter,system-ui,Segoe UI,Arial,sans-serif;color:{TINTA};background:transparent}}
.g{{font-family:'Space Grotesk',Inter,system-ui,sans-serif}}
@keyframes up{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:none}}}}
@keyframes pop{{0%{{transform:scale(.85);opacity:0}}60%{{transform:scale(1.04);opacity:1}}100%{{transform:scale(1)}}}}
</style>"""

# ---------- Plotly con la misma estética ----------
pio.templates["metis"] = go.layout.Template(layout=dict(
    font=dict(family="Inter, Segoe UI, Arial", color=TINTA, size=13),
    title=dict(font=dict(family="Space Grotesk, Inter, Arial", size=17, color=TINTA)),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    colorway=[NARANJA, AZUL, "#8A94A3", NARANJA2, "#7FA7D1"],
    xaxis=dict(gridcolor="#E7E4DA", zeroline=False), yaxis=dict(gridcolor="#E7E4DA", zeroline=False),
    margin=dict(l=10, r=10, t=50, b=10), hoverlabel=dict(font=dict(family="Inter")),
    transition=dict(duration=500, easing="cubic-in-out"),
))
pio.templates.default = "plotly_white+metis"


def inject_css() -> None:
    st.markdown(_sin_vacias(FUENTES + f"""
<style>
html, body, [class*="css"], .stMarkdown, .stText {{ font-family: Inter, system-ui, 'Segoe UI', sans-serif; }}
h1, h2, h3 {{ font-family: 'Space Grotesk', Inter, sans-serif !important; letter-spacing: -.01em; color: {TINTA}; }}
[data-testid="stAppViewContainer"] {{ background: {CREMA}; }}
[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 1.2rem; max-width: 1250px; }}

/* Entrada suave de cada bloque */
@keyframes metisUp {{ from {{ opacity: 0; transform: translateY(16px); }} to {{ opacity: 1; transform: none; }} }}
[data-testid="stMain"] [data-testid="stVerticalBlock"] > div {{ animation: metisUp .55s ease both; }}
[data-testid="stMain"] [data-testid="stVerticalBlock"] > div:nth-child(2) {{ animation-delay: .05s; }}
[data-testid="stMain"] [data-testid="stVerticalBlock"] > div:nth-child(3) {{ animation-delay: .1s; }}
[data-testid="stMain"] [data-testid="stVerticalBlock"] > div:nth-child(4) {{ animation-delay: .15s; }}
[data-testid="stMain"] [data-testid="stVerticalBlock"] > div:nth-child(n+5) {{ animation-delay: .2s; }}

/* Sidebar */
[data-testid="stSidebar"] {{ background: linear-gradient(180deg, {NAVY} 0%, {NAVY2} 100%); }}
[data-testid="stSidebar"] * {{ color: #E9ECF4 !important; }}
[data-testid="stSidebar"] [role="radiogroup"] label {{
  padding: 10px 14px; border-radius: 12px; margin-bottom: 4px; transition: all .2s ease; cursor: pointer; width: 100%;
}}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {{ background: rgba(255,255,255,.08); transform: translateX(3px); }}
[data-testid="stSidebar"] [role="radiogroup"] label[data-selected="true"] {{
  background: linear-gradient(90deg, {NARANJA} 0%, #F5A54F 100%); box-shadow: 0 6px 18px rgba(242,140,40,.35);
}}
[data-testid="stSidebar"] [role="radiogroup"] label[data-selected="true"] * {{ color: {NAVY} !important; font-weight: 600; }}
[data-testid="stSidebar"] [data-testid="stRadioOption"] > div > div:first-child {{ display: none; }}
[data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,.15); }}

/* Métricas como tarjetas */
[data-testid="stMetric"] {{
  background: #FCFBF8; border: 1px solid #E2E0D8; border-radius: 16px; padding: 16px 18px;
  transition: transform .2s ease, box-shadow .2s ease;
}}
[data-testid="stMetric"]:hover {{ transform: translateY(-3px); box-shadow: 0 10px 24px rgba(20,33,61,.10); }}
[data-testid="stMetricValue"] {{ font-family: 'Space Grotesk', Inter, sans-serif; color: {NARANJA2}; font-size: 1.8rem; }}

/* Botones */
.stButton > button, .stDownloadButton > button {{
  border-radius: 12px; border: 1px solid #E2E0D8; font-weight: 600; transition: all .2s ease;
}}
.stButton > button[kind="primary"] {{
  background: linear-gradient(90deg, {NARANJA} 0%, #F5A54F 100%); color: {NAVY}; border: 0;
  padding: .7rem 1.6rem; box-shadow: 0 8px 22px rgba(242,140,40,.35);
}}
.stButton > button[kind="primary"]:hover {{ transform: translateY(-2px) scale(1.02); box-shadow: 0 12px 28px rgba(242,140,40,.45); }}
.stDownloadButton > button:hover {{ border-color: {NARANJA}; color: {NARANJA2}; transform: translateY(-2px); }}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{ gap: 6px; }}
.stTabs [data-baseweb="tab"] {{ border-radius: 10px 10px 0 0; padding: 8px 16px; transition: background .2s; }}
.stTabs [data-baseweb="tab"]:hover {{ background: #ECE9DF; }}
.stTabs [aria-selected="true"] {{ color: {NARANJA2} !important; }}
.stTabs [data-baseweb="tab-highlight"] {{ background: {NARANJA}; }}

[data-testid="stExpander"], [data-testid="stDataFrame"] {{ border-radius: 14px; overflow: hidden; }}
[data-testid="stExpander"] {{ background: #FCFBF8; }}

/* Encabezado de sección */
.m-head {{ margin: 4px 0 14px; }}
.m-eyebrow {{ font-size: 13px; font-weight: 600; letter-spacing: 2px; text-transform: uppercase; color: {NARANJA2}; }}
.m-title {{ font-family: 'Space Grotesk', Inter, sans-serif; font-size: 40px; font-weight: 700; color: {TINTA}; line-height: 1.1; margin: 4px 0 6px; }}
.m-sub {{ color: {GRIS}; font-size: 17px; max-width: 900px; }}
.m-steps {{ display: flex; gap: 10px; margin-top: 14px; flex-wrap: wrap; }}
.m-step {{ display: flex; align-items: center; gap: 8px; background: #FCFBF8; border: 1px solid #E2E0D8;
  border-radius: 999px; padding: 6px 14px 6px 6px; font-size: 14px; color: {TINTA}; }}
.m-step b {{ display: inline-grid; place-items: center; width: 24px; height: 24px; border-radius: 50%;
  background: {NAVY}; color: #fff; font-size: 12px; }}

/* Tarjetas de producto */
.m-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px; }}
.m-card {{ background: #FCFBF8; border: 1px solid #E2E0D8; border-radius: 16px; padding: 16px; display: flex;
  flex-direction: column; gap: 8px; transition: transform .2s ease, box-shadow .2s ease; animation: metisUp .5s ease both; }}
.m-card:hover {{ transform: translateY(-4px); box-shadow: 0 14px 28px rgba(20,33,61,.12); border-color: {NARANJA}; }}
.m-card .cat {{ font-size: 12px; letter-spacing: 1px; text-transform: uppercase; color: {NARANJA2}; font-weight: 600; }}
.m-card .tit {{ font-weight: 600; font-size: 15px; line-height: 1.3; color: {TINTA}; min-height: 40px; }}
.m-card .row {{ display: flex; justify-content: space-between; font-size: 13px; color: {GRIS}; }}
.m-card .precio {{ font-family: 'Space Grotesk', Inter, sans-serif; font-size: 22px; font-weight: 700; color: {TINTA}; }}
.m-bar {{ height: 8px; background: #ECE9DF; border-radius: 99px; overflow: hidden; }}
.m-bar > span {{ display: block; height: 100%; border-radius: 99px; background: linear-gradient(90deg, {NARANJA}, #F5A54F);
  animation: metisBar 1.1s cubic-bezier(.2,.8,.2,1) both; }}
@keyframes metisBar {{ from {{ width: 0 !important; }} }}
.m-chip {{ display: inline-block; font-size: 12px; padding: 2px 10px; border-radius: 99px; background: #E8EEF6; color: {AZUL}; font-weight: 600; }}
.m-chip.ok {{ background: #FDEBD8; color: {NARANJA2}; }}
.m-card a {{ color: {AZUL}; font-size: 13px; text-decoration: none; font-weight: 600; }}
</style>
"""), unsafe_allow_html=True)


def _sin_vacias(texto: str) -> str:
    """Markdown corta los bloques HTML en las líneas vacías: se sacan para que el CSS se aplique entero."""
    return "\n".join(linea for linea in texto.splitlines() if linea.strip())


def header(eyebrow: str, titulo: str, sub: str = "", pasos: list[str] | None = None) -> None:
    pasos_html = ""
    if pasos:
        pasos_html = '<div class="m-steps">' + "".join(
            f'<span class="m-step"><b>{i}</b>{html.escape(p)}</span>' for i, p in enumerate(pasos, 1)) + "</div>"
    st.markdown(f'<div class="m-head"><div class="m-eyebrow">{eyebrow}</div><div class="m-title">{titulo}</div>'
                f'<div class="m-sub">{sub}</div>{pasos_html}</div>', unsafe_allow_html=True)


def hero() -> None:
    """Portada animada: el flujo completo con datos viajando entre las etapas."""
    nodos = [("Mercado Libre", "publicaciones"), ("Apify", "scraper"), ("Make", "orquesta"),
             ("Actor Metis", "ETL · EDA · modelo"), ("Cliente", "mail y tablero")]
    xs = [70, 250, 430, 640, 850]
    caja = "".join(
        f'<g class="n" style="animation-delay:{.15 + i * .18}s"><rect x="{x - 78}" y="128" width="156" height="64" rx="16"/>'
        f'<text x="{x}" y="156" class="t1">{a}</text><text x="{x}" y="176" class="t2">{b}</text></g>'
        for i, ((a, b), x) in enumerate(zip(nodos, xs)))
    lineas = "".join(f'<path id="p{i}" d="M{xs[i] + 78} 160 L{xs[i + 1] - 78} 160" class="l"/>' for i in range(4))
    puntos = "".join(
        f'<circle r="5" class="d"><animateMotion dur="1.6s" begin="{i * .4 + k * .8}s" repeatCount="indefinite">'
        f'<mpath href="#p{i}"/></animateMotion></circle>' for i in range(4) for k in range(2))
    contadores = [("1102", "publicaciones relevadas", 0, ""), ("1077", "productos en el dataset limpio", 0, ""),
                  ("0.917", "accuracy del modelo", 3, ""), ("7.1", "dentro de ±10 % del promedio", 1, " %")]
    kp = "".join(f'<div class="k" style="animation-delay:{.9 + i * .12}s"><div class="v g" data-v="{v}" data-d="{d}" '
                 f'data-s="{s}">0</div><div class="lb">{lb}</div></div>' for i, (v, lb, d, s) in enumerate(contadores))
    components.html(BASE_IFRAME + f"""
<style>
.hero{{position:relative;border-radius:22px;overflow:hidden;padding:30px 34px 26px;color:#F5F4EF;
  background:radial-gradient(1200px 400px at 10% -10%,#2A3F75 0%,transparent 60%),
             radial-gradient(800px 300px at 110% 120%,rgba(242,140,40,.28) 0%,transparent 60%),{NAVY};}}
.hero:before{{content:"";position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.04) 1px,transparent 1px),
  linear-gradient(90deg,rgba(255,255,255,.04) 1px,transparent 1px);background-size:36px 36px;
  animation:grid 18s linear infinite}}
@keyframes grid{{to{{background-position:36px 36px}}}}
.top{{position:relative;display:flex;justify-content:space-between;align-items:flex-end;gap:20px;flex-wrap:wrap}}
.ey{{font-size:12px;letter-spacing:2.5px;text-transform:uppercase;color:{NARANJA};font-weight:600;animation:up .5s both}}
h1{{font-size:64px;line-height:1;margin:6px 0 8px;animation:up .6s .05s both}}
h1 span{{background:linear-gradient(90deg,#fff,{NARANJA});-webkit-background-clip:text;background-clip:text;color:transparent}}
.sub{{font-size:18px;color:#C9D0E0;max-width:620px;animation:up .6s .15s both}}
.sub b{{color:#fff;font-weight:600}}
svg{{position:relative;width:100%;height:auto;margin-top:8px}}
.n{{animation:pop .6s both;transform-origin:center;transform-box:fill-box}}
.n rect{{fill:rgba(255,255,255,.06);stroke:rgba(255,255,255,.22);stroke-width:1.2}}
.n:nth-child(4) rect{{fill:rgba(242,140,40,.16);stroke:{NARANJA}}}
.t1{{fill:#fff;font:600 15px Inter,system-ui;text-anchor:middle}}
.t2{{fill:#AEB7CB;font:12px Inter,system-ui;text-anchor:middle}}
.l{{stroke:rgba(255,255,255,.25);stroke-width:2;stroke-dasharray:6 6;fill:none;animation:dash 1.2s linear infinite}}
@keyframes dash{{to{{stroke-dashoffset:-24}}}}
.d{{fill:{NARANJA};filter:drop-shadow(0 0 6px {NARANJA})}}
.ks{{position:relative;display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:6px}}
.k{{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);border-radius:14px;padding:12px 14px;animation:up .6s both}}
.v{{font-size:30px;font-weight:700;color:{NARANJA}}}
.lb{{font-size:13px;color:#C9D0E0}}
</style>
<div class="hero">
  <div class="top"><div><div class="ey">Capstone · Samsung Innovation Campus 2026</div>
  <h1 class="g"><span>Metis</span></h1>
  <div class="sub">Qué vender, <b>a qué precio</b> y <b>cuándo promocionar</b>, con datos reales de Mercado Libre.</div></div></div>
  <svg viewBox="-20 110 980 100">{lineas}{caja}{puntos}</svg>
  <div class="ks">{kp}</div>
</div>
<script>
document.querySelectorAll('.v').forEach((el,i)=>{{
  const fin=parseFloat(el.dataset.v),d=+el.dataset.d,s=el.dataset.s,t0=performance.now()+900+i*120,dur=1400;
  const f=n=>n.toLocaleString('es-AR',{{minimumFractionDigits:d,maximumFractionDigits:d}})+s;
  const paso=t=>{{const p=Math.min(Math.max((t-t0)/dur,0),1),e=1-Math.pow(1-p,3);el.textContent=f(fin*e);if(p<1)requestAnimationFrame(paso)}};
  requestAnimationFrame(paso);
}});
</script>""", height=445)


def pipeline(etapas: list[tuple[str, str]], segundos: float | None = None) -> None:
    """Etapas del actor que se van encendiendo una tras otra."""
    n = len(etapas)
    pasos = "".join(
        f'<div class="s" style="--d:{i * .45}s"><div class="c"><span>{i + 1}</span></div>'
        f'<div class="tt">{html.escape(a)}</div><div class="dd">{html.escape(b)}</div></div>'
        + (f'<div class="bar" style="--d:{i * .45 + .25}s"><i></i></div>' if i < n - 1 else "")
        for i, (a, b) in enumerate(etapas))
    fin = f'<div class="ok" style="--d:{n * .45}s">Listo en {segundos:.1f} s</div>' if segundos is not None else ""
    components.html(BASE_IFRAME + f"""
<style>
.w{{background:#FCFBF8;border:1px solid #E2E0D8;border-radius:18px;padding:18px 18px 14px}}
.r{{display:flex;align-items:flex-start}}
.s{{flex:1 1 0;min-width:0;text-align:center;opacity:.35;animation:on .4s var(--d) forwards}}
@keyframes on{{to{{opacity:1}}}}
.c{{width:46px;height:46px;margin:0 auto 8px;border-radius:50%;display:grid;place-items:center;
  background:#ECE9DF;color:{GRIS};font-weight:700;animation:lit .5s var(--d) forwards}}
@keyframes lit{{to{{background:{NARANJA};color:{NAVY};box-shadow:0 0 0 6px rgba(242,140,40,.18)}}}}
.tt{{font-weight:600;font-size:14px;color:{TINTA}}}
.dd{{font-size:12.5px;color:{GRIS};margin-top:2px;line-height:1.3}}
.bar{{flex:0 0 36px;height:4px;background:#ECE9DF;border-radius:4px;margin-top:21px;overflow:hidden}}
.bar i{{display:block;height:100%;width:0;background:{NARANJA};animation:fill .45s var(--d) forwards}}
@keyframes fill{{to{{width:100%}}}}
.ok{{margin-top:10px;text-align:right;font-size:13px;font-weight:600;color:{NARANJA2};opacity:0;animation:on .4s var(--d) forwards}}
</style>
<div class="w"><div class="r">{pasos}</div>{fin}</div>""", height=180 if segundos is not None else 160)


def tarjetas_productos(df, n: int = 9) -> None:
    filas = []
    for i, (_, r) in enumerate(df.head(n).iterrows()):
        prob = float(r.get("prob_vende_mucho", 0) or 0)
        dist = float(r.get("distancia_precio_prom_pct", 0) or 0)
        banda = "dentro del promedio" if abs(dist) <= 10 else ("más barato que su categoría" if dist < 0 else "más caro")
        url = r.get("url") or ""
        link = f'<a href="{html.escape(str(url))}" target="_blank">Ver publicación →</a>' if url else ""
        filas.append(f"""
<div class="m-card" style="animation-delay:{i * .06}s">
  <div class="cat">{html.escape(str(r.get('categoria', '')))}</div>
  <div class="tit">{html.escape(str(r.get('titulo', ''))[:80])}</div>
  <div class="row"><span class="precio">$ {f"{int(r['precio']):,}".replace(",", ".")}</span><span class="m-chip ok">score {r.get('score_costo_beneficio', 0):.0f}</span></div>
  <div class="row"><span>{html.escape(str(r.get('marca', '')))}</span><span class="m-chip">{dist:+.0f} % · {banda}</span></div>
  <div class="row"><span>Probabilidad de alta rotación</span><b>{prob * 100:.0f} %</b></div>
  <div class="m-bar"><span style="width:{prob * 100:.0f}%"></span></div>
  {link}
</div>""")
    st.markdown('<div class="m-grid">' + "".join(filas) + "</div>", unsafe_allow_html=True)


def banda_visual(pcts: dict[str, float], rot: dict[str, float]) -> None:
    """Barra animada de la métrica de negocio: abajo / dentro / arriba."""
    colores = {"abajo": AZUL, "dentro": NARANJA, "arriba": "#8A94A3"}
    nombres = {"abajo": "Más de 10 % abajo", "dentro": "Dentro de ±10 %", "arriba": "Más de 10 % arriba"}
    seg = "".join(f'<div class="sg" style="--w:{pcts[b]}%;--c:{colores[b]};--d:{i * .25}s" title="{nombres[b]}">'
                  f'<span>{pcts[b]:.1f} %</span></div>' for i, b in enumerate(["abajo", "dentro", "arriba"]))
    leyenda = "".join(f'<div class="lg"><i style="background:{colores[b]}"></i><div><b>{nombres[b]}</b><br>'
                      f'{pcts[b]:.1f} % del mercado · {rot[b]:.1f} % rota mucho</div></div>'
                      for b in ["abajo", "dentro", "arriba"])
    components.html(BASE_IFRAME + f"""
<style>
.w{{background:#FCFBF8;border:1px solid #E2E0D8;border-radius:18px;padding:18px}}
.b{{display:flex;height:46px;border-radius:12px;overflow:hidden;background:#ECE9DF}}
.sg{{width:0;background:var(--c);display:grid;place-items:center;color:#fff;font-weight:700;font-size:14px;
  white-space:nowrap;overflow:hidden;animation:gw .9s var(--d) cubic-bezier(.2,.8,.2,1) forwards}}
@keyframes gw{{to{{width:max(var(--w),6%)}}}}
.ls{{display:flex;gap:22px;margin-top:14px;flex-wrap:wrap}}
.lg{{display:flex;gap:10px;font-size:13px;color:{GRIS};line-height:1.4}}
.lg i{{width:14px;height:14px;border-radius:4px;margin-top:3px;flex:none}}
.lg b{{color:{TINTA}}}
</style><div class="w"><div class="b">{seg}</div><div class="ls">{leyenda}</div></div>""", height=205)


def json_bonito(d: dict) -> str:
    return json.dumps(d, ensure_ascii=False, indent=2)
