#!/usr/bin/env python3
"""Бункер A: пробный ролик на нарисованных фонах (illus) с 2D-персонажами (char).

python3 a_illus.py              -> video/bunker-A-test.mp4 (озвучка video/voice-A.mp3)
python3 a_illus.py --frames 3.5,20 -> отдельные кадры в illus_out/ для проверки
Тайминг сцен и субтитров берётся из озвучки по словам (motion.align).
"""
import math, os, sys, json, subprocess, struct, wave
import illus as I, char as C
import motion
import build_storyboard_3 as B3

HERE = os.path.dirname(os.path.abspath(__file__))
VOICE = os.path.join(HERE, "video", "voice-A.mp3")
OUT = os.path.join(HERE, "video", "bunker-A-test.mp4")
FPS = 30
SCALE = 4 / 3  # рендер 1440x2560 (векторы чётче, YouTube даёт лучший кодек), TikTok-версия даунскейлом в 1080
M = 1.75 / 1000
STRIDE = 2 * 2 * 412 * math.sin(0.42) * M  # метров за полный цикл шага: стопы не скользят

V = {v["slug"]: v for v in B3.VIDEOS60}["A"]
al = motion.align(V, VOICE)
D = al["d"]; T0 = [sum(D[:i]) for i in range(len(D))]
TOTAL = sum(D) + 1.0
HX, HZ, LZ = 1.0, -3.0, -3.2


# ---------- утилиты ----------
def ss(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)


def kv(K, u):
    """Ключи [(u, (значения...))] -> плавная интерполяция."""
    if u <= K[0][0]:
        return K[0][1]
    for (u0, a), (u1, b) in zip(K, K[1:]):
        if u <= u1:
            w = ss((u - u0) / (u1 - u0)) if u1 > u0 else 1
            return tuple(x + (y - x) * w for x, y in zip(a, b))
    return K[-1][1]


def step_of(K, u, default=None):
    v = default
    for uu, x in K:
        if u >= uu:
            v = x
    return v


CURT = [0.0]
KW = []  # времена красных ключевых слов: короткий наезд камеры


def punch(t):
    v = 0.0
    for k in KW:
        d = t - k
        if 0 <= d < 0.5:
            v = max(v, math.sin(min(1, d / 0.12) * math.pi / 2) * (1 - max(0, d - 0.12) / 0.38))
    return v


def cam(x, y, z, yaw=0.0, pitch=0.0, f=760):
    """Камера с «живым» дыханием (ручная съёмка) и наездом на ключевых словах."""
    t = CURT[0]
    return I.Cam(x=x + 0.012 * math.sin(t * 1.1), y=y + 0.008 * math.sin(t * 1.7 + 1), z=z, yaw=yaw + 0.004 * math.sin(t * 0.8),
                 pitch=pitch + 0.004 * math.sin(t * 1.3), f=f * (1 + 0.07 * punch(t)))


def shake(c, t, e):
    c.vx += math.sin(t * 95) * 16 * e; c.vy += math.cos(t * 80) * 12 * e


def walk(path, u, dur):
    """path [(u, x, z)] с постоянной скоростью на отрезках -> x, z, движется ли, фаза шага, направление (dx, dz)."""
    dist = 0.0
    if u <= path[0][0]:
        return path[0][1], path[0][2], False, 0.0, (0, 0)
    for (u0, x0, z0), (u1, x1, z1) in zip(path, path[1:]):
        L = math.hypot(x1 - x0, z1 - z0)
        if u <= u1:
            w = (u - u0) / (u1 - u0) if u1 > u0 else 1
            d = dist + L * w
            return x0 + (x1 - x0) * w, z0 + (z1 - z0) * w, L > 1e-4, d / STRIDE * math.tau, (x1 - x0, z1 - z0)
        dist += L
    return path[-1][1], path[-1][2], False, dist / STRIDE * math.tau, (0, 0)


def blink(t, off):
    return (t + off) % 3.3 < 0.11


def put(pic, svg, X, Z, Y=0.0, flip=False, dz=0.0, clip_y=None):
    x, y, d = pic.cam.p(X, Y, Z)
    g = C.place(svg, x, y, pic.cam.f / d * M, flip)
    if clip_y is not None:
        cid = C.uid("cl")
        g = f'<clipPath id="{cid}"><rect x="-2000" y="{clip_y:.0f}" width="6000" height="6000"/></clipPath><g clip-path="url(#{cid})">{g}</g>'
    pic.raw(d + dz, g)
    return x, y, d


def actor(pic, name, path, u, dur, t, faces=(), view="front", arms="down", prop=None, rim="#ffd59a", off=0.0,
          talk=(), Y=0.0, sit=0.0, light=(1, 1), standview=None, clip_y=None, cart=False):
    """Персонаж идёт по path; при ходьбе поперёк кадра — профиль, вдоль глубины — фронт/спина с шагом."""
    x, z, moving, ph, (dx, dz_) = walk(path, u, dur)
    face = step_of(list(faces), u, "neutral") if faces else "neutral"
    tk = 0.0
    for a, b in talk:
        if a <= u <= b:
            tk = 0.5 + 0.5 * math.sin(t * 19 + off)
    bl = blink(t, off)
    flip = False
    if moving:
        sx0 = pic.cam.p(x, 1.0, z)[0]; sx1 = pic.cam.p(x + dx * 0.01, 1.0, z + dz_ * 0.01)[0]
        lateral = abs(sx1 - sx0) > 0.002 * pic.cam.f
        if lateral:
            flip = sx1 < sx0
            svg = C.person(name, "side", face=face, phase=ph, arms="push" if cart else "down", prop=prop, blink=bl, talk=tk, rim=rim, light=light)
        else:
            v = "back" if dz_ < 0 and (standview or view) == "back" else view
            svg = C.person(name, v, face=face, arms=arms, prop=prop, blink=bl, talk=tk, rim=rim, light=light, step=1.0, t=ph / math.tau)
    else:
        v = standview or view
        if v == "side" or v == "sideL":
            flip = v == "sideL"
            svg = C.person(name, "side", face=face, arms=arms if arms in ("money", "hold", "push") else ("push" if cart else "down"), prop=prop,
                           blink=bl, talk=tk, rim=rim, light=light, sit=sit)
        else:
            svg = C.person(name, v, face=face, arms=arms, prop=prop, blink=bl, talk=tk, rim=rim, light=light, t=t * 0.9)
    if cart:
        svg = C.cart_side(300, 0) + svg
    return put(pic, svg, x, z, Y, flip, clip_y=clip_y)


# ---------- экранные элементы ----------
FONT = "Inter, 'DejaVu Sans', sans-serif"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def pop(t, t0, d=0.2):
    a = max(0.0, min(1.0, (t - t0) / d))
    return 0.6 + 0.4 * a + 0.12 * math.sin(a * math.pi), min(1.0, a * 2)


def pill(t, t0, t1, text, kind="w", slot=0):
    if not (t0 <= t < t1):
        return ""
    sc, op = pop(t, t0)
    fs = 52; w = int(len(text) * fs * 0.62 + 70); h = 92; y = 150 + slot * 112
    fill, fg = {"w": ("#f6f1e6", "#1d1a17"), "r": ("#d8362b", "#ffffff"), "y": ("#f2c94c", "#1d1a17")}[kind]
    return (f'<g opacity="{op:.2f}" transform="translate(540 {y + h / 2}) scale({sc:.3f})">'
            f'<rect x="{-w / 2}" y="{-h / 2}" width="{w}" height="{h}" rx="{h / 2}" fill="{fill}" stroke="#14110f" stroke-width="5"/>'
            f'<text x="0" y="{fs * 0.36:.0f}" text-anchor="middle" font-family="{FONT}" font-weight="800" font-size="{fs}" fill="{fg}">{esc(text)}</text></g>')


def caption(t):
    for i, cs in enumerate(al["caps"]):
        for c in cs:
            a, b = T0[i] + c["t0"], T0[i] + c["t1"]
            if a <= t < b:
                sc, op = pop(t, a, 0.12)
                tw = sum(len(w) + 1 for w, _ in c["w"]) * 86 * 0.64
                sc *= min(1.0, 980 / tw)
                y = {1: 1560, 7: 1500, 10: 1240}.get(i, 1200)
                spans = " ".join(f'<tspan fill="{"#ff3b30" if red else "#ffffff"}">{esc(w.upper())}</tspan>' for w, red in c["w"])
                return (f'<g transform="translate(540 {y}) scale({sc:.3f})"><text x="0" y="0" text-anchor="middle" font-family="{FONT}" font-weight="900" font-size="86" '
                        f'stroke="#0d0b0a" stroke-width="14" stroke-linejoin="round" paint-order="stroke" letter-spacing="1">{spans}</text></g>')
    return ""


def label_place(t, t0, t1, text):
    return pill(t, t0, t1, text, "y", 1)


# ---------- иконки-карточки по смыслу (вода, воздух, свет, еда) ----------
def word_time(i, prefix, nth=0):
    """Абсолютное время слова в озвучке (по субтитрам сцены i)."""
    n = 0
    for c in al["caps"][i]:
        ws = c["w"]
        for k, (w, _) in enumerate(ws):
            if w.lower().startswith(prefix.lower()):
                if n == nth:
                    return T0[i] + c["t0"] + (c["t1"] - c["t0"]) * k / max(1, len(ws))
                n += 1
    return T0[i] + D[i] * 0.5


def icon(kind, t):
    K = "#14110f"
    if kind == "drop":
        y = -20 + (t * 110) % 90
        return (f'<rect x="-80" y="-70" width="90" height="24" rx="6" fill="#9aa3ac" stroke="{K}" stroke-width="5"/><rect x="-6" y="-70" width="26" height="46" rx="5" fill="#9aa3ac" stroke="{K}" stroke-width="5"/>'
                f'<rect x="-40" y="-92" width="34" height="22" rx="4" fill="#c0392b" stroke="{K}" stroke-width="5"/>'
                f'<path d="M7 {y - 24} Q27 {y + 4} 7 {y + 14} Q-13 {y + 4} 7 {y - 24} Z" fill="#5ab8f0" stroke="{K}" stroke-width="5"/>'
                f'<ellipse cx="7" cy="82" rx="46" ry="10" fill="#5ab8f0" opacity=".6"/>')
    if kind == "bottle":
        return (f'<path d="M-46 -40 Q-46 -62 -24 -66 L-14 -82 L14 -82 L24 -66 Q46 -62 46 -40 L46 74 Q46 88 32 88 L-32 88 Q-46 88 -46 74 Z" fill="#bfe4f4" stroke="{K}" stroke-width="5"/>'
                f'<path d="M-44 -6 Q-22 -16 0 -6 Q22 4 44 -6 L44 74 Q44 86 32 86 L-32 86 Q-44 86 -44 74 Z" fill="#5ab8f0"/>'
                f'<rect x="-16" y="-96" width="32" height="18" rx="4" fill="#2c6aa0" stroke="{K}" stroke-width="5"/><rect x="-30" y="20" width="60" height="34" fill="#fff" stroke="{K}" stroke-width="3"/>'
                f'<text x="0" y="46" text-anchor="middle" font-family="Inter" font-weight="900" font-size="24" fill="#2c6aa0">5 Л</text>')
    if kind == "fan":
        a = t * 500
        return (f'<circle r="82" fill="#dfe6ea" stroke="{K}" stroke-width="6"/><g transform="rotate({a:.0f})">'
                + "".join(f'<path d="M0 0 Q-30 -40 0 -72 Q24 -40 0 0 Z" transform="rotate({k * 120})" fill="#8a9aa8" stroke="{K}" stroke-width="4"/>' for k in range(3))
                + f'</g><circle r="12" fill="#3a3e44"/>' + "".join(f'<path d="M95 {y} q20 -10 40 0 t40 0" fill="none" stroke="#5ab8f0" stroke-width="6" stroke-linecap="round" opacity="{0.4 + 0.6 * ((t * 3 + k) % 1):.2f}"/>' for k, y in enumerate((-30, 0, 30))))
    if kind == "bulb":
        g = 0.7 + 0.3 * math.sin(t * 12)
        return (f'<circle r="{95 * g:.0f}" fill="#ffe680" opacity=".35"/><path d="M-50 -10 A55 55 0 1 1 50 -10 Q34 18 28 40 L-28 40 Q-34 18 -50 -10 Z" fill="#ffd84a" stroke="{K}" stroke-width="5"/>'
                f'<rect x="-28" y="40" width="56" height="34" rx="6" fill="#9aa3ac" stroke="{K}" stroke-width="5"/><path d="M-14 30 L-6 -10 L6 -10 L14 30" fill="none" stroke="#c87a1a" stroke-width="4"/>')
    if kind == "gen":
        return (f'<rect x="-80" y="-50" width="160" height="110" rx="10" fill="#e0b040" stroke="{K}" stroke-width="5"/><rect x="-60" y="-30" width="70" height="60" fill="#2a2a2e" stroke="{K}" stroke-width="4"/>'
                f'<path d="M40 -32 L22 6 L40 6 L28 40 L60 -4 L42 -4 L54 -32 Z" fill="#fff6a0" stroke="{K}" stroke-width="4"/><rect x="40" y="-80" width="16" height="30" fill="#4a4a4e" stroke="{K}" stroke-width="4"/>'
                + f'<circle cx="{48 + 10 * ((t * 2) % 1):.0f}" cy="{-92 - 30 * ((t * 2) % 1):.0f}" r="{10 + 14 * ((t * 2) % 1):.0f}" fill="#9a9a9a" opacity="{1 - (t * 2) % 1:.2f}"/>')
    if kind == "can":
        return (f'<rect x="-56" y="-60" width="112" height="124" fill="#b8c0c8" stroke="{K}" stroke-width="5"/><ellipse cy="-60" rx="56" ry="16" fill="#d8dee4" stroke="{K}" stroke-width="5"/>'
                f'<path d="M-56 64 A56 16 0 0 0 56 64" fill="none" stroke="{K}" stroke-width="5"/><rect x="-56" y="-30" width="112" height="64" fill="#c0392b" stroke="{K}" stroke-width="4"/>'
                f'<text x="0" y="10" text-anchor="middle" font-family="Inter" font-weight="900" font-size="22" fill="#fff">ТУШЁНКА</text>')
    if kind == "mre":
        return (f'<path d="M-62 -70 L62 -70 L68 80 L-68 80 Z" fill="#6a7a3a" stroke="{K}" stroke-width="5" stroke-linejoin="round"/>'
                + "".join(f'<line x1="-62" y1="{-62 + k * 6}" x2="62" y2="{-62 + k * 6}" stroke="#4a5a2a" stroke-width="2"/>' for k in range(3))
                + f'<text x="0" y="22" text-anchor="middle" font-family="Inter" font-weight="900" font-size="54" fill="#f2ecd0">ИРП</text><text x="0" y="56" text-anchor="middle" font-family="Inter" font-weight="700" font-size="18" fill="#f2ecd0">СУТОЧНЫЙ</text>')
    if kind == "meal":
        st = "".join(f'<path d="M{x} -30 q-12 -20 0 -40 t0 -40" fill="none" stroke="#e8e8e8" stroke-width="5" stroke-linecap="round" opacity="{0.4 + 0.5 * math.sin(t * 4 + x):.2f}"/>' for x in (-26, 0, 26))
        return (st + f'<path d="M-80 -10 L80 -10 Q76 60 0 66 Q-76 60 -80 -10 Z" fill="#e8dcc4" stroke="{K}" stroke-width="5"/><ellipse cy="-10" rx="80" ry="16" fill="#c87a3a" stroke="{K}" stroke-width="5"/>'
                f'<circle cx="-24" cy="-14" r="8" fill="#7a9a3a"/><circle cx="18" cy="-12" r="9" fill="#a8322a"/>')
    if kind == "jar":
        return (f'<rect x="-46" y="-56" width="92" height="132" rx="16" fill="#7a9a3a" stroke="{K}" stroke-width="5"/>'
                + "".join(f'<ellipse cx="{x}" cy="14" rx="12" ry="44" fill="#a8c45a" stroke="#5a7a2a" stroke-width="3"/>' for x in (-22, 0, 22))
                + f'<rect x="-50" y="-78" width="100" height="26" rx="6" fill="#e8e4d8" stroke="{K}" stroke-width="5"/>')
    return ""


def card(t, t0, t1, kind, x, y, s=1.0, badge=None):
    if not (t0 <= t < t1):
        return ""
    sc, op = pop(t, t0, 0.22)
    out = min(1.0, (t1 - t) / 0.2)
    b = ""
    if badge:
        b = (f'<g transform="translate(70 -96)"><rect x="-56" y="-26" width="112" height="52" rx="26" fill="#d8362b" stroke="#14110f" stroke-width="4"/>'
             f'<text x="0" y="12" text-anchor="middle" font-family="Inter" font-weight="900" font-size="30" fill="#fff">{badge}</text></g>')
    return (f'<g opacity="{op * out:.2f}" transform="translate({x} {y}) scale({sc * s:.3f})"><rect x="-120" y="-120" width="240" height="240" rx="34" fill="#000" opacity=".25" transform="translate(8 10)"/>'
            f'<rect x="-120" y="-120" width="240" height="240" rx="34" fill="#f6f1e6" stroke="#14110f" stroke-width="6"/><g transform="scale(.95)">{icon(kind, t)}</g>{b}</g>')


def whip(svg, t):
    """Резкий панорамный переход между магазинами: смаз по горизонтали."""
    a, dirn = 0.0, 1
    for b in WHIPS:
        d = t - b
        if -0.13 < d < 0.13:
            a = 1 - abs(d) / 0.13; dirn = -1 if d < 0 else 1
    if a <= 0:
        return svg
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920" viewBox="0 0 1080 1920"><defs><filter id="wb" x="-30%" y="0" width="160%" height="100%">'
            f'<feGaussianBlur stdDeviation="{70 * a:.0f} 0"/></filter></defs><rect width="1080" height="1920" fill="#111"/><g filter="url(#wb)" transform="translate({-dirn * 260 * a:.0f} 0)">{svg}</g></svg>')



# ---------- сцены ----------
def S(i, f):
    return T0[i] + f * D[i]


def family(pic, u, t, stand_at=None, rim="#ffd59a", faces=None):
    out = []
    F = faces or {"grandpa": "tired", "mom": "worried", "girl": "scared", "kid": "scared"}
    for k, (n, x) in enumerate((("grandpa", -2.5), ("mom", -2.0), ("girl", -1.55), ("kid", -1.15))):
        sf = 1.0
        if stand_at:
            sf = 1.0 - ss((t - stand_at[k]) / 0.4)
        actor(pic, n, [(0, x, -3.25)], u, 1, t, faces=[(0, F[n])], standview="side", sit=sf, rim=rim, off=0.7 * k)


def knock_env(t):
    e = 0.0
    for a in KNOCKS:
        if a <= t < a + 0.25:
            e = max(e, 1 - (t - a) / 0.25)
    return e


WHIPS = []
KNOCKS = [S(0, 0.04) + k * 0.2 for k in range(3)] + [S(0, 0.58) + k * 0.2 for k in range(3)]


def frame(t):
    """Возвращает svg кадра для времени t."""
    CURT[0] = t
    i = next((k for k in range(len(D)) if t < T0[k] + D[k]), len(D) - 1)
    u = (t - T0[i]) / D[i]; dur = D[i]
    ov = ""; kw = dict(sky="#101014", particles=("dust", 45), vignette=0.68, grain=0, ptime=t)
    rim = "#ffd59a"

    if i == 0:  # стук: общий план -> люк снизу крупно (пыль) -> лицо крупно
        e = knock_env(t)
        tp = word_time(0, "порций"); tl = word_time(0, "люк")
        if u < 0.5:
            w = u / 0.5
            c = cam(*kv([(0, (-1.0, 1.25, 0.9, 0, .06, 800)), (1, (-0.2, 1.2, 0.4, 0, .07, 800))], w)); shake(c, t, e)
            p = I.bunker(c); family(p, u, t)
            actor(p, "hero", [(0, -2.6, -1.4), (0.1, -2.6, -1.4), (0.45, 0.25, -1.5)], u, dur, t, faces=[(0, "neutral"), (0.15, "worried")], standview="front")
        elif u < 0.72:
            w = (u - 0.5) / 0.22
            c = cam(*kv([(0, (0.8, 1.5, -1.75, 0.04, 0.85, 820)), (1, (0.85, 1.55, -1.9, 0.04, 0.9, 880))], w)); shake(c, t, e)
            p = I.bunker(c)
            hx_, hy_, _ = c.p(HX, 2.8, HZ)
            for a in KNOCKS:
                dt_ = t - a
                if 0 < dt_ < 1.3:
                    for k in range(10):
                        ox = (k * 37 % 160) - 80; yy = hy_ + 40 + dt_ * (300 + k * 25) + 200 * dt_ * dt_
                        ov += f'<circle cx="{hx_ + ox + 10 * math.sin(k + t * 3):.0f}" cy="{yy:.0f}" r="{2 + k % 3}" fill="#d8cdb8" opacity="{max(0, 0.8 - dt_ * 0.6):.2f}"/>'
        else:
            w = (u - 0.72) / 0.28
            c = cam(*kv([(0, (0.25, 1.48, -0.5, 0, .05, 1100)), (1, (0.25, 1.5, -0.68, 0, .06, 1150))], w)); shake(c, t, e)
            p = I.bunker(c); family(p, u, t)
            actor(p, "hero", [(0, 0.25, -1.5)], u, dur, t, faces=[(0, "scared")])
        if e > 0:
            x, y, _ = c.p(HX, 2.8, HZ)
            x = min(900, max(80, x)); y = min(1500, max(300, y))
            ov += f'<text x="{x + 30:.0f}" y="{y + 40:.0f}" font-family="{FONT}" font-weight="900" font-size="{80 + 40 * e:.0f}" fill="#ffffff" stroke="#0d0b0a" stroke-width="10" paint-order="stroke" transform="rotate(-8 {x:.0f} {y:.0f})">ТУК!</text>'
        ov += pill(t, S(0, .08), S(0, 1), "ЕДА: ≈11 000 ПОРЦИЙ", "w", 0) + pill(t, S(0, .35), S(0, 1), "5 ЧЕЛОВЕК · 2 ГОДА", "y", 1)
        ov += card(t, tp, tl, "can", 230, 1560, 0.85) + card(t, tp + 0.15, tl, "jar", 540, 1560, 0.85) + card(t, tp + 0.3, tl, "mre", 850, 1560, 0.85)
        return p.svg(overlay=ov + caption(t), **kw)

    if i == 1:  # телефон -> лицо в свете экрана -> наезд на «Никому.»
        if 0.45 <= u < 0.62:
            w = (u - 0.45) / 0.17
            c = cam(*kv([(0, (0.3, 1.5, -0.55, 0, .04, 1100)), (1, (0.3, 1.5, -0.7, 0, .04, 1150))], w))
            p = I.bunker(c); family(p, u, t)
            actor(p, "hero", [(0, 0.3, -1.6)], u, dur, t, faces=[(0, "worried")], arms="count", prop="phone")
            fx_, fy_, _ = c.p(0.3, 1.62, -1.6)
            ov += f'<circle cx="{fx_:.0f}" cy="{fy_ + 60:.0f}" r="420" fill="url(#pglow)" style="mix-blend-mode:screen"/>'
            return p.svg(overlay='<defs><radialGradient id="pglow"><stop offset="0" stop-color="#8ac4ff" stop-opacity=".45"/><stop offset="1" stop-color="#8ac4ff" stop-opacity="0"/></radialGradient></defs>' + ov + caption(t), **kw)
        c = cam(*kv([(0, (0.2, 1.4, 0.5, 0, .1, 760)), (1, (0.0, 1.4, 0.2, 0, .1, 760))], u))
        p = I.bunker(c); family(p, u, t)
        bg = p.svg(**kw)
        z = 1.0 if u < 0.45 else 1.0 + 0.5 * ss((u - 0.62) / 0.2)
        ph = f'<g transform="translate(540 820) scale({z:.3f}) translate(-540 -820)">{phone_svg(t, u)}</g>'
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920" viewBox="0 0 1080 1920"><defs><filter id="pb"><feGaussianBlur stdDeviation="10"/></filter></defs>'
                f'<g filter="url(#pb)">{bg}</g><rect width="1080" height="1920" fill="#000" opacity=".35"/>{ph}{caption(t)}</svg>')

    if i == 2:  # у люка считает -> рынок -> супермаркет -> аптека (с движением и резкими переходами)
        if u < 0.2:
            w = u / 0.2
            c = cam(*kv([(0, (-0.6, 1.25, 0.6, 0, .05, 760)), (1, (-0.2, 1.2, 0.0, 0, .05, 760))], w))
            p = I.bunker(c); family(p, u, t)
            actor(p, "hero", [(0, 0.3, -1.6)], u, dur, t, faces=[(0, "thinking")], arms="count", prop="notebook")
            return whip(p.svg(overlay=caption(t), **kw), t)
        if u < 0.46:  # рынок: подходит, платит, получает пакет, уходит
            w = (u - 0.2) / 0.26
            path = [(0, -2.7, -0.55), (0.3, -0.55, -0.55), (0.62, -0.55, -0.55), (1.0, 1.9, -0.55)]
            hx_, _, _, _, _ = walk(path, w, 1)
            c = cam(0.35 * hx_ + 0.15, 1.15, 1.45 - 0.3 * w, 0, .04, 820)
            p = I.market(c); rim = "#ffc890"
            give = 0.42 <= w < 0.6
            actor(p, "vendor", [(0, 0.45, -2.0)], w, 1, t, faces=[(0, "happy")], talk=[(0.3, 0.5)], rim=rim, light=(-1, 1), off=1.3,
                  arms="money" if give else "down", prop="bag1" if give else None)
            actor(p, "hero", path, w, 1, t, standview="side", arms="money" if 0.32 < w < 0.5 else "down", prop="bags" if w >= 0.58 else None, rim=rim,
                  faces=[(0, "neutral"), (0.55, "happy")])
            ov = label_place(t, S(2, .21), S(2, .46), "РЫНОК")
            return whip(p.svg(sky="#2c2c4a", particles=("snow", 140), vignette=0.6, grain=0, ptime=t, overlay=ov + caption(t)), t)
        if u < 0.72:  # супермаркет: едет с тележкой, берёт с полки, едет дальше
            w = (u - 0.46) / 0.26
            path = [(0, 0.45, -6.0), (0.38, 0.45, -4.9), (0.62, 0.45, -4.9), (1.0, 0.45, -3.3)]
            _, hz, _, _, _ = walk(path, w, 1)
            c = cam(-0.85, 1.15, hz + 0.55, yaw=math.pi / 2, pitch=-0.14, f=700)
            p = I.supermarket(c)
            if 0.4 < w < 0.6:
                put(p, C.cart_side(300, 0) + C.person("hero", "side", face="thinking", arms="take", rim="#ffffff", light=(-1, 1), blink=blink(t, 0)), 0.45, hz)
            else:
                actor(p, "hero", path, w, 1, t, faces=[(0, "serious")], cart=True, rim="#ffffff", light=(-1, 1))
            ov = label_place(t, S(2, .47), S(2, .72), "СУПЕРМАРКЕТ")
            return whip(p.svg(sky="#d8d0c0", vignette=0.45, grain=0, overlay=ov + caption(t)), t)
        w = (u - 0.72) / 0.28  # аптека: подходит к окошку, получает лекарства, уходит к камере
        c = cam(*kv([(0, (0.3, 1.3, 0.6, 0, -.06, 820)), (1, (0.15, 1.3, 0.9, 0, -.06, 820))], w))
        p = I.pharmacy(c)
        give = 0.36 <= w < 0.56
        actor(p, "pharm", [(0, 0.2, -2.95)], w, 1, t, faces=[(0, "neutral"), (0.3, "happy")], talk=[(0.3, 0.5)], rim="#ffffff", light=(-1, 1), off=2.1,
              arms="money" if give else "down", prop="box1" if give else None)
        if w < 0.6:
            actor(p, "hero", [(0, -1.2, -0.9), (0.32, -0.15, -1.55)], w, 1, t, view="back", standview="back", rim="#ffffff", light=(-1, 1))
        else:
            actor(p, "hero", [(0.6, -0.15, -1.55), (1.0, 0.0, -0.5)], w, 1, t, faces=[(0, "neutral")], prop="bag1", rim="#ffffff", light=(-1, 1))
        ov = label_place(t, S(2, .73), S(2, 1), "АПТЕКА")
        return whip(p.svg(sky="#dfe9e2", vignette=0.55, grain=0, overlay=ov + caption(t)), t)

    if i == 3:  # пересчёт: идёт вдоль стеллажа, семья встаёт по очереди, потом обратно
        path = [(0, -3.0, -2.55), (0.5, -0.5, -2.55), (0.56, -0.5, -2.55), (1.0, -2.7, -2.55)]
        hx_, _, _, _, _ = walk(path, u, dur)
        c = cam(max(-1.5, hx_ + 0.35), 1.15, -0.3, 0, .05, 760)
        p = I.bunker(c)
        xs = (-2.5, -2.0, -1.55, -1.15)
        stand = []
        for x in xs:  # момент, когда герой проходит мимо
            uu = (x + 0.15 - (-3.0)) / 2.5 * 0.5
            stand.append(S(3, uu))
        family(p, u, t, stand_at=stand)
        actor(p, "hero", path, u, dur, t, faces=[(0, "thinking"), (0.5, "worried")], standview="front", arms="count", prop="notebook")
        ov = (pill(t, S(3, .1), S(3, .55), "ЕДА: ≈11 000 ПОРЦИЙ", "w", 0) + pill(t, S(3, .6), S(3, 1), "НА 5 — 24 МЕСЯЦА", "w", 0)
              + pill(t, S(3, .78), S(3, 1), "НА 6 — 20 МЕСЯЦЕВ", "r", 1))
        return p.svg(overlay=ov + caption(t), **kw)

    if i == 4:  # вода (капли из крана, бутыль), воздух (вентилятор ФВУ), свет (генератор, лампа), затем еда у стеллажа
        tW, tA, tF, tE = word_time(4, "вода"), word_time(4, "воздух"), word_time(4, "четыре"), word_time(4, "пережить")
        tL = tA + 0.55 * (tF - tA)
        U = lambda tt: (tt - T0[4]) / D[4]
        if t < tF - 0.15:
            path = [(0, -2.6, -1.2), (U(tW) - 0.02, -1.45, -1.2), (U(tW) + 0.05, -1.45, -1.2), (U(tA) - 0.02, 0.0, -1.2), (U(tA) + 0.04, 0.0, -1.2), (U(tL) - 0.02, 1.3, -1.2), (1, 1.3, -1.2)]
            hx_, _, _, _, _ = walk(path, u, dur)
            c = cam(hx_ * 0.75 + 0.2, 1.15, 0.6, 0, .05, 760)
            fx = {"water": ss((t - tW + 0.3) / 0.3), "air": ss((t - tA + 0.3) / 0.3), "light": ss((t - tL + 0.2) / 0.3)}
            p = I.techroom(c, t=t, fx=fx)
            actor(p, "hero", path, u, dur, t, faces=[(0, "neutral"), (U(tW), "thinking"), (U(tL), "relieved")], standview="front")
            ov = (pill(t, tW, S(4, 1), "ВОДА — ЕСТЬ", "w", 0) + pill(t, tA, S(4, 1), "ВОЗДУХ — ЕСТЬ", "w", 1) + pill(t, tL, S(4, 1), "СВЕТ — ЕСТЬ", "w", 2)
                  + card(t, tW, tA, "drop", 330, 1560) + card(t, tW + 0.15, tA, "bottle", 750, 1560)
                  + card(t, tA, tL, "fan", 540, 1560, 1.1)
                  + card(t, tL, tF, "bulb", 330, 1560) + card(t, tL + 0.15, tF, "gen", 750, 1560))
            return p.svg(overlay=ov + caption(t), **kw)
        w = (t - tF) / max(0.5, S(4, 1) - tF)
        c = cam(*kv([(0, (-1.0, 1.25, -0.3, 0, .05, 760)), (1, (-1.1, 1.22, -0.7, 0, .05, 760))], w))
        p = I.bunker(c)
        family(p, u, t, stand_at=(-9, -9, -9, -9))
        actor(p, "hero", [(0, -0.35, -2.55)], w, 1, t, faces=[(0, "worried"), ((tE - tF) / max(0.5, S(4, 1) - tF), "relieved")])
        ov = (pill(t, tF, S(4, 1), "−4 МЕСЯЦА ЕДЫ", "r", 0)
              + card(t, tF + 0.05, S(4, 1) + 0.01, "can", 230, 1560, 0.9, "−") + card(t, tF + 0.2, S(4, 1) + 0.01, "mre", 540, 1560, 0.9, "−")
              + card(t, tF + 0.35, S(4, 1) + 0.01, "meal", 850, 1560, 0.9, "−"))
        return p.svg(overlay=ov + caption(t), **kw)

    if i == 5:  # открывает: лезет по лестнице, люк открывается, красный свет
        c = cam(*kv([(0, (2.2, 0.75, -0.6, -0.41, .38, 760)), (1, (2.1, 0.8, -0.8, -0.43, .42, 760))], u))
        op, red = u > 0.45, u > 0.6
        p = I.bunker(c, hatch_open=op, red=red, torch=red)
        Y = 0.75 * ss(min(1, u / 0.7))
        svg = C.person("hero", "back", arms="climb", step=1.0, t=u * 2.2, rim="#ff8a6a" if red else rim)
        put(p, svg, HX, -3.2, Y)
        if red:
            ov += '<rect width="1080" height="1920" fill="#ff2a1a" opacity=".14" style="mix-blend-mode:multiply"/>'
        return p.svg(overlay=ov + caption(t), **kw)

    if i == 6:  # друг спускается (общий) -> друг крупно «я всё знал» -> лицо героя в шоке
        rim = "#ff8a6a"
        redov = '<rect width="1080" height="1920" fill="#ff2a1a" opacity=".14" style="mix-blend-mode:multiply"/>'
        fpath = [(0, HX, -3.2), (0.25, 0.6, -2.5)]
        if u < 0.4:
            c = cam(*kv([(0, (-0.6, 1.3, -0.1, 0.28, .06, 760)), (1, (-0.5, 1.28, -0.4, 0.28, .05, 760))], u / 0.4))
            p = I.bunker(c, hatch_open=True, red=True, torch=True)
            clip = c.p(HX, 2.8, -3.2)[1]
            Y = 2.0 * (1 - ss(u / 0.38))
            put(p, C.person("friend", "back", arms="climb", step=1.0, t=u * 4, rim=rim), HX, -3.2, Y, clip_y=clip)
            actor(p, "hero", [(0, -0.6, -2.3)], u, dur, t, faces=[(0, "worried")], rim=rim)
            return p.svg(overlay=redov + caption(t), **kw)
        w = (u - 0.4) / 0.6
        if u < 0.75:
            ww = (u - 0.4) / 0.35
            c = cam(*kv([(0, (0.75, 1.5, -1.3, 0, .03, 1050)), (1, (0.7, 1.52, -1.5, 0, .03, 1100))], ww))
            p = I.bunker(c, hatch_open=True, red=True, torch=True)
            fx, fz, _, _, _ = walk(fpath, w, 1)
            actor(p, "friend", fpath, w, 1, t, faces=[(0, "serious")], talk=[(0.27, 0.6)], rim=rim, off=0.9)
            ov = redov
            if u >= 0.56:
                x, y, d = c.p(fx, 1.95, fz); x = min(700, x); y = max(260, y)
                sc, op_ = pop(t, S(6, .56))
                ov += (f'<g opacity="{op_:.2f}" transform="translate({x + 60:.0f} {y - 120:.0f}) scale({sc * 1.2:.3f})"><path d="M0 0 L280 0 Q300 0 300 20 L300 100 Q300 120 280 120 L70 120 L20 160 L36 120 L20 120 Q0 120 0 100 Z" fill="#f6f1e6" stroke="#14110f" stroke-width="5"/>'
                       f'<text x="150" y="76" text-anchor="middle" font-family="{FONT}" font-weight="800" font-size="46" fill="#1d1a17">Я всё знал.</text></g>')
            return p.svg(overlay=ov + caption(t), **kw)
        ww = (u - 0.75) / 0.25
        c = cam(*kv([(0, (-0.6, 1.5, -1.25, 0, .04, 1080)), (1, (-0.6, 1.5, -1.45, 0, .04, 1180))], ww)); shake(c, t, 0.35 * max(0, 1 - ww * 3))
        p = I.bunker(c, hatch_open=True, red=True, torch=True)
        actor(p, "hero", [(0, -0.6, -2.3)], u, dur, t, faces=[(0, "shocked")], rim=rim)
        return p.svg(overlay=redov + caption(t), **kw)

    if i in (7, 10):  # вид снизу в люк: фонарик и соседи
        appear = (S(7, .08), S(7, .25), S(7, .42)) if i == 7 else (-9, -9, -9)
        f = 1000 + 60 * u
        p, c = up_view(t, appear, f)
        ov += '<rect width="1080" height="1920" fill="#ff2a1a" opacity=".1" style="mix-blend-mode:multiply"/>'
        if i == 10:
            ov += pill(t, S(10, .08), TOTAL + 1, "СОСЕДЕЙ ПУСТИЛ БЫ?", "w", 0)
            if t >= S(10, .2):
                sc, op_ = pop(t, S(10, .2)); pulse = 1 + 0.04 * math.sin(t * 6)
                ov += (f'<g opacity="{op_:.2f}" transform="translate(540 1500) scale({sc * pulse:.3f})">'
                       f'<rect x="-330" y="-70" width="300" height="140" rx="30" fill="#2e8b57" stroke="#14110f" stroke-width="6"/><text x="-180" y="28" text-anchor="middle" font-family="{FONT}" font-weight="900" font-size="80" fill="#fff">ДА</text>'
                       f'<rect x="30" y="-70" width="300" height="140" rx="30" fill="#e8443a" stroke="#14110f" stroke-width="6"/><text x="180" y="28" text-anchor="middle" font-family="{FONT}" font-weight="900" font-size="80" fill="#fff">НЕТ</text></g>')
        return p.svg(sky="#0c0a0a", particles=("dust", 40), vignette=0.7, grain=0, ptime=t, overlay=ov + caption(t))

    if i == 8:  # год назад: машут через забор
        c = cam(*kv([(0, (-2.2, 1.5, 4.2, 0.55, 0.03, 820)), (1, (-2.0, 1.45, 3.6, 0.6, 0.03, 820))], u))
        p = I.village(c); rim = "#fff0c0"
        wv = lambda a: "wave" if u > a else "down"
        put(p, C.person("hero", "front", face="happy", arms=wv(0.2), t=t, blink=blink(t, 0), rim=rim), -1.5, 1.4)
        put(p, C.person("n1", "front", face="happy", arms=wv(0.4), t=t + 0.3, blink=blink(t, 1.1), rim=rim), 3.3, -1.9)
        ov += '<rect width="1080" height="1920" fill="#e8c890" opacity=".22" style="mix-blend-mode:multiply"/>' + pill(t, S(8, .02), S(8, 1), "ГОД НАЗАД", "y", 0)
        return p.svg(sky="#9cc4e0", particles=None, vignette=0.5, grain=0, overlay=ov + caption(t))

    # i == 9: расчёт: идёт к камере, затем лицо крупно
    ov = (pill(t, S(9, .08), S(9, 1), "+3 СОСЕДА", "w", 0) + pill(t, S(9, .3), S(9, 1), "11 000 ÷ (9 × 3)", "w", 1)
          + pill(t, S(9, .55), S(9, 1), "≈ 13 МЕСЯЦЕВ", "r", 2))
    if u < 0.6:
        c = cam(*kv([(0, (0.1, 1.2, 0.6, 0, .05, 760)), (1, (-0.1, 1.2, 0.3, 0, .05, 760))], u / 0.6))
        p = I.bunker(c); family(p, u, t, stand_at=(-9, -9, -9, -9))
        actor(p, "hero", [(0, -0.5, -3.0), (1.0, -0.4, -1.5)], u / 0.6, 1, t, faces=[(0, "worried")])
        return p.svg(overlay=ov + caption(t), **kw)
    w = (u - 0.6) / 0.4
    c = cam(*kv([(0, (-0.4, 1.5, -0.45, 0, .04, 1080)), (1, (-0.4, 1.5, -0.62, 0, .04, 1150))], w))
    p = I.bunker(c); family(p, u, t, stand_at=(-9, -9, -9, -9))
    actor(p, "hero", [(0, -0.4, -1.5)], u, dur, t, faces=[(0, "sad")])
    return p.svg(overlay=ov + caption(t), **kw)

def up_view(t, appear, f=1000):
    c = cam(1.0, 1.4, -2.35, 0, 1.3, f)
    Hc, hx, hz, r = 2.8, 1.0, -3.0, 0.42
    ring = [c.p(hx + math.cos(a) * r, Hc, hz + math.sin(a) * r) for a in [k / 48 * math.tau for k in range(48)]]
    cx = sum(q[0] for q in ring) / 48; cy = sum(q[1] for q in ring) / 48; rad = (max(q[0] for q in ring) - min(q[0] for q in ring)) / 2
    ppl = ""
    for k, (name, dx, dy, face, flip, sc) in enumerate((("n2", -0.55, -0.15, "angry", False, .58), ("n3", 0.58, -0.2, "serious", True, .58), ("n1", 0.0, -0.42, "angry", False, .66))):
        if t < appear[k]:
            continue
        a = ss((t - appear[k]) / 0.35)
        s_ = sc * rad / 152
        ppl += C.place(C.person(name, "front", face=face, arms="flashlight" if name == "n1" else "down", prop="flashlight" if name == "n1" else None,
                                rim="#ff9a7a", blink=blink(t, k)), cx + dx * rad, cy + (dy - 0.8 * (1 - a)) * rad + 924 * s_, s_, flip)
    return I.bunker_up(c, people_svg=ppl), c


def phone_svg(t, u):
    """Вид от первого лица: две руки держат телефон, большие пальцы на экране, рукава парки."""
    K = "#14110f"; SK = "#ecdcc0"; SL = "#6d8173"
    sway = 6 * math.sin(t * 1.6)
    hand = ""
    for sg in (-1, 1):
        X = (lambda x: x) if sg < 0 else (lambda x: 1080 - x)
        hand += (f'<path d="M{X(60)} 2000 L{X(250)} 1560" stroke="{K}" stroke-width="222" stroke-linecap="round"/><path d="M{X(60)} 2000 L{X(250)} 1560" stroke="{SL}" stroke-width="210" stroke-linecap="round"/>'
                 f'<path d="M{X(170)} 1640 L{X(320)} 1520" stroke="{K}" stroke-width="2" opacity=".0"/>'
                 f'<path d="M{X(150)} 1700 Q{X(250)} 1660 {X(350)} 1640" fill="none" stroke="{K}" stroke-width="4" opacity=".6"/>')
        # ладонь за телефоном и пальцы по внешнему краю
        hand += (f'<path d="M{X(330)} 1200 Q{X(205)} 1190 {X(196)} 1320 Q{X(190)} 1460 {X(250)} 1540 L{X(340)} 1560 Z" fill="{SK}" stroke="{K}" stroke-width="6" stroke-linejoin="round"/>'
                 + "".join(f'<path d="M{X(262)} {y} Q{X(206 - k * 2)} {y - 8} {X(204 - k * 2)} {y + 30} Q{X(206 - k * 2)} {y + 58} {X(262)} {y + 56}" fill="{SK}" stroke="{K}" stroke-width="5"/>' for k, y in enumerate((1070, 1135, 1200, 1265))))
    ph = (f'<rect x="262" y="380" width="556" height="1110" rx="62" fill="#15181d" stroke="{K}" stroke-width="8"/>'
          f'<rect x="290" y="420" width="500" height="1030" rx="40" fill="#17212b"/>'
          f'<rect x="290" y="420" width="500" height="130" rx="40" fill="#22303e"/><rect x="290" y="500" width="500" height="50" fill="#22303e"/>'
          f'<circle cx="360" cy="485" r="36" fill="#5c6a3e" stroke="#0d1218" stroke-width="3"/><text x="360" y="498" text-anchor="middle" font-family="Inter" font-weight="800" font-size="34" fill="#fff">Д</text>'
          f'<text x="414" y="476" font-family="Inter" font-weight="800" font-size="34" fill="#fff">Друг</text><text x="414" y="514" font-family="Inter" font-weight="600" font-size="24" fill="#7f91a4">был(а) год назад</text>'
          f'<rect x="460" y="575" width="160" height="40" rx="20" fill="#2a3a4a"/><text x="540" y="603" text-anchor="middle" font-family="Inter" font-weight="700" font-size="22" fill="#9fb0c4">12 марта</text>')
    y = 650
    for f0, txt, tm in ((0.25, ["Через год", "начнётся война."], "03:12"), (0.6, ["Никому."], "03:12")):
        if u >= f0:
            sc, op = pop(u * D[1], f0 * D[1])
            h = 50 + 56 * len(txt); w = 400 if len(txt) > 1 else 250
            ph += (f'<g opacity="{op:.2f}" transform="translate(312 {y}) scale({sc:.3f})"><rect x="0" y="0" width="{w}" height="{h}" rx="26" fill="#2b5278"/>'
                   + "".join(f'<text x="26" y="{62 + 56 * k}" font-family="Inter" font-weight="700" font-size="44" fill="#fff">{esc(line)}</text>' for k, line in enumerate(txt))
                   + f'<text x="{w - 18}" y="{h - 14}" text-anchor="end" font-family="Inter" font-weight="600" font-size="22" fill="#8fb0d0">{tm}</text></g>')
        y += 220
    thumbs = ""
    for sg in (-1, 1):
        X = (lambda x: x) if sg < 0 else (lambda x: 1080 - x)
        thumbs += (f'<path d="M{X(250)} 1520 Q{X(300)} 1420 {X(380)} 1330" fill="none" stroke="{K}" stroke-width="86" stroke-linecap="round"/>'
                   f'<path d="M{X(250)} 1520 Q{X(300)} 1420 {X(380)} 1330" fill="none" stroke="{SK}" stroke-width="74" stroke-linecap="round"/>'
                   f'<ellipse cx="{X(376)}" cy="{1338}" rx="20" ry="16" transform="rotate({-40 * -sg} {X(376)} 1338)" fill="#f6e8d4" stroke="{K}" stroke-width="3"/>'
                   f'<path d="M{X(300)} 1440 q{-sg * -14} 4 {-sg * -22} -6" fill="none" stroke="{K}" stroke-width="3" opacity=".6"/>')
    return f'<g transform="translate(0 {sway:.1f})">{hand}{ph}{thumbs}</g>'


# ---------- звук: глухие удары в люк ----------
def knocks_wav(path):
    sr = 44100; n = int(TOTAL * sr); buf = [0.0] * n
    for a in KNOCKS:
        s0 = int(a * sr)
        for k in range(int(0.4 * sr)):
            tt = k / sr
            v = 0.9 * math.sin(2 * math.pi * 52 * tt) * math.exp(-14 * tt) + 0.35 * math.sin(2 * math.pi * 140 * tt) * math.exp(-30 * tt)
            if s0 + k < n:
                buf[s0 + k] += v
    with wave.open(path, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, x)) * 30000)) for x in buf))


WHIPS[:] = [S(2, .2), S(2, .46), S(2, .72)]
for _i, _cs in enumerate(al["caps"]):
    for _c in _cs:
        for _k, (_w, _red) in enumerate(_c["w"]):
            if _red:
                KW.append(T0[_i] + _c["t0"] + (_c["t1"] - _c["t0"]) * _k / max(1, len(_c["w"])))


def main():
    if "--frames" in sys.argv:
        ts = [float(x) for x in sys.argv[sys.argv.index("--frames") + 1].split(",")]
        fs = []
        for tt in ts:
            fn = os.path.join(HERE, "illus_out", f"t{tt:05.1f}.svg"); open(fn, "w").write(frame(tt)); fs.append(fn)
        subprocess.run(["node", os.path.join(HERE, "render_frames.js"), "--png", *fs], check=True)
        return
    tmp = os.path.join(HERE, "video", "_a_video.mp4")
    n = int(TOTAL * FPS)
    pr = subprocess.Popen(["node", os.path.join(HERE, "render_frames.js"), tmp, str(FPS), str(SCALE)], stdin=subprocess.PIPE)
    for k in range(n):
        pr.stdin.write((json.dumps({"i": k, "svg": frame(k / FPS)}) + "\n").encode())
        if k % 120 == 0:
            print(f"кадр {k}/{n}", flush=True)
    pr.stdin.close(); pr.wait()
    kn = os.path.join(HERE, "video", "_knocks.wav"); knocks_wav(kn)
    common = ["-c:v", "libx264", "-preset", "slow", "-tune", "animation", "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", str(FPS), "-g", str(FPS * 2),
              "-x264-params", "aq-mode=3:aq-strength=0.9:deblock=-1,-1", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
              "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-t", f"{TOTAL:.2f}", "-movflags", "+faststart"]
    af = "[1:a]loudnorm=I=-14:TP=-1.5:LRA=11[va];[2:a]volume=0.7[k];[va][k]amix=inputs=2:duration=longest:normalize=0[a]"
    yt = OUT.replace(".mp4", "-youtube-1440p.mp4"); tt = OUT.replace(".mp4", "-tiktok-1080p.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-i", VOICE, "-i", kn, "-filter_complex", "[0:v]null[v];" + af,
                    "-map", "[v]", "-map", "[a]", "-crf", "16", "-maxrate", "40M", "-bufsize", "80M", *common, yt], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-i", VOICE, "-i", kn, "-filter_complex", "[0:v]scale=1080:1920:flags=lanczos[v];" + af,
                    "-map", "[v]", "-map", "[a]", "-crf", "17", "-maxrate", "20M", "-bufsize", "40M", *common, tt], check=True)
    os.remove(tmp)
    print(yt, tt)


if __name__ == "__main__":
    main()
