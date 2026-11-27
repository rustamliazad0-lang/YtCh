#!/usr/bin/env python3
"""2D-персонажи в манере референса.

Круглая светлая голова, тонкий тёмный контур, простое лицо: тяжёлые веки над полукруглым зрачком,
короткие густые брови, маленький нос-крючок, короткий рот, точки щетины. Одежда реалистичная:
парка с клапанами карманов, молния, резинка, манжеты, спортивные штаны с лампасами, грубые ботинки.
Шапок нет. Виды: front, side (профиль вправо, настоящая походка: ноги идут вперёд-назад), back.

Локальные координаты: ступни в (0,0), y вниз, рост взрослого 1000 единиц = 1.75 м.
"""
import math, random

INK = "#2b231d"
SW, FINE = 3.0, 1.8
_uid = [0]


def uid(p="c"):
    _uid[0] += 1
    return f"{p}{_uid[0]}"


def hexrgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def shade(c, k):
    r, g, b = hexrgb(c); return "#%02x%02x%02x" % tuple(max(0, min(255, int(v * k))) for v in (r, g, b))


def mix(a, b, u):
    A, B = hexrgb(a), hexrgb(b); return "#%02x%02x%02x" % tuple(int(A[i] + (B[i] - A[i]) * u) for i in range(3))


def pts(P):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in P)


def pl(P):
    return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in P)


def limb(P, w, col, sw=SW):
    """Конечность с контуром: два штриха (тёмный шире, цветной уже)."""
    d = pl(P)
    return (f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{w + 2 * sw:.1f}" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{w:.1f}" stroke-linecap="round" stroke-linejoin="round"/>')


def offset(P, d):
    out = []
    for i, (x, y) in enumerate(P):
        a = P[max(0, i - 1)]; b = P[min(len(P) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy) or 1
        out.append((x - dy / L * d, y + dx / L * d))
    return out


def along(P, t):
    """Точка на ломаной по доле длины."""
    seg = [math.dist(P[i], P[i + 1]) for i in range(len(P) - 1)]; s = sum(seg) * t
    for i, L in enumerate(seg):
        if s <= L or i == len(seg) - 1:
            u = s / L if L else 0; return (P[i][0] + (P[i + 1][0] - P[i][0]) * u, P[i][1] + (P[i + 1][1] - P[i][1]) * u)
        s -= L


def sub(P, t0, t1, n=6):
    return [along(P, t0 + (t1 - t0) * k / n) for k in range(n + 1)]


def ik(S, T, L1, L2, bend):
    """Две кости. bend: 'low' — локоть ниже (руки опущены, у груди), 'out' — локоть наружу от тела (рука вверх),
    'fwd' — локоть вперёд (профиль), или число ±1 (старый режим)."""
    dx, dy = T[0] - S[0], T[1] - S[1]
    d = max(abs(L1 - L2) + 1e-3, min(math.hypot(dx, dy), L1 + L2 - 1e-3)); a = math.atan2(dy, dx)
    b = math.acos(max(-1.0, min(1.0, (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d))))
    cand = [(S[0] + L1 * math.cos(a + sg * b), S[1] + L1 * math.sin(a + sg * b)) for sg in (1, -1)]
    if bend == "low":
        E = max(cand, key=lambda e: e[1])
    elif bend == "out":
        E = max(cand, key=lambda e: abs(e[0]) * (1 if S[0] * e[0] >= 0 else -1))
    elif bend == "fwd":
        E = max(cand, key=lambda e: e[0])
    else:
        E = cand[0] if bend > 0 else cand[1]
    return [S, E, (S[0] + d * math.cos(a), S[1] + d * math.sin(a))]


def fk(S, a1, L1, a2, L2):
    """Углы от вертикали вниз; плюс = вперёд (+x)."""
    E = (S[0] + L1 * math.sin(a1), S[1] + L1 * math.cos(a1))
    return [S, E, (E[0] + L2 * math.sin(a2), E[1] + L2 * math.cos(a2))]


# ---------- внешность ----------
BASE = dict(h=1000, skin="#ecdcc0", hair="short", hairc="#3b2c22", top="parka", topc="#6d8173", inner="#26292b",
            pants="#3b4866", stripes=True, boots="#a8774a", sole="#d9bb8c", hands="#2b2b2b", stubble=False,
            mustache=None, beard=None, glasses=False, lashes=False, lips=None, apron=None, badge=False, coatlen=-478)
LOOKS = {
    # как в первой части: герой в красной толстовке и джинсах, дед седой в оливковой куртке, Макс в камуфляже
    "hero": dict(hair="short", hairc="#2e221c", top="hoodie", topc="#b8322a", inner="#7a1e1a", pants="#2c3a56", stripes=False,
                 boots="#f2f2ee", sole="#bdbdbd", hands="#ecdcc0", stubble=False),
    "friend": dict(h=1010, hair="buzz", hairc="#2a2420", topc="#5c6a3e", camo=True, pants="#4e5a36", stripes=False, boots="#2a2622", sole="#4a4038",
                   hands="#e4d0b0", stubble=True),
    "grandpa": dict(h=960, hair="short", hairc="#e8e6e0", top="coat", topc="#6e6a3c", inner="#efefe8", pants="#55555a", stripes=False,
                    boots="#5a4030", sole="#7a6a58", hands="#e2cfb2", skin="#e8d2b2", coatlen=-420),
    "mom": dict(h=940, hair="long", hairc="#5a3a24", top="coat", topc="#c8962e", inner="#d8c8b0", pants="#363644", stripes=False,
                boots="#3e3028", sole="#6a5a4a", hands="#ecdcc0", lashes=True, lips="#b0605a", coatlen=-330),
    "kid": dict(h=700, hair="short", hairc="#7a5434", top="hoodie", topc="#3c6a98", inner="#2c4e72", pants="#46566e", stripes=False,
                boots="#e8e8e4", sole="#bdbdbd", hands="#ecdcc0"),
    "girl": dict(h=620, hair="tails", hairc="#6a4428", top="coat", topc="#c8607a", inner="#f0d8dc", pants="#5a4a6a", stripes=False,
                 boots="#f0ece4", sole="#c8c0b4", hands="#ecdcc0", lashes=True, coatlen=-390),
    "vendor": dict(h=930, hair="bun", hairc="#4a3020", top="coat", topc="#7a6248", inner="#c8b090", pants="#3a3a3a", stripes=False,
                   boots="#3a2e26", sole="#5a4a3a", hands="#ecdcc0", apron="#a83a2a", lashes=True, coatlen=-400),
    "cashier": dict(h=940, hair="tails", hairc="#2e2018", top="vest", topc="#2f8a5a", inner="#f2f2ee", pants="#2e2e36", stripes=False,
                    boots="#2a2a2a", sole="#555", hands="#ecdcc0", lashes=True, badge=True),
    "pharm": dict(h=950, hair="bun", hairc="#8a6a3a", top="labcoat", topc="#f2f2ee", inner="#9ac0d8", pants="#3a4a5a", stripes=False,
                  boots="#e8e8e8", sole="#bbb", hands="#ecdcc0", glasses=True, lashes=True, coatlen=-360),
    "n1": dict(h=1030, hair="bald", hairc="#4a3a30", top="coat", topc="#3a3a42", inner="#6a2a2a", pants="#2e2e34", stripes=False,
               boots="#2a2420", sole="#4a4038", beard="#4a3a30", coatlen=-420),
    "n2": dict(h=950, hair="long", hairc="#2a2224", top="coat", topc="#7a7a80", inner="#c0b0a0", pants="#34343c", stripes=False,
               boots="#3a2a26", sole="#5a4a42", hands="#ecdcc0", lashes=True, coatlen=-360),
    "n3": dict(h=990, hair="short", hairc="#6a4a2a", topc="#b8682a", inner="#2a2a2a", pants="#2e3a4a", stripes=True, boots="#3a3a3a", sole="#777", stubble=True),
}

FACES = {
    # bi/bo: брови у переносицы/снаружи (минус = выше); ui/uo: верхнее веко у переносицы/снаружи; lo: нижнее веко;
    # pr: зрачок; white: видны белки; low: линия нижнего века (прищур); wr: морщины на лбу; fr: складка между бровями
    "neutral":    dict(bi=0, bo=0, ui=-1, uo=-1, lo=10, pr=9, mouth="line"),
    "worried":    dict(bi=-15, bo=4, ui=-8, uo=0, lo=13, pr=8, white=True, wr=2, mouth="worry"),
    "anxious":    dict(bi=-16, bo=5, ui=-9, uo=-1, lo=13, pr=7, white=True, wr=2, gaze=5, mouth="grimace", sweat=True),
    "scared":     dict(bi=-19, bo=-5, eye="wide", rx=12, ry=12, tilt=12, pr=5.5, wr=3, mouth="fear", sweat=True),
    "shocked":    dict(bi=-18, bo=-17, eye="wide", rx=13, ry=14, tilt=0, pr=5, wr=3, mouth="drop"),
    "angry":      dict(bi=12, bo=-7, ui=4, uo=-4, lo=6, pr=8.5, white=True, low=True, fr=True, mouth="teeth"),
    "sad":        dict(bi=-13, bo=6, ui=-3, uo=4, lo=10, pr=8, white=True, gy=3, wr=1, mouth="sad", tear=True),
    "happy":      dict(bi=-6, bo=-4, eye="happy", mouth="grin", cheeks=True),
    "tired":      dict(bi=1, bo=5, ui=4, uo=5, lo=10, pr=8.5, mouth="tired", bags=True),
    "serious":    dict(bi=6, bo=-2, ui=0, uo=-2, lo=8, pr=8.5, low=True, mouth="firm"),
    "determined": dict(bi=10, bo=-5, ui=2, uo=-3, lo=7, pr=8.5, white=True, low=True, fr=True, mouth="set"),
    "relieved":   dict(bi=-9, bo=3, eye="closed", wr=1, mouth="smile_s"),
    "thinking":   dict(bi=-2, bo=-12, ui=-2, uo=-4, lo=10, pr=8, white=True, gaze=6, gy=-4, mouth="side"),
}


def look(name):
    d = dict(BASE); d.update(LOOKS.get(name, {})); return d


# ---------- голова ----------
R = 76


def stubble_dots(cx, cy, side=False, n=46, seed=5):
    rnd = random.Random(seed); s = ""
    for _ in range(n):
        for _ in range(20):
            x, y = rnd.uniform(-R, R), rnd.uniform(14, R)
            if side:
                x = rnd.uniform(8, R)
            if math.hypot(x, y) < R - 9 and not (abs(x - (14 if side else 0)) < 22 and 26 < y < 50) and (abs(x) > 22 or y > 50 or side):
                break
        s += f'<circle cx="{cx + x:.1f}" cy="{cy + y:.1f}" r="1.7" fill="{INK}" opacity=".55"/>'
    return s


def hair_front(L, cx, cy, back=False):
    h, c = L["hair"], L["hairc"]; Rr = R + 4; s = ""
    if h in ("short", "long", "tails", "bun", "buzz"):
        a0, a1 = (175, 365) if not back else (160, 380)
        arc = [(cx + Rr * math.cos(math.radians(a)), cy + Rr * math.sin(math.radians(a))) for a in range(a0, a1 + 1, 8)]
        if back:
            line = [(cx + 70, cy + 30), (cx + 30, cy + 40), (cx - 30, cy + 40), (cx - 70, cy + 30)]
        elif h in ("long", "tails"):
            line = [(cx + 72, cy + 8), (cx + 62, cy - 36), (cx + 20, cy - 50), (cx - 6, cy - 38), (cx - 40, cy - 54), (cx - 66, cy - 32), (cx - 72, cy + 8)]
        else:
            line = [(cx + 68, cy - 8), (cx + 62, cy - 34), (cx + 34, cy - 52), (cx, cy - 56), (cx - 34, cy - 52), (cx - 62, cy - 34), (cx - 68, cy - 8)]
        op = ' opacity=".75"' if h == "buzz" else ""
        s += f'<polygon points="{pts(arc + line)}" fill="{c}" stroke="{INK}" stroke-width="{SW}" stroke-linejoin="round"{op}/>'
        if h == "bun":
            s = f'<circle cx="{cx}" cy="{cy - 80}" r="27" fill="{c}" stroke="{INK}" stroke-width="{SW}"/>' + s
    elif h == "bald":
        for sg in (-1, 1):
            P = [(cx + sg * 77, cy - 22), (cx + sg * 80, cy), (cx + sg * 72, cy + 26), (cx + sg * 62, cy + 18), (cx + sg * 64, cy - 4), (cx + sg * 66, cy - 20)]
            s += f'<polygon points="{pts(P)}" fill="{c}" stroke="{INK}" stroke-width="{FINE}" stroke-linejoin="round"/>'
        if back:
            s += f'<path d="M{cx - 72} {cy + 10} Q{cx} {cy + 44} {cx + 72} {cy + 10} L{cx + 60} {cy + 44} Q{cx} {cy + 64} {cx - 60} {cy + 44} Z" fill="{c}" stroke="{INK}" stroke-width="{FINE}"/>'
        else:
            s += "".join(f'<path d="M{cx - 22} {cy - k} Q{cx} {cy - k - 4} {cx + 22} {cy - k}" fill="none" stroke="{INK}" stroke-width="1.4" opacity=".5"/>' for k in (44, 52))
    return s


def hair_behind(L, cx, cy):
    h, c = L["hair"], L["hairc"]
    if h == "long":
        return f'<path d="M{cx - 80} {cy - 14} Q{cx - 98} {cy + 70} {cx - 90} {cy + 128} L{cx + 90} {cy + 128} Q{cx + 98} {cy + 70} {cx + 80} {cy - 14} Z" fill="{c}" stroke="{INK}" stroke-width="{SW}"/>'
    if h == "tails":
        s = ""
        for sg in (-1, 1):
            s += (f'<ellipse cx="{cx + sg * 92}" cy="{cy + 34}" rx="17" ry="36" transform="rotate({sg * -14} {cx + sg * 92} {cy + 34})" fill="{c}" stroke="{INK}" stroke-width="{SW}"/>'
                  f'<circle cx="{cx + sg * 84}" cy="{cy + 2}" r="7" fill="#d8484a" stroke="{INK}" stroke-width="{FINE}"/>')
        return s
    return ""


def eye(cx, cy, F, sg, blink, gaze):
    ex, ey = cx + sg * 30, cy + 2; kind = F.get("eye", "open"); s = ""
    gz = F.get("gaze", 0) + gaze; gy = F.get("gy", 0)
    if blink and kind in ("open", "wide"):
        kind = "blink"
    if kind == "open":
        ui, uo, lo = F.get("ui", -1), F.get("uo", -1), F.get("lo", 10)
        xi, xo = ex - sg * 15, ex + sg * 15          # у переносицы / снаружи
        top = [(xi, ey + ui), (ex, ey + (ui + uo) / 2 - 2), (xo, ey + uo)]
        cid = uid("ey")
        um = (ui + uo) / 2 - 2                        # середина верхнего века
        shape = f"M{xi:.1f} {ey + ui:.1f} Q{ex:.1f} {ey + (ui + uo) / 2 - 4:.1f} {xo:.1f} {ey + uo:.1f} C{xo - sg * 1:.1f} {ey + lo + 4:.1f} {xi + sg * 1:.1f} {ey + lo + 4:.1f} {xi:.1f} {ey + ui:.1f} Z"
        s += f'<clipPath id="{cid}"><path d="{shape}"/></clipPath>'
        pr = F.get("pr", 9)
        py = (ey + um + ey + 0.75 * (lo + 4) + 0.125 * (ui + uo)) / 2 + gy if F.get("white") else ey + um + 3 + gy   # белки: зрачок по центру; тяжёлое веко: срезан пополам
        s += (f'<g clip-path="url(#{cid})"><circle cx="{ex + gz:.1f}" cy="{py:.1f}" r="{pr}" fill="{INK}"/>'
              f'<circle cx="{ex + gz + pr * 0.35:.1f}" cy="{py - pr * 0.4:.1f}" r="{max(1.4, pr * 0.28):.1f}" fill="#ffffff" opacity=".55"/></g>')
        s += f'<path d="M{xi - sg * 1:.1f} {ey + ui:.1f} Q{ex:.1f} {ey + (ui + uo) / 2 - 4:.1f} {xo + sg * 2:.1f} {ey + uo + 1:.1f}" fill="none" stroke="{INK}" stroke-width="4.6" stroke-linecap="round"/>'
        if F.get("low"):
            s += f'<path d="M{xi:.1f} {ey + ui:.1f} C{xi + sg * 1:.1f} {ey + lo + 4:.1f} {xo - sg * 1:.1f} {ey + lo + 4:.1f} {xo:.1f} {ey + uo:.1f}" fill="none" stroke="{INK}" stroke-width="{2.8 if F.get("low") else 1.8}" stroke-linecap="round"/>'
        if F.get("_lashes"):
            s += f'<line x1="{xo + sg * 1:.1f}" y1="{ey + uo:.1f}" x2="{xo + sg * 7:.1f}" y2="{ey + uo - 5:.1f}" stroke="{INK}" stroke-width="2.6" stroke-linecap="round"/>'
    elif kind == "wide":  # испуг/шок: зрачок-точка, над ним высокая дуга века, без белков и обводки
        rx, ry, tl = F.get("rx", 12), F.get("ry", 14), F.get("tilt", 0) * -sg
        pr = F.get("pr", 6)
        s += (f'<g transform="rotate({tl} {ex} {ey})"><circle cx="{ex + gz:.1f}" cy="{ey + 2 + gy:.1f}" r="{pr}" fill="{INK}"/>'
              f'<circle cx="{ex + gz + pr * .4:.1f}" cy="{ey + 2 + gy - pr * .45:.1f}" r="{pr * .3:.1f}" fill="#fff" opacity=".6"/>'
              f'<path d="M{ex - rx} {ey + 1} A{rx} {ry} 0 0 1 {ex + rx} {ey + 1}" fill="none" stroke="{INK}" stroke-width="4.4" stroke-linecap="round"/></g>')
    elif kind == "blink":
        s += f'<path d="M{ex - 14} {ey + 3} Q{ex} {ey + 7} {ex + 14} {ey + 3}" fill="none" stroke="{INK}" stroke-width="4.4" stroke-linecap="round"/>'
    elif kind == "happy":
        s += f'<path d="M{ex - 14} {ey + 6} Q{ex} {ey - 12} {ex + 14} {ey + 6}" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>'
        s += f'<path d="M{ex - 10} {ey + 16} Q{ex} {ey + 12} {ex + 10} {ey + 16}" fill="none" stroke="{INK}" stroke-width="1.6" opacity=".6"/>'
    elif kind == "closed":
        s += f'<path d="M{ex - 14} {ey} Q{ex} {ey + 10} {ex + 14} {ey}" fill="none" stroke="{INK}" stroke-width="4.6" stroke-linecap="round"/>'
    if F.get("bags"):
        s += f'<path d="M{ex - 12} {ey + 16} Q{ex} {ey + 22} {ex + 12} {ey + 16}" fill="none" stroke="#7a5a4a" stroke-width="2" opacity=".7"/>'
    if F.get("tear") and sg > 0:
        s += f'<path d="M{ex + 6} {ey + 14} Q{ex + 12} {ey + 28} {ex + 6} {ey + 32} Q{ex} {ey + 28} {ex + 6} {ey + 14} Z" fill="#bfe4f4" stroke="{INK}" stroke-width="1.6"/>'
    by = ey - 25; bi, bo = F.get("bi", 0), F.get("bo", 0)
    xi, xo = ex - sg * 12, ex + sg * 16
    s += f'<path d="M{xi} {by + bi} Q{ex + sg * 2} {by + (bi + bo) / 2 - 3} {xo} {by + bo}" fill="none" stroke="{INK}" stroke-width="7.5" stroke-linecap="round"/>'
    return s


def mouth(mx, my, F, talk):
    k = F.get("mouth", "line"); D_ = "#4a2420"; T = "#f6f2e8"
    if talk > 0.05 and k not in ("O", "scream", "teeth", "grimace"):
        h = 3 + talk * 10
        return f'<path d="M{mx - 13} {my} Q{mx} {my - 3} {mx + 13} {my} Q{mx} {my + h * 2:.1f} {mx - 13} {my} Z" fill="{D_}" stroke="{INK}" stroke-width="2.6" stroke-linejoin="round"/>'
    st = f'fill="none" stroke="{INK}" stroke-width="3.6" stroke-linecap="round"'
    return {
        "line": f'<line x1="{mx - 13}" y1="{my}" x2="{mx + 13}" y2="{my}" {st}/>',
        "firm": f'<path d="M{mx - 16} {my + 1} L{mx + 16} {my + 1}" {st}/><path d="M{mx - 18} {my - 2} l3 4 M{mx + 18} {my - 2} l-3 4" fill="none" stroke="{INK}" stroke-width="2" stroke-linecap="round"/>',
        "set": f'<path d="M{mx - 17} {my + 3} Q{mx} {my - 2} {mx + 17} {my + 3}" {st}/>',
        "worry": f'<path d="M{mx - 17} {my + 4} Q{mx - 9} {my - 3} {mx - 1} {my + 1} Q{mx + 8} {my + 4} {mx + 17} {my + 5}" {st}/>',
        "sad": f'<path d="M{mx - 18} {my + 7} Q{mx} {my - 7} {mx + 18} {my + 7}" {st}/><path d="M{mx - 7} {my + 9} Q{mx} {my + 7} {mx + 7} {my + 9}" fill="none" stroke="{INK}" stroke-width="1.6" opacity=".6"/>',
        "tired": f'<path d="M{mx - 12} {my + 1} Q{mx} {my + 4} {mx + 12} {my + 1}" {st}/>',
        "smile_s": f'<path d="M{mx - 14} {my - 2} Q{mx} {my + 9} {mx + 14} {my - 2}" {st}/>',
        "grin": f'<path d="M{mx - 20} {my - 5} Q{mx} {my - 1} {mx + 20} {my - 5} Q{mx + 14} {my + 18} {mx} {my + 18} Q{mx - 14} {my + 18} {mx - 20} {my - 5} Z" fill="{D_}" stroke="{INK}" stroke-width="3"/><path d="M{mx - 17} {my - 3} Q{mx} {my + 1} {mx + 17} {my - 3} L{mx + 14} {my + 4} Q{mx} {my + 7} {mx - 14} {my + 4} Z" fill="{T}"/>',
        "side": f'<path d="M{mx - 8} {my + 2} Q{mx + 4} {my + 1} {mx + 16} {my - 4}" {st}/>',
        "grimace": f'<rect x="{mx - 18}" y="{my - 6}" width="36" height="13" rx="4" fill="{T}" stroke="{INK}" stroke-width="2.8"/><path d="M{mx - 18} {my} L{mx + 18} {my} M{mx - 6} {my - 6} l0 13 M{mx + 6} {my - 6} l0 13" stroke="{INK}" stroke-width="1.4"/><path d="M{mx - 20} {my - 6} l-4 6 M{mx + 20} {my - 6} l4 6" fill="none" stroke="{INK}" stroke-width="2.4" stroke-linecap="round"/>',
        "fear": f'<path d="M{mx - 15} {my + 6} Q{mx} {my - 6} {mx + 15} {my + 6} Q{mx} {my + 13} {mx - 15} {my + 6} Z" fill="{D_}" stroke="{INK}" stroke-width="2.8" stroke-linejoin="round"/><path d="M{mx - 18} {my + 8} l-3 3 M{mx + 18} {my + 8} l3 3" fill="none" stroke="{INK}" stroke-width="2" stroke-linecap="round"/>',
        "drop": f'<ellipse cx="{mx}" cy="{my + 9}" rx="11" ry="17" fill="{D_}" stroke="{INK}" stroke-width="3"/><path d="M{mx - 6} {my - 2} Q{mx} {my - 4} {mx + 6} {my - 2}" fill="none" stroke="#f6f2e8" stroke-width="3" stroke-linecap="round"/>',
        "scream": f'<path d="M{mx - 18} {my - 2} Q{mx} {my - 6} {mx + 18} {my - 2} L{mx + 14} {my + 16} Q{mx} {my + 21} {mx - 14} {my + 16} Z" fill="{D_}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/><path d="M{mx - 16} {my - 1} Q{mx} {my - 5} {mx + 16} {my - 1} L{mx + 15} {my + 4} L{mx - 15} {my + 4} Z" fill="{T}"/><path d="M{mx - 19} {my - 3} l-5 7 M{mx + 19} {my - 3} l5 7" fill="none" stroke="{INK}" stroke-width="2.4" stroke-linecap="round"/>',
        "O": f'<ellipse cx="{mx}" cy="{my + 6}" rx="13" ry="18" fill="{D_}" stroke="{INK}" stroke-width="3"/><ellipse cx="{mx}" cy="{my + 16}" rx="8" ry="5" fill="#c0605a"/>',
        "teeth": f'<path d="M{mx - 21} {my + 6} L{mx - 15} {my - 4} L{mx + 15} {my - 4} L{mx + 21} {my + 6} L{mx + 15} {my + 10} L{mx - 15} {my + 10} Z" fill="{T}" stroke="{INK}" stroke-width="2.8" stroke-linejoin="round"/><path d="M{mx - 18} {my + 3} L{mx + 18} {my + 3} M{mx - 6} {my - 4} l0 14 M{mx + 6} {my - 4} l0 14" stroke="{INK}" stroke-width="1.4"/>',
    }.get(k, f'<line x1="{mx - 13}" y1="{my}" x2="{mx + 13}" y2="{my}" {st}/>')


def head_front(L, F, blink=False, talk=0.0, gaze=0, back=False):
    cx, cy = 0, -R  # от точки шеи
    F = dict(F); F["_skin"] = L["skin"]; F["_lashes"] = L["lashes"]
    s = hair_behind(L, cx, cy) if not back else ""
    for sg in (-1, 1):
        s += f'<ellipse cx="{cx + sg * 75}" cy="{cy + 4}" rx="11" ry="15" fill="{L["skin"]}" stroke="{INK}" stroke-width="{SW}"/>'
    s += f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="{L["skin"]}" stroke="{INK}" stroke-width="{SW}"/>'
    if back:
        return s + hair_front(L, cx, cy, back=True)
    if L["stubble"]:
        s += stubble_dots(cx, cy)
    if L["beard"]:
        s += f'<path d="M{cx - 66} {cy + 8} Q{cx - 60} {cy + 86} {cx} {cy + 90} Q{cx + 60} {cy + 86} {cx + 66} {cy + 8} Q{cx + 40} {cy + 30} {cx + 22} {cy + 32} Q{cx} {cy + 26} {cx - 22} {cy + 32} Q{cx - 40} {cy + 30} {cx - 66} {cy + 8} Z" fill="{L["beard"]}" stroke="{INK}" stroke-width="{FINE}"/>'
    if F.get("pale"):
        pass
    for k in range(F.get("wr", 0)):  # морщины на лбу
        y = cy - 36 - k * 7
        s += f'<path d="M{cx - 18 + k * 3} {y} Q{cx} {y - 4} {cx + 18 - k * 3} {y}" fill="none" stroke="{INK}" stroke-width="1.8" opacity=".55"/>'
    if F.get("fr"):
        s += f'<path d="M{cx - 5} {cy - 22} l2 10 M{cx + 5} {cy - 22} l-2 10" stroke="{INK}" stroke-width="2" opacity=".6"/>'
    if F.get("cheeks"):
        s += "".join(f'<ellipse cx="{cx + sg * 46}" cy="{cy + 24}" rx="13" ry="7" fill="#e8907a" opacity=".45"/>' for sg in (-1, 1))
    s += hair_front(L, cx, cy)
    for sg in (-1, 1):
        s += eye(cx, cy, F, sg, blink, gaze)
    if L["glasses"]:
        s += "".join(f'<circle cx="{cx + sg * 30}" cy="{cy + 3}" r="19" fill="#ffffff" fill-opacity=".12" stroke="{INK}" stroke-width="2.6"/>' for sg in (-1, 1))
        s += f'<line x1="{cx - 11}" y1="{cy + 1}" x2="{cx + 11}" y2="{cy + 1}" stroke="{INK}" stroke-width="2.4"/>'
    s += f'<path d="M{cx + 2} {cy + 10} Q{cx + 8} {cy + 19} {cx} {cy + 23}" fill="none" stroke="{INK}" stroke-width="2.6" stroke-linecap="round"/>'
    if L["mustache"]:
        s += f'<path d="M{cx - 26} {cy + 40} Q{cx - 14} {cy + 26} {cx} {cy + 32} Q{cx + 14} {cy + 26} {cx + 26} {cy + 40} Q{cx} {cy + 36} {cx - 26} {cy + 40} Z" fill="{L["mustache"]}" stroke="{INK}" stroke-width="{FINE}"/>'
    s += mouth(cx, cy + 42, F, talk)
    if L["lips"] and F.get("mouth") in ("line", "smile_s", "firm") and talk < 0.05:
        s += f'<line x1="{cx - 9}" y1="{cy + 43}" x2="{cx + 9}" y2="{cy + 43}" stroke="{L["lips"]}" stroke-width="3" stroke-linecap="round"/>'
    if L["h"] < 800:
        s += "".join(f'<ellipse cx="{cx + sg * 46}" cy="{cy + 28}" rx="11" ry="6" fill="#e89a8a" opacity=".45"/>' for sg in (-1, 1))
    if F.get("sweat"):
        s += f'<path d="M{cx + 62} {cy - 44} Q{cx + 72} {cy - 26} {cx + 62} {cy - 22} Q{cx + 52} {cy - 26} {cx + 62} {cy - 44} Z" fill="#bfe4f4" stroke="{INK}" stroke-width="2"/>'
    return s


def head_side(L, F, blink=False, talk=0.0):
    """Профиль, лицо вправо."""
    cx, cy = 4, -R
    F = dict(F); F["_skin"] = L["skin"]; F["_lashes"] = L["lashes"]; s = ""
    h, c = L["hair"], L["hairc"]
    if h == "long":
        s += f'<path d="M{cx - 30} {cy - 60} Q{cx - 100} {cy - 10} {cx - 74} {cy + 128} L{cx + 10} {cy + 120} L{cx + 10} {cy} Z" fill="{c}" stroke="{INK}" stroke-width="{SW}"/>'
    if h == "tails":
        s += f'<ellipse cx="{cx - 84}" cy="{cy + 30}" rx="17" ry="36" transform="rotate(18 {cx - 84} {cy + 30})" fill="{c}" stroke="{INK}" stroke-width="{SW}"/>'
    if h == "bun":
        s += f'<circle cx="{cx - 58}" cy="{cy - 58}" r="26" fill="{c}" stroke="{INK}" stroke-width="{SW}"/>'
    # нос выступает за круг
    s += f'<path d="M{cx + 70} {cy - 8} Q{cx + 90} {cy + 12} {cx + 74} {cy + 20}" fill="{L["skin"]}" stroke="{INK}" stroke-width="{SW}" stroke-linejoin="round"/>'
    s += f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="{L["skin"]}" stroke="{INK}" stroke-width="{SW}"/>'
    s += f'<path d="M{cx + 70} {cy - 7} Q{cx + 88} {cy + 12} {cx + 73} {cy + 19}" fill="{L["skin"]}" stroke="none"/>'
    if L["stubble"]:
        s += stubble_dots(cx, cy, side=True, n=30)
    if L["beard"]:
        s += f'<path d="M{cx - 20} {cy + 10} Q{cx - 10} {cy + 80} {cx + 40} {cy + 82} Q{cx + 70} {cy + 60} {cx + 72} {cy + 30} L{cx + 40} {cy + 32} Q{cx + 10} {cy + 34} {cx - 20} {cy + 10} Z" fill="{L["beard"]}" stroke="{INK}" stroke-width="{FINE}"/>'
    Rr = R + 4
    if h in ("short", "long", "tails", "bun", "buzz"):
        arc = [(cx + Rr * math.cos(math.radians(a)), cy + Rr * math.sin(math.radians(a))) for a in range(140, 322, 8)]
        line = [(cx + 46, cy - 50), (cx + 12, cy - 40), (cx - 14, cy - 12), (cx - 40, cy + 22), (cx - 58, cy + 48)]
        op = ' opacity=".75"' if h == "buzz" else ""
        s += f'<polygon points="{pts(arc + line)}" fill="{c}" stroke="{INK}" stroke-width="{SW}" stroke-linejoin="round"{op}/>'
    elif h == "bald":
        s += f'<path d="M{cx - 74} {cy - 10} Q{cx - 80} {cy + 30} {cx - 50} {cy + 46} L{cx - 30} {cy + 20} L{cx - 40} {cy - 14} Z" fill="{c}" stroke="{INK}" stroke-width="{FINE}"/>'
    s += f'<path d="M{cx - 14} {cy - 10} Q{cx - 30} {cy + 4} {cx - 14} {cy + 20}" fill="{L["skin"]}" stroke="{INK}" stroke-width="{SW}"/>'  # ухо
    ex, ey = cx + 44, cy + 2; kind = F.get("eye", "open")
    if blink and kind in ("open", "wide"):
        kind = "closed"
    if kind == "open":
        ui, uo, lo = F.get("ui", -1), F.get("uo", -1), F.get("lo", 10)
        cid = uid("es")
        shape = f"M{ex - 11} {ey + uo:.1f} Q{ex} {ey + (ui + uo) / 2 - 4:.1f} {ex + 11} {ey + ui:.1f} Q{ex + 4} {ey + lo + 5:.1f} {ex - 11} {ey + uo:.1f} Z"
        s += f'<clipPath id="{cid}"><path d="{shape}"/></clipPath>'
        pr = F.get("pr", 9) * 0.92
        s += f'<g clip-path="url(#{cid})"><circle cx="{ex + 4}" cy="{ey + 2 + F.get("gy", 0)}" r="{pr:.1f}" fill="{INK}"/></g>'
        s += f'<path d="M{ex - 12} {ey + uo + 1:.1f} Q{ex} {ey + (ui + uo) / 2 - 4:.1f} {ex + 12} {ey + ui:.1f}" fill="none" stroke="{INK}" stroke-width="4.4" stroke-linecap="round"/>'
        if F.get("low"):
            s += f'<path d="M{ex - 9} {ey + lo - 1} Q{ex} {ey + lo + 4} {ex + 10} {ey + lo - 2}" fill="none" stroke="{INK}" stroke-width="2.4" stroke-linecap="round"/>'
    elif kind == "wide":
        s += f'<circle cx="{ex + 3}" cy="{ey + 2}" r="{F.get("pr", 6) * .9:.1f}" fill="{INK}"/><path d="M{ex - 10} {ey - 3} A10 14 0 0 1 {ex + 10} {ey - 3}" fill="none" stroke="{INK}" stroke-width="4.2" stroke-linecap="round"/>'
    elif kind == "happy":
        s += f'<path d="M{ex - 10} {ey + 4} Q{ex} {ey - 10} {ex + 10} {ey + 4}" fill="none" stroke="{INK}" stroke-width="4.4" stroke-linecap="round"/>'
    else:
        s += f'<path d="M{ex - 10} {ey - 1} Q{ex} {ey + 8} {ex + 10} {ey - 1}" fill="none" stroke="{INK}" stroke-width="4.4" stroke-linecap="round"/>'
    by = ey - 25; bi, bo = F.get("bi", 0), F.get("bo", 0)
    s += f'<path d="M{ex + 12} {by + bi} Q{ex} {by + (bi + bo) / 2 - 3} {ex - 12} {by + bo}" fill="none" stroke="{INK}" stroke-width="7.5" stroke-linecap="round"/>'
    for k in range(F.get("wr", 0)):
        s += f'<path d="M{ex - 8} {cy - 36 - k * 7} Q{ex + 6} {cy - 40 - k * 7} {ex + 18} {cy - 36 - k * 7}" fill="none" stroke="{INK}" stroke-width="1.8" opacity=".55"/>'
    if L["glasses"]:
        s += f'<circle cx="{ex + 2}" cy="{ey + 2}" r="17" fill="#fff" fill-opacity=".12" stroke="{INK}" stroke-width="2.6"/><line x1="{ex - 15}" y1="{ey}" x2="{cx - 10}" y2="{cy - 4}" stroke="{INK}" stroke-width="2.4"/>'
    if L["mustache"]:
        s += f'<path d="M{cx + 46} {cy + 38} Q{cx + 58} {cy + 26} {cx + 74} {cy + 30} Q{cx + 66} {cy + 40} {cx + 46} {cy + 38} Z" fill="{L["mustache"]}" stroke="{INK}" stroke-width="{FINE}"/>'
    mk = F.get("mouth", "line"); mx, my = cx + 58, cy + 42
    if talk > 0.05 or mk in ("O", "scream", "drop", "fear"):
        s += f'<ellipse cx="{mx}" cy="{my + 2}" rx="8" ry="{3 + max(talk, .9 if mk in ("O", "scream", "drop") else .4 if mk == "fear" else 0) * 9:.1f}" fill="#4a2420" stroke="{INK}" stroke-width="2.4"/>'
    elif mk in ("smile", "smile_s", "grin"):
        s += f'<path d="M{mx - 8} {my - 3} Q{mx + 2} {my + 6} {mx + 12} {my - 4}" fill="none" stroke="{INK}" stroke-width="3.4" stroke-linecap="round"/>'
    elif mk in ("frown", "wavy", "worry", "sad", "set"):
        s += f'<path d="M{mx - 8} {my + 4} Q{mx + 2} {my - 4} {mx + 12} {my + 2}" fill="none" stroke="{INK}" stroke-width="3.4" stroke-linecap="round"/>'
    else:
        s += f'<line x1="{mx - 6}" y1="{my}" x2="{mx + 12}" y2="{my}" stroke="{INK}" stroke-width="3.4" stroke-linecap="round"/>'
    if F.get("sweat"):
        s += f'<path d="M{cx - 2} {cy - 44} Q{cx + 8} {cy - 26} {cx - 2} {cy - 22} Q{cx - 12} {cy - 26} {cx - 2} {cy - 44} Z" fill="#bfe4f4" stroke="{INK}" stroke-width="2"/>'
    return s


# ---------- одежда ----------
def camo(L, d):
    if not L.get("camo"):
        return ""
    cid = uid("cm"); rnd = random.Random(3); s = f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">'
    for _ in range(26):
        x, y = rnd.uniform(-130, 130), rnd.uniform(-860, -440)
        s += f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{rnd.uniform(14, 34):.0f}" ry="{rnd.uniform(8, 18):.0f}" transform="rotate({rnd.uniform(-40, 40):.0f} {x:.0f} {y:.0f})" fill="{rnd.choice(["#3e4a2a", "#7a7a52", "#2e3420"])}" opacity=".8"/>'
    return s + "</g>"


def torso_front(L, back=False):
    c, yb = L["topc"], L["coatlen"]; kind = L["top"]
    fl = 0 if yb > -460 else 0
    fl = 14 if yb > -440 else 0
    d = (f"M-44 -850 L44 -850 Q100 -838 114 -816 Q122 -800 120 -770 L{118 + fl} {yb} L{-118 - fl} {yb} L-120 -770 Q-122 -800 -114 -816 Q-100 -838 -44 -850 Z")
    s = f'<path d="{d}" fill="{c}" stroke="{INK}" stroke-width="{SW}" stroke-linejoin="round"/>' + camo(L, d)
    s += f'<path d="M60 -830 Q104 -800 106 -700 L104 {yb + 20}" fill="none" stroke="{shade(c, .78)}" stroke-width="18" opacity=".45"/>'  # тень справа
    if back:
        s += f'<path d="M-110 -760 Q0 -742 110 -760" fill="none" stroke="{INK}" stroke-width="{FINE}" opacity=".7"/>'
        if kind == "hoodie":
            s += f'<path d="M-70 -850 Q0 -760 70 -850 Q40 -880 0 -880 Q-40 -880 -70 -850 Z" fill="{shade(c, .9)}" stroke="{INK}" stroke-width="{SW}"/>'
        if kind in ("parka", "quilted"):
            s += f'<rect x="-118" y="{yb - 36}" width="236" height="36" fill="{shade(c, .92)}" stroke="{INK}" stroke-width="{FINE}"/>' + "".join(f'<line x1="{x}" y1="{yb - 34}" x2="{x}" y2="{yb - 2}" stroke="{INK}" stroke-width="1.1" opacity=".45"/>' for x in range(-110, 112, 9))
        return s
    # ворот и то, что под ним
    if kind in ("parka", "quilted"):
        s += f'<path d="M-30 -850 L30 -850 L22 -800 L-22 -800 Z" fill="{L["inner"]}" stroke="{INK}" stroke-width="{FINE}"/>'
        s += f'<path d="M-50 -852 L-30 -868 L-24 -820 L-48 -812 Z M50 -852 L30 -868 L24 -820 L48 -812 Z" fill="{shade(c, 1.06)}" stroke="{INK}" stroke-width="{FINE}" stroke-linejoin="round"/>'
        s += f'<line x1="0" y1="-806" x2="0" y2="{yb}" stroke="{INK}" stroke-width="{FINE}"/><rect x="-4" y="-800" width="8" height="18" rx="2" fill="#b8b8b0" stroke="{INK}" stroke-width="1.2"/>'
        if kind == "parka":
            for sg in (-1, 1):
                x0 = sg * 38 if sg > 0 else -92
                s += (f'<rect x="{x0}" y="-742" width="54" height="52" fill="{shade(c, .97)}" stroke="{INK}" stroke-width="{FINE}"/>'
                      f'<path d="M{x0 - 2} -752 L{x0 + 56} -752 L{x0 + 56} -728 L{x0 - 2} -728 Z" fill="{shade(c, 1.05)}" stroke="{INK}" stroke-width="{FINE}"/>'
                      f'<circle cx="{x0 + 27}" cy="-737" r="3.2" fill="{INK}"/>')
            s += f'<rect x="-118" y="{yb - 36}" width="236" height="36" fill="{shade(c, .92)}" stroke="{INK}" stroke-width="{FINE}"/>' + "".join(f'<line x1="{x}" y1="{yb - 34}" x2="{x}" y2="{yb - 2}" stroke="{INK}" stroke-width="1.1" opacity=".45"/>' for x in range(-110, 112, 9))
        else:
            for y in range(-790, yb, 38):
                s += f'<path d="M-118 {y} Q-60 {y + 6} -4 {y} M4 {y} Q60 {y + 6} 118 {y}" fill="none" stroke="{INK}" stroke-width="1.3" opacity=".55"/>'
    elif kind == "coat":
        s += f'<path d="M-26 -850 L26 -850 L0 -770 Z" fill="{L["inner"]}" stroke="{INK}" stroke-width="{FINE}"/>'
        s += f'<path d="M-48 -852 L-4 -770 L-40 -730 L-62 -820 Z M48 -852 L4 -770 L40 -730 L62 -820 Z" fill="{shade(c, 1.08)}" stroke="{INK}" stroke-width="{FINE}" stroke-linejoin="round"/>'
        s += "".join(f'<circle cx="14" cy="{y}" r="4.5" fill="{shade(c, .6)}" stroke="{INK}" stroke-width="1.2"/>' for y in range(-730, yb + 30, 70))
        s += f'<line x1="2" y1="-770" x2="2" y2="{yb}" stroke="{INK}" stroke-width="{FINE}"/>'
        s += f'<path d="M-96 {yb + 120 if yb > -440 else -560} l40 0 M56 {yb + 120 if yb > -440 else -560} l40 0" stroke="{INK}" stroke-width="{FINE}"/>'
        s += f'<rect x="-118" y="-600" width="236" height="20" fill="{shade(c, .9)}" stroke="{INK}" stroke-width="{FINE}"/><rect x="-14" y="-604" width="28" height="28" rx="3" fill="none" stroke="#c8a040" stroke-width="3"/>' if L["h"] > 800 and L["apron"] is None else ""
    elif kind == "hoodie":
        s += f'<path d="M-70 -852 Q0 -800 70 -852" fill="none" stroke="{INK}" stroke-width="{SW}"/>'
        s += f'<path d="M-62 -846 Q0 -790 62 -846 Q30 -830 0 -830 Q-30 -830 -62 -846 Z" fill="{L["inner"]}"/>'
        s += "".join(f'<line x1="{sg * 16}" y1="-826" x2="{sg * 18}" y2="-750" stroke="#f0f0f0" stroke-width="4" stroke-linecap="round"/>' for sg in (-1, 1))
        s += f'<path d="M-70 -600 L70 -600 L88 -510 L-88 -510 Z" fill="{shade(c, .94)}" stroke="{INK}" stroke-width="{FINE}"/>'
        s += f'<rect x="-118" y="{yb - 30}" width="236" height="30" fill="{shade(c, .9)}" stroke="{INK}" stroke-width="{FINE}"/>'
    elif kind == "vest":
        s += f'<path d="M-30 -850 L30 -850 L0 -800 Z" fill="{L["inner"]}"/>'
        s += f'<path d="M-118 -800 L-60 -850 L-6 -760 L-6 {yb} L-118 {yb} Z M118 -800 L60 -850 L6 -760 L6 {yb} L118 {yb} Z" fill="{c}" stroke="{INK}" stroke-width="{FINE}" stroke-linejoin="round"/>'
        s += f'<path d="M-6 -760 L-6 {yb} L6 {yb} L6 -760 L0 -770 Z" fill="{L["inner"]}" stroke="{INK}" stroke-width="{FINE}"/>'
        if L["badge"]:
            s += f'<rect x="40" y="-760" width="46" height="22" rx="3" fill="#fbfbf6" stroke="{INK}" stroke-width="1.4"/><line x1="46" y1="-749" x2="78" y2="-749" stroke="#3a6a9a" stroke-width="3"/>'
    elif kind == "labcoat":
        s += f'<path d="M-26 -850 L26 -850 L0 -780 Z" fill="{L["inner"]}" stroke="{INK}" stroke-width="{FINE}"/>'
        s += f'<path d="M-48 -852 L-4 -780 L-30 -700 L-60 -820 Z M48 -852 L4 -780 L30 -700 L60 -820 Z" fill="#ffffff" stroke="{INK}" stroke-width="{FINE}" stroke-linejoin="round"/>'
        s += f'<line x1="0" y1="-780" x2="0" y2="{yb}" stroke="{INK}" stroke-width="{FINE}"/>'
        s += f'<rect x="38" y="-730" width="50" height="46" fill="none" stroke="{INK}" stroke-width="{FINE}"/><line x1="52" y1="-746" x2="52" y2="-720" stroke="#2c6aa0" stroke-width="5"/><line x1="64" y1="-744" x2="64" y2="-722" stroke="#c0392b" stroke-width="5"/>'
        s += f'<rect x="-92" y="-560" width="56" height="54" fill="none" stroke="{INK}" stroke-width="{FINE}"/><rect x="36" y="-560" width="56" height="54" fill="none" stroke="{INK}" stroke-width="{FINE}"/>'
    if L["apron"]:
        a = L["apron"]
        s += (f'<path d="M-70 -780 L70 -780 L76 -620 L96 {yb + 20} L-96 {yb + 20} L-76 -620 Z" fill="{a}" stroke="{INK}" stroke-width="{SW}" stroke-linejoin="round"/>'
              f'<path d="M-70 -780 L-44 -850 M70 -780 L44 -850" stroke="{a}" stroke-width="10"/><rect x="-50" y="-600" width="100" height="60" fill="none" stroke="{INK}" stroke-width="{FINE}"/>')
    return s


def torso_side(L):
    c, yb = L["topc"], L["coatlen"]; kind = L["top"]
    fl = 12 if yb > -440 else 0
    d = f"M-38 -852 L34 -852 Q62 -838 68 -800 L72 -640 L{68 + fl} {yb} L{-64 - fl} {yb} L-66 -650 Q-72 -790 -60 -830 Q-52 -848 -38 -852 Z"
    s = f'<path d="{d}" fill="{c}" stroke="{INK}" stroke-width="{SW}" stroke-linejoin="round"/>' + camo(L, d)
    s += f'<path d="M-50 -820 Q-62 -720 -56 {yb + 16}" fill="none" stroke="{shade(c, .78)}" stroke-width="16" opacity=".45"/>'
    if kind in ("parka", "quilted"):
        s += f'<path d="M14 -852 L30 -870 L44 -846 L40 -818 Z" fill="{shade(c, 1.06)}" stroke="{INK}" stroke-width="{FINE}"/>'
        s += f'<path d="M58 -820 L64 {yb}" stroke="{INK}" stroke-width="{FINE}"/>'
        if kind == "parka":
            s += f'<rect x="22" y="-742" width="34" height="50" fill="{shade(c, .97)}" stroke="{INK}" stroke-width="{FINE}"/><rect x="20" y="-752" width="38" height="24" fill="{shade(c, 1.05)}" stroke="{INK}" stroke-width="{FINE}"/>'
            s += f'<rect x="{-64}" y="{yb - 36}" width="{132}" height="36" fill="{shade(c, .92)}" stroke="{INK}" stroke-width="{FINE}"/>' + "".join(f'<line x1="{x}" y1="{yb - 34}" x2="{x}" y2="{yb - 2}" stroke="{INK}" stroke-width="1.1" opacity=".45"/>' for x in range(-58, 66, 9))
        else:
            s += "".join(f'<path d="M-66 {y} Q0 {y + 6} 70 {y}" fill="none" stroke="{INK}" stroke-width="1.3" opacity=".55"/>' for y in range(-790, yb, 38))
    elif kind == "hoodie":
        s += f'<path d="M-60 -852 Q-30 -900 20 -860 L10 -830 Q-30 -856 -50 -826 Z" fill="{shade(c, .9)}" stroke="{INK}" stroke-width="{SW}"/>'
        s += f'<path d="M10 -600 L68 -600 L72 -510 L20 -510 Z" fill="{shade(c, .94)}" stroke="{INK}" stroke-width="{FINE}"/>'
    elif kind in ("coat", "labcoat", "vest"):
        s += f'<path d="M30 -852 L56 -770 L64 {yb}" fill="none" stroke="{INK}" stroke-width="{FINE}"/>'
        if kind == "coat":
            s += "".join(f'<circle cx="56" cy="{y}" r="4" fill="{shade(c, .6)}"/>' for y in range(-730, yb + 30, 70))
    if L["apron"]:
        s += f'<path d="M50 -780 L74 -780 L80 -620 L{92} {yb + 20} L52 {yb + 20} Z" fill="{L["apron"]}" stroke="{INK}" stroke-width="{SW}"/>'
    return s


def legs_draw(L, legs, view="front", far=False):
    """legs: список ломаных [бедро, колено, щиколотка]."""
    s = ""; pc = L["pants"] if not far else shade(L["pants"], .82)
    for i, P in enumerate(legs):
        s += limb(P, 54 if L["h"] > 800 else 50, pc)
        if L["stripes"]:
            sg = -1 if (view == "front" and P[0][0] < 0) else 1
            off = (-17 if view == "front" else 4) * sg
            Q = offset(sub(P, 0.02, 0.98), off)
            s += f'<path d="{pl(Q)}" fill="none" stroke="#e8e8e6" stroke-width="4"/><path d="{pl(offset(Q, (-7 if view == "front" else 8) * sg))}" fill="none" stroke="#e8e8e6" stroke-width="4"/>'
        # складки у колена
        k = P[1]
        s += f'<path d="M{k[0] - 14} {k[1] - 6} q8 6 18 2" fill="none" stroke="{INK}" stroke-width="1.3" opacity=".5"/>'
    return s


def boot_front(L, A, lift=0.0):
    x, y = A; b, so = L["boots"], L["sole"]
    if lift > 0.05:  # стопа в воздухе, носок вниз и к зрителю: ботинок короче и чуть крупнее
        k = 1 + 0.1 * lift; h = 70 - 18 * lift
        return (f'<g transform="translate({x} {y}) scale({k:.3f}) translate({-x} {-y})"><path d="M{x - 28} {y - 8} L{x + 28} {y - 8} L{x + 34} {y + h - 16} Q{x + 36} {y + h + 6} {x} {y + h + 8} Q{x - 36} {y + h + 6} {x - 34} {y + h - 16} Z" fill="{b}" stroke="{INK}" stroke-width="{SW}" stroke-linejoin="round"/>'
                f'<path d="M{x - 14} {y + 6} l28 0 M{x - 14} {y + 18} l28 0" stroke="{INK}" stroke-width="1.4" opacity=".7"/>'
                f'<path d="M{x - 30} {y + h - 6} Q{x} {y + h + 12} {x + 30} {y + h - 6}" fill="none" stroke="{so}" stroke-width="7"/></g>')
    return (f'<path d="M{x - 30} {y - 8} L{x + 30} {y - 8} L{x + 36} {y + 52} Q{x + 40} {y + 70} {x + 28} {y + 70} L{x - 28} {y + 70} Q{x - 40} {y + 70} {x - 36} {y + 52} Z" fill="{b}" stroke="{INK}" stroke-width="{SW}" stroke-linejoin="round"/>'
            f'<path d="M{x - 38} {y + 58} L{x + 38} {y + 58} L{x + 36} {y + 70} L{x - 36} {y + 70} Z" fill="{so}" stroke="{INK}" stroke-width="{FINE}"/>'
            f'<path d="M{x - 10} {y + 8} l20 0 M{x - 10} {y + 20} l20 0 M{x - 10} {y + 32} l20 0" stroke="{INK}" stroke-width="1.4" opacity=".7"/>')


def boot_side(L, A, ang=0.0, far=False):
    x, y = A; b = L["boots"] if not far else shade(L["boots"], .82); so = L["sole"] if not far else shade(L["sole"], .85)
    g = f'<g transform="rotate({math.degrees(ang):.1f} {x:.1f} {y:.1f})">'
    return (g + f'<path d="M{x - 28} {y - 10} L{x + 22} {y - 10} L{x + 26} {y + 30} Q{x + 66} {y + 32} {x + 72} {y + 54} L{x + 72} {y + 70} L{x - 30} {y + 70} Z" fill="{b}" stroke="{INK}" stroke-width="{SW}" stroke-linejoin="round"/>'
            f'<path d="M{x - 30} {y + 58} L{x + 72} {y + 58} L{x + 72} {y + 70} L{x - 30} {y + 70} Z" fill="{so}" stroke="{INK}" stroke-width="{FINE}"/>'
            f'<path d="M{x + 4} {y + 4} l14 6 M{x + 6} {y + 18} l14 6" stroke="{INK}" stroke-width="1.4" opacity=".7"/></g>')


def arm_draw(L, P, far=False, sleeve=None):
    c = sleeve or (L["topc"] if L["top"] not in ("vest",) else L["inner"])
    if far:
        c = shade(c, .82)
    w = 40 if L["h"] > 800 else 34
    s = limb(P, w, c)
    cuff = sub(P, 0.9, 0.985, 2)
    s += limb(cuff, w + 2, shade(c, .88), sw=FINE)
    e = P[1]
    s += f'<path d="M{e[0] - 10} {e[1] - 8} q10 4 18 -2" fill="none" stroke="{INK}" stroke-width="1.3" opacity=".5"/>'
    hx, hy = P[-1]; dx, dy = P[-1][0] - P[-2][0], P[-1][1] - P[-2][1]; Ln = math.hypot(dx, dy) or 1
    hx, hy = hx + dx / Ln * 18, hy + dy / Ln * 18
    hc = L["hands"] if not far else shade(L["hands"], .85)
    s += f'<ellipse cx="{hx:.1f}" cy="{hy:.1f}" rx="21" ry="24" transform="rotate({math.degrees(math.atan2(dy, dx)) - 90:.1f} {hx:.1f} {hy:.1f})" fill="{hc}" stroke="{INK}" stroke-width="{SW}"/>'
    return s, (hx, hy)


# ---------- позы рук (цели для кистей, фронт) ----------
def arms_front(pose, t=0.0, sh=(-112, -808)):
    """Цели для кистей (левая и правая на экране) и режим локтя."""
    L1, L2 = 178, 170
    P = {
        "down": [((-142, -452), "low"), ((142, -452), "low")],
        "hold": [((-96, -560), "side"), ((96, -560), "side")],
        "count": [((-142, -452), "low"), ((30, -650), "side")],
        "wave": [((-142, -452), "low"), ((215 + 18 * math.sin(t * 9), -1000), "out")],
        "head": [((-66, -930), "out"), ((66, -930), "out")],
        "reach": [((-80, -1060), "out"), ((80, -1060), "out")],
        "shrug": [((-200, -640), "low"), ((200, -640), "low")],
        "point": [((-142, -452), "low"), ((330, -830), "low")],
        "bags": [((-150, -460), "low"), ((150, -460), "low")],
        "money": [((-142, -452), "low"), ((150, -560), "side")],
        "phone": [((-142, -452), "low"), ((66, -920), "out")],
        "climb": [((-118, -1070 - 50 * math.sin(t * 2 * math.pi)), "rail"), ((118, -1070 + 50 * math.sin(t * 2 * math.pi)), "rail")],
        "flashlight": [((-142, -452), "low"), ((40, -650), "side")],
    }[pose]
    out = []; dy = sh[1] + 808
    for i, (T, b) in enumerate(P):
        T = (T[0], T[1] + dy)
        S = (sh[0], sh[1]) if i == 0 else (-sh[0], sh[1])
        if b == "side":  # плечо висит вдоль тела, локоть у бока, предплечье к зрителю (укорочено)
            sg = -1 if S[0] < 0 else 1
            out.append([S, (sg * 132, -616 + dy), T])
        elif b == "rail":  # лестница со спины: плечо уходит вперёд к перекладине (укорочено), локоть чуть наружу
            sg = -1 if S[0] < 0 else 1
            out.append([S, (sg * 142, (S[1] + T[1]) / 2 + 30), T])
        else:
            out.append(ik(S, T, L1, L2, b))
    return out


def person(name="hero", view="front", face="neutral", phase=None, arms="down", blink=False, talk=0.0, gaze=0,
           sit=False, prop=None, light=(1, 1), rim="#ffd59a", t=0.0, step=0.0):
    """SVG-группа персонажа в локальных координатах (ступни в 0,0).

    view: front | side | back. phase: фаза шага (рад) для side; step: 0..1 амплитуда шага на месте для front.
    arms: поза рук (см. arms_front) для front/back; для side руки машут при ходьбе или arms='hold'/'push'.
    prop: 'bags' | 'notebook' | 'box' | 'money' | 'flashlight' | None.
    """
    L = look(name); F = FACES[face]; k = L["h"] / 1000
    hk = 1.0 if L["h"] > 800 else 1.25  # у детей голова крупнее
    s = ""
    drop = 0.0; LIFT = [0.0, 0.0]
    if view in ("front", "back"):
        if sit:
            drop = 200
            hipL, hipR = (-36, -478 + drop), (36, -478 + drop)
            legs = [[hipL, (-44, -300 + drop * 0.25), (-46, -70)], [hipR, (44, -300 + drop * 0.25), (46, -70)]]
        else:
            # шаг на камеру/от камеры: узкая колея, маховая нога сгибается в колене к зрителю (укорачивается),
            # стопа отрывается носком вниз, таз смещается на опорную ногу, корпус покачивается вверх-вниз
            ph = t * 2 * math.pi
            sway = 9 * math.sin(ph) * step
            lifts = [max(0.0, math.sin(ph)) * step, max(0.0, -math.sin(ph)) * step]
            legs, LIFT = [], lifts
            for li, sg in enumerate((-1, 1)):
                hx_ = sg * 37 + sway; fx = sg * (31 if step else 40) + sway * 0.4
                ay = -70 - 64 * lifts[li]
                kx = (hx_ + fx) / 2 + sg * 2; ky = (-478 + ay) / 2 + 22 * lifts[li]
                legs.append([(hx_, -478), (kx, ky), (fx, ay)])
            drop = -abs(math.sin(ph)) * step * 9 + 3 * step
        body_dy = drop
        armP = arms_front(arms, t, sh=(-112, -808 + body_dy))
        if step and arms == "down" and not sit:
            ph = t * 2 * math.pi
            armP = [ik((-112, -808 + body_dy), (-134 + 8 * max(0, -math.sin(ph)), -452 + body_dy - 18 * max(0, -math.sin(ph))), 178, 170, "low"),
                    ik((112, -808 + body_dy), (134 - 8 * max(0, math.sin(ph)), -452 + body_dy - 18 * max(0, math.sin(ph))), 178, 170, "low")]
        if view == "back":
            armP = [[(-p[0], p[1]) for p in a] for a in armP[::-1]]
        # тень
        s += '<ellipse cx="0" cy="0" rx="120" ry="20" fill="#000" opacity=".28"/>'
        order = sorted(range(len(legs)), key=lambda q: LIFT[q])  # маховая нога ближе к зрителю: рисуем последней
        for q in order:
            P = legs[q]; lf = (LIFT[q] if not sit and step else 0.0)
            s += legs_draw(L, [P], "front") + boot_front(L, P[-1], lf)
        if L["hair"] in ("long", "tails") and view == "front":
            s += f'<g transform="translate(0 {-846 + body_dy:.1f}) scale({hk})">{hair_behind(L, 0, -R)}</g>'
        s += f'<g transform="translate(0 {body_dy:.1f})">{torso_front(L, back=view == "back")}</g>'
        hands = []
        prop_s = ""
        if prop == "box" and arms == "hold":
            prop_s = f'<g transform="translate(0 {body_dy:.1f})"><rect x="-100" y="-660" width="200" height="150" fill="#b08a5a" stroke="{INK}" stroke-width="{SW}"/><path d="M-100 -660 L100 -660 L84 -690 L-84 -690 Z" fill="#c8a070" stroke="{INK}" stroke-width="{FINE}"/><rect x="-30" y="-660" width="60" height="150" fill="#9a7444" opacity=".5"/></g>'
            s += prop_s
        for i, P in enumerate(armP):
            a, hpt = arm_draw(L, P); s += a; hands.append(hpt)
        if prop == "bags":
            for hx, hy in hands:
                s += bag(hx, hy + 10)
        if prop == "notebook" and arms == "count":
            hx, hy = hands[1]
            s += (f'<g transform="rotate(-8 {hx} {hy})"><rect x="{hx - 70}" y="{hy - 70}" width="96" height="120" rx="4" fill="#f4efe2" stroke="{INK}" stroke-width="{SW}"/>'
                  + "".join(f'<line x1="{hx - 60}" y1="{hy - 50 + j * 16}" x2="{hx + 14}" y2="{hy - 50 + j * 16}" stroke="#7a8aa0" stroke-width="2"/>' for j in range(6))
                  + f'<rect x="{hx - 74}" y="{hy - 74}" width="104" height="14" rx="3" fill="#a83a2a" stroke="{INK}" stroke-width="{FINE}"/></g>'
                  + f'<ellipse cx="{hx + 10}" cy="{hy + 6}" rx="20" ry="22" fill="{L["hands"]}" stroke="{INK}" stroke-width="{SW}"/>')
        if prop == "phone":
            hx, hy = hands[1]
            s += f'<rect x="{hx - 30}" y="{hy - 64}" width="60" height="104" rx="9" fill="#15181d" stroke="{INK}" stroke-width="{SW}"/><rect x="{hx - 24}" y="{hy - 56}" width="48" height="86" rx="5" fill="#9ac8f0"/><ellipse cx="{hx + 6}" cy="{hy + 18}" rx="20" ry="22" fill="{L["hands"]}" stroke="{INK}" stroke-width="{SW}"/>'
        if prop == "bag1":
            hx, hy = hands[1]
            s += bag(hx, hy + 6)
        if prop == "box1":
            hx, hy = hands[1]
            s += f'<rect x="{hx - 40}" y="{hy - 30}" width="80" height="56" rx="4" fill="#f4f4f0" stroke="{INK}" stroke-width="{SW}"/><rect x="{hx - 10}" y="{hy - 22}" width="20" height="40" fill="#2ab060"/><rect x="{hx - 20}" y="{hy - 12}" width="40" height="20" fill="#2ab060"/>'
        if prop == "money":
            hx, hy = hands[1]
            s += f'<rect x="{hx - 10}" y="{hy - 46}" width="70" height="36" rx="3" transform="rotate(-20 {hx} {hy})" fill="#9ac08a" stroke="{INK}" stroke-width="{FINE}"/><ellipse cx="{hx}" cy="{hy}" rx="20" ry="22" fill="{L["hands"]}" stroke="{INK}" stroke-width="{SW}"/>'
        if prop == "flashlight":
            hx, hy = hands[1]
            s += f'<rect x="{hx - 14}" y="{hy - 10}" width="28" height="70" rx="5" fill="#3a3a3e" stroke="{INK}" stroke-width="{SW}"/><circle cx="{hx}" cy="{hy + 64}" r="20" fill="#fffbe8" stroke="{INK}" stroke-width="{FINE}"/>'
        s += f'<g transform="translate(0 {-846 + body_dy:.1f}) scale({hk})">{head_front(L, F, blink, talk, gaze, back=view == "back")}</g>'
    else:  # профиль, идёт вправо
        L1, L2, ank = 206, 206, 70
        ph = phase if phase is not None else 0.0
        walking = phase is not None

        def leg_angles(p):
            if not walking:
                return 0.02, 0.0
            a = 0.42 * math.sin(p)
            kf = 0.06 + 0.8 * max(0.0, math.cos(p + 0.55)) ** 1.6
            return a, a - kf
        A = [leg_angles(ph), leg_angles(ph + math.pi)]
        reach = [L1 * math.cos(a1) + L2 * math.cos(a2) for a1, a2 in A]
        hip_y = -(max(reach) + ank)
        body_dy = hip_y + 478
        legs = [fk((0, hip_y), A[i][0], L1, A[i][1], L2) for i in range(2)]
        hx = 0.0
        if sit:  # sit: 1 = сидит, 0 = встал (ступни на месте, корпус переезжает)
            sf = float(sit); a1 = 0.02 + (math.pi / 2 - 0.02) * sf
            hip_y = -(L1 * math.cos(a1) + L2 + ank); body_dy = hip_y + 478; hx = 190 - L1 * math.sin(a1)
            A = [(a1, 0.0), (a1, 0.03)]
            legs = [fk((hx, hip_y), a1, L1, 0.0, L2), fk((hx - 8, hip_y), a1, L1 - 8, 0.03, L2)]
            if arms == "down" and sf > 0.5:
                arms = "knees"
            sit = sf > 0.01
        s += '<ellipse cx="10" cy="0" rx="110" ry="18" fill="#000" opacity=".28"/>'
        sw_a = 0.38 * math.sin(ph) if walking else 0.0
        far_i, near_i = 1, 0
        # дальняя рука, дальняя нога
        shS = (-4 + hx, -808 + body_dy)
        if arms in ("hold", "push"):
            tgt = (290, -548 + body_dy) if arms == "push" else (120, -580 + body_dy)
            armFar = ik((shS[0] + 10, shS[1]), (tgt[0] + 12, tgt[1] - 4), 178, 170, "low"); armNear = ik(shS, tgt, 178, 170, "low")
        elif arms == "take":
            armFar = fk((shS[0] + 10, shS[1]), 0.05, 178, 0.2, 170); armNear = ik(shS, (262, -1030 + body_dy * 0.3), 178, 170, "low")
        elif arms == "knees":
            armFar = ik((shS[0] + 10, shS[1]), (170 + hx * 0, -300), 178, 170, "low"); armNear = ik(shS, (160, -296), 178, 170, "low")
        elif arms == "money":
            armFar = fk((shS[0] + 10, shS[1]), -sw_a, 178, -sw_a + 0.1, 170); armNear = ik(shS, (150, -640 + body_dy), 178, 170, "low")
        else:
            armFar = fk((shS[0] + 10, shS[1]), sw_a, 178, sw_a + 0.25, 170)
            armNear = fk(shS, -sw_a, 178, -sw_a + 0.25, 170)
        a, hf = arm_draw(L, armFar, far=True); s += a
        if prop == "bags":
            s += bag(hf[0], hf[1] + 10, far=True)
        s += legs_draw(L, [legs[far_i]], "side", far=True)
        P = legs[far_i]; s += boot_side(L, P[-1], ang=(-0.3 * (A[far_i][1]) if (P[-1][1] < -ank - 3 and not sit) else 0), far=True)
        s += legs_draw(L, [legs[near_i]], "side")
        P = legs[near_i]; s += boot_side(L, P[-1], ang=(-0.3 * (A[near_i][1]) if (P[-1][1] < -ank - 3 and not sit) else 0))
        if L["hair"] == "long":
            pass
        s += f'<g transform="translate({hx:.1f} {body_dy:.1f})">{torso_side(L)}</g>'
        a, hn = arm_draw(L, armNear); s += a
        if prop == "bags":
            s += bag(hn[0], hn[1] + 10)
        if prop == "money":
            s += f'<rect x="{hn[0] + 4}" y="{hn[1] - 40}" width="66" height="34" rx="3" transform="rotate(-12 {hn[0]} {hn[1]})" fill="#9ac08a" stroke="{INK}" stroke-width="{FINE}"/><ellipse cx="{hn[0]}" cy="{hn[1]}" rx="20" ry="22" fill="{L["hands"]}" stroke="{INK}" stroke-width="{SW}"/>'
        s += f'<g transform="translate({6 + hx:.1f} {-846 + body_dy:.1f}) scale({hk})">{head_side(L, F, blink, talk)}</g>'
    g = uid("rim")
    dx, dy = 5 * light[0], 3 * light[1]
    defs = (f'<filter id="{g}" x="-15%" y="-10%" width="130%" height="120%"><feMorphology in="SourceAlpha" operator="erode" radius="3.2" result="i"/>'
            f'<feOffset in="i" dx="{dx}" dy="{dy}" result="o"/><feComposite in="i" in2="o" operator="out" result="e"/><feFlood flood-color="{rim}" flood-opacity=".7"/><feComposite in2="e" operator="in" result="r"/>'
            f'<feOffset in="i" dx="{-dx * 5.5}" dy="{-dy * 1.5}" result="o2"/><feComposite in="i" in2="o2" operator="out" result="e2"/><feGaussianBlur in="e2" stdDeviation="3" result="e2b"/>'
            f'<feFlood flood-color="#1a1426" flood-opacity=".34"/><feComposite in2="e2b" operator="in" result="d0"/><feComposite in="d0" in2="SourceAlpha" operator="in" result="d"/>'
            f'<feMerge><feMergeNode in="SourceGraphic"/><feMergeNode in="d"/><feMergeNode in="r"/></feMerge></filter>')
    return f'<g transform="scale({k:.3f})"><defs>{defs}</defs><g filter="url(#{g})">{s}</g></g>'


def bag(x, y, far=False):
    c = "#e9edf0" if not far else "#c8ccd0"
    return (f'<g><path d="M{x - 14} {y} Q{x} {y - 30} {x + 14} {y}" fill="none" stroke="{INK}" stroke-width="5"/>'
            f'<path d="M{x - 40} {y + 30} L{x - 34} {y + 2} L{x + 34} {y + 2} L{x + 40} {y + 30} L{x + 46} {y + 150} Q{x} {y + 166} {x - 46} {y + 150} Z" fill="{c}" stroke="{INK}" stroke-width="{SW}" stroke-linejoin="round"/>'
            f'<rect x="{x - 26}" y="{y - 22}" width="20" height="40" rx="6" fill="#d8a04a" stroke="{INK}" stroke-width="{FINE}"/><rect x="{x + 6}" y="{y - 30}" width="14" height="46" rx="4" fill="#3a8a5a" stroke="{INK}" stroke-width="{FINE}"/>'
            f'<path d="M{x - 30} {y + 60} Q{x} {y + 70} {x + 34} {y + 58}" fill="none" stroke="#b0b8c0" stroke-width="3"/></g>')


def cart_side(x=0, y=0):
    """Тележка в профиль (ручка слева, едет вправо). Высота ~ 0.55 роста."""
    s = f'<g transform="translate({x} {y})">'
    s += f'<path d="M-20 -540 L30 -540 L60 -300 L420 -300 L450 -540 L40 -540" fill="none" stroke="{INK}" stroke-width="{SW + 7}" stroke-linejoin="round"/>'
    s += f'<path d="M-20 -540 L30 -540 L60 -300 L420 -300 L450 -540 L40 -540" fill="none" stroke="#a8b0b8" stroke-width="7" stroke-linejoin="round"/>'
    for xx in range(80, 440, 34):
        s += f'<line x1="{xx}" y1="-536" x2="{xx - 4 + (xx - 60) * 0.02}" y2="-304" stroke="#8a929a" stroke-width="3"/>'
    for yy in range(-510, -300, 40):
        s += f'<line x1="{40 + (yy + 540) * 0.08:.0f}" y1="{yy}" x2="{450 - (yy + 540) * 0.13:.0f}" y2="{yy}" stroke="#8a929a" stroke-width="3"/>'
    # товары в корзине
    for i, (dx, w, h, c) in enumerate(((90, 70, 120, "#c0392b"), (170, 60, 150, "#e0a72a"), (240, 80, 100, "#2c6aa0"), (330, 70, 130, "#3a9a5a"))):
        s += f'<rect x="{dx}" y="{-540 - h + 60}" width="{w}" height="{h}" fill="{c}" stroke="{INK}" stroke-width="{FINE}"/><rect x="{dx + 8}" y="{-540 - h + 80}" width="{w - 16}" height="{h * .3:.0f}" fill="#fff" opacity=".7"/>'
    s += f'<path d="M60 -300 L80 -60 L420 -60 L420 -300" fill="none" stroke="{INK}" stroke-width="{SW + 6}"/><path d="M60 -300 L80 -60 L420 -60 L420 -300" fill="none" stroke="#a8b0b8" stroke-width="6"/>'
    for wx in (90, 400):
        s += f'<circle cx="{wx}" cy="-28" r="28" fill="#2a2a2e" stroke="{INK}" stroke-width="{SW}"/><circle cx="{wx}" cy="-28" r="9" fill="#8a929a"/>'
    s += f'<rect x="-34" y="-556" width="40" height="22" rx="8" fill="#c0392b" stroke="{INK}" stroke-width="{FINE}"/>'
    return s + '</g>'


def place(svg, x, y, s, flip=False):
    return f'<g transform="translate({x:.1f} {y:.1f}) scale({-s if flip else s:.4f} {s:.4f})">{svg}</g>'


if __name__ == "__main__":
    # лист проверки: все персонажи и эмоции
    out = []
    names = list(LOOKS)
    for i, n in enumerate(names):
        out.append(place(person(n, "front", face=list(FACES)[i % len(FACES)]), 110 + i * 160, 900, 0.62))
    for i, f in enumerate(FACES):
        out.append(place(f'<g transform="translate(0 846)">{head_front(look("hero"), FACES[f])}</g>', 90 + i * 160, 1150, 0.9))
    for i in range(8):
        out.append(place(person("hero", "side", phase=i / 8 * math.tau), 110 + i * 240, 1820, 0.5))
    W = 2000
    open("/tmp/char_sheet.svg", "w").write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="1920" viewBox="0 0 {W} 1920"><rect width="{W}" height="1920" fill="#8a8478"/>{"".join(out)}</svg>')
