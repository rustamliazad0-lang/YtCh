#!/usr/bin/env python3
"""Видео с движением, глубиной и перспективой: python3 motion.py A [B ...] [--preview 6]

Каждая сцена разбирается на слои (стены/свет, предметы, люди, частицы) и ставится в 3D на разную
глубину. Камера на каждом плане движется по шаблону (наезд, проезд, облёт, кран, нижний ракурс),
каждая сцена снимается двумя планами (общий и крупный), между сценами переход «рывком».
Люди входят в кадр с шагом, частицы летят на разной глубине, субтитры идут по 1-3 слова,
ключевые слова красным. Кадр полный (без рамки), субтитры в безопасной зоне (62% высоты).
Правила описаны в скилле .claude/skills/yt-motion/SKILL.md.
"""
import json, os, random, re, subprocess, sys
import build_storyboard as B1
import build_storyboard_2 as B2

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "video")
ALL = {v["slug"]: v for v in B1.VIDEOS + B2.VIDEOS2}
P = 1500  # перспектива, px
DEPTH = {"fill": -1100, "bg": -520, "mid": -180, "fg": 0}
OVERSCAN = {"fill": 1.35, "bg": 1.2, "mid": 0.9, "fg": 1.0}
KEY = set("""никогда нельзя соседи соседей соседям шестой шестого тишина тишину сломается вручную радиацию кипячение
коробки коробку коробок ночью стучит стук люк скважины скважину война войну туалет генератор девять пятерых
двадцать тринадцать одиннадцать тридцать сорок пятьдесят девяносто""".split())
CAMS = {
    "push":   ({"tz": 0, "ry": -5}, {"tz": 170, "ry": -1}),
    "truckL": ({"tx": 70, "tz": 110, "ry": 5}, {"tx": -70, "tz": 140, "ry": -5}),
    "orbit":  ({"ry": -10, "tz": 120}, {"ry": 9, "tz": 150}),
    "crane":  ({"ty": 240, "rx": 13, "tz": 90}, {"ty": 0, "rx": 3, "tz": 140}),
    "truckR": ({"tx": -70, "tz": 110, "ry": -5}, {"tx": 70, "tz": 140, "ry": 5}),
    "low":    ({"ty": -150, "rx": -11, "tz": 110}, {"ty": -90, "rx": -5, "tz": 170}),
    "pull":   ({"tz": 230, "rx": 4}, {"tz": 30, "rx": 0}),
}


def svg(fn):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {B1.W} {B1.H}" preserveAspectRatio="xMidYMid slice">{fn()}</svg>'


def chunks(text):
    out, cur = [], []
    for w in text.split():
        cur.append(w)
        if len(cur) == 3 or re.search(r"[.,:?!]$", w):
            out.append(" ".join(cur)); cur = []
    if cur:
        out.append(" ".join(cur))
    return out


def plan(v):
    scenes, t0, names = [], 0.0, list(CAMS)
    for i, (fn, tm, narr, *_r) in enumerate(v["scenes"]):
        a, b = map(int, re.match(r"(\d+)-(\d+)", tm).groups())
        d = b - a
        cam = names[i % len(names)]
        shots = [{"t0": 0.0, "t1": d, "cam": CAMS[cam]}]
        if d >= 4:
            cut = round(d * 0.55, 2)
            other = CAMS[names[(i + 3) % len(names)]]  # второй план: другой ракурс, а не приближение
            shots = [{"t0": 0.0, "t1": cut, "cam": CAMS[cam]}, {"t0": cut, "t1": d, "cam": other}]
        cs = chunks(narr)
        lens = [len(c) for c in cs]
        tot, acc, caps = sum(lens), 0.15, []
        for c, L in zip(cs, lens):
            dur = (d - 0.3) * L / tot
            words = [(w, bool(re.search(r"\d", w)) or re.sub(r"[^\w]", "", w.lower()) in KEY) for w in c.split()]
            caps.append({"t0": round(acc, 3), "t1": round(acc + dur, 3), "w": words}); acc += dur
        markup = svg(fn)
        # субтитр уходит наверх, если в его полосе (1060-1420 px) есть текст самой сцены
        art = re.sub(r'<g data-l="cap">.*?</g>', "", markup, flags=re.S)
        ts = [(int(float(y)) * 3 + 120, int(fs)) for y, fs in re.findall(r'<text x="[^"]+" y="([\d.]+)"[^>]*font-size="(\d+)"', art)]
        clash = lambda lo, hi: sum(fs for y, fs in ts if lo <= y + 10 and y - fs * 3 <= hi)  # текст занимает [y-fs*3, y]
        spots = [1150, 250, 1000, 1300, 700]  # по порядку предпочтения; первое место без текста сцены
        cap_top = next((y for y in spots if clash(y, y + 220) == 0), min(spots, key=lambda y: clash(y, y + 220)))
        rnd = random.Random(i * 7 + len(narr))
        dust = [[rnd.uniform(0, 1080), rnd.uniform(0, 1920), rnd.uniform(2, 6), rnd.uniform(8, 40)] for _ in range(36)]
        scenes.append({"t0": t0, "d": d, "shots": shots, "caps": caps, "svg": markup, "dust": dust,
                       "siren": "#ff2d2d" in markup, "cap_top": cap_top, "room": "#0e1014" in markup, "outdoor": "#0e1014" not in markup})
        t0 += d
    return scenes


CSS = f"""
html,body{{margin:0;width:1080px;height:1920px;overflow:hidden;background:#07080b}}
#stage{{position:absolute;inset:0;perspective:{P}px;perspective-origin:50% 46%;overflow:hidden}}
#world{{position:absolute;inset:0;transform-style:preserve-3d;transform-origin:540px 883px}}
.sc{{position:absolute;inset:0;transform-style:preserve-3d;display:none}}
.pl{{position:absolute;inset:0;transform-origin:540px 960px}}
.pl svg{{width:100%;height:100%;display:block}}
.bg svg>:not([data-l=bg]){{display:none}} .mid svg>[data-l]{{display:none}}
.fg svg>:not([data-l=fg]){{display:none}} .fill svg>[data-l=cap],.fill svg>[data-l=fg],.fill svg text{{display:none}}
.fill:after{{content:"";position:absolute;inset:0;background:rgba(0,0,0,.55)}}
.floor{{position:absolute;left:-760px;width:2600px;height:2400px;transform-origin:50% 0;
  background:repeating-linear-gradient(90deg,rgba(255,255,255,.07) 0 3px,transparent 3px 160px),repeating-linear-gradient(0deg,rgba(255,255,255,.06) 0 3px,transparent 3px 160px)}}
.dust{{position:absolute;inset:-200px;transform-style:preserve-3d}}
.d{{position:absolute;border-radius:50%;background:#ffe9b8}}
#siren{{position:absolute;inset:0;background:radial-gradient(circle at 15% 10%,rgba(255,40,40,.55),transparent 60%),radial-gradient(circle at 90% 80%,rgba(255,40,40,.45),transparent 60%);opacity:0;mix-blend-mode:screen}}
#vig{{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 45%,transparent 55%,rgba(0,0,0,.65) 100%)}}
#cap{{position:absolute;left:60px;right:60px;top:1150px;text-align:center;font:900 92px/1.05 'DejaVu Sans',Arial,sans-serif;
  color:#fff;text-transform:uppercase;letter-spacing:1px;-webkit-text-stroke:14px #000;paint-order:stroke fill;
  text-shadow:0 8px 24px rgba(0,0,0,.6);transform-origin:50% 50%}}
#cap .k{{color:#ff3b30}}
"""

JS = r"""
const S = DATA, P = PERSP, DEP = DEPTHS, OV = OVERS;
const ease = u => u < .5 ? 4*u*u*u : 1 - Math.pow(-2*u + 2, 3)/2, eo = u => 1 - Math.pow(1 - u, 3), cl = u => Math.max(0, Math.min(1, u));
const W = document.getElementById('world'), C = document.getElementById('cap'), SI = document.getElementById('siren');
const els = S.map((s, i) => document.getElementById('s' + i));
const people = els.map(e => [...e.querySelectorAll('.fg .p')]);
const dust = els.map(e => [...e.querySelectorAll('.d')]);
const mids = els.map(e => e.querySelector('.mid'));
function lerp(a, b, u) { const o = {}; for (const k of new Set([...Object.keys(a), ...Object.keys(b)])) o[k] = (a[k]||0) + ((b[k]||0) - (a[k]||0))*u; return o; }
let cur = -1;
window.R = function (t) {
  let i = S.findIndex(s => t >= s.t0 && t < s.t0 + s.d); if (i < 0) i = S.length - 1;
  const s = S[i], lt = t - s.t0;
  if (i !== cur) { els.forEach((e, k) => e.style.display = k === i ? 'block' : 'none'); cur = i; }
  const sh = s.shots.find(x => lt >= x.t0 && lt < x.t1) || s.shots[s.shots.length - 1];
  const c = lerp(sh.cam[0], sh.cam[1], ease(cl((lt - sh.t0)/(sh.t1 - sh.t0))));
  // переход рывком между сценами
  c.ty = (c.ty||0) + 120; const dir = i % 2 ? -1 : 1; let blur = 0;
  if (lt > s.d - .18 && i < S.length - 1) { const u = (lt - (s.d - .18))/.18; c.tx = (c.tx||0) + 620*u*u*dir; blur = 16*u; }
  if (lt < .18 && i > 0) { const u = 1 - eo(lt/.18); c.tx = (c.tx||0) - 620*u*(i % 2 ? 1 : -1); blur = Math.max(blur, 16*u); }
  W.style.transform = `translate3d(${c.tx||0}px,${c.ty||0}px,${c.tz||0}px) rotateX(${c.rx||0}deg) rotateY(${c.ry||0}deg)`;
  document.getElementById('stage').style.filter = blur > .5 ? `blur(${blur.toFixed(1)}px)` : 'none';
  // средний план «собирается» в начале сцены
  const pop = eo(cl(lt/.3)); const m = mids[i];
  m.style.opacity = pop; m.style.transform = `translateZ(${DEP.mid}px) scale(${((P - DEP.mid)/P*OV.mid*(.95 + .05*pop)).toFixed(4)})`;
  // люди входят с шагом, потом дышат
  people[i].forEach((p, k) => {
    const u = cl((lt - .05 - .08*k)/.7), e = eo(u), side = k % 2 ? 1 : -1;
    const dx = (1 - e)*320*side, dy = -Math.abs(Math.sin(lt*13 + k))*12*(1 - e) + Math.sin(lt*2 + k)*2;
    p.style.transform = `translate(${dx.toFixed(1)}px,${dy.toFixed(1)}px)`;
  });
  // частицы
  dust[i].forEach((d, k) => { const sp = +d.dataset.sp; const y = (+d.dataset.y + sp*lt*6) % 2300 - 200; d.style.transform = `translate3d(${(+d.dataset.x + Math.sin(lt + k)*20).toFixed(1)}px,${y.toFixed(1)}px,${d.dataset.z}px)`; });
  SI.style.opacity = s.siren ? (.35 + .3*Math.sin(t*6)).toFixed(3) : 0;
  // субтитры по 1-3 слова
  const cp = s.caps.find(x => lt >= x.t0 && lt < x.t1);
  C.style.top = s.cap_top + 'px';
  if (cp) { C.innerHTML = cp.w.map(([w, k]) => k ? `<span class="k">${w}</span>` : w).join(' ');
    const u = eo(cl((lt - cp.t0)/.14)); C.style.transform = `scale(${(.82 + .18*u).toFixed(3)})`; C.style.opacity = u; }
  else C.style.opacity = 0;
};
"""


def page(scenes):
    body = []
    for i, s in enumerate(scenes):
        sc = lambda L: f"translateZ({DEPTH[L]}px) scale({(P - DEPTH[L]) / P * OVERSCAN[L]:.4f})"
        parts = [f'<div class="pl fill" style="transform:{sc("fill")}">{s["svg"]}</div>']
        if not s["outdoor"]:
            parts.append(f'<div class="pl bg" style="transform:{sc("bg")}">{s["svg"]}</div>')
            parts.append(f'<div class="floor" style="top:1364px;transform:translateZ({DEPTH["bg"]}px) rotateX(62deg)"></div>')
        parts.append(f'<div class="pl mid" style="transform:{sc("mid")}">{s["svg"]}</div>')
        parts.append(f'<div class="pl fg" style="transform:{sc("fg")}">{s["svg"]}</div>')
        dots = "".join(f'<div class="d" style="width:{r:.1f}px;height:{r:.1f}px;opacity:{0.15 + r / 25:.2f}" data-x="{x:.0f}" data-y="{y:.0f}" data-sp="{sp:.1f}" data-z="{[260, -320][k % 2]}"></div>'
                       for k, (x, y, r, sp) in enumerate(s["dust"]))
        parts.append(f'<div class="dust">{dots}</div>')
        body.append(f'<div class="sc" id="s{i}">{"".join(parts)}</div>')
    data = [{k: s[k] for k in ("t0", "d", "shots", "caps", "siren", "cap_top")} for s in scenes]
    js = JS.replace("DATA", json.dumps(data, ensure_ascii=False)).replace("PERSP", str(P)).replace("DEPTHS", json.dumps(DEPTH)).replace("OVERS", json.dumps(OVERSCAN))
    return (f'<!doctype html><meta charset="utf-8"><style>{CSS}</style><div id="stage"><div id="world">{"".join(body)}</div></div>'
            f'<div id="siren"></div><div id="vig"></div><div id="cap"></div><script>{js}</script>')


def render(slug, preview=None):
    v = ALL[slug]
    scenes = plan(v)
    total = scenes[-1]["t0"] + scenes[-1]["d"]
    os.makedirs(OUT, exist_ok=True)
    html = os.path.join(OUT, f"motion-{slug}.html")
    open(html, "w", encoding="utf8").write(page(scenes))
    out = os.path.join(OUT, f"bunker-{slug}{'-preview' if preview else ''}.mp4")
    subprocess.run(["node", os.path.join(HERE, "motion_render.js"), html, out, str(preview or total)], check=True)
    print("ok", os.path.basename(out), round(os.path.getsize(out) / 1e6, 1), "МБ")


if __name__ == "__main__":
    a = sys.argv[1:]
    pv = float(a[a.index("--preview") + 1]) if "--preview" in a else None
    slugs = [x for x in a if re.fullmatch(r"[A-Z]", x)]
    for s in slugs or ["A"]:
        render(s, pv)
