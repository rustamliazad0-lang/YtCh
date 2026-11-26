// 2D-персонажи поверх 3D: жирный контур, реалистичная одежда (складки, швы, молнии), простое лицо с мимикой.
// Суставы: бёдра, колени, плечи, локти, голова. Ноги шагают сами, когда персонаж перемещается.
const NS = 'http://www.w3.org/2000/svg';
const INK = '#14110f', SW = 4.2;
const el = (tag, attrs, parent) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; };
const P = (d, fill, parent, extra = {}) => el('path', { d, fill, stroke: INK, 'stroke-width': SW, 'stroke-linejoin': 'round', 'stroke-linecap': 'round', ...extra }, parent);
const L = (d, parent, w = 2, col = INK, op = 0.55) => el('path', { d, fill: 'none', stroke: col, 'stroke-width': w, 'stroke-linecap': 'round', opacity: op }, parent);

export const LOOKS = {
  hero:    { jacket: '#2d5584', dark: '#1f3d61', pants: '#2c2f38', boots: '#b07a45', sole: '#3a2818', hand: '#1c1f24', skin: '#f2d2b0', hair: '#2b211b', stripe: true, quilt: true, stubble: true },
  friend:  { jacket: '#5b6a43', dark: '#3f4a2e', pants: '#4c5737', boots: '#3a3027', sole: '#1b1612', hand: '#e9c9a6', skin: '#e9c9a6', hair: '#2b211b', camo: true, cap: '#45512f' },
  grandpa: { jacket: '#9a9a96', dark: '#6c6c68', pants: '#45464d', boots: '#5a4334', sole: '#2a1f17', hand: '#e9c9a6', skin: '#efcfae', hair: '#d8d8d8', vest: '#5d5f55', ushanka: '#5a4a3a', mustache: true },
  mom:     { jacket: '#c9973e', dark: '#9a7028', pants: '#4b3a46', boots: '#6a4a35', sole: '#2e2018', hand: '#f2d2b0', skin: '#f2d2b0', hair: '#5a3622', longHair: true, knit: true, long: true },
  kid:     { jacket: '#c4433b', dark: '#922e28', pants: '#34506a', boots: '#8a5a3a', sole: '#3a2618', hand: '#24364a', skin: '#f2d2b0', hair: '#3a2a1a', beanie: '#3a6fa0', quilt: true, scale: 0.68 },
  girl:    { jacket: '#c4433b', dark: '#922e28', pants: '#4a3a60', boots: '#8a5a3a', sole: '#3a2618', hand: '#24364a', skin: '#f2d2b0', hair: '#6a4024', beanie: '#3a6fa0', quilt: true, scale: 0.62, braids: true },
  n1:      { jacket: '#6f4f86', dark: '#523a66', pants: '#33333d', boots: '#4a3a2e', sole: '#221a14', hand: '#2a2630', skin: '#f2d2b0', hair: '#6a4a30', longHair: true, fur: true },
  n2:      { jacket: '#5a7a4a', dark: '#405a34', pants: '#3a3a36', boots: '#4a3a2e', sole: '#221a14', hand: '#26302c', skin: '#e9c9a6', hair: '#3a2a20', quilt: true },
  n3:      { jacket: '#8a5a3a', dark: '#6a4028', pants: '#30344a', boots: '#3a2e25', sole: '#1d1814', hand: '#2a2420', skin: '#efcfae', hair: '#2a2420', beanie: '#5a5a5a', stubble: true },
};

// мимика: наклон бровей (+ внутренний край вверх), подъём бровей, открытость глаз, «большие глаза», улыбка/грусть, открытый рот
export const FACES = {
  neutral:  { bt: 0, by: 0, eo: 0.62, big: 0, mc: 0, mo: 0 },
  worried:  { bt: 16, by: 2, eo: 0.9, big: 0, mc: -0.5, mo: 0 },
  scared:   { bt: 22, by: 5, eo: 1, big: 1, mc: -0.6, mo: 0.35 },
  shocked:  { bt: 10, by: 7, eo: 1, big: 1, mc: 0, mo: 0.9 },
  angry:    { bt: -20, by: -2, eo: 0.75, big: 0, mc: -0.6, mo: 0.1 },
  sad:      { bt: 18, by: 1, eo: 0.7, big: 0, mc: -0.9, mo: 0 },
  happy:    { bt: -2, by: 2, eo: 0.15, big: 0, mc: 1, mo: 0.25 },
  tired:    { bt: 6, by: -1, eo: 0.45, big: 0, mc: -0.2, mo: 0 },
  serious:  { bt: -8, by: -1, eo: 0.6, big: 0, mc: -0.2, mo: 0 },
  thinking: { bt: 4, by: 1, eo: 0.55, big: 0, mc: -0.15, mo: 0 },
  anxious:  { bt: 20, by: 3, eo: 0.95, big: 0.4, mc: -0.5, mo: 0.15 },
  relieved: { bt: 8, by: 1, eo: 0.6, big: 0, mc: 0.5, mo: 0 },
};

export class Char {
  constructor(svg, look) {
    this.o = LOOKS[look]; this.look = look;
    this.root = el('g', {}, svg);
    this.shadow = el('ellipse', { cx: 0, cy: 0, rx: 30, ry: 7, fill: '#000', opacity: 0.35 }, this.root);
    this.body = el('g', {}, this.root);
    const o = this.o;
    // ноги
    this.leg = {};
    for (const s of [-1, 1]) {
      const thigh = el('g', {}, this.body), shin = el('g', {}, thigh);
      const x0 = s * 10;
      P(`M${x0 - 10} -94 L${x0 + 10} -94 L${x0 + 8} -46 L${x0 - 8} -46 Z`, o.pants, thigh);
      L(`M${x0 - 2} -80 q4 4 2 10 M${x0 + 3} -62 q-3 3 -1 7`, thigh, 1.6);
      P(`M${x0 - 8} -48 L${x0 + 8} -48 L${x0 + 7} -12 L${x0 - 7} -12 Z`, o.pants, shin);
      L(`M${x0 - 7} -22 h14`, shin, 1.6, INK, 0.4);
      P(s > 0 ? `M${x0 - 9} -15 h18 v8 q9 1 9 5 v2 h-27 q-1 0 -1 -3 z` : `M${x0 + 9} -15 h-18 v8 q-9 1 -9 5 v2 h27 q1 0 1 -3 z`, o.boots, shin);
      el('rect', { x: x0 - (s > 0 ? 10 : 16), y: -3.5, width: 26, height: 3.5, rx: 1.5, fill: o.sole }, shin);
      L(`M${x0 - 6} -12 l3 3 M${x0} -12 l3 3`, shin, 1.4, '#000', 0.5);
      this.leg[s] = { thigh, shin, hip: [x0, -92], knee: [x0, -47] };
    }
    // туловище
    this.torso = el('g', {}, this.body);
    const long = o.long ? -60 : -82;
    const tor = `M-24 -150 Q-31 -118 -28 ${long} Q0 ${long + 6} 28 ${long} Q31 -118 24 -150 Q0 -158 -24 -150 Z`;
    this.armBack = el('g', {}, this.torso);
    P(tor, o.vest ? o.jacket : o.jacket, this.torso);
    if (o.camo) for (const [cx, cy, r, c] of [[-12, -136, 8, '#3f4a2e'], [10, -120, 10, '#7a8a5a'], [-8, -100, 9, '#3a3324'], [14, -94, 7, '#3f4a2e'], [-18, -116, 6, '#7a8a5a']]) el('ellipse', { cx, cy, rx: r, ry: r * 0.6, fill: c, transform: `rotate(-20 ${cx} ${cy})` }, this.torso);
    if (o.quilt) for (const y of [-138, -124, -110, -96]) L(`M-28 ${y} Q0 ${y + 3} 28 ${y}`, this.torso, 1.8, o.dark, 0.9);
    if (o.knit) for (let x = -22; x <= 22; x += 5) L(`M${x} -148 L${x * 1.08} ${long + 3}`, this.torso, 1.2, o.dark, 0.6);
    if (o.vest) P(`M-28 -150 L-6 -150 L-8 -84 L-28 -84 Z M28 -150 L6 -150 L8 -84 L28 -84 Z`, o.vest, this.torso, { 'stroke-width': 3 });
    if (o.stripe) { el('rect', { x: -29, y: -128, width: 58, height: 7, fill: '#f08a2a' }, this.torso); el('rect', { x: -29, y: -120, width: 58, height: 3, fill: '#d9d6cc' }, this.torso); }
    if (o.fur) P(`M-20 -152 q20 12 40 0 q-4 -8 -20 -8 q-16 0 -20 8 z`, '#e6dccb', this.torso, { 'stroke-width': 3 });
    L(`M0 -150 L0 ${long + 4}`, this.torso, 2.2, INK, 0.8);                        // молния
    L(`M-3 -146 h6 M-3 -136 h6 M-3 -126 h6`, this.torso, 1, INK, 0.5);
    P(`M-20 -104 h13 v-3 h-13 z M7 -104 h13 v-3 h-13 z`, o.dark, this.torso, { 'stroke-width': 2.2 }); // клапаны карманов
    L(`M-26 -146 Q-28 -118 -26 ${long + 4} M26 -146 Q28 -118 26 ${long + 4}`, this.torso, 1.4, INK, 0.35); // боковые швы
    L(`M-14 -152 L0 -141 L14 -152`, this.torso, 2.4, INK, 0.9);                     // воротник
    // руки
    this.arm = {};
    for (const s of [-1, 1]) {
      const up = el('g', {}, this.torso), fore = el('g', {}, up);
      const sx = s * 22;
      P(`M${sx - 7 * s} -150 Q${sx + 9 * s} -144 ${sx + 10 * s} -116 L${sx - 1 * s} -114 Q${sx - 2 * s} -134 ${sx - 9 * s} -142 Z`, o.jacket, up);
      L(`M${sx + 1 * s} -132 q4 2 8 0`, up, 1.6, o.dark, 0.9);
      P(`M${sx + 10 * s} -118 L${sx + 9 * s} -90 L${sx - 1 * s} -90 L${sx - 1 * s} -116 Z`, o.jacket, fore);
      el('rect', { x: Math.min(sx - 1 * s, sx + 9 * s) - 1, y: -94, width: 12, height: 5, fill: o.dark }, fore);
      el('ellipse', { cx: sx + 4 * s, cy: -84, rx: 6.5, ry: 7.5, fill: o.hand, stroke: INK, 'stroke-width': SW }, fore);
      this.arm[s] = { up, fore, sh: [sx, -146], el: [sx + 5 * s, -116] };
    }
    // голова
    this.head = el('g', {}, this.torso);
    el('rect', { x: -6, y: -158, width: 12, height: 9, fill: o.skin, stroke: INK, 'stroke-width': 3 }, this.head);
    if (o.longHair) P(`M-22 -178 Q-26 -140 -16 -138 L16 -138 Q26 -140 22 -178 Z`, o.hair, this.head);
    if (o.ushanka) { P(`M-27 -178 h11 v26 h-11 z`, o.ushanka, this.head); P(`M16 -178 h11 v26 h-11 z`, o.ushanka, this.head); }
    el('ellipse', { cx: -19, cy: -170, rx: 4.5, ry: 6, fill: o.skin, stroke: INK, 'stroke-width': 3 }, this.head);
    el('ellipse', { cx: 19, cy: -170, rx: 4.5, ry: 6, fill: o.skin, stroke: INK, 'stroke-width': 3 }, this.head);
    this.skull = el('ellipse', { cx: 0, cy: -172, rx: 19, ry: 21, fill: o.skin, stroke: INK, 'stroke-width': SW }, this.head);
    if (o.stubble) for (const [dx, dy] of [[-12, -164], [-9, -159], [-5, -156], [0, -155], [5, -156], [9, -159], [12, -164], [-7, -161], [7, -161], [-13, -168], [13, -168]]) el('circle', { cx: dx, cy: dy + 1, r: 0.45, fill: '#8a7a6c', opacity: 0.55 }, this.head);
    if (o.mustache) P(`M-9 -163 q9 -5 18 0 q-9 4 -18 0 z`, '#e0e0e0', this.head, { 'stroke-width': 2 });
    this.face = el('g', {}, this.head);
    this.eye = [-1, 1].map(s => ({ s, white: el('ellipse', { cx: s * 7.5, cy: -172, rx: 5, ry: 6, fill: '#fff', stroke: INK, 'stroke-width': 2 }, this.face),
      pupil: el('ellipse', { cx: s * 7.5, cy: -172, rx: 2.6, ry: 3.4, fill: INK }, this.face),
      lid: el('path', { d: '', fill: 'none', stroke: INK, 'stroke-width': 2.6, 'stroke-linecap': 'round' }, this.face),
      brow: el('path', { d: '', fill: 'none', stroke: INK, 'stroke-width': 3.6, 'stroke-linecap': 'round' }, this.face) }));
    L(`M-1 -168 q3 4 -1 6`, this.face, 2, INK, 0.8);                                    // нос
    this.mouth = el('path', { d: '', fill: '#5a1f1f', stroke: INK, 'stroke-width': 2.6, 'stroke-linejoin': 'round' }, this.face);
    this.sweat = el('path', { d: 'M17 -184 q4 6 0 9 q-4 -3 0 -9 z', fill: '#8fd0ff', stroke: INK, 'stroke-width': 1.5, opacity: 0 }, this.head);
    // волосы/шапка сверху
    if (o.cap) { P(`M-20 -176 Q-20 -197 0 -197 Q20 -197 20 -176 Z`, o.cap, this.head); P(`M-4 -178 Q14 -182 28 -175 L26 -171 Q12 -175 -4 -174 Z`, o.cap, this.head); }
    else if (o.beanie) { P(`M-20.5 -176 Q-21 -199 0 -199 Q21 -199 20.5 -176 Z`, o.beanie, this.head); el('rect', { x: -22, y: -181, width: 44, height: 8, rx: 3, fill: o.beanie, stroke: INK, 'stroke-width': 3 }, this.head); }
    else if (o.ushanka) P(`M-22 -175 Q-22 -203 0 -203 Q22 -203 22 -175 Z`, o.ushanka, this.head);
    else P(`M-19.5 -174 Q-21 -195 0 -195 Q21 -195 19.5 -174 Q14 -184 5 -183 Q-3 -188 -9 -182 Q-15 -184 -19.5 -174 Z`, o.hair, this.head);
    this.backHair = P(`M-20 -186 Q0 -200 20 -186 L20 -158 Q0 -150 -20 -158 Z`, o.beanie || o.cap || o.ushanka || o.hair, this.head, { opacity: 0 });
    this.f = { ...FACES.neutral };
  }

  // st: {x,y (экран), k (масштаб), flip, back, hips:[l,r], knees:[l,r], sh:[l,r], elb:[l,r], head, bob, breath, face, blink, talk, sweat}
  draw(st) {
    const k = st.k * (this.o.scale || 1);
    this.root.setAttribute('transform', `translate(${st.x.toFixed(1)},${st.y.toFixed(1)}) scale(${(k * (st.flip ? -1 : 1)).toFixed(4)},${k.toFixed(4)})`);
    this.body.setAttribute('transform', `translate(0,${(st.bob || 0).toFixed(2)})`);
    for (const [i, s] of [[0, -1], [1, 1]]) {
      const g = this.leg[s], ts = 1 - 0.9 * (st.sit || 0);
      g.thigh.setAttribute('transform', `translate(0 -46) scale(1 ${ts.toFixed(4)}) translate(0 46) rotate(${(st.hips?.[i] || 0).toFixed(2)} ${g.hip[0]} ${g.hip[1]})`);
      g.shin.setAttribute('transform', `translate(0 -46) scale(1 ${(1 / ts).toFixed(4)}) translate(0 46) rotate(${(st.knees?.[i] || 0).toFixed(2)} ${g.knee[0]} ${g.knee[1]})`);
      const a = this.arm[s]; a.up.setAttribute('transform', `rotate(${(st.sh?.[i] || 0).toFixed(2)} ${a.sh[0]} ${a.sh[1]})`);
      a.fore.setAttribute('transform', `rotate(${(st.elb?.[i] || 0).toFixed(2)} ${a.el[0]} ${a.el[1]})`);
    }
    const br = 1 + (st.breath || 0);
    this.torso.setAttribute('transform', `translate(0,${((st.torsoY || 0) + 41 * (st.sit || 0)).toFixed(2)}) scale(1,${br.toFixed(4)})`);
    this.head.setAttribute('transform', `rotate(${(st.head || 0).toFixed(2)} 0 -152) translate(${(st.look || 0).toFixed(2)} 0) translate(0 -150) scale(1.32) translate(0 150)`);
    // лицо
    const f = st.face, back = !!st.back;
    this.face.setAttribute('opacity', back ? 0 : 1); this.backHair.setAttribute('opacity', back ? 1 : 0);
    const eo = Math.max(0.05, f.eo * (st.blink ?? 1));
    for (const e of this.eye) {
      const cx = e.s * 7.5 + (st.gaze || 0), cy = -172 - (st.gazeY || 0);
      const big = f.big;
      e.white.setAttribute('opacity', big); e.white.setAttribute('ry', (6 * eo).toFixed(2)); e.white.setAttribute('cx', e.s * 7.5);
      e.pupil.setAttribute('cx', cx.toFixed(2)); e.pupil.setAttribute('cy', cy.toFixed(2));
      e.pupil.setAttribute('rx', (2.6 - 0.9 * big).toFixed(2)); e.pupil.setAttribute('ry', ((3.4 - 1.2 * big) * Math.min(1, eo * 1.3)).toFixed(2));
      const half = eo < 0.8; // веко: дуга над глазом при прищуре и при улыбке
      e.lid.setAttribute('d', f.mc > 0.7 && f.eo < 0.3 ? `M${e.s * 7.5 - 5} -171 Q${e.s * 7.5} -177 ${e.s * 7.5 + 5} -171` : (half ? `M${e.s * 7.5 - 4.5} ${-172 - 3.4 * eo} h9` : ''));
      if (f.mc > 0.7 && f.eo < 0.3) e.pupil.setAttribute('ry', 0.01);
      const tilt = f.bt * e.s * -1, by = -181 - f.by - big * 2;
      e.brow.setAttribute('d', `M${e.s * 7.5 - 5} ${by} L${e.s * 7.5 + 5} ${by}`); e.brow.setAttribute('transform', `rotate(${tilt} ${e.s * 7.5} ${by})`);
    }
    const mo = Math.min(1, f.mo + (st.talk || 0)), w = 7 - mo * 2, c = f.mc;
    const yC = -160 - c * 2.5, yM = -160 + c * 2.5;
    this.mouth.setAttribute('d', mo > 0.05 ? `M${-w} ${yC} Q0 ${yM - 2} ${w} ${yC} Q0 ${yM + 3 + mo * 9} ${-w} ${yC} Z` : `M${-w} ${yC} Q0 ${yM + 1} ${w} ${yC}`);
    this.mouth.setAttribute('fill', mo > 0.05 ? '#5a1f1f' : 'none');
    this.sweat.setAttribute('opacity', st.sweat || 0);
  }
}

export function lerpFace(a, b, u) { const o = {}; for (const k in a) o[k] = a[k] + (b[k] - a[k]) * u; return o; }
