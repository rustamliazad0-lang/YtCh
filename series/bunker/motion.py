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
import build_storyboard_4 as B4
ALL = {v["slug"]: v for v in B1.VIDEOS + B2.VIDEOS2 + B4.VIDEOS60}  # минутные версии с постановкой перекрывают старые
import build_img_A as BIA
ALL.update({v["slug"]: v for v in BIA.VIDEOS})  # A на иллюстрациях
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


VOW = set("аеёиоуыэюя")


def syl(w):
    return max(1, sum(ch in VOW for ch in w.lower())) + 0.35


def align(v, audio=None):
    """Время каждого слова. С голосом: слова раскладываются по звучащим участкам записи пропорционально
    слогам (тишину из silencedetect пропускаем). Без голоса: темп ~0,2 с на слог и паузы на знаках.
    Возвращает длительности сцен и субтитры (по 1-3 слова) во времени сцены."""
    words = [(i, w) for i, sc in enumerate(v["scenes"]) for w in sc[2].split()]
    W = [syl(w) for _, w in words]
    if audio:
        T = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", audio],
                                 capture_output=True, text=True).stdout)
        log = subprocess.run(["ffmpeg", "-hide_banner", "-i", audio, "-af", "silencedetect=noise=-35dB:d=0.1", "-f", "null", "-"],
                             capture_output=True, text=True).stderr
        st_ = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
        en_ = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
        sil = list(zip(st_, en_ + [T] * (len(st_) - len(en_))))
        voiced, cur = [], 0.0
        for a, b in sil:
            if a > cur + 0.02:
                voiced.append((cur, a))
            cur = max(cur, b)
        if cur < T - 0.02:
            voiced.append((cur, T))
        total_v = sum(b - a for a, b in voiced)
        def at(f):  # доля звучащего времени -> секунды записи
            need = f * total_v
            for a, b in voiced:
                if need <= b - a:
                    return a + need
                need -= b - a
            return voiced[-1][1]
        tw, acc, st, en = sum(W), 0.0, [], []
        for w in W:
            st.append(at(acc / tw)); acc += w; en.append(at(acc / tw) - 0.02)
        end = T + 0.8
    else:
        t, st, en = 0.3, [], []
        for (_, w), ww in zip(words, W):
            st.append(t); t += 0.16 * ww; en.append(t)  # 0,16 с на слог: замер по записи A
            t += 0.38 if re.search(r"[.?!:]$", w) else (0.18 if w.endswith(",") else 0.0)
        end = t + 0.8
    first = {}
    for k, (i, _) in enumerate(words):
        first.setdefault(i, k)
    n = len(v["scenes"])
    bounds = [0.0] + [(en[first[i] - 1] + st[first[i]]) / 2 for i in range(1, n)] + [end]
    durs = [round(b - a, 3) for a, b in zip(bounds, bounds[1:])]
    caps = []
    for i in range(n):
        ks = [k for k, (j, _) in enumerate(words) if j == i]
        groups, cur = [], []
        for k in ks:
            cur.append(k)
            if len(cur) == 3 or re.search(r"[.,:?!]$", words[k][1]):
                groups.append(cur); cur = []
        if cur:
            groups.append(cur)
        cs = []
        for gi, g in enumerate(groups):
            t0 = max(0.0, st[g[0]] - 0.04 - bounds[i])
            t1 = (st[groups[gi + 1][0]] - 0.04 - bounds[i]) if gi + 1 < len(groups) else durs[i] - 0.05
            ws = [(words[k][1], bool(re.search(r"\d", words[k][1])) or re.sub(r"[^\w]", "", words[k][1].lower()) in KEY) for k in g]
            cs.append({"t0": round(t0, 3), "t1": round(t1, 3), "w": ws})
        caps.append(cs)
    return {"d": durs, "caps": caps}


def plan(v, al):
    scenes, t0, names = [], 0.0, list(CAMS)
    for i, sc in enumerate(v["scenes"]):
        fn, tm, narr = sc[0], sc[1], sc[2]
        acts = sc[5] if len(sc) > 5 else []
        d = al["d"][i]
        cam = names[i % len(names)]
        shots = [{"t0": 0.0, "t1": d, "cam": CAMS[cam]}]
        if len(sc) > 6 and sc[6]:  # планы заданы сценой (иллюстрации): делим сцену поровну
            k = len(sc[6])
            shots = [{"t0": round(d * j / k, 3), "t1": round(d * (j + 1) / k, 3), "cam": sc[6][j]} for j in range(k)]
        elif d >= 4:
            cut = round(d * 0.55, 2)
            other = CAMS[names[(i + 3) % len(names)]]  # второй план: другой ракурс, а не приближение
            shots = [{"t0": 0.0, "t1": cut, "cam": CAMS[cam]}, {"t0": cut, "t1": d, "cam": other}]
            if d >= 8:  # длинная сцена: три ракурса, ни один план не дольше ~4 с
                c1, c2 = round(d * 0.34, 2), round(d * 0.68, 2)
                third = CAMS[names[(i + 5) % len(names)]]
                shots = [{"t0": 0.0, "t1": c1, "cam": CAMS[cam]}, {"t0": c1, "t1": c2, "cam": other}, {"t0": c2, "t1": d, "cam": third}]
        caps = al["caps"][i]
        # время действий задано долями сцены, переводим в секунды
        acts_s = [{**a, "t0": round(a.get("t0", 0) * d, 3), "t1": round(a.get("t1", 1) * d, 3)} for a in acts]
        markup = svg(fn)
        # субтитр уходит наверх, если в его полосе (1060-1420 px) есть текст самой сцены
        art = re.sub(r'<g data-l="cap">.*?</g>', "", markup, flags=re.S)
        ts = [(int(float(y)) * 3 + 120, int(fs)) for y, fs in re.findall(r'<text x="[^"]+" y="([\d.]+)"[^>]*font-size="(\d+)"', art)]
        clash = lambda lo, hi: sum(fs for y, fs in ts if lo <= y + 10 and y - fs * 3 <= hi)  # текст занимает [y-fs*3, y]
        spots = [1150, 250, 1000, 1300, 700]  # по порядку предпочтения; первое место без текста сцены
        cap_top = next((y for y in spots if clash(y, y + 220) == 0), min(spots, key=lambda y: clash(y, y + 220)))
        rnd = random.Random(i * 7 + len(narr))
        dust = [[rnd.uniform(0, 1080), rnd.uniform(0, 1920), rnd.uniform(2, 6), rnd.uniform(8, 40)] for _ in range(36)]
        scenes.append({"t0": t0, "d": d, "shots": shots, "caps": caps, "svg": markup, "dust": dust, "acts": acts_s,
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
[data-a]{{transform-box:fill-box;transform-origin:50% 100%}}
.lgL,.lgR{{transform-box:fill-box;transform-origin:50% 0%}}
.amL,.amR{{transform-box:fill-box;transform-origin:50% 6%}}
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
function runActs(i, lt) {
  const s = S[i], root = els[i], by = {};
  for (const a of (s.acts || [])) (by[a.a] = by[a.a] || []).push(a);
  for (const id in by) {
    const list = by[id].sort((p, q) => p.t0 - q.t0), st = {x: 0, y: 0, r: 0, s: 1, sx: 1, sy: 1, o: 1};
    const mv = list.filter(a => a.k === 'move'); let walk = false, org = null;
    if (mv.length && lt < mv[0].t0) Object.assign(st, mv[0].f || {});
    for (const a of list) {
      if (a.org) org = a.org;
      if (lt < a.t0) continue;
      const u = cl((lt - a.t0)/Math.max(.001, a.t1 - a.t0)), on = lt <= a.t1;
      if (a.k === 'move') { const e = a.e === 'lin' ? u : (a.e === 'o' ? eo(u) : ease(u));
        for (const k in a.to) { const f = (a.f && a.f[k] !== undefined) ? a.f[k] : st[k]; st[k] = f + (a.to[k] - f)*e; } }
      else if (a.k === 'walk' && on) walk = true;
      else if (a.k === 'spin' && on) st.r += 360*(a.rps || 1)*(lt - a.t0);
      else if (a.k === 'shake' && on) st.x += (a.amp || 4)*Math.sin(lt*(a.hz || 70))*(1 - u*0.5);
      else if (a.k === 'bob' && on) st.y -= Math.abs(Math.sin(lt*(a.hz || 6)))*(a.amp || 6);
      else if (a.k === 'pulse' && on) st.s *= 1 + (a.amp || .08)*Math.sin(lt*(a.hz || 8));
    }
    const ph = Math.sin(lt*2*Math.PI*1.7), ang = walk ? 24*ph : 0, dy = walk ? -Math.abs(ph)*3 : 0;
    root.querySelectorAll(`[data-a="${id}"]`).forEach(n => {
      if (org) n.style.transformOrigin = org;
      n.style.transform = `translate(${st.x.toFixed(2)}px,${(st.y + dy).toFixed(2)}px) rotate(${st.r.toFixed(2)}deg) scale(${(st.sx*st.s).toFixed(4)},${(st.sy*st.s).toFixed(4)})`;
      n.style.opacity = st.o;
      n.querySelectorAll('.lgL').forEach(q => q.style.transform = `rotate(${ang}deg)`);
      n.querySelectorAll('.lgR').forEach(q => q.style.transform = `rotate(${-ang}deg)`);
      n.querySelectorAll('.amL').forEach(q => q.style.transform = `rotate(${-ang*.7}deg)`);
      n.querySelectorAll('.amR').forEach(q => q.style.transform = `rotate(${ang*.7}deg)`);
    });
  }
}
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
  // люди слегка дышат; всё остальное движение задают действия сцены
  people[i].forEach((p, k) => { p.style.transform = `translate(0px,${(Math.sin(lt*2 + k)*1.5).toFixed(2)}px)`; });
  runActs(i, lt);
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
    uniq = lambda m, k: m.replace('id="', f'id="q{k}_').replace("url(#", f"url(#q{k}_")  # id не повторяются между слоями
    for i, s in enumerate(scenes):
        sc = lambda L: f"translateZ({DEPTH[L]}px) scale({(P - DEPTH[L]) / P * OVERSCAN[L]:.4f})"
        parts = [f'<div class="pl fill" style="transform:{sc("fill")}">{uniq(s["svg"], f"{i}0")}</div>']
        if not s["outdoor"]:
            parts.append(f'<div class="pl bg" style="transform:{sc("bg")}">{uniq(s["svg"], f"{i}1")}</div>')
            parts.append(f'<div class="floor" style="top:1364px;transform:translateZ({DEPTH["bg"]}px) rotateX(62deg)"></div>')
        parts.append(f'<div class="pl mid" style="transform:{sc("mid")}">{uniq(s["svg"], f"{i}2")}</div>')
        parts.append(f'<div class="pl fg" style="transform:{sc("fg")}">{uniq(s["svg"], f"{i}3")}</div>')
        dots = "".join(f'<div class="d" style="width:{r:.1f}px;height:{r:.1f}px;opacity:{0.15 + r / 25:.2f}" data-x="{x:.0f}" data-y="{y:.0f}" data-sp="{sp:.1f}" data-z="{[260, -320][k % 2]}"></div>'
                       for k, (x, y, r, sp) in enumerate(s["dust"]))
        parts.append(f'<div class="dust">{dots}</div>')
        body.append(f'<div class="sc" id="s{i}">{"".join(parts)}</div>')
    data = [{k: s[k] for k in ("t0", "d", "shots", "caps", "siren", "cap_top", "acts")} for s in scenes]
    js = JS.replace("DATA", json.dumps(data, ensure_ascii=False)).replace("PERSP", str(P)).replace("DEPTHS", json.dumps(DEPTH)).replace("OVERS", json.dumps(OVERSCAN))
    return (f'<!doctype html><meta charset="utf-8"><style>{CSS}</style><div id="stage"><div id="world">{"".join(body)}</div></div>'
            f'<div id="siren"></div><div id="vig"></div><div id="cap"></div><script>{js}</script>')


def render(slug, preview=None):
    v = ALL[slug]
    voice = os.path.join(OUT, f"voice-{slug}.mp3")
    has_voice = os.path.exists(voice) and not preview
    scenes = plan(v, align(v, voice if has_voice else None))
    total = scenes[-1]["t0"] + scenes[-1]["d"]
    os.makedirs(OUT, exist_ok=True)
    html = os.path.join(OUT, f"motion-{slug}.html")
    open(html, "w", encoding="utf8").write(page(scenes))
    out = os.path.join(OUT, f"bunker-{slug}{'-preview' if preview else ''}.mp4")
    silent = out.replace(".mp4", "-silent.mp4") if has_voice else out
    subprocess.run(["node", os.path.join(HERE, "motion_render.js"), html, silent, str(preview or total)], check=True)
    if has_voice:  # голос: громкость -14 LUFS (норма YouTube), AAC 192k, длина по видео
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", voice, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,apad", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest",
                        "-movflags", "+faststart", out], check=True)
        os.remove(silent)
    print("ok", os.path.basename(out), round(os.path.getsize(out) / 1e6, 1), "МБ", "с голосом" if has_voice else "без голоса")


if __name__ == "__main__":
    a = sys.argv[1:]
    pv = float(a[a.index("--preview") + 1]) if "--preview" in a else None
    slugs = [x for x in a if re.fullmatch(r"[A-Z]", x)]
    for s in slugs or ["A"]:
        render(s, pv)
