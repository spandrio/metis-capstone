# Metis Analytics · sitio web

Sitio de una sola página con la demo interactiva de Metis. Corre todo en el navegador:

- `assets/datos.js` (y los mismos datos en `assets/mercado.json` y `assets/modelo.json`): las 1.088 publicaciones del relevamiento del 18/11/2026 y el modelo general (Random Forest de 200 árboles) exportado del pickle de `actor_general`.
- Las predicciones del navegador dan exactamente lo mismo que el modelo de scikit-learn.

## Cómo verlo

Doble clic en `index.html`. Necesita internet solo para las fuentes y las animaciones (GSAP).

## Cómo publicarlo

Es un sitio estático: sirve tal cual en GitHub Pages, Vercel o Netlify, sin compilar nada.

## Qué falta configurar

En `app.js`, `CONFIG.email`: el mail que recibe los pedidos de piloto del formulario.
