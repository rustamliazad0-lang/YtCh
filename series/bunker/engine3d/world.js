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
  // правая стена с дверным проёмом в техкомнату (z от -2.4 до -1.3)
  const DZ0 = -2.4, DZ1 = -1.3, DH = 2.1;
  plane(Z0 - DZ1, H, wallM, [W / 2, H / 2, (Z0 + DZ1) / 2], [0, -Math.PI / 2, 0]);
  plane(DZ0 - (Z0 - D), H, wallM, [W / 2, H / 2, (DZ0 + Z0 - D) / 2], [0, -Math.PI / 2, 0]);
  plane(DZ1 - DZ0, H - DH, wallM, [W / 2, DH + (H - DH) / 2, (DZ0 + DZ1) / 2], [0, -Math.PI / 2, 0]);
  const jamb = new THREE.MeshStandardMaterial({ map: metalTex(23, [70, 74, 78]), metalness: 0.6, roughness: 0.5 });
  for (const z of [DZ0, DZ1]) box(0.12, DH, 0.08, jamb, W / 2, DH / 2, z);
  box(0.12, 0.08, DZ1 - DZ0 + 0.08, jamb, W / 2, DH, (DZ0 + DZ1) / 2);
  // шахта люка вверх
  const shaftM = new THREE.MeshStandardMaterial({ map: concrete(41, [70, 66, 62]), roughness: 1, side: THREE.BackSide });
  const SH = 0.35; const shaft = new THREE.Mesh(new THREE.CylinderGeometry(hr, hr, SH, 32, 1, true), shaftM); shaft.position.set(hx, H + SH / 2, hz); scene.add(shaft);
  const skyM = new THREE.MeshBasicMaterial({ color: '#120808', transparent: true, opacity: 0 }); const sky = new THREE.Mesh(new THREE.CircleGeometry(hr, 32), skyM); sky.rotation.x = Math.PI / 2; sky.position.set(hx, H + 5, hz); scene.add(sky);
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
  const ext = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.5, 20), new THREE.MeshStandardMaterial({ color: '#a3241c', metalness: 0.3, roughness: 0.35 })); ext.position.set(W / 2 - 0.12, 0.9, 0.2); ext.castShadow = true; scene.add(ext);
  box(0.06, 0.55, 0.42, new THREE.MeshStandardMaterial({ map: metalTex(13, [90, 96, 100]), metalness: 0.5, roughness: 0.6 }), W / 2 - 0.04, 1.7, -3.4);
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
  // холодная заливка от люка (как в референсе: тёплый свет лампы против холодных теней)
  const cool = new THREE.PointLight('#6a7fb0', 2.2, 8, 1.5); cool.position.set(hx - 0.5, H - 0.3, hz + 0.8); scene.add(cool);
  const blue = new THREE.MeshStandardMaterial({ color: '#2f6fb0', roughness: 0.45, metalness: 0.1 });
  const pipeM = new THREE.MeshStandardMaterial({ color: '#7a8088', metalness: 0.8, roughness: 0.35 });
  // ящики штабелем у задней стены справа
  const wM = new THREE.MeshStandardMaterial({ map: woodTex(8), roughness: 0.8 });
  for (const [x, y] of [[1.9, 0.18], [2.35, 0.18], [2.1, 0.54]]) box(0.42, 0.34, 0.4, wM, x, y, Z0 - D + 0.35);
  // над люком: темнота, слабый красный отсвет сирены, фонарик светит вниз (людей рисует 2D-слой)
  const up = new THREE.Group(); scene.add(up);
  const voidM = new THREE.MeshStandardMaterial({ color: '#0d0b0b', roughness: 1, side: THREE.BackSide });
  const voidBox = new THREE.Mesh(new THREE.BoxGeometry(6, 3, 6), voidM); voidBox.position.set(hx, H + SH + 1.5, hz); up.add(voidBox);
  const gFloor = new THREE.Mesh(new THREE.RingGeometry(hr + 0.01, 3, 40), new THREE.MeshStandardMaterial({ map: concrete(51, [60, 56, 52]), roughness: 0.95 })); gFloor.rotation.x = -Math.PI / 2; gFloor.position.set(hx, H + SH, hz); up.add(gFloor);
  const upRed = new THREE.PointLight('#ff3020', 0, 6, 1.6); upRed.position.set(hx - 1.2, H + SH + 2.2, hz + 1.0); up.add(upRed);
  const upBulb = new THREE.Mesh(new THREE.SphereGeometry(0.001), new THREE.MeshBasicMaterial()); up.add(upBulb); upBulb.material.emissiveIntensity = 0;
  const torch = new THREE.SpotLight('#fff1d6', 0, 9, 0.32, 0.5, 1.0); torch.position.set(hx + 0.12, H + SH + 1.05, hz + 0.25); torch.target.position.set(hx, 0, hz + 0.3); torch.castShadow = true; torch.shadow.mapSize.set(512, 512); up.add(torch); up.add(torch.target);
  const lens = new THREE.Mesh(new THREE.CircleGeometry(0.035, 16), new THREE.MeshBasicMaterial({ color: '#fffbe8' })); lens.rotation.x = Math.PI / 2; lens.position.copy(torch.position).add(new THREE.Vector3(0, -0.01, 0)); up.add(lens);
  const coneM = new THREE.MeshBasicMaterial({ color: '#fff3d0', transparent: true, opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide });
  const cone = new THREE.Mesh(new THREE.ConeGeometry(0.75, 3.6, 24, 1, true), coneM); cone.position.set(hx + 0.06, H + SH + 1.05 - 1.8, hz + 0.27); scene.add(cone);
  // техкомната за проёмом в правой стене: бочка воды со скважиной, ФВУ с ручкой, генератор
  const TX = W / 2, tw = 3.0;
  const tFloor = new THREE.Mesh(new THREE.PlaneGeometry(tw, D), floorM); tFloor.rotation.x = -Math.PI / 2; tFloor.position.set(TX + tw / 2, 0, Z0 - D / 2); tFloor.receiveShadow = true; scene.add(tFloor);
  const tCeil = new THREE.Mesh(new THREE.PlaneGeometry(tw, D), ceilM); tCeil.rotation.x = Math.PI / 2; tCeil.position.set(TX + tw / 2, H, Z0 - D / 2); scene.add(tCeil);
  plane(D, H, wallM, [TX + tw, H / 2, Z0 - D / 2], [0, -Math.PI / 2, 0]);
  plane(tw, H, wallM, [TX + tw / 2, H / 2, Z0 - D], [0, 0, 0]);
  const tank2 = new THREE.Mesh(new THREE.CylinderGeometry(0.42, 0.42, 1.1, 28), blue); tank2.position.set(TX + 2.3, 0.55, -0.6); tank2.castShadow = true; scene.add(tank2);
  const pipe2 = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 1.6, 12), pipeM); pipe2.position.set(TX + 2.75, 0.8, -0.6); scene.add(pipe2);
  box(0.55, 0.8, 0.6, new THREE.MeshStandardMaterial({ map: metalTex(17, [80, 92, 84]), metalness: 0.5, roughness: 0.55 }), TX + 2.6, 1.2, -1.9);
  const crank2 = new THREE.Group(); crank2.position.set(TX + 2.28, 1.2, -1.9); scene.add(crank2);
  const arm2 = new THREE.Mesh(new THREE.BoxGeometry(0.03, 0.22, 0.03), pipeM); arm2.position.y = 0.1; crank2.add(arm2);
  box(0.8, 0.55, 0.5, new THREE.MeshStandardMaterial({ color: '#c8a62c', roughness: 0.5, metalness: 0.2 }), TX + 2.3, 0.3, -3.3);
  const exh = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 2.2, 10), pipeM); exh.position.set(TX + 2.75, 1.5, -3.3); scene.add(exh);
  const tLamp = new THREE.PointLight('#ffc27a', 5, 6, 1.6); tLamp.position.set(TX + 1.4, H - 0.4, -1.8); tLamp.castShadow = true; tLamp.shadow.mapSize.set(512, 512); scene.add(tLamp);
  const tb = new THREE.Mesh(new THREE.SphereGeometry(0.06, 12, 8), new THREE.MeshStandardMaterial({ color: '#ffd9a0', emissive: '#ffb050', emissiveIntensity: 5 })); tb.position.copy(tLamp.position); scene.add(tb);
  return { lidPivot, lamp, red, bulb, sky, skyM, hatch: HATCH, H, SH, crank: crank2, upRed, upBulb, cool, up, torch, coneM };
}


// ---------- улица (воспоминание «год назад»): снег, забор, гаражи, вечернее небо ----------
export function buildVillage(scene, renderer) {
  const pm = new THREE.PMREMGenerator(renderer);
  scene.environment = pm.fromScene(new RoomEnvironment(), 0.04).texture; scene.environmentIntensity = 0.35;
  const c = document.createElement('canvas'); c.width = 4; c.height = 256; const g = c.getContext('2d');
  const gr = g.createLinearGradient(0, 0, 0, 256); gr.addColorStop(0, '#3b3c6a'); gr.addColorStop(0.45, '#9a6a86'); gr.addColorStop(0.75, '#e8a070'); gr.addColorStop(1, '#f6c48a');
  g.fillStyle = gr; g.fillRect(0, 0, 4, 256); const skyT = new THREE.CanvasTexture(c); skyT.colorSpace = THREE.SRGBColorSpace;
  scene.background = skyT; scene.fog = new THREE.Fog('#b88a90', 12, 45);
  const snowT = concrete(61, [228, 232, 240]); snowT.repeat.set(8, 8);
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(80, 80), new THREE.MeshStandardMaterial({ map: snowT, roughness: 0.9 })); ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);
  const road = new THREE.Mesh(new THREE.PlaneGeometry(3.5, 80), new THREE.MeshStandardMaterial({ map: concrete(63, [70, 66, 66]), roughness: 0.9 })); road.rotation.x = -Math.PI / 2; road.position.set(-3.5, 0.01, 0); road.receiveShadow = true; scene.add(road);
  const wood = new THREE.MeshStandardMaterial({ map: woodTex(70), roughness: 0.8 });
  for (let x = -1.6; x <= 6; x += 0.18) { const pl = new THREE.Mesh(new THREE.BoxGeometry(0.12, 1.25, 0.04), wood); pl.position.set(x, 0.62, -0.6); pl.castShadow = true; scene.add(pl); }
  for (const y of [0.35, 0.95]) { const rail = new THREE.Mesh(new THREE.BoxGeometry(7.8, 0.08, 0.05), wood); rail.position.set(2.2, y, -0.63); scene.add(rail); }
  const brick = new THREE.MeshStandardMaterial({ map: concrete(65, [120, 70, 55], 3), roughness: 0.9 });
  const roof = new THREE.MeshStandardMaterial({ map: snowT, roughness: 0.9 });
  const doorCols = ['#3a6a5a', '#7a2a24', '#3a5a7a', '#6a6a3a'];
  for (let k = 0; k < 6; k++) { const x = -1 + k * 3.2, z = -7;
    const b = new THREE.Mesh(new THREE.BoxGeometry(3, 2.6, 5), brick); b.position.set(x, 1.3, z); b.castShadow = true; b.receiveShadow = true; scene.add(b);
    const rf = new THREE.Mesh(new THREE.BoxGeometry(3.2, 0.25, 5.4), roof); rf.position.set(x, 2.72, z); scene.add(rf);
    const dr = new THREE.Mesh(new THREE.PlaneGeometry(2.2, 2.0), new THREE.MeshStandardMaterial({ color: doorCols[k % 4], metalness: 0.4, roughness: 0.6 })); dr.position.set(x, 1.05, z + 2.51); scene.add(dr); }
  for (let k = 0; k < 4; k++) { const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.09, 7, 8), new THREE.MeshStandardMaterial({ color: '#3a3430' })); pole.position.set(-5.5, 3.5, -4 - k * 8); scene.add(pole); }
  scene.add(new THREE.HemisphereLight('#a8b0e0', '#806070', 0.9));
  const sun = new THREE.DirectionalLight('#ffb070', 3.2); sun.position.set(-10, 6, -12); sun.castShadow = true; sun.shadow.mapSize.set(1024, 1024);
  Object.assign(sun.shadow.camera, { left: -12, right: 12, top: 12, bottom: -12 }); scene.add(sun);
  return {};
}


// ---------- город: три места покупок для воспоминания «целый год понемногу в разных магазинах» ----------
export const SHOPS = { market: 0, super: 40, pharm: 80 };
export function buildTown(scene, renderer) {
  const pm = new THREE.PMREMGenerator(renderer);
  scene.environment = pm.fromScene(new RoomEnvironment(), 0.04).texture; scene.environmentIntensity = 0.3;
  scene.background = new THREE.Color('#2a2c44'); scene.fog = new THREE.Fog('#3a3448', 10, 40);
  const box = (w, h, d, m, x, y, z) => { const o = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m); o.position.set(x, y, z); o.castShadow = true; o.receiveShadow = true; scene.add(o); return o; };
  const wood = new THREE.MeshStandardMaterial({ map: woodTex(80), roughness: 0.8 });
  const snowT = concrete(81, [228, 232, 240]); snowT.repeat.set(6, 6);
  // рынок: снег, прилавок под навесом, ящики с овощами, мешки
  const mx = SHOPS.market;
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(30, 30), new THREE.MeshStandardMaterial({ map: snowT, roughness: 0.9 })); ground.rotation.x = -Math.PI / 2; ground.position.x = mx; ground.receiveShadow = true; scene.add(ground);
  box(2.4, 0.9, 0.8, wood, mx, 0.45, -1.5);
  const awn = new THREE.Mesh(new THREE.BoxGeometry(2.8, 0.06, 1.4), new THREE.MeshStandardMaterial({ color: '#a83a2c', roughness: 0.8 })); awn.position.set(mx, 2.3, -1.6); awn.rotation.x = 0.2; scene.add(awn);
  for (const x of [-1.3, 1.3]) box(0.08, 2.3, 0.08, wood, mx + x, 1.15, -1.0);
  const veg = ['#d0682a', '#7a9a3a', '#a8322a', '#d8b04a'];
  for (let k = 0; k < 4; k++) { box(0.5, 0.18, 0.35, wood, mx - 0.85 + k * 0.57, 0.99, -1.45); for (let j = 0; j < 6; j++) { const b = new THREE.Mesh(new THREE.SphereGeometry(0.055, 10, 8), new THREE.MeshStandardMaterial({ color: veg[k], roughness: 0.6 })); b.position.set(mx - 1.0 + k * 0.57 + (j % 3) * 0.1, 1.12, -1.5 + Math.floor(j / 3) * 0.1); scene.add(b); } }
  for (const x of [-1.5, -1.0]) { const s = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.26, 0.6, 12), new THREE.MeshStandardMaterial({ color: '#b8a27a', roughness: 0.95 })); s.position.set(mx + x - 0.4, 0.3, -0.6); scene.add(s); }
  const brick = new THREE.MeshStandardMaterial({ map: concrete(83, [120, 70, 55], 3), roughness: 0.9 });
  box(12, 4, 0.5, brick, mx, 2, -4);
  const mLamp = new THREE.PointLight('#ffb070', 8, 8, 1.6); mLamp.position.set(mx, 2.1, -1.2); mLamp.castShadow = true; mLamp.shadow.mapSize.set(512, 512); scene.add(mLamp);
  // супермаркет: пол-плитка, ряды полок с товаром, лампы дневного света, касса
  const sx = SHOPS.super;
  const tile = document.createElement('canvas'); tile.width = tile.height = 128; { const g = tile.getContext('2d'); g.fillStyle = '#cfcac0'; g.fillRect(0, 0, 128, 128); g.strokeStyle = '#a8a298'; g.lineWidth = 3; g.strokeRect(0, 0, 64, 64); g.strokeRect(64, 64, 64, 64); g.strokeRect(64, 0, 64, 64); g.strokeRect(0, 64, 64, 64); }
  const tileT = new THREE.CanvasTexture(tile); tileT.wrapS = tileT.wrapT = THREE.RepeatWrapping; tileT.repeat.set(10, 10); tileT.colorSpace = THREE.SRGBColorSpace;
  const sFloor = new THREE.Mesh(new THREE.PlaneGeometry(14, 14), new THREE.MeshStandardMaterial({ map: tileT, roughness: 0.4 })); sFloor.rotation.x = -Math.PI / 2; sFloor.position.set(sx, 0, -2); sFloor.receiveShadow = true; scene.add(sFloor);
  const sWall = new THREE.MeshStandardMaterial({ color: '#d8d4ca', roughness: 0.9, side: THREE.BackSide }); const room = new THREE.Mesh(new THREE.BoxGeometry(14, 3.4, 14), sWall); room.position.set(sx, 1.7, -2); scene.add(room);
  const shelfM = new THREE.MeshStandardMaterial({ color: '#e6e6e2', metalness: 0.3, roughness: 0.5 });
  const goods = ['#c03a2a', '#2a6ac0', '#e0b030', '#3a9a4a', '#e07a2a', '#7a3ac0'];
  for (const z of [-1.6, -4.0]) for (const side of [-1, 1]) {
    box(6, 1.9, 0.5, shelfM, sx, 0.95, z + side * 0.9);
    for (let y = 0.35; y < 1.9; y += 0.42) for (let k = 0; k < 22; k++) { const g = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.26, 0.2), new THREE.MeshStandardMaterial({ color: goods[(k + Math.round(y * 10)) % 6], roughness: 0.6 })); g.position.set(sx - 2.8 + k * 0.27, y + 0.14, z + side * 0.66); scene.add(g); }
  }
  box(1.6, 0.9, 0.6, new THREE.MeshStandardMaterial({ color: '#3a3d44', metalness: 0.4, roughness: 0.5 }), sx + 2.4, 0.45, 0.6);
  for (const z of [0, -2.8]) { const tube = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.05, 0.12), new THREE.MeshStandardMaterial({ color: '#ffffff', emissive: '#e8f2ff', emissiveIntensity: 3 })); tube.position.set(sx, 3.3, z); scene.add(tube);
    const rl = new THREE.RectAreaLight ? null : null; const pl = new THREE.PointLight('#e8f0ff', 6, 9, 1.5); pl.position.set(sx, 3.1, z); scene.add(pl); }
  // аптека: прилавок, полки с коробками, зелёный крест
  const px = SHOPS.pharm;
  const pFloor = new THREE.Mesh(new THREE.PlaneGeometry(10, 10), new THREE.MeshStandardMaterial({ map: tileT, roughness: 0.4 })); pFloor.rotation.x = -Math.PI / 2; pFloor.position.set(px, 0, -1.5); pFloor.receiveShadow = true; scene.add(pFloor);
  const pRoom = new THREE.Mesh(new THREE.BoxGeometry(10, 3.2, 10), new THREE.MeshStandardMaterial({ color: '#e2ece6', roughness: 0.9, side: THREE.BackSide })); pRoom.position.set(px, 1.6, -1.5); scene.add(pRoom);
  box(3.2, 1.0, 0.6, new THREE.MeshStandardMaterial({ color: '#f2f0ea', roughness: 0.5 }), px, 0.5, -2.2);
  box(4, 2.2, 0.35, new THREE.MeshStandardMaterial({ color: '#ffffff', roughness: 0.6 }), px, 1.1, -3.6);
  const med = ['#e8e8f0', '#3a7ac0', '#e05a4a', '#4ab07a', '#f0c040'];
  for (let y = 0.5; y < 2.1; y += 0.4) for (let k = 0; k < 16; k++) { const g = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.2, 0.12), new THREE.MeshStandardMaterial({ color: med[(k + Math.round(y * 7)) % 5], roughness: 0.6 })); g.position.set(px - 1.8 + k * 0.24, y, -3.38); scene.add(g); }
  const crossM = new THREE.MeshStandardMaterial({ color: '#2ab060', emissive: '#18a050', emissiveIntensity: 2.5 });
  box(0.5, 0.15, 0.05, crossM, px, 2.75, -3.4); box(0.15, 0.5, 0.05, crossM, px, 2.75, -3.4);
  const phl = new THREE.PointLight('#f0fff6', 6, 8, 1.5); phl.position.set(px, 2.8, -0.8); phl.castShadow = true; phl.shadow.mapSize.set(512, 512); scene.add(phl);
  scene.add(new THREE.HemisphereLight('#c8d0e8', '#605048', 0.6));
  return {};
}
