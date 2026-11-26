// Режиссёр сцены: камера, перемещения персонажей (шаг считается от пройденного пути), мимика, моргание, стук, пыль.
import * as THREE from 'three';
import { buildBunker } from './world.js';
import { Char, FACES, lerpFace } from './rig.js';

const W = 1080, H = 1920;
const ease = u => u < .5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2, cl = u => Math.max(0, Math.min(1, u));
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(W, H);
renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.15;
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.getElementById('stage').appendChild(renderer.domElement);
const scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(62, W / H, 0.05, 40);
const B = buildBunker(scene, renderer);
const svg = document.getElementById('chars');

// пыль: из люка при стуке и в воздухе
const NDUST = 500, dpos = new Float32Array(NDUST * 3), dseed = [];
for (let i = 0; i < NDUST; i++) dseed.push([Math.random(), Math.random(), Math.random(), Math.random()]);
const dgeo = new THREE.BufferGeometry(); dgeo.setAttribute('position', new THREE.BufferAttribute(dpos, 3));
const dotC = document.createElement('canvas'); dotC.width = dotC.height = 32; { const g = dotC.getContext('2d'), gr = g.createRadialGradient(16, 16, 0, 16, 16, 16); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 32, 32); }
const dust = new THREE.Points(dgeo, new THREE.PointsMaterial({ color: '#d8c8a8', size: 0.014, map: new THREE.CanvasTexture(dotC), transparent: true, opacity: 0.75, depthWrite: false })); scene.add(dust);

function keyAt(keys, t) {   // keys: [[t, {..}], ...] -> значения с плавностью + пройденный путь (для шага)
  if (t <= keys[0][0]) return { v: keys[0][1], dist: 0, moving: 0 };
  let dist = 0;
  for (let i = 0; i < keys.length - 1; i++) {
    const [t0, a] = keys[i], [t1, b] = keys[i + 1];
    const seg = Math.hypot((b.x ?? a.x) - a.x, (b.z ?? a.z) - a.z, (b.y ?? a.y ?? 0) - (a.y ?? 0));
    if (t < t1) { const u = (t - t0) / (t1 - t0), e = b.lin ? u : ease(u); const v = {}; for (const k in a) v[k] = typeof a[k] === 'number' ? a[k] + ((b[k] ?? a[k]) - a[k]) * e : a[k];
      return { v, dist: dist + seg * e, moving: seg > 0.01 ? Math.sin(Math.PI * u) : 0 }; }
    dist += seg;
  }
  return { v: keys[keys.length - 1][1], dist, moving: 0 };
}
function faceAt(list, t) { let f = FACES[list[0][1]]; for (let i = 0; i < list.length; i++) { const [ft, name] = list[i]; if (t >= ft) { const prev = i ? FACES[list[i - 1][1]] : FACES[name]; f = lerpFace(prev, FACES[name], cl((t - ft) / 0.25)); } } return f; }

const chars = [];
export function setup(spec) {
  window.SPEC = spec;
  for (const c of spec.chars) chars.push({ spec: c, rig: new Char(svg, c.look) });
}

const v3 = new THREE.Vector3();
function project(x, y, z) { v3.set(x, y, z).project(cam); return [(v3.x + 1) / 2 * W, (1 - v3.y) / 2 * H, v3.z]; }

window.R = function (t) {
  const S = window.SPEC;
  const c = keyAt(S.camera, t).v; cam.position.set(c.x, c.y, c.z); cam.lookAt(c.tx, c.ty, c.tz); cam.updateMatrixWorld();
  // стук в крышку: дрожь и пыль
  let knock = 0; for (const [a, b] of (S.knocks || [])) if (t >= a && t <= b) knock = 1;
  B.lidPivot.rotation.x = knock ? 0.035 * Math.sin(t * 55) : 0; B.lidPivot.position.y = 2.82 + (knock ? 0.006 * Math.sin(t * 80) : 0);
  const lidOpen = S.lidOpen ? cl((t - S.lidOpen[0]) / (S.lidOpen[1] - S.lidOpen[0])) : 0;
  B.lidPivot.rotation.x += -ease(lidOpen) * 1.9;
  B.red.intensity = S.red ? (lidOpen || S.redAlways ? 60 * (0.75 + 0.25 * Math.sin(t * 6)) * Math.max(lidOpen, S.redAlways ? 1 : 0) : 0) : 0;
  B.skyM.color.set(lidOpen > 0.05 || S.redAlways ? '#7a1208' : '#120808');
  for (let i = 0; i < NDUST; i++) {
    const [a, b, cc, d] = dseed[i];
    if (i < 260) { // пыль из люка: вспышки после каждого стука
      let age = 99; for (const [k0] of (S.knocks || [])) if (t >= k0) age = Math.min(age, t - k0);
      const fall = age * (0.8 + b * 1.2);
      dpos[i * 3] = B.hatch.x + (a - 0.5) * 0.7 + Math.sin(age * 2 + i) * 0.05; dpos[i * 3 + 2] = B.hatch.z + (cc - 0.5) * 0.7;
      dpos[i * 3 + 1] = age < 3 ? 2.75 - fall : -5;
    } else { // взвесь в воздухе
      dpos[i * 3] = -2.8 + a * 5.6 + Math.sin(t * 0.3 + i) * 0.1; dpos[i * 3 + 1] = 0.2 + ((b * 2.6 + t * 0.03 * (d + 0.3)) % 2.6); dpos[i * 3 + 2] = -4.2 + cc * 4.2;  // не ближе метра к камере, чтобы пылинки не становились пятнами
    }
  }
  dgeo.attributes.position.needsUpdate = true;
  renderer.render(scene, cam);
  // персонажи
  const order = [];
  for (const ch of chars) {
    const s = ch.spec, P = keyAt(s.path, t), p = P.v;
    const climb = s.climb && s.climb.some(([a, b]) => t >= a && t <= b);
    const phase = P.dist / (climb ? 0.32 : 0.72) * Math.PI * 2, amp = Math.min(1, P.moving * 3);
    const st = { face: faceAt(s.faces, t), blink: (((t + s.blinkOff) % 3.1) < 0.12) ? 0.05 : 1, breath: 0.012 * Math.sin(t * 2.2 + s.blinkOff), flip: p.flip > 0, back: climb || p.back > 0 };
    if (climb) {
      const sw = Math.sin(phase);
      st.sh = [170 + 15 * sw, -170 + 15 * sw]; st.elb = [-25 - 15 * sw, 25 - 15 * sw];
      st.hips = [-20 * Math.max(0, sw), -20 * Math.max(0, -sw)]; st.knees = [40 * Math.max(0, sw), 40 * Math.max(0, -sw)];
    } else {
      const sw = Math.sin(phase) * amp;
      st.hips = [28 * sw, -28 * sw]; st.knees = [Math.max(0, 40 * Math.sin(phase + 1.6)) * amp, Math.max(0, 40 * Math.sin(phase + 1.6 + Math.PI)) * amp];
      st.sh = [-20 * sw + (p.armL || 0), 20 * sw + (p.armR || 0)]; st.elb = [-10 * amp + (p.elbL || 0), 10 * amp + (p.elbR || 0)];
      st.bob = -Math.abs(Math.sin(phase)) * 4 * amp;
    }
    st.head = p.head || 0; st.gazeY = p.gazeY || 0; st.gaze = p.gaze || 0; st.look = p.look || 0;
    st.talk = s.talk && s.talk.some(([a, b]) => t >= a && t <= b) ? 0.35 + 0.35 * Math.sin(t * 22) : 0;
    st.sweat = p.sweat || 0;
    const [fx, fy, fz] = project(p.x, p.y || 0, p.z), [, hy] = project(p.x, (p.y || 0) + 1.75, p.z);
    st.x = fx; st.y = fy; st.k = (fy - hy) / 180;
    ch.rig.draw(st);
    ch.rig.shadow.setAttribute('opacity', climb || (p.y || 0) > 0.05 ? 0 : 0.35);
    order.push([fz, ch.rig.root]);
  }
  order.sort((a, b) => b[0] - a[0]).forEach(([, r]) => svg.appendChild(r));
  // цвет сирены поверх персонажей
  document.getElementById('tint').style.opacity = S.red && (lidOpen > 0.3 || S.redAlways) ? (0.18 + 0.08 * Math.sin(t * 6)).toFixed(3) : 0;
};
