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
FPS = 24
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


def cam(x, y, z, yaw=0.0, pitch=0.0, f=760):
    return I.Cam(x=x, y=y, z=z, yaw=yaw, pitch=pitch, f=f)


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


KNOCKS = [S(0, 0.04) + k * 0.2 for k in range(3)] + [S(0, 0.58) + k * 0.2 for k in range(3)]


def frame(t):
    """Возвращает svg кадра для времени t."""
    i = next((k for k in range(len(D)) if t < T0[k] + D[k]), len(D) - 1)
    u = (t - T0[i]) / D[i]; dur = D[i]
    ov = ""; kw = dict(sky="#101014", particles=("dust", 45), vignette=0.68, grain=0, ptime=t)
    rim = "#ffd59a"

    if i == 0:  # стук: герой проходит к люку, смотрит вверх
        e = knock_env(t)
        c = cam(*kv([(0, (-1.0, 1.25, 0.9, 0, .06, 800)), (1, (0.1, 1.2, 0.3, 0, .08, 800))], u))
        c.vx += math.sin(t * 95) * 14 * e; c.vy += math.cos(t * 80) * 10 * e
        p = I.bunker(c)
        family(p, u, t)
        actor(p, "hero", [(0, -2.6, -1.4), (0.1, -2.6, -1.4), (0.45, 0.25, -1.5)], u, dur, t,
              faces=[(0, "neutral"), (0.15, "worried"), (0.6, "scared")], standview="front")
        if e > 0:
            x, y, _ = c.p(HX, 2.8, HZ)
            ov += f'<text x="{x + 60:.0f}" y="{y + 40:.0f}" font-family="{FONT}" font-weight="900" font-size="{70 + 30 * e:.0f}" fill="#ffffff" stroke="#0d0b0a" stroke-width="10" paint-order="stroke" transform="rotate(-8 {x:.0f} {y:.0f})">ТУК!</text>'
        ov += pill(t, S(0, .08), S(0, 1), "ЕДА: ≈11 000 ПОРЦИЙ", "w", 0) + pill(t, S(0, .35), S(0, 1), "5 ЧЕЛОВЕК · 2 ГОДА", "y", 1)
        return p.svg(overlay=ov + caption(t), **kw)

    if i == 1:  # сообщение от друга год назад
        c = cam(*kv([(0, (0.2, 1.4, 0.5, 0, .1, 760)), (1, (0.0, 1.4, 0.2, 0, .1, 760))], u))
        p = I.bunker(c); family(p, u, t)
        bg = p.svg(**kw)
        ph = phone_svg(t, u)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920" viewBox="0 0 1080 1920"><defs><filter id="pb"><feGaussianBlur stdDeviation="10"/></filter></defs>'
                f'<g filter="url(#pb)">{bg}</g><rect width="1080" height="1920" fill="#000" opacity=".35"/>{ph}{caption(t)}</svg>')

    if i == 2:  # у люка считает -> рынок -> супермаркет -> аптека
        if u < 0.22:
            w = u / 0.22
            c = cam(*kv([(0, (-0.6, 1.25, 0.6, 0, .05, 760)), (1, (-0.3, 1.2, 0.1, 0, .05, 760))], w))
            p = I.bunker(c); family(p, u, t)
            actor(p, "hero", [(0, 0.3, -1.6)], u, dur, t, faces=[(0, "thinking")], arms="count", prop="notebook")
            return p.svg(overlay=caption(t), **kw)
        if u < 0.48:
            w = (u - 0.22) / 0.26
            c = cam(*kv([(0, (0.3, 1.15, 1.5, 0, .04, 820)), (1, (0.1, 1.12, 1.2, 0, .04, 820))], w))
            p = I.market(c); rim = "#ffc890"
            actor(p, "vendor", [(0, 0.45, -2.0)], w, 1, t, faces=[(0, "happy")], talk=[(0.45, 0.8)], rim=rim, light=(-1, 1), off=1.3)
            actor(p, "hero", [(0, -1.9, -0.55), (0.5, -0.55, -0.55)], w, 1, t, standview="side", arms="money" if w > 0.55 else "down", rim=rim)
            ov = label_place(t, S(2, .23), S(2, .48), "РЫНОК")
            return p.svg(sky="#2c2c4a", particles=("snow", 140), vignette=0.6, grain=0, ptime=t, overlay=ov + caption(t))
        if u < 0.74:
            w = (u - 0.48) / 0.26
            hz = -5.3 + 1.9 * w
            c = cam(-0.85, 1.15, hz + 0.6 - 0.25 * w, yaw=math.pi / 2, pitch=-0.14, f=700)
            p = I.supermarket(c)
            actor(p, "hero", [(0, 0.45, -5.3), (1, 0.45, -3.4)], w, 1, t, faces=[(0, "serious")], cart=True, rim="#ffffff", light=(-1, 1))
            ov = label_place(t, S(2, .49), S(2, .74), "СУПЕРМАРКЕТ")
            return p.svg(sky="#d8d0c0", vignette=0.45, grain=0, overlay=ov + caption(t))
        w = (u - 0.74) / 0.26
        c = cam(*kv([(0, (0.3, 1.3, 0.6, 0, -.06, 820)), (1, (0.2, 1.3, 0.3, 0, -.06, 820))], w))
        p = I.pharmacy(c)
        actor(p, "pharm", [(0, 0.2, -2.95)], w, 1, t, faces=[(0, "neutral"), (0.6, "happy")], talk=[(0.55, 0.85)], rim="#ffffff", light=(-1, 1), off=2.1)
        actor(p, "hero", [(0, -0.2, -0.2), (0.55, -0.15, -1.55)], w, 1, t, view="back", standview="back", rim="#ffffff", light=(-1, 1))
        ov = label_place(t, S(2, .75), S(2, 1), "АПТЕКА")
        return p.svg(sky="#dfe9e2", vignette=0.55, grain=0, overlay=ov + caption(t))

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

    if i == 4:  # техкомната: вода, воздух, свет
        path = [(0, -2.6, -1.2), (0.22, -1.45, -1.2), (0.38, -1.45, -1.2), (0.52, 0.0, -1.2), (0.64, 0.0, -1.2), (0.78, 1.35, -1.2), (1, 1.35, -1.2)]
        hx_, _, _, _, _ = walk(path, u, dur)
        c = cam(hx_ * 0.75 + 0.2, 1.15, 0.6, 0, .05, 760)
        p = I.techroom(c)
        actor(p, "hero", path, u, dur, t, faces=[(0, "neutral"), (0.3, "thinking"), (0.85, "relieved")], standview="front")
        ov = (pill(t, S(4, .26), S(4, 1), "ВОДА — ЕСТЬ", "w", 0) + pill(t, S(4, .55), S(4, 1), "ВОЗДУХ — ЕСТЬ", "w", 1)
              + pill(t, S(4, .8), S(4, 1), "СВЕТ — ЕСТЬ", "w", 2) + pill(t, S(4, .9), S(4, 1), "−4 МЕСЯЦА ЕДЫ", "r", 3))
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

    if i == 6:  # друг спускается, «я всё знал», герой в шоке
        c = cam(*kv([(0, (-0.6, 1.3, -0.1, 0.28, .06, 760)), (1, (-0.45, 1.28, -0.55, 0.28, .05, 760))], u))
        p = I.bunker(c, hatch_open=True, red=True, torch=True); rim = "#ff8a6a"
        clip = c.p(HX, 2.8, -3.2)[1]
        if u < 0.4:
            Y = 2.0 * (1 - ss(u / 0.38))
            put(p, C.person("friend", "back", arms="climb", step=1.0, t=u * 4, rim=rim), HX, -3.2, Y, clip_y=clip)
            fx, fz = HX, -3.2
        else:
            w = (u - 0.4) / 0.6
            fx, fz, _, _, _ = walk([(0, HX, -3.2), (0.25, 0.6, -2.5)], w, 1)
            actor(p, "friend", [(0, HX, -3.2), (0.25, 0.6, -2.5)], w, 1, t, faces=[(0, "serious")], talk=[(0.27, 0.65)], rim=rim, off=0.9)
        actor(p, "hero", [(0, -0.6, -2.3)], u, dur, t, faces=[(0, "worried"), (0.58, "shocked")], rim=rim)
        ov += '<rect width="1080" height="1920" fill="#ff2a1a" opacity=".14" style="mix-blend-mode:multiply"/>'
        if u >= 0.56:
            x, y, d = c.p(fx, 1.95, fz)
            sc, op_ = pop(t, S(6, .56))
            ov += (f'<g opacity="{op_:.2f}" transform="translate({x + 40:.0f} {y - 60:.0f}) scale({sc:.3f})"><path d="M0 0 L280 0 Q300 0 300 20 L300 100 Q300 120 280 120 L70 120 L20 160 L36 120 L20 120 Q0 120 0 100 Z" fill="#f6f1e6" stroke="#14110f" stroke-width="5"/>'
                   f'<text x="150" y="76" text-anchor="middle" font-family="{FONT}" font-weight="800" font-size="46" fill="#1d1a17">Я всё знал.</text></g>')
        return p.svg(overlay=ov + caption(t), **kw)

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
        c = cam(*kv([(0, (0.0, 1.3, 3.6, 0, 0, 820)), (1, (-0.25, 1.3, 3.1, 0, 0, 820))], u))
        p = I.village(c); rim = "#fff0c0"
        wv = lambda a: "wave" if u > a else "down"
        put(p, C.person("hero", "front", face="happy", arms=wv(0.2), t=t, blink=blink(t, 0), rim=rim), -0.7, 1.0)
        put(p, C.person("n1", "front", face="happy", arms=wv(0.4), t=t + 0.3, blink=blink(t, 1.1), rim=rim), 0.9, -1.9)
        ov += '<rect width="1080" height="1920" fill="#e8c890" opacity=".35" style="mix-blend-mode:multiply"/>' + pill(t, S(8, .02), S(8, 1), "ГОД НАЗАД", "y", 0)
        return p.svg(sky="#9cc4e0", particles=None, vignette=0.5, grain=0, overlay=ov + caption(t))

    # i == 9: расчёт у стеллажа
    c = cam(*kv([(0, (0.1, 1.2, 0.6, 0, .05, 760)), (1, (-0.1, 1.2, 0.15, 0, .05, 760))], u))
    p = I.bunker(c); family(p, u, t, stand_at=(-9, -9, -9, -9))
    actor(p, "hero", [(0, -0.5, -2.9), (0.6, -0.4, -1.5)], u, dur, t, faces=[(0, "worried"), (0.6, "sad")])
    ov = (pill(t, S(9, .08), S(9, 1), "+3 СОСЕДА", "w", 0) + pill(t, S(9, .3), S(9, 1), "11 000 ÷ (9 × 3)", "w", 1)
          + pill(t, S(9, .55), S(9, 1), "≈ 13 МЕСЯЦЕВ", "r", 2))
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
    s = ('<g stroke="#14110f" stroke-width="10" stroke-linejoin="round" transform="translate(90 300)">'
         '<path d="M-40 1400 L120 1000 L300 1060 L230 1400 Z" fill="#6d8173"/><path d="M940 1400 L780 1000 L600 1060 L670 1400 Z" fill="#6d8173"/>'
         '<rect x="190" y="150" width="520" height="980" rx="60" fill="#15181d"/><rect x="225" y="215" width="450" height="860" rx="24" fill="#1d2633"/>'
         '<ellipse cx="205" cy="980" rx="95" ry="120" fill="#2b2b2b"/><ellipse cx="695" cy="980" rx="95" ry="120" fill="#2b2b2b"/></g>')
    s += f'<text x="540" y="590" text-anchor="middle" font-family="{FONT}" font-weight="700" font-size="34" fill="#9fb0c4">Друг · год назад</text>'
    y = 650
    for f0, txt in ((0.25, ["Через год", "начнётся война."]), (0.6, ["Никому."])):
        if u >= f0:
            sc, op = pop(u * D[1], f0 * D[1])
            h = 40 + 56 * len(txt); w = 380
            s += (f'<g opacity="{op:.2f}" transform="translate(345 {y}) scale({sc:.3f})"><rect x="0" y="0" width="{w}" height="{h}" rx="26" fill="#2f4a6a"/>'
                  + "".join(f'<text x="24" y="{62 + 56 * k}" font-family="{FONT}" font-weight="700" font-size="44" fill="#fff">{esc(line)}</text>' for k, line in enumerate(txt)) + "</g>")
        y += 200
    return s


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
    pr = subprocess.Popen(["node", os.path.join(HERE, "render_frames.js"), tmp, str(FPS)], stdin=subprocess.PIPE)
    for k in range(n):
        pr.stdin.write((json.dumps({"i": k, "svg": frame(k / FPS)}) + "\n").encode())
        if k % 120 == 0:
            print(f"кадр {k}/{n}", flush=True)
    pr.stdin.close(); pr.wait()
    kn = os.path.join(HERE, "video", "_knocks.wav"); knocks_wav(kn)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-i", VOICE, "-i", kn,
                    "-filter_complex", "[0:v]noise=alls=5:allf=t,format=yuv420p[v];[1:a]loudnorm=I=-14:TP=-1.5:LRA=11[va];[2:a]volume=0.7[k];[va][k]amix=inputs=2:duration=longest:normalize=0[a]",
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-aq-mode", "3",
                    "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-c:a", "aac", "-b:a", "192k",
                    "-t", f"{TOTAL:.2f}", "-movflags", "+faststart", OUT], check=True)
    os.remove(tmp)
    print(OUT)


if __name__ == "__main__":
    main()
