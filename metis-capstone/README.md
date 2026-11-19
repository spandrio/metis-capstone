# Metis · Inteligencia competitiva para cualquier rubro

**Equipo Metis · Samsung Innovation Campus 2026 · Comisión 1**
Ramiro Spandrio (Business, líder) · Helen Garcia (Solution Engineer) · Yamila Jordan (Data Scientist)

---

## 1. El problema (Business)

Los comercios que venden online ponen precios "a ojo". Para saber cómo están parados revisan a mano cientos de publicaciones de la competencia, los datos se vencen en una semana y terminan llegando tarde a las promos. Pierden ventas por estar caros o margen por estar baratos.

**Primer caso:** seguridad electrónica para el hogar (cámaras WiFi, kits CCTV, alarmas y cerraduras inteligentes).
**Generalidad:** el mismo sistema sirve para cualquier rubro de Mercado Libre. Solo cambia lo que se busca.

**Para quién:** comercios y revendedores multicanal. Cada rol saca su respuesta del mismo tablero:

| Rol | Pregunta que responde |
|---|---|
| Dirección | ¿En qué rubro conviene entrar? |
| Comercial | ¿A qué precio vendo y qué promos lanzo? |
| Compras | ¿Qué productos traigo? |
| Marketing | ¿Cuándo promociono? |

## 2. La solución

```
Google Drive (configuración / CSV) ──► Make ──► Actor Metis (Apify) ──► Google Drive (resultados) ──► Dashboard
                                                   │
                                                   └─ scraper de Mercado Libre (por rubro y búsquedas)
```

1. **Extracción:** el actor busca en Mercado Libre las palabras clave del rubro que le pasemos.
2. **ETL general:** limpia y normaliza cualquier rubro, usando la categoría que trae cada publicación.
3. **Métrica de negocio:** distancia de cada precio al promedio de su categoría.
4. **Modelo:** predice qué productos tienen alta rotación.
5. **Dashboard:** EDA, métrica de negocio, oportunidades y modelo, con filtro por rubro.

## 3. Datos (Data Scientist)

- **Fuente única:** publicaciones de Mercado Libre Argentina extraídas con Apify.
- **Rubro entregado:** seguridad electrónica, 4 búsquedas, ~1.080 publicaciones únicas.
- **ETL:** duplicados, precios a número, precio anterior y % de descuento, cuotas sin interés, envío gratis, tienda oficial, combos detectados en el título, rating faltante con la mediana de su categoría, precios absurdos fuera.
- **Target:** `vende_mucho` = 1 si los vendidos superan el percentil 75 de su categoría.
- **Colab del EDA y el modelo original:** ver carpeta del proyecto en Drive.

### Las 10 features (todas relativas o binarias, por eso sirven en cualquier rubro)

`precio_rel` (precio / mediana de su categoría) · `descuento_pct` · `cuotas_sin_interes` · `envio_gratis` · `tienda_oficial` · `es_combo` · `rating` · `tiene_rating` · `resenas_log` · `resenas_rel`

`vendidos` **no** entra al modelo: de ahí sale el target (evita leakage).

### Modelo general (Random Forest, 200 árboles, profundidad 6)

| Métrica | Valor |
|---|---|
| Accuracy train | 91,0 % |
| Accuracy CV (5 folds) | 89,3 % |
| Diferencia train − CV | 0,017 (sin overfitting, < 0,05) |
| Accuracy test | 93,1 % |
| Precisión | 81,4 % |
| Recall | 96,6 % |
| F1 | 88,4 % |

Reentrenar con más rubros: `python modelo/entrenar_modelo_general.py actor/model/modelo_general.pickle "Rubro A=a1.csv,a2.csv" "Rubro B=b1.csv"`

## 4. Actor de Apify (Solution Engineer)

Carpeta `actor/`. Un solo actor para cualquier rubro.

**Entrada**

| Campo | Qué es |
|---|---|
| `rubro` | Nombre del rubro (ej. "Herramientas eléctricas") |
| `modo` | `busqueda` (busca ahora en Mercado Libre) o `archivo` (analiza un CSV crudo, el que manda Make) |
| `busquedas` | Palabras clave, una por línea |
| `max_por_busqueda` | Publicaciones por búsqueda |
| `archivo_csv_url` | Link del CSV crudo (sirve un link de Drive compartido) |

**Salida**
- Dataset con cada publicación: categoría, precio, distancia al promedio, banda de precio, score de costo-beneficio, probabilidad y predicción de alta rotación.
- `RESUMEN` (KPIs del rubro) y `RESULTADOS_CSV` en el key-value store, para que Make lo suba a Drive.

**Archivos:** `src/main.py` (actor), `src/metis_core.py` (ETL, métrica y features), `model/modelo_general.pickle`, `requirements.txt` (pandas 2.2.3, numpy 2.4.6, scikit-learn 1.6.1), `.actor/` (actor.json, input_schema, dataset_schema), `Dockerfile` (Python 3.13).

**Flujo de Make:** Google Drive (nuevo CSV o planilla de configuración) → Apify "Run an Actor" (Metis) → Apify "Get record" `RESULTADOS_CSV` → Google Drive "Upload a file" (`resultados_<rubro>_<fecha>.csv`).

## 5. Dashboard

Carpeta `dashboard/` (Streamlit). Pestañas: Mercado, EDA y features, Métrica de negocio, Modelo. Filtro por rubro y categoría, y carga del CSV de un rubro nuevo desde la barra lateral.

```
pip install -r dashboard/requirements.txt
streamlit run dashboard/app.py
```

## 6. Métrica de negocio y KPI (Business)

**Distancia del precio al promedio de su categoría (%).** El precio tiene una distribución muy asimétrica (cola larga a la derecha) y cambia mucho entre categorías, por eso se compara cada producto contra el promedio de la suya.

En seguridad, los productos más de 10 % debajo del promedio tienen alta rotación en un tercio de los casos, contra cerca del 13 % de los que están más de 10 % arriba. Solo ~7 % del mercado está dentro de ±10 % del promedio.

**KPI para el cliente:** % de sus productos dentro de ±10 % del promedio del mercado, y % de sus productos con alta rotación.

## 7. Precio (Business)

Costos estimados por rubro (a confirmar con el consumo real de Apify):

| Concepto | Estimado |
|---|---|
| Extracción, ~1.200 publicaciones por corrida | ~US$ 0,60 |
| Actor de inferencia por corrida | ~US$ 0,01 |
| 4 corridas al mes (semanal) | ~US$ 2,50 |
| Make y Google Drive (planes gratuitos) | US$ 0 |

**Precio de venta propuesto**

| Plan | Incluye | Precio |
|---|---|---|
| Rubro | 1 rubro, relevamiento semanal, dashboard y alertas | US$ 30 / mes |
| Multirrubro | hasta 3 rubros (ideal para evaluar entrar a un rubro nuevo) | US$ 75 / mes |

Margen bruto estimado: más del 90 %.

## 8. Próximos pasos

- Correr un segundo rubro de demostración y reentrenar el modelo general con los dos rubros.
- Alertas por mail cuando la competencia lanza cuotas o descuentos.
- Seguimiento semanal de la métrica de negocio por cliente.
