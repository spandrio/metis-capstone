/* Metis Analytics · sitio y demo interactiva.
   Todo corre en el navegador con los datos reales del relevamiento (assets/mercado.json)
   y el modelo general exportado del pickle (assets/modelo.json). */
const CONFIG = {
  // Mail del equipo que recibe los pedidos de piloto. Si queda vacío, el formulario muestra el aviso igual.
  email: 'ramirospandrio@gmail.com'
};

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const fmt = (v, d = 0) => Number(v).toLocaleString('es-AR', { minimumFractionDigits: d, maximumFractionDigits: d });
const pesos = v => '$\u00a0' + fmt(Math.round(v));
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const G = window.gsap;
if (G && window.ScrollTrigger) G.registerPlugin(ScrollTrigger);

/* ---------------- Stickers dibujados (originales) ---------------- */
const BLOB = 'M52 4c14 1 30 8 38 20s9 30 3 43-19 26-34 28-31 0-42-9S-1 62 2 47 14 15 25 9s18-6 27-5z';
const STK = {
  etiqueta: { bg: '#FFB8C8', ink: '#7A1E3A', d: '<path d="M30 30h30l18 18-30 30-18-18z" fill="#fff" stroke="INK" stroke-width="4" stroke-linejoin="round"/><circle cx="40" cy="40" r="5" fill="none" stroke="INK" stroke-width="4"/><path d="M52 52c4-3 9-1 9 3s-9 3-9 7 6 5 9 2M56 46v4M56 64v4" fill="none" stroke="INK" stroke-width="3.5" stroke-linecap="round"/>' },
  rayo: { bg: '#8FB7FF', ink: '#14275E', d: '<path d="M56 16 30 54h18l-6 30 28-40H52z" fill="#FFE86B" stroke="INK" stroke-width="4" stroke-linejoin="round"/>' },
  grafico: { bg: '#D7F36B', ink: '#2F4A0A', d: '<path d="M22 74V26M22 74h56" fill="none" stroke="INK" stroke-width="4" stroke-linecap="round"/><path d="M28 64l14-14 10 8 18-22" fill="none" stroke="INK" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M60 34h11v11" fill="none" stroke="INK" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>' },
  lupa: { bg: '#D7F36B', ink: '#2F4A0A', d: '<circle cx="44" cy="42" r="17" fill="#fff" stroke="INK" stroke-width="4.5"/><path d="M57 55l17 17" stroke="INK" stroke-width="7" stroke-linecap="round"/><path d="M36 38c2-4 5-6 9-6" fill="none" stroke="INK" stroke-width="3" stroke-linecap="round"/><path d="M76 20l2 6 6 2-6 2-2 6-2-6-6-2 6-2z" fill="INK"/>' },
  carrito: { bg: '#FFC58C', ink: '#6B330A', d: '<path d="M18 26h10l8 32h32l7-22H32" fill="none" stroke="INK" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/><circle cx="40" cy="70" r="5" fill="INK"/><circle cx="64" cy="70" r="5" fill="INK"/><path d="M44 40l6 6 12-12" fill="none" stroke="INK" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>' },
  estrella: { bg: '#9FE3C9', ink: '#0F4A35', d: '<path d="M50 18l7 22 22 7-22 7-7 22-7-22-22-7 22-7z" fill="#fff" stroke="INK" stroke-width="4" stroke-linejoin="round"/><circle cx="76" cy="22" r="4" fill="INK"/><circle cx="24" cy="76" r="3" fill="INK"/>' }
};
$$('[data-sticker]').forEach(el => {
  const s = STK[el.dataset.sticker]; if (!s) return;
  el.innerHTML = `<svg viewBox="-4 -4 108 108" width="100%" height="100%"><path d="${BLOB}" fill="${s.bg}" stroke="#fff" stroke-width="5"/>${s.d.replaceAll('INK', s.ink)}</svg>`;
});

/* ---------------- Datos ---------------- */
let MERCADO = [], MODELO = null;
(window.METIS_MERCADO ? Promise.resolve([window.METIS_MERCADO, window.METIS_MODELO]) : Promise.all([fetch('assets/mercado.json').then(r => r.json()), fetch('assets/modelo.json').then(r => r.json())]))
  .then(([m, mod]) => {
    MERCADO = m.rows.map(r => Object.fromEntries(m.cols.map((c, i) => [c, r[i]])));
    MODELO = mod;
    iniciarDatos();
  })
  .catch(() => { $('#verCaro').textContent = 'Abrí la página desde un servidor para cargar los datos.'; });

const predecir = x => {
  let s = 0;
  for (const t of MODELO.trees) { let n = 0; while (t.l[n] !== -1) n = x[t.f[n]] <= t.t[n] ? t.l[n] : t.r[n]; s += t.p[n]; }
  return s / MODELO.trees.length;
};
const CATS_DEMO = ['Cámaras / Kits CCTV', 'Cerraduras digitales', 'Alarmas inteligentes', 'Accesorios'];
const NOMBRE_CORTO = { 'Cámaras / Kits CCTV': 'Cámaras y CCTV', 'Cerraduras digitales': 'Cerraduras', 'Alarmas inteligentes': 'Alarmas', 'Accesorios': 'Accesorios' };
const banda = d => d < -10 ? 'abajo' : d > 10 ? 'arriba' : 'dentro';

function iniciarDatos() {
  heroFlotantes(); ticker(); mail(); demoCaro(); demoModelo(); oportunidades(); barrasModelos();
}

/* ---------------- Intro + hero ---------------- */
window.addEventListener('load', () => {
  if (!G || reduce) { $('#intro').remove(); return; }
  const tl = G.timeline();
  tl.to('#intro .logo-grande span', { y: 0, duration: .7, stagger: .06, ease: 'power4.out' })
    .to('#intro small', { opacity: 1, duration: .3 }, '<.3')
    .to('#intro', { yPercent: -100, duration: .9, ease: 'power4.inOut', delay: .35 })
    .from('#hero .lin > span', { yPercent: 110, duration: 1, stagger: .12, ease: 'power4.out' }, '-=.35')
    .from('#hero .tag, #hero p.lead, #hero .hero-cta', { y: 24, opacity: 0, duration: .7, stagger: .1, ease: 'power3.out' }, '-=.7')
    .from('#hero .sticker', { scale: 0, rotate: -40, duration: .7, stagger: .1, ease: 'back.out(2)' }, '-=.6')
    .add(() => $('#intro').remove());
});

const nav = $('#nav');
addEventListener('scroll', () => nav.classList.toggle('solida', scrollY > innerHeight * .8), { passive: true });

function heroFlotantes() {
  const box = $('#flota');
  const elegidos = MERCADO.filter(r => r.precio > 15000 && r.titulo.length < 60).sort(() => Math.random() - .5).slice(0, innerWidth > 980 ? 8 : 3);
  const zonas = innerWidth > 980 ? [[70, 22], [74, 36], [67, 49], [72, 62], [66, 75], [71, 87], [62, 12], [76, 12]] : [[60, 12], [4, 86], [50, 90]];
  elegidos.forEach((r, i) => {
    const el = document.createElement('div');
    const b = banda(r.distancia_precio_prom_pct);
    el.className = 'precio-pill';
    el.innerHTML = `${r.titulo.split(' ').slice(0, 4).join(' ')} <b>${pesos(r.precio)}</b><span class="d ${b}">${r.distancia_precio_prom_pct > 0 ? '+' : ''}${fmt(r.distancia_precio_prom_pct)} %</span>`;
    const [x, y] = zonas[i % zonas.length];
    el.style.left = x + '%'; el.style.top = y + '%'; el.style.opacity = .0;
    box.appendChild(el);
    if (G && !reduce) {
      G.to(el, { opacity: i % 3 === 0 ? .85 : .5, duration: 1, delay: 2.2 + i * .08 });
      G.to(el, { y: -30 - Math.random() * 40, x: (Math.random() - .5) * 40, duration: 6 + Math.random() * 6, repeat: -1, yoyo: true, ease: 'sine.inOut' });
    } else el.style.opacity = .6;
  });
  if (G && !reduce) {
    $('#hero').addEventListener('mousemove', e => {
      const dx = (e.clientX / innerWidth - .5), dy = (e.clientY / innerHeight - .5);
      G.to('#flota', { x: dx * -30, y: dy * -20, duration: 1.2, ease: 'power3.out' });
      G.to('#hero .sticker', { x: dx * 26, y: dy * 18, duration: 1.2, ease: 'power3.out' });
    });
  }
}

function ticker() {
  const cats = Object.entries(MODELO.cats).filter(([, v]) => v.n >= 20);
  const piezas = cats.map(([c, v]) => `<span><b>${c}</b> · ${v.n} publicaciones · promedio ${pesos(v.prom)}</span>`);
  piezas.push('<span><b>7,1 %</b> del mercado en precio</span>', '<span><b>0,918</b> accuracy en validación cruzada</span>', '<span><b>US$ 30</b> por mes por rubro</span>');
  $('#ticker').innerHTML = piezas.join('') + piezas.join('');
}

/* ---------------- Kinetic typography ---------------- */
if (G && !reduce) {
  const lineas = $$('[data-kin]');
  lineas.forEach(l => { l.innerHTML = [...l.textContent].map(c => `<span class="ch">${c === ' ' ? '&nbsp;' : c}</span>`).join(''); });
  const chars = $$('#kinetic .ch');
  chars.forEach(ch => G.set(ch, { x: (Math.random() - .5) * innerWidth * 1.1, y: (Math.random() - .5) * innerHeight * 1.2, rotate: (Math.random() - .5) * 140, opacity: 0 }));
  const tl = G.timeline({ scrollTrigger: { trigger: '#kinetic', start: 'top top', end: '70% bottom', scrub: 1 } });
  tl.to(chars, { x: 0, y: 0, rotate: 0, opacity: 1, ease: 'power3.out', stagger: { each: .01, from: 'random' } })
    .to('#trazo1 path:first-child', { strokeDashoffset: 0, ease: 'none' }, '<.2')
    .to('#trazo1 path:last-child', { opacity: 1 }, '>-0.1')
    .fromTo('#kinStk1, #kinStk2', { scale: 0, opacity: 0 }, { scale: 1, opacity: 1, ease: 'back.out(2)', stagger: .1 }, '<')
    .to('#kinP', { opacity: 1, y: 0 }, '<.1');
}

/* ---------------- Reveals y contadores ---------------- */
if (G && !reduce) {
  ScrollTrigger.batch('.rev', { start: 'top 88%', onEnter: els => G.to(els, { opacity: 1, y: 0, duration: .9, stagger: .09, ease: 'power3.out' }) });
} else $$('.rev').forEach(e => { e.style.opacity = 1; e.style.transform = 'none'; });

$$('[data-cuenta]').forEach(el => {
  const fin = parseFloat(el.dataset.cuenta), dec = +(el.dataset.dec || 0);
  const correr = () => {
    if (!G || reduce) { el.textContent = fmt(fin, dec); return; }
    const o = { v: 0 };
    G.to(o, { v: fin, duration: 1.8, ease: 'power3.out', onUpdate: () => el.textContent = fmt(o.v, dec) });
  };
  if (G && window.ScrollTrigger) ScrollTrigger.create({ trigger: el, start: 'top 90%', once: true, onEnter: correr }); else correr();
});

/* ---------------- Flujo animado ---------------- */
(function flujo() {
  const g = $('#puntos'); const ns = 'http://www.w3.org/2000/svg';
  [0, 1, 2, 3].forEach(i => [0, 1].forEach(k => {
    const c = document.createElementNS(ns, 'circle'); c.setAttribute('r', 6); c.setAttribute('fill', '#F28C28');
    c.setAttribute('style', 'filter:drop-shadow(0 0 6px #F28C28)');
    const a = document.createElementNS(ns, 'animateMotion');
    a.setAttribute('dur', '1.6s'); a.setAttribute('repeatCount', 'indefinite'); a.setAttribute('begin', `${i * .4 + k * .8}s`);
    const mp = document.createElementNS(ns, 'mpath'); mp.setAttribute('href', `#fp${i}`);
    a.appendChild(mp); c.appendChild(a); g.appendChild(c);
  }));
})();

function mail() {
  const top = MERCADO.filter(r => r.prob_vende_mucho >= .9 && r.distancia_precio_prom_pct < -10).sort((a, b) => b.score_costo_beneficio - a.score_costo_beneficio).slice(0, 5);
  $('#mailFilas').innerHTML = top.map(r => `<div class="fila-mail"><span>${r.titulo.slice(0, 54)}</span><b>${pesos(r.precio)}</b><span class="chip rot">${fmt(r.prob_vende_mucho * 100)} % rota</span></div>`).join('');
  if (G && !reduce) {
    G.from('#mailMock', { scrollTrigger: { trigger: '#mailMock', start: 'top 85%' }, y: 80, rotateX: 18, opacity: 0, duration: 1.1, ease: 'power3.out' });
    G.from('.fila-mail', { scrollTrigger: { trigger: '#mailMock', start: 'top 70%' }, x: -30, opacity: 0, stagger: .12, duration: .6, ease: 'power3.out', delay: .4 });
  }
}

/* ---------------- Tabs ---------------- */
$$('.tab').forEach(t => t.addEventListener('click', () => {
  $$('.tab').forEach(x => x.classList.toggle('on', x === t));
  $$('.panel').forEach(p => p.classList.toggle('on', p.id === 'p-' + t.dataset.tab));
  if (t.dataset.tab === 'mapa') scatter();
  if (t.dataset.tab === 'oport') mostrarCartas();
}));

function chips(cont, lista, inicial, alCambiar, todas = false) {
  const items = todas ? ['Todas', ...lista] : lista;
  cont.innerHTML = items.map(c => `<button type="button" data-c="${c}" class="${c === inicial ? 'on' : ''}">${NOMBRE_CORTO[c] || c}</button>`).join('');
  cont.addEventListener('click', e => {
    const b = e.target.closest('button'); if (!b) return;
    $$('button', cont).forEach(x => x.classList.toggle('on', x === b)); alCambiar(b.dataset.c);
  });
}
const escalaLog = (cat, t) => { const c = MODELO.cats[cat]; const lo = Math.log(Math.max(c.min, 3000)), hi = Math.log(Math.min(c.max, c.prom * 5)); return Math.exp(lo + (hi - lo) * t); };
const inversaLog = (cat, p) => { const c = MODELO.cats[cat]; const lo = Math.log(Math.max(c.min, 3000)), hi = Math.log(Math.min(c.max, c.prom * 5)); return clamp((Math.log(p) - lo) / (hi - lo), 0, 1); };

/* ---------------- ¿Caro o barato? ---------------- */
function demoCaro() {
  let cat = CATS_DEMO[0];
  const inp = $('#precioCaro'), sl = $('#sliderCaro');
  const leer = () => +inp.value.replace(/\D/g, '') || 0;
  const calc = () => {
    const p = leer(), c = MODELO.cats[cat]; if (!p) return;
    const d = (p - c.prom) / c.prom * 100, b = banda(d);
    const deCat = MERCADO.filter(r => r.categoria === cat);
    const masBaratos = deCat.filter(r => r.precio < p).length / deCat.length * 100;
    const enBanda = deCat.filter(r => banda(r.distancia_precio_prom_pct) === b);
    const rota = enBanda.length ? enBanda.filter(r => r.prob_vende_mucho >= .5).length / enBanda.length * 100 : 0;
    const ver = { abajo: 'Estás <em class="s">más barato</em> que tu categoría.', dentro: 'Estás <em class="s">en precio.</em>', arriba: 'Estás <em class="s">más caro</em> que tu categoría.' };
    $('#verCaro').innerHTML = ver[b];
    $('#txtCaro').textContent = `Tu precio está ${fmt(Math.abs(d))} % ${d < 0 ? 'debajo' : 'arriba'} del promedio de ${NOMBRE_CORTO[cat]}, que es ${pesos(c.prom)}. ` +
      (b === 'arriba' ? 'Revisá si tu producto justifica la diferencia o sumá cuotas y envío gratis.' : b === 'abajo' ? 'Tenés margen para promocionar o para subir un poco el precio.' : 'Estás donde está solo el 7 % del mercado.');
    $('#agujaCaro').style.left = ((clamp(d, -90, 90) + 90) / 180 * 100) + '%';
    $('#agujaTxt').textContent = (d > 0 ? '+' : '') + fmt(d) + ' %';
    $('#d1').textContent = pesos(c.prom); $('#d2').textContent = fmt(masBaratos) + ' %'; $('#d3').textContent = fmt(rota) + ' %';
  };
  inp.addEventListener('input', () => { const p = leer(); inp.value = p ? fmt(p) : ''; sl.value = inversaLog(cat, p || 1) * 1000; calc(); });
  sl.addEventListener('input', () => { const p = Math.round(escalaLog(cat, sl.value / 1000) / 100) * 100 - 1; inp.value = fmt(p); calc(); });
  chips($('#catCaro'), CATS_DEMO, cat, c => { cat = c; sl.value = inversaLog(cat, leer() || 1) * 1000; calc(); });
  sl.value = inversaLog(cat, leer()) * 1000; calc();
}

/* ---------------- Probá el modelo ---------------- */
function demoModelo() {
  let cat = CATS_DEMO[0];
  const tog = { envio: 1, cuotas: 0, oficial: 0, combo: 0 };
  const resDe = v => Math.round(Math.expm1(v / 100 * Math.log1p(2000)));
  const calc = () => {
    const c = MODELO.cats[cat];
    const precio = escalaLog(cat, $('#mPrecio').value / 1000), desc = +$('#mDesc').value, rat = $('#mRat').value / 10, res = resDe(+$('#mRes').value);
    $('#lPrecio').textContent = pesos(precio) + ` · ${fmt((precio / c.med - 1) * 100)} % vs la mediana`;
    $('#lDesc').textContent = desc + ' %'; $('#lRat').textContent = rat ? fmt(rat, 1) + ' ★' : 'sin rating'; $('#lRes').textContent = fmt(res);
    const x = [precio / c.med, desc, tog.cuotas, tog.envio, tog.oficial, tog.combo, rat, rat > 0 ? 1 : 0, Math.log1p(res), res / Math.max(c.medRes, 1)];
    const p = predecir(x);
    const aro = $('#aro'); aro.style.strokeDashoffset = 653.5 * (1 - p); aro.style.stroke = p >= .5 ? '#F28C28' : '#8FA3C9';
    const v = $('#probV'), desde = parseFloat(v.dataset.v || 0); v.dataset.v = p * 100;
    if (G && !reduce) { const o = { n: desde }; G.to(o, { n: p * 100, duration: .7, ease: 'power3.out', onUpdate: () => v.innerHTML = fmt(o.n) + '<small>%</small>' }); }
    else v.innerHTML = fmt(p * 100) + '<small>%</small>';
    $('#verMod').innerHTML = p >= .5 ? 'Va a <em class="s">rotar.</em>' : 'Rotación <em class="s">estándar.</em>';
  };
  chips($('#catMod'), CATS_DEMO, cat, c => { cat = c; calc(); });
  ['#mPrecio', '#mDesc', '#mRat', '#mRes'].forEach(s => $(s).addEventListener('input', calc));
  $$('#mTog .toggle').forEach(t => t.addEventListener('click', () => { tog[t.dataset.k] ^= 1; t.classList.toggle('on', !!tog[t.dataset.k]); calc(); }));
  calc();
}

/* ---------------- Oportunidades ---------------- */
let opCat = 'Todas', opOrden = 'prob', opN = 9;
function oportunidades() {
  chips($('#catOp'), CATS_DEMO, 'Todas', c => { opCat = c; opN = 9; mostrarCartas(); }, true);
  $('#ordenOp').addEventListener('change', e => { opOrden = e.target.value; opN = 9; mostrarCartas(); });
  $('#masOp').addEventListener('click', () => { opN += 9; mostrarCartas(); });
  mostrarCartas();
}
function mostrarCartas() {
  let l = MERCADO.filter(r => r.prob_vende_mucho >= .5 && banda(r.distancia_precio_prom_pct) !== 'arriba' && (opCat === 'Todas' || r.categoria === opCat));
  const key = { prob: r => -r.prob_vende_mucho * 1000 - r.score_costo_beneficio, score: r => -r.score_costo_beneficio, dist: r => r.distancia_precio_prom_pct };
  l.sort((a, b) => key[opOrden](a) - key[opOrden](b));
  $('#masOp').style.display = l.length > opN ? '' : 'none';
  $('#cardsOp').innerHTML = l.slice(0, opN).map(r => {
    const b = banda(r.distancia_precio_prom_pct);
    return `<article class="prod"><span class="cat">${NOMBRE_CORTO[r.categoria] || r.categoria}</span><div class="tit">${r.titulo}</div>
      <div class="fila"><span class="pr">${pesos(r.precio)}</span><span class="chip ${b}">${r.distancia_precio_prom_pct > 0 ? '+' : ''}${fmt(r.distancia_precio_prom_pct)} %</span></div>
      <div class="fila"><span>${r.marca}</span><span>score ${fmt(r.score_costo_beneficio)}</span></div>
      <div class="fila"><span>Probabilidad de rotar</span><b>${fmt(r.prob_vende_mucho * 100)} %</b></div>
      <div class="barra"><i data-w="${r.prob_vende_mucho * 100}"></i></div>
      ${r.url ? `<a href="${r.url}" target="_blank" rel="noopener">Ver en Mercado Libre →</a>` : ''}</article>`;
  }).join('');
  requestAnimationFrame(() => $$('#cardsOp .prod').forEach((c, i) => setTimeout(() => { c.classList.add('vis'); const bar = $('.barra i', c); bar.style.width = bar.dataset.w + '%'; }, 40 * (i % 9))));
}

/* ---------------- Mapa del mercado ---------------- */
let scatterHecho = false;
function scatter() {
  if (scatterHecho || !MERCADO.length) return; scatterHecho = true;
  const svg = $('#scatter'), ns = 'http://www.w3.org/2000/svg', W = 1060, H = 460, L = 60, R = 20, T = 20, B = 50;
  const X = d => L + (clamp(d, -100, 150) + 100) / 250 * (W - L - R), Y = s => H - B - clamp(s, 0, 100) / 100 * (H - T - B);
  let h = `<rect x="${X(-10)}" y="${T}" width="${X(10) - X(-10)}" height="${H - T - B}" fill="#F28C28" opacity=".1"/>`;
  [-100, -50, 0, 50, 100, 150].forEach(v => h += `<line x1="${X(v)}" x2="${X(v)}" y1="${T}" y2="${H - B}" stroke="#E4DFD3"/><text x="${X(v)}" y="${H - B + 22}" text-anchor="middle" font-size="12" fill="#5E6678">${v > 0 ? '+' : ''}${v} %${v === 150 ? ' o más' : ''}</text>`);
  [0, 20, 40, 60, 80, 100].forEach(v => h += `<line x1="${L}" x2="${W - R}" y1="${Y(v)}" y2="${Y(v)}" stroke="#E4DFD3"/><text x="${L - 10}" y="${Y(v) + 4}" text-anchor="end" font-size="12" fill="#5E6678">${v}</text>`);
  h += `<text x="${(W + L) / 2}" y="${H - 6}" text-anchor="middle" font-size="12.5" fill="#5E6678">Distancia al precio promedio de su categoría</text><text transform="translate(16 ${(H - B) / 2}) rotate(-90)" text-anchor="middle" font-size="12.5" fill="#5E6678">Score costo-beneficio</text>`;
  svg.innerHTML = h;
  const col = { abajo: '#3D63D6', dentro: '#F28C28', arriba: '#E0577D' }, tip = $('#tip');
  MERCADO.forEach((r, i) => {
    const c = document.createElementNS(ns, 'circle'), rr = 2.5 + r.prob_vende_mucho * 5;
    c.setAttribute('cx', X(r.distancia_precio_prom_pct)); c.setAttribute('cy', Y(r.score_costo_beneficio)); c.setAttribute('r', reduce ? rr : 0);
    c.setAttribute('fill', col[banda(r.distancia_precio_prom_pct)]); c.setAttribute('fill-opacity', .55);
    c.addEventListener('mouseenter', e => { c.setAttribute('fill-opacity', 1); tip.innerHTML = `<b>${r.titulo}</b><br>${pesos(r.precio)} · ${r.distancia_precio_prom_pct > 0 ? '+' : ''}${fmt(r.distancia_precio_prom_pct)} % · score ${fmt(r.score_costo_beneficio)} · rota ${fmt(r.prob_vende_mucho * 100)} %`; tip.style.opacity = 1; });
    c.addEventListener('mousemove', e => { tip.style.left = Math.min(e.clientX + 14, innerWidth - 300) + 'px'; tip.style.top = (e.clientY + 14) + 'px'; });
    c.addEventListener('mouseleave', () => { c.setAttribute('fill-opacity', .55); tip.style.opacity = 0; });
    svg.appendChild(c);
    if (G && !reduce) G.to(c, { attr: { r: rr }, duration: .6, delay: (r.distancia_precio_prom_pct + 100) / 250 * 1.2, ease: 'back.out(3)' });
  });
}

/* ---------------- Barras de modelos ---------------- */
function barrasModelos() {
  const ms = [['Random Forest', .918], ['Gradient Boosting', .911], ['Red neuronal', .875], ['Regresión logística', .830], ['KNN', .830], ['SVM', .804]];
  $('#modelos').innerHTML = '<p style="font-size:13px;color:#C9D1E6;margin-bottom:4px">Accuracy en validación cruzada de los 6 modelos</p>' +
    ms.map(([n, v], i) => `<div class="m ${i === 0 ? 'gana' : ''}"><span>${n}</span><span class="b"><i data-w="${v * 100}"></i></span><span>${fmt(v, 3)}</span></div>`).join('');
  const llenar = () => $$('#modelos i').forEach((b, i) => setTimeout(() => b.style.width = b.dataset.w + '%', i * 120));
  if (window.ScrollTrigger) ScrollTrigger.create({ trigger: '#modelos', start: 'top 85%', once: true, onEnter: llenar }); else llenar();
}

/* ---------------- Calculadora ---------------- */
(function calculadora() {
  let cuota = 30;
  const anim = (el, v, txt) => {
    if (!G || reduce) { el.textContent = txt(v); return; }
    const o = { n: parseFloat(el.dataset.v || 0) }; el.dataset.v = v;
    G.to(o, { n: v, duration: .6, ease: 'power3.out', onUpdate: () => el.textContent = txt(o.n) });
  };
  const calc = () => {
    const h = +$('#calcH').value, v = +$('#calcV').value;
    $('#cH').textContent = h + ' h'; $('#cV').textContent = 'US$ ' + fmt(v, 1);
    const horas = h * 4.33, valor = horas * v, neto = valor - cuota, roi = neto / cuota * 100, dias = cuota / (valor / 30);
    anim($('#cNeto'), neto, n => fmt(n)); anim($('#cHoras'), horas, n => fmt(n) + ' h'); anim($('#cValor'), valor, n => 'US$ ' + fmt(n));
    $('#cCuota').textContent = 'US$ ' + cuota; anim($('#cROI'), roi, n => fmt(n) + ' %'); anim($('#cDias'), dias, n => fmt(n) + (Math.round(n) === 1 ? ' día' : ' días'));
  };
  ['#calcH', '#calcV'].forEach(s => $(s).addEventListener('input', calc));
  $$('#calcPlan button').forEach(b => b.addEventListener('click', () => { cuota = +b.dataset.p; $$('#calcPlan button').forEach(x => x.classList.toggle('on', x === b)); calc(); }));
  calc();
})();

/* ---------------- Abanico de servicios ---------------- */
(function abanico() {
  const cartas = $$('.carta');
  if (innerWidth <= 980) return;
  const k = Math.min(1, (innerWidth - 120) / 1240); const pos = [[-470 * k, 40, -13], [-235 * k, 10, -6], [0, 0, 0], [235 * k, 10, 6], [470 * k, 40, 13]];
  cartas.forEach((c, i) => {
    c.style.zIndex = i === 2 ? 5 : 5 - Math.abs(i - 2);
    const [x, y, r] = pos[i];
    if (G && !reduce) {
      G.set(c, { x: 0, y: 60, rotate: (i - 2) * 3 });
      G.to(c, { x, y, rotate: r, duration: 1.2, ease: 'power4.out', delay: i * .05, scrollTrigger: { trigger: '#abanico', start: 'top 75%' } });
    } else c.style.transform = `translate(${x}px,${y}px) rotate(${r}deg)`;
    c.addEventListener('mouseenter', () => G && G.to(c, { y: y - 40, rotate: 0, scale: 1.04, zIndex: 9, duration: .4, ease: 'power3.out' }));
    c.addEventListener('mouseleave', () => G && G.to(c, { y, rotate: r, scale: 1, zIndex: i === 2 ? 5 : 5 - Math.abs(i - 2), duration: .5, ease: 'power3.out' }));
  });
})();

/* ---------------- Tipeo de rubros ---------------- */
(function tipeo() {
  const el = $('#tipeo'), palabras = ['herramientas', 'celulares', 'repuestos', 'cosmética', 'juguetes', 'tu rubro'];
  if (reduce) { el.textContent = 'tu rubro'; return; }
  let i = 0, j = palabras[0].length, borrando = true;
  setInterval(() => {
    const w = palabras[i];
    if (borrando) { j--; if (j <= 0) { borrando = false; i = (i + 1) % palabras.length; } }
    else { j++; if (j >= palabras[i].length) { borrando = true; j = palabras[i].length + 8; } }
    el.textContent = palabras[i].slice(0, Math.max(0, Math.min(j, palabras[i].length))) || ' ';
  }, 110);
})();

/* ---------------- Formulario del piloto ---------------- */
$('#formPiloto').addEventListener('submit', e => {
  e.preventDefault();
  const d = Object.fromEntries(new FormData(e.target));
  if (CONFIG.email) {
    const cuerpo = `Hola, soy ${d.nombre} de ${d.comercio}. Quiero el piloto de 30 días de Metis Analytics para el rubro ${d.rubro}. Mi mail es ${d.email}.`;
    location.href = `mailto:${CONFIG.email}?subject=${encodeURIComponent('Piloto Metis Analytics · ' + d.comercio)}&body=${encodeURIComponent(cuerpo)}`;
  }
  $('#gracias').style.display = 'block';
  if (!CONFIG.email) $('#gracias').textContent = 'Este formulario todavía no está conectado a un mail. Mientras tanto, pedí el piloto escribiéndole al equipo.';
});
