// 2D-персонажи в манере референса (ролик про гаражи): тонкий тёмно-коричневый контур, круглая бледная голова
// без шеи на собранном капюшоне, глаза-точки под тяжёлым веком, короткие толстые брови, щетина точками,
// парка с клапанами карманов, молнией и шнурками, мягкая тень сбоку, спортивные штаны с лампасами, массивные ботинки.
// Шапок нет (кроме армейской кепки друга). Суставы: бёдра, колени, плечи, локти, голова.
const NS = 'http://www.w3.org/2000/svg';
const INK = '#3b3026', SW = 0.95, FINE = 0.6;
const el = (tag, attrs, parent) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; };
const P = (d, fill, parent, w = SW) => el('path', { d, fill, stroke: INK, 'stroke-width': w, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' }, parent);
const L = (d, parent, w = FINE, col = INK, op = 0.7) => el('path', { d, fill: 'none', stroke: col, 'stroke-width': w, 'stroke-linecap': 'round', opacity: op }, parent);

export const LOOKS = {
  hero:    { coat: '#33598a', shade: '#24426a', pants: '#252a38', stripes: 2, boots: '#b98a4e', sole: '#3a2a1c', glove: '#3a3d42', skin: '#e2d6c0', hair: 'short', hairC: '#2b221c', reflect: true, stubble: true, cords: true },
  friend:  { coat: '#5e6b47', shade: '#47523a', pants: '#4f593a', stripes: 0, boots: '#3d3228', sole: '#1e1814', glove: '#d9c3a6', skin: '#dcc7ab', hair: 'short', hairC: '#2b221c', camo: true, cap: '#46512f', stubble: true },
  grandpa: { coat: '#8c8a84', shade: '#6c6a65', pants: '#43454d', stripes: 0, boots: '#5a4334', sole: '#2a1f17', glove: '#e2cfb6', skin: '#e6d7c2', hair: 'bald', hairC: '#cfcfcb', vest: '#5d5f55', mustache: true },
  mom:     { coat: '#c49340', shade: '#9a7028', pants: '#4b3a46', stripes: 0, boots: '#6a4a35', sole: '#2e2018', glove: '#e2d6c0', skin: '#e8dac4', hair: 'long', hairC: '#5a3622', knit: true, long: true },
  kid:     { coat: '#b84238', shade: '#8e2f28', pants: '#2f4a64', stripes: 2, boots: '#8a5a3a', sole: '#3a2618', glove: '#2a3a52', skin: '#e8dac4', hair: 'short', hairC: '#3a2a1a', scale: 0.7, cords: true },
  girl:    { coat: '#b84238', shade: '#8e2f28', pants: '#4a3a60', stripes: 0, boots: '#8a5a3a', sole: '#3a2618', glove: '#2a3a52', skin: '#e8dac4', hair: 'tails', hairC: '#6a4024', scale: 0.64 },
  n1:      { coat: '#6b4d82', shade: '#513a64', pants: '#30303a', stripes: 0, boots: '#4a3a2e', sole: '#221a14', glove: '#2a2630', skin: '#e6d8c2', hair: 'long', hairC: '#6a4a30', fur: true },
  n2:      { coat: '#5c7a4c', shade: '#435b37', pants: '#353532', stripes: 2, boots: '#4a3a2e', sole: '#221a14', glove: '#26302c', skin: '#dccbb2', hair: 'short', hairC: '#3a2a20', stubble: true, cords: true },
  n3:      { coat: '#8a5c3c', shade: '#6a432a', pants: '#2e3246', stripes: 0, boots: '#3a2e25', sole: '#1d1814', glove: '#2a2420', skin: '#e2d2bb', hair: 'receding', hairC: '#3a2e26', stubble: true },
  vendor:  { coat: '#7a4a3a', shade: '#5c3628', pants: '#3a3030', stripes: 0, boots: '#3a2e25', sole: '#1d1814', glove: '#e2cfb6', skin: '#e6d4bd', hair: 'bun', hairC: '#4a3a30', apron: '#d8cfc0', long: true },
  cashier: { coat: '#2f6a5a', shade: '#22503f', pants: '#2a2a32', stripes: 0, boots: '#2a2420', sole: '#151210', glove: '#e2d6c0', skin: '#e8dac4', hair: 'long', hairC: '#2a2018' },
  pharm:   { coat: '#e9e6df', shade: '#c9c5bb', pants: '#3a3d48', stripes: 0, boots: '#2a2420', sole: '#151210', glove: '#e2d6c0', skin: '#e6d6c0', hair: 'short', hairC: '#7a6a5a', glasses: true, long: true },
};

// мимика: наклон бровей (+ внутренний край вверх), подъём бровей, открытость глаз, «большие глаза», улыбка/грусть, рот
export const FACES = {
  neutral:  { bt: 0, by: 0, eo: 0.5, big: 0, mc: 0, mo: 0 },
  thinking: { bt: 6, by: 1, eo: 0.42, big: 0, mc: -0.2, mo: 0 },
  worried:  { bt: 18, by: 2, eo: 0.75, big: 0, mc: -0.6, mo: 0 },
  anxious:  { bt: 22, by: 3, eo: 0.95, big: 0.5, mc: -0.6, mo: 0.15 },
  scared:   { bt: 24, by: 4, eo: 1, big: 1, mc: -0.7, mo: 0.35 },
  shocked:  { bt: 12, by: 6, eo: 1, big: 1, mc: 0, mo: 0.9 },
  angry:    { bt: -22, by: -2, eo: 0.55, big: 0, mc: -0.6, mo: 0.1 },
  sad:      { bt: 20, by: 1, eo: 0.45, big: 0, mc: -0.9, mo: 0 },
  happy:    { bt: -2, by: 2, eo: 0.12, big: 0, mc: 1, mo: 0.2 },
  tired:    { bt: 6, by: -1, eo: 0.3, big: 0, mc: -0.25, mo: 0 },
  serious:  { bt: -10, by: -1, eo: 0.45, big: 0, mc: -0.25, mo: 0 },
  relieved: { bt: 8, by: 1, eo: 0.35, big: 0, mc: 0.5, mo: 0 },
};

export class Char {
  constructor(svg, look) {
    const o = this.o = LOOKS[look]; this.look = look;
    this.root = el('g', {}, svg);
    this.shadow = el('ellipse', { cx: 0, cy: 0, rx: 26, ry: 6, fill: '#000', opacity: 0.35 }, this.root);
    this.body = el('g', {}, this.root);
    // ноги: спортивные штаны с лампасами, массивные ботинки
    this.leg = {};
    for (const s of [-1, 1]) {
      const thigh = el('g', {}, this.body), shin = el('g', {}, thigh), x0 = s * 9.5;
      P(`M${x0 - 8.5} -92 L${x0 + 8.5} -92 L${x0 + 7} -47 L${x0 - 7} -47 Z`, o.pants, thigh);
      P(`M${x0 - 7} -49 L${x0 + 7} -49 L${x0 + 6.5} -13 L${x0 - 6.5} -13 Z`, o.pants, shin);
      if (o.stripes) for (const dx of [s * 5.6, s * 4.0]) { L(`M${x0 + dx} -90 L${x0 + dx * 0.95} -48`, thigh, 0.8, '#e8e4dc', 0.95); L(`M${x0 + dx * 0.95} -48 L${x0 + dx * 0.92} -14`, shin, 0.8, '#e8e4dc', 0.95); }
      L(`M${x0 - 3} -78 q3 3 1 8 M${x0 + 2} -36 q-3 2 -1 6 M${x0 - 4} -22 q4 1 7 0`, thigh, FINE, INK, 0.45);
      const toe = s > 0 ? 1 : -1;
      P(`M${x0 - 7.5 * toe} -15 h${15 * toe} v7 q${9 * toe} 1 ${9 * toe} 5 v1 h${-24 * toe} z`, o.boots, shin);
      el('rect', { x: s > 0 ? x0 - 8 : x0 - 17, y: -3, width: 25, height: 3.4, rx: 1.4, fill: o.sole, stroke: INK, 'stroke-width': FINE }, shin);
      L(`M${x0 - 4 * toe} -13 l${3 * toe} 2 M${x0 - 1 * toe} -13 l${3 * toe} 2`, shin, FINE, INK, 0.6);
      this.leg[s] = { thigh, shin, hip: [x0, -91], knee: [x0, -48] };
    }
    // туловище: парка
    this.torso = el('g', {}, this.body);
    const hem = o.long ? -60 : -84;
    const tor = `M-22 -146 Q-29 -116 -27 ${hem} Q0 ${hem + 4} 27 ${hem} Q29 -116 22 -146 Q0 -152 -22 -146 Z`;
    this.armBack = el('g', {}, this.torso);
    P(tor, o.coat, this.torso);
    el('path', { d: `M8 -149 Q27 -142 27 -116 Q28 ${hem + 20} 27 ${hem} Q18 ${hem + 3} 10 ${hem + 3} Q14 -116 8 -149 Z`, fill: o.shade, opacity: 0.55 }, this.torso); // мягкая тень сбоку
    if (o.camo) for (const [cx, cy, r, c] of [[-12, -132, 7, '#47523a'], [10, -118, 9, '#7a8a5c'], [-8, -100, 8, '#3d3626'], [14, -94, 6, '#47523a'], [-18, -114, 5, '#7a8a5c']]) el('ellipse', { cx, cy, rx: r, ry: r * 0.6, fill: c, opacity: 0.85, transform: `rotate(-20 ${cx} ${cy})` }, this.torso);
    if (o.knit) for (let x = -20; x <= 20; x += 4) L(`M${x} -144 L${x * 1.08} ${hem + 3}`, this.torso, 0.5, o.shade, 0.7);
    if (o.vest) P(`M-27 -144 L-7 -144 L-8 ${hem} L-27 ${hem} Z M27 -144 L7 -144 L8 ${hem} L27 ${hem} Z`, o.vest, this.torso, FINE);
    if (o.apron) P(`M-17 -132 h34 L19 ${hem + 2} H-19 Z`, o.apron, this.torso, FINE);
    if (o.reflect) { el('rect', { x: -27.5, y: -124, width: 55, height: 4.5, fill: '#e08534', opacity: 0.95 }, this.torso); el('rect', { x: -27.5, y: -119, width: 55, height: 1.8, fill: '#d6d2c8' }, this.torso); }
    L(`M0 -146 L0 ${hem + 2}`, this.torso, 0.9, INK, 0.9);                                                  // молния
    el('rect', { x: -1.2, y: -137, width: 2.4, height: 4, rx: 0.8, fill: '#b8b2a6', stroke: INK, 'stroke-width': 0.4 }, this.torso);
    for (const sx of [-1, 1]) {                                                                              // клапаны карманов с пуговицей
      P(`M${sx * 5} -114 h${sx * 13} v-6 h${-sx * 13} z`, o.coat, this.torso, FINE);
      el('circle', { cx: sx * 11.5, cy: -116.5, r: 0.9, fill: INK }, this.torso);
      L(`M${sx * 6} -106 q${sx * 6} 3 ${sx * 14} 0`, this.torso, FINE, INK, 0.45);
    }
    L(`M-20 -135 q8 4 16 2 M6 -100 q8 3 16 0`, this.torso, FINE, INK, 0.4);                                // складки
    if (o.cords && !o.long) for (const x of [-11, 11]) L(`M${x} ${hem + 2} l1 9 m-1 -9 l-1 9`, this.torso, 0.7, '#ece6da', 0.95);
    if (o.fur) P(`M-17 -148 q17 10 34 0 q-3 -7 -17 -7 q-14 0 -17 7 z`, '#e6dccb', this.torso, FINE);
    // руки: трубчатые рукава с манжетой, перчатки
    this.arm = {};
    for (const s of [-1, 1]) {
      const up = el('g', {}, this.torso), fore = el('g', {}, up), sx = s * 21;
      P(`M${sx - 6 * s} -147 Q${sx + 8 * s} -145 ${sx + 9 * s} -117 L${sx - 1 * s} -115 Q${sx - 2 * s} -134 ${sx - 8 * s} -140 Z`, o.coat, up);
      L(`M${sx + 1 * s} -130 q4 2 7 0`, up, FINE, INK, 0.45);
      P(`M${sx + 9 * s} -119 L${sx + 8 * s} -91 L${sx - 1 * s} -91 L${sx - 1 * s} -117 Z`, o.coat, fore);
      P(`M${sx + 8.5 * s} -95 L${sx - 1.5 * s} -95 L${sx - 1.5 * s} -91 L${sx + 8.5 * s} -91 Z`, o.shade, fore, FINE);
      P(`M${sx - 0.5 * s} -91 h${9 * s} q${1 * s} 6 ${-1 * s} 9 q${-3 * s} 2 ${-6 * s} 0 q${-3 * s} -3 ${-2 * s} -9 z`, o.glove, fore);
      this.bag = this.bag || null;
      this.arm[s] = { up, fore, sh: [sx, -144], el: [sx + 4 * s, -117], hand: [sx + 4 * s, -84] };
    }
    // пакет с продуктами в правой руке (показывается при st.bag)
    this.bagG = el('g', { opacity: 0 }, this.arm[1].fore);
    P(`M${this.arm[1].hand[0] - 9} -82 h18 l2 26 h-22 z`, '#d9cdb2', this.bagG, FINE);
    L(`M${this.arm[1].hand[0] - 5} -82 q5 -6 10 0`, this.bagG, 0.8, INK, 0.8);
    el('rect', { x: this.arm[1].hand[0] - 6, y: -76, width: 6, height: 8, fill: '#a33a2a', stroke: INK, 'stroke-width': 0.4 }, this.bagG);
    el('rect', { x: this.arm[1].hand[0] + 1, y: -74, width: 5, height: 6, fill: '#3a6a3a', stroke: INK, 'stroke-width': 0.4 }, this.bagG);
    // голова: без шеи, сидит на собранном капюшоне
    this.head = el('g', {}, this.torso);
    P(`M-17 -142 Q-19 -152 -11 -154 Q0 -150 11 -154 Q19 -152 17 -142 Q0 -136 -17 -142 Z`, o.coat, this.head, SW);  // капюшон-воротник
    L(`M-12 -146 q4 3 9 2 M3 -144 q5 1 9 -2`, this.head, FINE, INK, 0.5);
    if (o.hair === 'long' || o.hair === 'tails') P(`M-22 -176 Q-26 -146 -16 -141 L16 -141 Q26 -146 22 -176 Z`, o.hairC, this.head);
    if (o.hair === 'tails') { P(`M-23 -166 q-8 6 -4 16 q5 -4 6 -12 z`, o.hairC, this.head, FINE); P(`M23 -166 q8 6 4 16 q-5 -4 -6 -12 z`, o.hairC, this.head, FINE); }
    this.skull = el('circle', { cx: 0, cy: -170, r: 21, fill: o.skin, stroke: INK, 'stroke-width': SW }, this.head);
    if (o.stubble) for (const [dx, dy] of [[-13, -163], [-11, -159], [-8, -156], [-4, -154], [0, -153.5], [4, -154], [8, -156], [11, -159], [13, -163], [-15, -167], [15, -167], [-9, -161], [9, -161], [-6, -158], [6, -158], [-12, -165], [12, -165], [-2, -156], [2, -156]])
      el('circle', { cx: dx, cy: dy, r: 0.38, fill: '#5a4a3c', opacity: 0.75 }, this.head);
    if (o.mustache) P(`M-8 -161 q8 -4 16 0 q-8 3 -16 0 z`, '#e8e6e0', this.head, FINE);
    this.face = el('g', {}, this.head);
    this.eye = [-1, 1].map(s => {
      const g = el('g', {}, this.face), cx = s * 7;
      return { s, cx, white: el('circle', { cx, cy: -171, r: 3.4, fill: '#fbf8f2', stroke: INK, 'stroke-width': FINE }, g),
        pupil: el('ellipse', { cx, cy: -170.6, rx: 2.0, ry: 2.3, fill: INK }, g),
        cover: el('rect', { x: cx - 4, y: -176, width: 8, height: 4, fill: o.skin }, g),
        lid: el('path', { d: '', fill: 'none', stroke: INK, 'stroke-width': 1.0, 'stroke-linecap': 'round' }, g),
        brow: el('path', { d: '', fill: 'none', stroke: INK, 'stroke-width': 2.1, 'stroke-linecap': 'round' }, g) };
    });
    if (o.glasses) for (const s of [-1, 1]) el('circle', { cx: s * 7, cy: -171, r: 4.3, fill: 'none', stroke: INK, 'stroke-width': 0.7 }, this.face);
    L(`M-0.5 -168 q2.6 1.8 0 3.4`, this.face, 0.8, INK, 0.85);                                              // нос
    this.mouth = el('path', { d: '', fill: '#6a2a24', stroke: INK, 'stroke-width': 1.0, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' }, this.face);
    this.sweat = el('path', { d: 'M16 -182 q3 5 0 7 q-3 -2 0 -7 z', fill: '#9fd6ff', stroke: INK, 'stroke-width': 0.5, opacity: 0 }, this.head);
    // волосы
    const hc = o.hairC;
    if (o.cap) { P(`M-20 -176 Q-20 -195 0 -195 Q20 -195 20 -176 Z`, o.cap, this.head); P(`M-4 -178 Q13 -181 26 -175 L24 -172 Q11 -175 -4 -174 Z`, o.cap, this.head, FINE); }
    else if (o.hair === 'short') P(`M-20.5 -173 Q-21 -192 0 -192 Q21 -192 20.5 -173 Q17 -183 8 -184 Q0 -186 -8 -184 Q-17 -183 -20.5 -173 Z`, hc, this.head);
    else if (o.hair === 'receding') P(`M-20.5 -172 Q-20 -186 -12 -188 Q-14 -182 -17 -176 Z M20.5 -172 Q20 -186 12 -188 Q14 -182 17 -176 Z`, hc, this.head, FINE);
    else if (o.hair === 'bald') { P(`M-20.8 -170 Q-21 -180 -17 -183 L-15 -176 Z M20.8 -170 Q21 -180 17 -183 L15 -176 Z`, hc, this.head, FINE); }
    else if (o.hair === 'bun') { P(`M-20.5 -172 Q-21 -192 0 -192 Q21 -192 20.5 -172 Q10 -184 0 -184 Q-10 -184 -20.5 -172 Z`, hc, this.head); el('circle', { cx: 0, cy: -195, r: 6, fill: hc, stroke: INK, 'stroke-width': SW }, this.head); }
    else P(`M-20.5 -172 Q-21 -193 0 -193 Q21 -193 20.5 -172 Q12 -182 2 -181 Q-8 -184 -20.5 -172 Z`, hc, this.head);
    this.backHair = P(`M-21 -175 Q-21 -192 0 -192 Q21 -192 21 -175 Q21 -158 0 -152 Q-21 -158 -21 -175 Z`, o.cap || hc, this.head);
    this.backHair.setAttribute('opacity', 0);
  }

  // st: x,y,k, flip, back, sit, hips/knees/sh/elb [l,r], head, look, gaze, gazeY, bob, breath, face, blink, talk, sweat, bag
  draw(st) {
    const k = st.k * (this.o.scale || 1);
    this.root.setAttribute('transform', `translate(${st.x.toFixed(1)},${st.y.toFixed(1)}) scale(${(k * (st.flip ? -1 : 1)).toFixed(4)},${k.toFixed(4)})`);
    this.body.setAttribute('transform', `translate(0,${(st.bob || 0).toFixed(2)})`);
    for (const [i, s] of [[0, -1], [1, 1]]) {
      const g = this.leg[s], ts = 1 - 0.9 * (st.sit || 0);
      g.thigh.setAttribute('transform', `translate(0 -48) scale(1 ${ts.toFixed(4)}) translate(0 48) rotate(${(st.hips?.[i] || 0).toFixed(2)} ${g.hip[0]} ${g.hip[1]})`);
      g.shin.setAttribute('transform', `translate(0 -48) scale(1 ${(1 / ts).toFixed(4)}) translate(0 48) rotate(${(st.knees?.[i] || 0).toFixed(2)} ${g.knee[0]} ${g.knee[1]})`);
      const a = this.arm[s]; a.up.setAttribute('transform', `rotate(${(st.sh?.[i] || 0).toFixed(2)} ${a.sh[0]} ${a.sh[1]})`);
      a.fore.setAttribute('transform', `rotate(${(st.elb?.[i] || 0).toFixed(2)} ${a.el[0]} ${a.el[1]})`);
    }
    const br = 1 + (st.breath || 0);
    this.torso.setAttribute('transform', `translate(0,${((st.torsoY || 0) + 41 * (st.sit || 0)).toFixed(2)}) scale(1,${br.toFixed(4)})`);
    this.head.setAttribute('transform', `rotate(${(st.head || 0).toFixed(2)} 0 -146) translate(${(st.look || 0).toFixed(2)} 0) translate(0 -146) scale(1.3) translate(0 146)`);
    this.bagG.setAttribute('opacity', st.bag ? 1 : 0);
    const f = st.face, back = !!st.back;
    this.face.setAttribute('opacity', back ? 0 : 1); this.backHair.setAttribute('opacity', back ? 1 : 0);
    const eo = Math.max(0.04, f.eo * (st.blink ?? 1)), big = f.big, happy = f.mc > 0.7 && f.eo < 0.25;
    for (const e of this.eye) {
      const gx = e.cx + (st.gaze || 0), gy = -170.6 - (st.gazeY || 0);
      e.white.setAttribute('opacity', big); e.white.setAttribute('r', (3.4 * (0.7 + 0.3 * big)).toFixed(2));
      e.pupil.setAttribute('cx', gx.toFixed(2)); e.pupil.setAttribute('cy', gy.toFixed(2));
      e.pupil.setAttribute('rx', (2.0 - 0.6 * big).toFixed(2)); e.pupil.setAttribute('ry', happy ? 0.01 : (2.3 - 0.7 * big).toFixed(2));
      // тяжёлое веко: прямая линия, всё выше неё закрыто цветом кожи
      const lidY = -170.6 - 2.3 + 4.6 * (1 - Math.min(1, eo)) * (big ? 0 : 1);
      e.cover.setAttribute('y', (lidY - 4.5).toFixed(2)); e.cover.setAttribute('height', big ? 0 : 4.5);
      e.lid.setAttribute('d', happy ? `M${e.cx - 3.5} -170 Q${e.cx} -174 ${e.cx + 3.5} -170` : (big ? '' : `M${e.cx - 3.8} ${lidY.toFixed(2)} h7.6`));
      const tilt = f.bt * e.s * -1, by = -178.5 - f.by - big * 1.5;
      e.brow.setAttribute('d', `M${e.cx - 3.2} ${by} L${e.cx + 3.2} ${by}`); e.brow.setAttribute('transform', `rotate(${tilt} ${e.cx} ${by})`);
    }
    const mo = Math.min(1, f.mo + (st.talk || 0)), w = 4.2 - mo * 1.2, c = f.mc, yC = -161 - c * 1.6, yM = -161 + c * 1.6;
    this.mouth.setAttribute('d', mo > 0.05 ? `M${-w} ${yC} Q0 ${yM - 1} ${w} ${yC} Q0 ${yM + 2 + mo * 6} ${-w} ${yC} Z` : `M${-w} ${yC} Q0 ${yM + 0.6} ${w} ${yC}`);
    this.mouth.setAttribute('fill', mo > 0.05 ? '#6a2a24' : 'none');
    this.sweat.setAttribute('opacity', st.sweat || 0);
  }
}

export function lerpFace(a, b, u) { const o = {}; for (const k in a) o[k] = a[k] + (b[k] - a[k]) * u; return o; }
