// 3D-бункер: процедурные текстуры (бетон, металл, дерево), свет лампы и сирены, тени, туман.
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

// ---------- процедурные текстуры ----------
function rng(seed) { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }
function noiseCanvas(size, seed, fn) {
  const c = document.createElement('canvas'); c.width = c.height = size;
  const g = c.getContext('2d'); fn(g, size, rng(seed)); return c;
}
function fbm(g, size, r, base, amp, scales) {
  const img = g.getImageData(0, 0, size, size), d = img.data;
  const grids = scales.map(sc => { const n = Math.ceil(size / sc) + 2, a = new Float32Array(n * n); for (let i = 0; i < a.length; i++) a[i] = r(); return { sc, n, a }; });
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    let v = 0, w = 1, tw = 0;
    for (const G of grids) {
      const fx = x / G.sc, fy = y / G.sc, ix = Math.floor(fx), iy = Math.floor(fy), tx = fx - ix, ty = fy - iy;
      const at = (i, j) => G.a[(j % G.n) * G.n + (i % G.n)];
      const sx = tx * tx * (3 - 2 * tx), sy = ty * ty * (3 - 2 * ty);
      const top = at(ix, iy) * (1 - sx) + at(ix + 1, iy) * sx, bot = at(ix, iy + 1) * (1 - sx) + at(ix + 1, iy + 1) * sx;
      v += (top * (1 - sy) + bot * sy) * w; tw += w; w *= 0.55;
    }
    v = v / tw; const k = (y * size + x) * 4;
    for (let ch = 0; ch < 3; ch++) d[k + ch] = Math.max(0, Math.min(255, base[ch] + (v - 0.5) * amp));
    d[k + 3] = 255;
  }
  g.putImageData(img, 0, 0);
}
export function concrete(seed, base = [128, 124, 118], panels = 0) {
  const c = noiseCanvas(512, seed, (g, s, r) => {
    g.fillStyle = '#888'; g.fillRect(0, 0, s, s);
    fbm(g, s, r, base, 70, [128, 48, 16, 5]);
    for (let i = 0; i < 900; i++) { g.fillStyle = `rgba(${r() < .5 ? '40,38,36' : '200,196,190'},${0.25 * r()})`; g.fillRect(r() * s, r() * s, 1 + r() * 2.5, 1 + r() * 2.5); }
    for (let i = 0; i < 7; i++) { const x = r() * s; const gr = g.createLinearGradient(x, 0, x, s * (0.4 + r() * .6)); gr.addColorStop(0, 'rgba(30,25,20,.28)'); gr.addColorStop(1, 'rgba(30,25,20,0)'); g.fillStyle = gr; g.fillRect(x, 0, 6 + r() * 24, s); }
    if (panels) { g.strokeStyle = 'rgba(20,18,16,.75)'; g.lineWidth = 4; for (let k = 0; k <= panels; k++) { g.beginPath(); g.moveTo(k * s / panels, 0); g.lineTo(k * s / panels, s); g.stroke(); } g.beginPath(); g.moveTo(0, s / 2); g.lineTo(s, s / 2); g.stroke();
      g.fillStyle = 'rgba(30,30,30,.8)'; for (let k = 0; k < panels; k++) for (const yy of [.12, .38, .62, .88]) { g.beginPath(); g.arc(k * s / panels + 14, yy * s, 3.5, 0, 7); g.arc((k + 1) * s / panels - 14, yy * s, 3.5, 0, 7); g.fill(); } }
  });
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t;
}
function bumpOf(tex) { const b = tex.clone(); b.colorSpace = THREE.NoColorSpace; b.needsUpdate = true; return b; }
function metalTex(seed, base) {
  const c = noiseCanvas(256, seed, (g, s, r) => { fbm(g, s, r, base, 50, [64, 16, 4]); for (let i = 0; i < 40; i++) { g.fillStyle = `rgba(110,60,30,${.35 * r()})`; g.beginPath(); g.ellipse(r() * s, r() * s, 4 + r() * 18, 3 + r() * 10, r() * 3, 0, 7); g.fill(); } });
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.colorSpace = THREE.SRGBColorSpace; return t;
}
function woodTex(seed) {
  const c = noiseCanvas(256, seed, (g, s, r) => { g.fillStyle = '#6b4a2c'; g.fillRect(0, 0, s, s);
    for (let y = 0; y < s; y += 2) { g.strokeStyle = `rgba(${r() < .5 ? '40,25,12' : '140,100,60'},${.15 + .2 * r()})`; g.beginPath(); g.moveTo(0, y); for (let x = 0; x <= s; x += 16) g.lineTo(x, y + Math.sin(x * .03 + y * .2) * 2); g.stroke(); }
    for (let k = 0; k < s; k += s / 4) { g.fillStyle = 'rgba(20,12,6,.6)'; g.fillRect(0, k, s, 3); } });
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.colorSpace = THREE.SRGBColorSpace; return t;
}
function labelTex(seed) {
  const c = noiseCanvas(128, seed, (g, s, r) => { const cols = ['#8a3a2e', '#3a5a7a', '#6a7a3a', '#a07a2a', '#5a3a6a']; g.fillStyle = cols[Math.floor(r() * cols.length)]; g.fillRect(0, 0, s, s); g.fillStyle = '#e9e2cf'; g.fillRect(0, s * .35, s, s * .3); g.fillStyle = 'rgba(0,0,0,.5)'; g.fillRect(s * .1, s * .45, s * .5, s * .06); });
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}

// ---------- сборка бункера ----------
export const HATCH = { x: 1.0, z: -3.0, r: 0.42, y: 2.8 };
export function buildBunker(scene, renderer) {
  const pm = new THREE.PMREMGenerator(renderer);
  scene.environment = pm.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environmentIntensity = 0.18;
  scene.background = new THREE.Color('#050506');
  scene.fog = new THREE.Fog('#0a0a0b', 6, 13);
  const W = 6.4, D = 6, H = 2.8, Z0 = 1.6;
  const wallT = concrete(11, [122, 118, 110], 4); wallT.repeat.set(2, 1);
  const wallM = new THREE.MeshStandardMaterial({ map: wallT, bumpMap: bumpOf(wallT), bumpScale: 2.2, roughness: 0.92 });
  const floorT = concrete(23, [86, 82, 76]); floorT.repeat.set(3, 3);
  const floorM = new THREE.MeshStandardMaterial({ map: floorT, bumpMap: bumpOf(floorT), bumpScale: 1.5, roughness: 0.85 });
  const ceilT = concrete(37, [96, 92, 86], 3); ceilT.repeat.set(2, 2);
  const ceilM = new THREE.MeshStandardMaterial({ map: ceilT, bumpMap: bumpOf(ceilT), bumpScale: 1.5, roughness: 0.95 });
  const box = (w, h, d, m, x, y, z, cast = true) => { const o = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m); o.position.set(x, y, z); o.castShadow = cast; o.receiveShadow = true; scene.add(o); return o; };
  const plane = (w, h, m, pos, rot) => { const o = new THREE.Mesh(new THREE.PlaneGeometry(w, h), m); o.position.set(...pos); o.rotation.set(...rot); o.receiveShadow = true; scene.add(o); return o; };
  plane(W, D, floorM, [0, 0, Z0 - D / 2], [-Math.PI / 2, 0, 0]);
  // потолок с вырезом под люк: четыре полосы вокруг проёма
  const hx = HATCH.x, hz = HATCH.z, hr = HATCH.r + 0.08;
  plane(W, (Z0) - (hz + hr), ceilM, [0, H, (Z0 + hz + hr) / 2], [Math.PI / 2, 0, 0]);
  plane(W, (hz - hr) - (Z0 - D), ceilM, [0, H, (hz - hr + Z0 - D) / 2], [Math.PI / 2, 0, 0]);
  plane((hx - hr) + W / 2, 2 * hr, ceilM, [(-W / 2 + hx - hr) / 2, H, hz], [Math.PI / 2, 0, 0]);
  plane(W / 2 - (hx + hr), 2 * hr, ceilM, [(W / 2 + hx + hr) / 2, H, hz], [Math.PI / 2, 0, 0]);
  plane(W, H, wallM, [0, H / 2, Z0 - D], [0, 0, 0]);
  plane(D, H, wallM, [-W / 2, H / 2, Z0 - D / 2], [0, Math.PI / 2, 0]);
  plane(D, H, wallM, [W / 2, H / 2, Z0 - D / 2], [0, -Math.PI / 2, 0]);
  // шахта люка вверх
  const shaftM = new THREE.MeshStandardMaterial({ map: concrete(41, [70, 66, 62]), roughness: 1, side: THREE.BackSide });
  const shaft = new THREE.Mesh(new THREE.CylinderGeometry(hr, hr, 0.9, 32, 1, true), shaftM); shaft.position.set(hx, H + 0.45, hz); scene.add(shaft);
  const skyM = new THREE.MeshBasicMaterial({ color: '#120808' }); const sky = new THREE.Mesh(new THREE.CircleGeometry(hr, 32), skyM); sky.rotation.x = Math.PI / 2; sky.position.set(hx, H + 0.9, hz); scene.add(sky);
  const metal = new THREE.MeshStandardMaterial({ map: metalTex(5, [96, 100, 106]), metalness: 0.75, roughness: 0.42 });
  const rim = new THREE.Mesh(new THREE.TorusGeometry(hr, 0.05, 12, 40), metal); rim.rotation.x = Math.PI / 2; rim.position.set(hx, H - 0.02, hz); rim.castShadow = true; scene.add(rim);
  // крышка: шарнир у дальнего края, открывается вверх
  const lidPivot = new THREE.Group(); lidPivot.position.set(hx, H + 0.02, hz - HATCH.r); scene.add(lidPivot);
  const lid = new THREE.Mesh(new THREE.CylinderGeometry(HATCH.r, HATCH.r, 0.06, 40), metal); lid.position.set(0, 0, HATCH.r); lid.castShadow = true; lidPivot.add(lid);
  const wheel = new THREE.Mesh(new THREE.TorusGeometry(0.14, 0.018, 8, 24), metal); wheel.rotation.x = Math.PI / 2; wheel.position.set(0, -0.06, HATCH.r); lidPivot.add(wheel);
  for (const a of [0, Math.PI / 2]) { const sp = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.02, 0.02), metal); sp.rotation.y = a; sp.position.set(0, -0.06, HATCH.r); lidPivot.add(sp); }
  // лестница от пола до люка
  const ladM = new THREE.MeshStandardMaterial({ map: metalTex(9, [80, 86, 92]), metalness: 0.7, roughness: 0.5 });
  for (const dx of [-0.24, 0.24]) box(0.05, H, 0.05, ladM, hx + dx, H / 2, hz - HATCH.r + 0.05);
  for (let y = 0.3; y < H; y += 0.32) box(0.48, 0.035, 0.035, ladM, hx, y, hz - HATCH.r + 0.05);
  // короб вентиляции и кабели под потолком
  const ductM = new THREE.MeshStandardMaterial({ color: '#8a9096', metalness: 0.85, roughness: 0.35 });
  const duct = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.2, D, 24), ductM); duct.rotation.x = Math.PI / 2; duct.position.set(-2.2, H - 0.3, Z0 - D / 2); duct.castShadow = true; scene.add(duct);
  for (let z = Z0 - D + 0.3; z < Z0; z += 0.6) { const ring = new THREE.Mesh(new THREE.TorusGeometry(0.205, 0.015, 6, 24), ductM); ring.position.set(-2.2, H - 0.3, z); scene.add(ring); }
  const cableM = new THREE.MeshStandardMaterial({ color: '#151515', roughness: 0.6 });
  for (const [x, c] of [[-1.4, cableM], [-1.3, new THREE.MeshStandardMaterial({ color: '#5a2420', roughness: 0.6 })]]) { const cb = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, D, 8), c); cb.rotation.x = Math.PI / 2; cb.position.set(x, H - 0.08, Z0 - D / 2); scene.add(cb); }
  // стеллаж с банками слева
  const shelfM = new THREE.MeshStandardMaterial({ color: '#5d646c', metalness: 0.6, roughness: 0.5 });
  const sx = -W / 2 + 0.35, r = rng(77);
  for (const z of [-0.2, -2.0]) {
    for (const dz of [-0.75, 0.75]) for (const dx of [-0.22, 0.22]) box(0.04, 2.0, 0.04, shelfM, sx + dx, 1.0, z + dz);
    for (const y of [0.35, 0.85, 1.35, 1.85]) {
      box(0.5, 0.03, 1.55, shelfM, sx, y, z);
      for (let k = 0; k < 9; k++) {
        if (r() < 0.25) { const crate = box(0.4, 0.24, 0.3, new THREE.MeshStandardMaterial({ map: woodTex(k + y * 10), roughness: 0.8 }), sx, y + 0.135, z - 0.7 + k * 0.17); continue; }
        const can = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.13, 16), [new THREE.MeshStandardMaterial({ map: labelTex(k * 7 + y * 31 + z), roughness: 0.6 }), new THREE.MeshStandardMaterial({ color: '#b5b9bd', metalness: 0.9, roughness: 0.3 }), new THREE.MeshStandardMaterial({ color: '#b5b9bd', metalness: 0.9, roughness: 0.3 })]);
        can.position.set(sx - 0.1 + r() * 0.2, y + 0.08, z - 0.7 + k * 0.17); can.castShadow = true; scene.add(can);
      }
    }
  }
  // огнетушитель и щиток справа
  const ext = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.5, 20), new THREE.MeshStandardMaterial({ color: '#a3241c', metalness: 0.3, roughness: 0.35 })); ext.position.set(W / 2 - 0.12, 0.9, -1.0); ext.castShadow = true; scene.add(ext);
  box(0.06, 0.55, 0.42, new THREE.MeshStandardMaterial({ map: metalTex(13, [90, 96, 100]), metalness: 0.5, roughness: 0.6 }), W / 2 - 0.04, 1.7, -2.2);
  // лавка вдоль задней стены слева
  const benchM = new THREE.MeshStandardMaterial({ map: woodTex(3), roughness: 0.75 });
  box(2.6, 0.06, 0.42, benchM, -1.4, 0.46, Z0 - D + 0.35); for (const x of [-2.55, -0.25]) box(0.08, 0.44, 0.36, benchM, x, 0.22, Z0 - D + 0.35);
  // лампа в сетке
  const lampPos = new THREE.Vector3(-0.4, H - 0.45, -1.6);
  const bulb = new THREE.Mesh(new THREE.SphereGeometry(0.07, 16, 12), new THREE.MeshStandardMaterial({ color: '#ffd9a0', emissive: '#ffb050', emissiveIntensity: 6 })); bulb.position.copy(lampPos); scene.add(bulb);
  const cage = new THREE.Mesh(new THREE.SphereGeometry(0.1, 8, 6), new THREE.MeshStandardMaterial({ color: '#222', wireframe: true })); cage.position.copy(lampPos); scene.add(cage);
  const cord = new THREE.Mesh(new THREE.CylinderGeometry(0.008, 0.008, 0.38), cableM); cord.position.set(lampPos.x, H - 0.2, lampPos.z); scene.add(cord);
  // свет
  scene.add(new THREE.HemisphereLight('#8090a0', '#2a2018', 0.25));
  const lamp = new THREE.PointLight('#ffb468', 9, 9, 1.6); lamp.position.copy(lampPos).add(new THREE.Vector3(0, -0.12, 0)); lamp.castShadow = true; lamp.shadow.mapSize.set(1024, 1024); lamp.shadow.bias = -0.002; scene.add(lamp);
  const red = new THREE.SpotLight('#ff2a1a', 0, 7, 0.75, 0.6, 1.2); red.position.set(hx, H + 0.8, hz); red.target.position.set(hx, 0, hz + 0.6); red.castShadow = true; red.shadow.mapSize.set(512, 512); scene.add(red); scene.add(red.target);
  return { lidPivot, lamp, red, bulb, sky, skyM, hatch: HATCH, H };
}
