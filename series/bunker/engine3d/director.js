// Режиссёр ролика: миры (бункер/улица), камера по планам, размытие фона на крупных планах, 2D-персонажи с шагом,
// лестницей, посадкой и мимикой, таблички как в референсе, телефон от первого лица, реплики, субтитры, опрос.
import * as THREE from 'three';
import { buildBunker, buildVillage } from './world.js';
import { Char, FACES, lerpFace } from './rig.js';

const W = 1080, H = 1920;
const ease = u => u < .5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2, cl = u => Math.max(0, Math.min(1, u)), eo = u => 1 - Math.pow(1 - u, 3);
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(W, H);
renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.15;
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
const canvas = renderer.domElement; document.getElementById('stage').appendChild(canvas);
const worlds = { bunker: new THREE.Scene(), village: new THREE.Scene() };
const B = buildBunker(worlds.bunker, renderer); buildVillage(worlds.village, renderer);
const cam = new THREE.PerspectiveCamera(62, W / H, 0.05, 80);
const svg = document.getElementById('chars'), ui = document.getElementById('ui'), capEl = document.getElementById('cap');

// частицы: пыль в бункере, снег на улице
const dotC = document.createElement('canvas'); dotC.width = dotC.height = 32; { const g = dotC.getContext('2d'), gr = g.createRadialGradient(16, 16, 0, 16, 16, 16); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 32, 32); }
const dotT = new THREE.CanvasTexture(dotC);
function particles(scene, n, color, size) { const pos = new Float32Array(n * 3), geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  scene.add(new THREE.Points(geo, new THREE.PointsMaterial({ color, size, map: dotT, transparent: true, opacity: 0.8, depthWrite: false }))); return { pos, geo, seed: Array.from({ length: n }, () => [Math.random(), Math.random(), Math.random(), Math.random()]) }; }
const dust = particles(worlds.bunker, 520, '#d8c8a8', 0.014), snow = particles(worlds.village, 900, '#ffffff', 0.05), snowUp = particles(worlds.bunker, 160, '#ffffff', 0.03);

function keyAt(keys, t) {
  if (t <= keys[0][0]) return { v: keys[0][1], dist: 0, moving: 0 };
  let dist = 0;
  for (let i = 0; i < keys.length - 1; i++) {
    const [t0, a] = keys[i], [t1, b] = keys[i + 1];
    const seg = Math.hypot((b.x ?? a.x) - a.x, (b.z ?? a.z) - a.z, (b.y ?? a.y ?? 0) - (a.y ?? 0));
    if (t < t1) { const u = (t - t0) / Math.max(1e-4, t1 - t0), e = b.lin ? u : ease(u), v = {};
      for (const k of new Set([...Object.keys(a), ...Object.keys(b)])) { const av = a[k] ?? 0, bv = b[k] ?? av; v[k] = typeof av === 'number' ? av + (bv - av) * e : bv; }
      return { v, dist: dist + seg * e, moving: seg > 0.01 ? Math.sin(Math.PI * u) : 0 }; }
    dist += seg;
  }
  return { v: keys[keys.length - 1][1], dist, moving: 0 };
}
function faceAt(list, t) { let f = FACES[list[0][1]]; for (let i = 0; i < list.length; i++) { const [ft, name] = list[i]; if (t >= ft) { const prev = i ? FACES[list[i - 1][1]] : FACES[name]; f = lerpFace(prev, FACES[name], cl((t - ft) / 0.22)); } } return f; }
const inAny = (iv, t) => (iv || []).some(([a, b]) => t >= a && t <= b);

let S, chars = [], uiEls = [];
export function setup(spec) {
  S = spec; window.SPEC = spec;
  for (const c of spec.chars) { const rig = new Char(svg, c.look); let node = rig.root;
    if (c.clip) { node = document.createElementNS('http://www.w3.org/2000/svg', 'g'); node.setAttribute('clip-path', 'url(#hclip)'); svg.appendChild(node); node.appendChild(rig.root); }
    chars.push({ spec: c, rig, node }); }
  for (const u of spec.ui || []) { const d = document.createElement('div'); d.className = 'u ' + u.kind; d.innerHTML = u.html; Object.assign(d.style, u.css || {}); ui.appendChild(d); uiEls.push([u, d]); }
}

const v3 = new THREE.Vector3();
function project(x, y, z) { v3.set(x, y, z).project(cam); return [(v3.x + 1) / 2 * W, (1 - v3.y) / 2 * H, v3.z]; }

window.R = function (t) {
  const shot = S.shots.find(s => t >= s.t0 && t < s.t1) || S.shots[S.shots.length - 1];
  const scene = worlds[shot.world || 'bunker'];
  const c = keyAt(shot.cam, t).v; cam.position.set(c.x, c.y, c.z); cam.lookAt(c.tx, c.ty, c.tz); cam.fov = c.fov || 62; cam.updateProjectionMatrix(); cam.updateMatrixWorld();
  // люк: стук, открытие, красный свет сверху
  const knock = inAny(S.knocks, t);
  const lidOpen = S.lidOpen ? cl((t - S.lidOpen[0]) / (S.lidOpen[1] - S.lidOpen[0])) : 0;
  B.lidPivot.rotation.x = (knock ? 0.035 * Math.sin(t * 55) : 0) - ease(lidOpen) * 1.9;
  const redOn = S.redFrom != null && t >= S.redFrom ? 1 : 0, flick = 0.75 + 0.25 * Math.sin(t * 6);
  B.red.intensity = 60 * Math.max(lidOpen, 0) * redOn * flick; B.upRed.intensity = 14 * redOn * flick; B.upBulb.material.emissiveIntensity = 5 * redOn;
  B.crank.rotation.x = inAny(S.crank, t) ? t * 5 : 0;
  const lampOn = S.lampOff && t >= S.lampOff ? 0 : 1; B.lamp.intensity = 9 * lampOn; B.bulb.material.emissiveIntensity = 6 * lampOn;
  // частицы
  for (let i = 0; i < 520; i++) { const [a, b, cc, d] = dust.seed[i];
    if (i < 260) { let age = 99; for (const [k0] of (S.knocks || [])) if (t >= k0) age = Math.min(age, t - k0);
      dust.pos[i * 3] = B.hatch.x + (a - 0.5) * 0.7 + Math.sin(age * 2 + i) * 0.05; dust.pos[i * 3 + 2] = B.hatch.z + (cc - 0.5) * 0.7; dust.pos[i * 3 + 1] = age < 3 ? 2.75 - age * (0.8 + b * 1.2) : -5; }
    else { dust.pos[i * 3] = -2.8 + a * 5.6 + Math.sin(t * 0.3 + i) * 0.1; dust.pos[i * 3 + 1] = 0.2 + ((b * 2.6 + t * 0.03 * (d + 0.3)) % 2.6); dust.pos[i * 3 + 2] = -4.2 + cc * 4.2; } }
  dust.geo.attributes.position.needsUpdate = true;
  for (let i = 0; i < 900; i++) { const [a, b, cc, d] = snow.seed[i]; snow.pos[i * 3] = -8 + a * 20 + Math.sin(t * 0.7 + i) * 0.3; snow.pos[i * 3 + 1] = 8 - ((b * 8 + t * (0.5 + d * 0.6)) % 8); snow.pos[i * 3 + 2] = -14 + cc * 18; }
  snow.geo.attributes.position.needsUpdate = true;
  for (let i = 0; i < 160; i++) { const [a, b, cc, d] = snowUp.seed[i]; snowUp.pos[i * 3] = B.hatch.x - 1.5 + a * 3; snowUp.pos[i * 3 + 1] = 6 - ((b * 2.6 + t * (0.4 + d * 0.4)) % 2.6); snowUp.pos[i * 3 + 2] = B.hatch.z + 1 + cc * 1.4; }
  snowUp.geo.attributes.position.needsUpdate = true;
  renderer.render(scene, cam);
  canvas.style.filter = shot.blur ? `blur(${shot.blur}px)` : 'none';
  // персонажи
  const order = [];
  for (const ch of chars) {
    const s = ch.spec, vis = inAny(s.vis, t) && (s.world || 'bunker') === (shot.world || 'bunker');
    ch.node.style.display = vis ? '' : 'none'; if (!vis) continue;
    const Pk = keyAt(s.path, t), p = Pk.v, climb = inAny(s.climb, t);
    const phase = Pk.dist / (climb ? 0.32 : 0.72) * Math.PI * 2, amp = climb ? 1 : Math.min(1, Pk.moving * 3);
    const st = { face: faceAt(s.faces, t), blink: (((t + s.blinkOff) % 3.1) < 0.12) ? 0.05 : 1, breath: 0.012 * Math.sin(t * 2.2 + s.blinkOff), flip: (p.flip || 0) > 0.5, back: climb || (p.back || 0) > 0.5, sit: p.sit || 0 };
    if (climb) { const sw = Math.sin(phase); st.sh = [165 + 15 * sw, -165 + 15 * sw]; st.elb = [-20 - 15 * sw, 20 - 15 * sw]; st.hips = [-22 * Math.max(0, sw), -22 * Math.max(0, -sw)]; st.knees = [45 * Math.max(0, sw), 45 * Math.max(0, -sw)]; }
    else { const sw = Math.sin(phase) * amp;
      st.hips = [28 * sw, -28 * sw]; st.knees = [Math.max(0, 40 * Math.sin(phase + 1.6)) * amp, Math.max(0, 40 * Math.sin(phase + 1.6 + Math.PI)) * amp];
      const wave = p.wave || 0;
      st.sh = [-20 * sw + (p.armL || 0) - 12 * st.sit, 20 * sw + (p.armR || 0) + 12 * st.sit - wave * (150 + 12 * Math.sin(t * 9))];
      st.elb = [-10 * amp + (p.elbL || 0) - 45 * st.sit, 10 * amp + (p.elbR || 0) + 45 * st.sit - wave * 20]; st.bob = -Math.abs(Math.sin(phase)) * 4 * amp; }
    st.head = p.head || 0; st.gazeY = p.gazeY || 0; st.gaze = p.gaze || 0; st.look = p.look || 0; st.sweat = p.sweat || 0;
    st.talk = inAny(s.talk, t) ? 0.35 + 0.35 * Math.sin(t * 22) : 0;
    const y0 = p.y || 0, [fx, fy, fz] = project(p.x, y0, p.z), [, hy] = project(p.x, y0 + 1.75, p.z);
    st.x = fx; st.y = fy; st.k = (fy - hy) / 180;
    ch.rig.draw(st); ch.rig.shadow.setAttribute('opacity', climb || y0 > 0.05 && !s.onFloorAbove ? 0 : 0.35);
    ch.rig.root.style.filter = shot.charFilter || '';
    order.push([fz, ch.node]); ch.screen = [fx, hy];
  }
  order.sort((a, b) => b[0] - a[0]).forEach(([, r]) => svg.appendChild(r));
  // проём люка на экране: кто стоит наверху, виден только сквозь него
  const poly = []; for (let k = 0; k < 32; k++) { const a = k / 32 * Math.PI * 2; const [px, py] = project(B.hatch.x + Math.cos(a) * B.hatch.r, B.H + 0.02, B.hatch.z + Math.sin(a) * B.hatch.r); poly.push(px.toFixed(1) + ',' + py.toFixed(1)); }
  document.getElementById('hpoly').setAttribute('points', poly.join(' '));
  document.getElementById('tint').style.opacity = (shot.red ? (0.16 + 0.07 * Math.sin(t * 6)) : 0).toFixed(3);
  // интерфейс: таблички, телефон, реплики, опрос (появление с «пружиной»)
  for (const [u, d] of uiEls) {
    const on = t >= u.t0 && t < u.t1; d.style.display = on ? '' : 'none'; if (!on) continue;
    const k = eo(cl((t - u.t0) / 0.18)); let tr = `scale(${(0.6 + 0.4 * k).toFixed(3)})`;
    if (u.kind.includes('pulse')) tr = `scale(${(1 + 0.05 * Math.sin(t * 7)).toFixed(3)})`;
    if (u.anchor != null && chars[u.anchor].screen) { const [sx, sy] = chars[u.anchor].screen; const w = d.offsetWidth || 400; d.style.left = Math.max(30, Math.min(1050 - w, sx - 40)) + 'px'; d.style.top = Math.max(120, sy - 170) + 'px'; }
    d.style.transform = tr; d.style.opacity = k.toFixed(3);
    for (const m of d.querySelectorAll('[data-t]')) { const mt = +m.dataset.t; m.style.opacity = t >= mt ? eo(cl((t - mt) / 0.2)).toFixed(3) : 0; m.style.transform = `translateY(${(1 - eo(cl((t - mt) / 0.2))) * 20}px)`; }
  }
  // субтитры по словам
  const cp = (S.caps || []).find(x => t >= x.t0 && t < x.t1);
  if (cp) { capEl.innerHTML = cp.w.map(([w, k]) => k ? `<span class="k">${w}</span>` : w).join(' '); const k = eo(cl((t - cp.t0) / 0.14)); capEl.style.transform = `scale(${(0.82 + 0.18 * k).toFixed(3)})`; capEl.style.opacity = k; capEl.style.top = (cp.top || 1150) + 'px'; }
  else capEl.style.opacity = 0;
};
