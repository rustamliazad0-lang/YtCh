"""Детальная рисовка для раскадровок и видео: персонажи и предметы бункера.

Манера: крупная круглая светлая голова, тонкое тело в пухлой одежде со стёжкой, тонкий тёмный контур,
тень с одной стороны, щетина точками и полуприкрытые глаза у главного героя. Второстепенные герои без лиц.
Все функции рисуют в координатах кадра 360x640 и совместимы со старыми вызовами.
"""
import itertools, math

INK = "#241f1b"
SKIN = "#efe6d8"
_ids = itertools.count()

OUTFITS = {
    "hero":   dict(top="#2f5d8a", dark="#22476b", pants="#2b2f3a", stripe="#d6d2c8", boot="#b8874f", sole="#4a3424", glove="#1f2226", hair="#2b211b", hat=None, face=True, reflect=True),
    "friend": dict(top="#55623f", dark="#3f4a2e", pants="#3d4530", stripe=None, boot="#3a2f25", sole="#1d1814", glove="#1f2226", hair=None, hat="kepi", hatc="#3f4a2e", camo=True),
    "mom":    dict(top="#c99a45", dark="#a67a2f", pants="#4b3a46", stripe=None, boot="#6a4a35", sole="#2e2018", glove="#7a5a3a", hair="#4a2f1e", hat=None, long_hair=True, cardigan=True),
    "grandpa": dict(top="#7d8590", dark="#5d646d", pants="#45464d", stripe=None, boot="#5a4334", sole="#2a1f17", glove="#2f2a26", hair=None, hat="ushanka", hatc="#6a5a48", vest="#4c4f44"),
    "kid":    dict(top="#c24b4b", dark="#9a3535", pants="#34506a", stripe="#d6d2c8", boot="#8a5a3a", sole="#3a2618", glove="#24364a", hair="#3a2a1a", hat="beanie", hatc="#3f6f9a", k=0.66),
    "n1":     dict(top="#7a5c8a", dark="#5e456c", pants="#3a3a44", stripe=None, boot="#4a3a2e", sole="#221a14", glove="#2a2630", hair="#777", hat=None),
    "n2":     dict(top="#5c8a7a", dark="#456b5e", pants="#3d3d3a", stripe=None, boot="#4a3a2e", sole="#221a14", glove="#26302c", hair=None, hat="beanie", hatc="#8a7a4a"),
    "n3":     dict(top="#9a6a4a", dark="#7a5038", pants="#34384a", stripe=None, boot="#3a2e25", sole="#1d1814", glove="#2a2420", hair="#3a2a20", hat=None),
    "shadow": dict(top="#14181d", dark="#101317", pants="#14181d", stripe=None, boot="#14181d", sole="#101317", glove="#101317", hair=None, hat=None, sil=True),
}

TORSO = "M-24 -110 Q-28 -84 -26 -56 Q0 -50 26 -56 Q28 -84 24 -110 Q0 -117 -24 -110 Z"


def _o(c, w=1.6, sil=False):
    return f'fill="{c}"' + ("" if sil else f' stroke="{INK}" stroke-width="{w}" stroke-linejoin="round"')


def _head(o, hx, hy, show_face, mood):
    sil = o.get("sil")
    skin = o["top"] if sil else SKIN
    h = ""
    if o.get("long_hair"):
        h += f'<path d="M{hx-21} {hy-4} Q{hx-24} {hy+26} {hx-14} {hy+30} L{hx+14} {hy+30} Q{hx+24} {hy+26} {hx+21} {hy-4} Z" {_o(o["hair"], 1.4)}/>'
    if o.get("hat") == "ushanka":
        h += f'<rect x="{hx-25}" y="{hy-6}" width="10" height="22" rx="5" {_o(o["hatc"], 1.4)}/><rect x="{hx+15}" y="{hy-6}" width="10" height="22" rx="5" {_o(o["hatc"], 1.4)}/>'
    h += f'<circle cx="{hx-18}" cy="{hy+1}" r="4.2" {_o(skin, 1.3, sil)}/><circle cx="{hx+18}" cy="{hy+1}" r="4.2" {_o(skin, 1.3, sil)}/>'
    h += f'<ellipse cx="{hx}" cy="{hy}" rx="19" ry="20" {_o(skin, 1.7, sil)}/>'
    if not sil:
        h += f'<path d="M{hx+5} {hy-19.5} A19 20 0 0 1 {hx+5} {hy+19.5} A15 20 0 0 0 {hx+5} {hy-19.5} Z" fill="#000" fill-opacity=".10"/>'
    if o.get("hair") and not o.get("hat"):
        h += f'<path d="M{hx-19} {hy-2} Q{hx-21} {hy-22} {hx} {hy-22} Q{hx+21} {hy-22} {hx+19} {hy-2} Q{hx+14} {hy-12} {hx+6} {hy-11} Q{hx-2} {hy-16} {hx-8} {hy-10} Q{hx-14} {hy-12} {hx-19} {hy-2} Z" {_o(o["hair"], 1.4)}/>'
    hat = o.get("hat")
    if hat == "beanie":
        h += f'<path d="M{hx-19.5} {hy-5} Q{hx-20} {hy-27} {hx} {hy-27} Q{hx+20} {hy-27} {hx+19.5} {hy-5} Z" {_o(o["hatc"], 1.5)}/>'
        h += f'<rect x="{hx-21}" y="{hy-9}" width="42" height="8" rx="3" {_o(o["hatc"], 1.4)}/>'
        h += "".join(f'<line x1="{hx-17+i*5}" y1="{hy-8}" x2="{hx-17+i*5}" y2="{hy-2}" stroke="{INK}" stroke-opacity=".35" stroke-width="1"/>' for i in range(8))
        h += f'<circle cx="{hx}" cy="{hy-29}" r="5" {_o(o["hatc"], 1.3)}/>'
    elif hat == "kepi":
        h += f'<path d="M{hx-19} {hy-6} Q{hx-19} {hy-26} {hx} {hy-26} Q{hx+19} {hy-26} {hx+19} {hy-6} Z" {_o(o["hatc"], 1.5)}/><path d="M{hx-4} {hy-7} Q{hx+14} {hy-10} {hx+27} {hy-4} L{hx+25} {hy-1} Q{hx+12} {hy-4} {hx-4} {hy-3} Z" {_o(o["hatc"], 1.3)}/>'
    elif hat == "ushanka":
        h += f'<path d="M{hx-21} {hy-4} Q{hx-21} {hy-30} {hx} {hy-30} Q{hx+21} {hy-30} {hx+21} {hy-4} Z" {_o(o["hatc"], 1.5)}/><path d="M{hx-21} {hy-10} Q{hx} {hy-16} {hx+21} {hy-10}" stroke="{INK}" stroke-opacity=".4" fill="none"/>'
    if o.get("face") and show_face:
        for ex in (-7, 6):
            h += f'<circle cx="{hx+ex}" cy="{hy+1.4}" r="2.3" fill="{INK}"/><rect x="{hx+ex-3}" y="{hy-1.6}" width="6" height="3" fill="{SKIN}"/>'
            h += f'<path d="M{hx+ex-3} {hy+1.4} Q{hx+ex} {hy} {hx+ex+3} {hy+1.4}" stroke="{INK}" stroke-width="1.3" fill="none"/>'
        br = {"calm": 0, "worried": 2.5, "pain": 3.5}[mood]
        h += f'<path d="M{hx-10} {hy-4+br} L{hx-4} {hy-5}" stroke="{INK}" stroke-width="1.4"/><path d="M{hx+9} {hy-4+br} L{hx+3} {hy-5}" stroke="{INK}" stroke-width="1.4"/>'
        h += f'<path d="M{hx-0.5} {hy+5} q2 2 0 3.5" stroke="{INK}" stroke-width="1.1" fill="none"/>'
        mouth = f"M{hx-4} {hy+12} h7" if mood == "calm" else f"M{hx-4} {hy+13} q3.5 -3 7 0"
        h += f'<path d="{mouth}" stroke="{INK}" stroke-width="1.4" fill="none" stroke-linecap="round"/>'
        for dx, dy in ((-11, 8), (-9, 12), (-6, 15), (-2, 16), (2, 16), (6, 15), (9, 12), (11, 8), (-12, 4), (12, 4), (-4, 13), (4, 13), (-8, 9), (8, 9)):
            h += f'<circle cx="{hx+dx}" cy="{hy+dy}" r=".7" fill="#7a6555" fill-opacity=".7"/>'
    return h


def _body(o, pose):
    sil = o.get("sil")
    g = ""
    # ботинки и штаны
    for sx in (-1, 1):
        x0 = -19 if sx < 0 else 2
        g += f'<path d="M{-16 if sx<0 else 3} -60 L{-2 if sx<0 else 16} -60 L{-3 if sx<0 else 15} -12 L{-16 if sx<0 else 2} -12 Z" {_o(o["pants"], 1.5, sil)}/>'
        if o.get("stripe") and not sil:
            xs = -15 if sx < 0 else 14.5
            g += f'<line x1="{xs}" y1="-58" x2="{xs}" y2="-14" stroke="{o["stripe"]}" stroke-width="1.7"/>'
        g += f'<path d="M{x0} -14 h17 v10 q0 4 -4 4 h-12 q-{3 if sx<0 else 1} 0 -{3 if sx<0 else 1} -3 z" {_o(o["boot"], 1.4, sil)}/>'
        g += f'<rect x="{x0-1}" y="-3.5" width="19" height="3.5" rx="1.5" fill="{o["sole"]}"/>'
    # руки
    def sleeve_down(sx):
        p = f'M{-24*sx} -108 Q{-34*sx} -100 {-33*sx} -84 L{-32*sx} -66 L{-23*sx} -66 L{-23*sx} -84 Q{-23*sx} -98 {-18*sx} -104 Z'
        return f'<path d="{p}" {_o(o["top"], 1.5, sil)}/><line x1="{-32.5*sx}" y1="-86" x2="{-23*sx}" y2="-86" stroke="{o["dark"]}" stroke-width="1.2"/><ellipse cx="{-27.5*sx}" cy="-61" rx="5.5" ry="6.5" {_o(o["glove"], 1.3, sil)}/>'
    if pose == "down":
        g += f'<path d="M-21 -104 Q-30 -88 -9 -96" stroke="{INK}" stroke-width="12" fill="none" stroke-linecap="round"/><path d="M-21 -104 Q-30 -88 -9 -96" stroke="{o["top"]}" stroke-width="9" fill="none" stroke-linecap="round"/>'
        g += f'<path d="M21 -104 Q30 -88 25 -98" stroke="{INK}" stroke-width="12" fill="none" stroke-linecap="round"/><path d="M21 -104 Q30 -88 25 -98" stroke="{o["top"]}" stroke-width="9" fill="none" stroke-linecap="round"/>'
    elif pose == "arm_up":
        g += sleeve_down(1)
        g += f'<path d="M17 -107 L27 -111 L49 -150 L40 -155 Z" {_o(o["top"], 1.5, sil)}/><circle cx="45" cy="-156" r="6.5" {_o(o["glove"], 1.3, sil)}/>'
    else:
        g += sleeve_down(1) + sleeve_down(-1)
    # куртка
    long = o.get("cardigan")
    torso = TORSO if not long else "M-24 -110 Q-28 -80 -27 -42 Q0 -38 27 -42 Q28 -80 24 -110 Q0 -117 -24 -110 Z"
    g += f'<path d="M-16 -113 Q0 -103 16 -113 Q14 -122 0 -121 Q-14 -122 -16 -113 Z" {_o(o["dark"], 1.3, sil)}/>'
    g += f'<path d="{torso}" {_o(o["top"], 1.7, sil)}/>'
    if not sil:
        n = next(_ids)
        g += f'<clipPath id="tc{n}"><path d="{torso}"/></clipPath><g clip-path="url(#tc{n})">'
        if o.get("camo"):
            for cx, cy, rx, c in ((-14, -98, 9, "#3f4a2e"), (10, -88, 11, "#6f7a52"), (-6, -72, 10, "#3a3324"), (16, -66, 8, "#3f4a2e"), (-18, -62, 7, "#6f7a52")):
                g += f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{rx*0.6}" fill="{c}" transform="rotate(-20 {cx} {cy})"/>'
        if o.get("vest"):
            g += f'<path d="M-28 -112 L-6 -112 L-8 -50 L-28 -50 Z M28 -112 L6 -112 L8 -50 L28 -50 Z" fill="{o["vest"]}"/>'
            g += "".join(f'<path d="M-28 {y} L-6 {y} M6 {y} L28 {y}" stroke="#000" stroke-opacity=".25"/>' for y in (-98, -86, -74, -62))
        if not o.get("cardigan") and not o.get("vest"):
            g += "".join(f'<path d="M-27 {y} Q0 {y+3} 27 {y}" stroke="{o["dark"]}" stroke-width="1.2" fill="none"/>' for y in (-98, -86, -74, -62))
        if o.get("cardigan"):
            g += "".join(f'<line x1="{x}" y1="-110" x2="{x}" y2="-40" stroke="{o["dark"]}" stroke-opacity=".5"/>' for x in range(-24, 26, 4))
            g += "".join(f'<circle cx="3" cy="{y}" r="1.6" fill="{INK}"/>' for y in (-96, -82, -68, -54))
        if o.get("reflect"):
            g += f'<rect x="-30" y="-84" width="60" height="6" fill="#f2b04a"/><rect x="-30" y="-75" width="60" height="2.5" fill="#d9d6cc"/>'
        g += f'<path d="M8 -116 Q28 -108 28 -84 Q29 -60 28 -40 L10 -40 Q14 -84 8 -116 Z" fill="#000" fill-opacity=".17"/></g>'
        g += f'<line x1="0" y1="-112" x2="0" y2="{-40 if long else -54}" stroke="{INK}" stroke-width="1.2" stroke-opacity=".8"/>'
        g += f'<path d="M-19 -70 L-10 -67 M19 -70 L10 -67" stroke="{INK}" stroke-width="1.2"/>'
        if pose == "down":
            g += f'<ellipse cx="-8" cy="-96" rx="5.5" ry="6.5" {_o(o["glove"], 1.3)}/><ellipse cx="25" cy="-99" rx="5.5" ry="6.5" {_o(o["glove"], 1.3)}/>'
    g += f'<rect x="-5" y="-115" width="10" height="6" fill="{SKIN if not sil else o["top"]}"/>'
    return g


def person(x, y, who="hero", s=1.0, pack=False, down=False, lie=False, mood="calm", arm_up=False):
    o = OUTFITS[who]
    s = s * o.get("k", 1.0) * 1.3
    pose = "down" if down else ("arm_up" if arm_up else "stand")
    hx, hy = (9, -106) if down else (0, -132)
    inner = ""
    if pack:
        inner += f'<path d="M-40 -104 h20 v54 h-20 q-4 0 -4 -4 v-46 q0 -4 4 -4 z" {_o("#b8452e", 1.5)}/><rect x="-40" y="-82" width="18" height="4" fill="#7d2a1a"/>'
    inner += _body(o, pose) + _head(o, hx, hy, not down, mood)
    if lie:
        return f'<g transform="translate({x},{y}) scale({s*0.77:.3f}) translate(75,-28) rotate(-90)">{inner}</g>'
    y2 = min(y + 70, 600)
    return f'<g transform="translate({x},{y2}) scale({s:.3f})">{inner}</g>'


# ---------- окружение ----------
def room(dark=False):
    wall = "#15181d" if dark else "#2a3038"
    seam = "#0e1014" if dark else "#1b2027"
    s = f'<rect width="360" height="640" fill="#0e1014"/><rect width="360" height="420" fill="{wall}"/>'
    for i, (cx, cy, rx, ry) in enumerate(((60, 150, 40, 26), (250, 300, 50, 30), (150, 360, 30, 16), (310, 120, 26, 40), (110, 250, 22, 34))):
        s += f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="#000" fill-opacity=".07"/>'
    for x in (90, 180, 270):
        s += f'<line x1="{x}" y1="48" x2="{x}" y2="412" stroke="{seam}" stroke-width="2.5"/>'
        s += "".join(f'<circle cx="{x+dx}" cy="{yy}" r="1.7" fill="#4a535e" fill-opacity=".7"/>' for dx in (-7, 7) for yy in (70, 200, 330, 400))
    s += f'<line x1="0" y1="215" x2="360" y2="215" stroke="{seam}" stroke-width="2.5"/>'
    for x, h in ((40, 40), (205, 60), (300, 30)):
        s += f'<rect x="{x}" y="215" width="3" height="{h}" fill="#000" fill-opacity=".12"/>'
    s += f'<rect width="360" height="48" fill="#1c2026"/>'
    s += f'<rect x="-6" y="12" width="372" height="26" rx="6" fill="#4b535d" stroke="{INK}" stroke-width="1.5"/><rect x="-6" y="14" width="372" height="5" fill="#fff" fill-opacity=".08"/>'
    s += "".join(f'<line x1="{x}" y1="12" x2="{x}" y2="38" stroke="#353c45" stroke-width="2"/><rect x="{x-3}" y="2" width="6" height="12" fill="#353c45"/>' for x in range(20, 360, 46))
    s += f'<path d="M0 52 Q60 58 120 52 T240 52 T360 54" stroke="#0b0c0e" stroke-width="3" fill="none"/><path d="M0 57 Q70 62 140 56 T280 57 T360 58" stroke="#5a2a22" stroke-width="2" fill="none"/>'
    s += f'<rect x="336" y="48" width="9" height="372" fill="#59606b" stroke="{INK}" stroke-width="1.2"/>' + "".join(f'<rect x="332" y="{yy}" width="17" height="6" fill="#3d434b"/>' for yy in (90, 220, 350))
    # стеллаж слева
    s += f'<rect x="6" y="230" width="4" height="190" fill="#4a5058"/><rect x="66" y="230" width="4" height="190" fill="#4a5058"/>'
    for sy in (270, 330, 390):
        s += f'<rect x="4" y="{sy}" width="68" height="4" fill="#5a616a" stroke="{INK}" stroke-width=".8"/>'
    for i, sy in enumerate((270, 330, 390)):
        for j in range(4):
            cx = 13 + j * 14
            if (i + j) % 3 == 2:
                s += f'<rect x="{cx-3}" y="{sy-18}" width="16" height="18" fill="#7a603c" stroke="{INK}" stroke-width=".8"/><line x1="{cx-3}" y1="{sy-12}" x2="{cx+13}" y2="{sy-12}" stroke="{INK}" stroke-opacity=".4"/>'
            else:
                s += f'<rect x="{cx}" y="{sy-14}" width="10" height="14" fill="#8a9097" stroke="{INK}" stroke-width=".8"/><rect x="{cx}" y="{sy-10}" width="10" height="5" fill="{["#8a3a2e", "#3a5a7a", "#6a7a3a"][j % 3]}"/><ellipse cx="{cx+5}" cy="{sy-14}" rx="5" ry="1.5" fill="#b0b5bb"/>'
    # огнетушитель и щиток
    s += f'<rect x="314" y="368" width="15" height="42" rx="6" fill="#9b2d24" stroke="{INK}" stroke-width="1.2"/><rect x="317" y="361" width="9" height="8" fill="#2a2a2a"/><rect x="316" y="382" width="11" height="8" fill="#e9e2cf"/>'
    s += f'<rect x="262" y="236" width="32" height="42" rx="3" fill="#4f565f" stroke="{INK}" stroke-width="1.1" opacity=".8"/><path d="M278 245 l6 10 h-12z" fill="#c9952e" stroke="{INK}" stroke-width=".8"/><line x1="267" y1="266" x2="289" y2="266" stroke="{INK}" stroke-opacity=".5"/>'
    # пол: стыки уходят в точку схода
    s += f'<rect y="412" width="360" height="8" fill="#23282f"/>'
    for x in range(-240, 620, 80):
        x2 = 180 + (x - 180) * 0.353
        s += f'<line x1="{x}" y1="640" x2="{x2:.1f}" y2="420" stroke="#262b32" stroke-width="1.6"/>'
    for yy in (462, 530, 610):
        s += f'<line x1="0" y1="{yy}" x2="360" y2="{yy}" stroke="#262b32" stroke-width="1.6"/>'
    s += f'<ellipse cx="262" cy="575" rx="24" ry="6" fill="#16191d" stroke="#2c3138"/>' + "".join(f'<line x1="{x}" y1="571" x2="{x}" y2="579" stroke="#2c3138"/>' for x in range(244, 282, 5))
    return s


def lamp(x=180, y=0, r=150, on=True):
    if not on:
        return ""
    n = next(_ids)
    return (f'<defs><radialGradient id="lg{n}"><stop offset="0" stop-color="#f2b04a" stop-opacity=".55"/><stop offset="1" stop-color="#f2b04a" stop-opacity="0"/></radialGradient></defs>'
            f'<circle cx="{x}" cy="{y+44}" r="{r}" fill="url(#lg{n})"/><line x1="{x}" y1="0" x2="{x}" y2="{y+20}" stroke="#2a2a2a" stroke-width="1.5"/>'
            f'<rect x="{x-6}" y="{y+18}" width="12" height="7" rx="2" fill="#3a3a3a" stroke="{INK}"/><ellipse cx="{x}" cy="{y+36}" rx="9" ry="11" fill="#fff4d6"/>'
            f'<g stroke="#3a3a3a" stroke-width="1.3" fill="none"><ellipse cx="{x}" cy="{y+36}" rx="10" ry="12"/><line x1="{x}" y1="{y+24}" x2="{x}" y2="{y+48}"/>'
            f'<path d="M{x-10} {y+36} h20 M{x-8} {y+29} h16 M{x-8} {y+43} h16"/></g>')


def door_extra(cx, cy, r):
    s = f'<rect x="{cx-r-20}" y="{cy-r*0.55}" width="22" height="26" rx="4" fill="#4a525c" stroke="{INK}" stroke-width="1.5"/><rect x="{cx-r-20}" y="{cy+r*0.35}" width="22" height="26" rx="4" fill="#4a525c" stroke="{INK}" stroke-width="1.5"/>'
    s += f'<path d="M{cx+r*0.2} {cy-r*0.98} A{r} {r} 0 0 1 {cx+r*0.98} {cy+r*0.2} A{r*0.9} {r*0.9} 0 0 0 {cx+r*0.2} {cy-r*0.98} Z" fill="#000" fill-opacity=".18"/>'
    s += f'<path d="M{cx-r*0.75} {cy-r*0.55} A{r*0.92} {r*0.92} 0 0 1 {cx-r*0.1} {cy-r*0.9}" stroke="#fff" stroke-opacity=".18" stroke-width="5" fill="none"/>'
    for dx, dy, rr in ((-0.5, 0.45, 0.12), (0.55, -0.4, 0.08), (0.3, 0.6, 0.1)):
        s += f'<ellipse cx="{cx+dx*r:.1f}" cy="{cy+dy*r:.1f}" rx="{rr*r:.1f}" ry="{rr*r*0.6:.1f}" fill="#7a4a2a" fill-opacity=".35"/>'
    s += f'<rect x="{cx-r*0.35}" y="{cy+r*0.62}" width="{r*0.7}" height="{r*0.13}" fill="#e2b13c" stroke="{INK}" stroke-width="1"/>'
    s += "".join(f'<path d="M{cx-r*0.35+i*r*0.14:.1f} {cy+r*0.75:.1f} l{r*0.07:.1f} {-r*0.13:.1f} h{r*0.06:.1f} l{-r*0.07:.1f} {r*0.13:.1f} z" fill="{INK}"/>' for i in range(5))
    return s


def barrel(x, y, w=54, h=84, level=1.0, label=None, color="#4aa3df"):
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="#9fb6c6" fill-opacity=".35" stroke="{INK}" stroke-width="1.6"/>'
    lh = (h - 12) * level
    if lh > 0:
        s += f'<rect x="{x+4}" y="{y+h-6-lh}" width="{w-8}" height="{lh}" rx="5" fill="{color}" fill-opacity=".85"/><rect x="{x+4}" y="{y+h-6-lh}" width="{w-8}" height="3" fill="#fff" fill-opacity=".35"/>'
    for f in (0.3, 0.7):
        s += f'<rect x="{x-1}" y="{y+h*f-2}" width="{w+2}" height="5" rx="2" fill="#5e7685" stroke="{INK}" stroke-width=".8"/>'
    s += f'<rect x="{x+2}" y="{y-3}" width="{w-4}" height="8" rx="3" fill="#6e8796" stroke="{INK}" stroke-width="1.2"/>'
    s += f'<rect x="{x+w*0.22}" y="{y-7}" width="8" height="5" fill="#d9d6cc" stroke="{INK}" stroke-width=".8"/><rect x="{x+w*0.62}" y="{y-6}" width="6" height="4" fill="#d9d6cc" stroke="{INK}" stroke-width=".8"/>'
    s += f'<rect x="{x+6}" y="{y+10}" width="5" height="{h-20}" rx="2" fill="#fff" fill-opacity=".22"/><rect x="{x+w-12}" y="{y+6}" width="10" height="{h-12}" rx="4" fill="#000" fill-opacity=".14"/>'
    if label:
        s += f'<text x="{x+w/2}" y="{y+h+20}" font-family="DejaVu Sans, Arial, sans-serif" font-size="13" font-weight="bold" fill="#9fb3c8" text-anchor="middle">{label}</text>'
    return s


def generator(x, y, s=1.0, smoke=False, run=False):
    g = f'<g transform="translate({x},{y}) scale({s})">'
    g += f'<circle cx="-38" cy="5" r="9" fill="#1a1a1a" stroke="{INK}"/><circle cx="-38" cy="5" r="3.5" fill="#777"/><circle cx="38" cy="5" r="9" fill="#1a1a1a" stroke="{INK}"/><circle cx="38" cy="5" r="3.5" fill="#777"/>'
    g += f'<rect x="-56" y="-68" width="112" height="70" rx="8" fill="none" stroke="#1f1f1f" stroke-width="5"/>'
    g += f'<rect x="-44" y="-66" width="78" height="22" rx="7" fill="#d4b62f" stroke="{INK}" stroke-width="1.5"/><rect x="-40" y="-63" width="70" height="5" rx="2" fill="#fff" fill-opacity=".25"/><circle cx="22" cy="-67" r="5" fill="#2a2a2a" stroke="{INK}"/><circle cx="-26" cy="-55" r="4.5" fill="#f4efe4" stroke="{INK}"/>'
    g += f'<rect x="-42" y="-42" width="40" height="38" rx="4" fill="#5b6068" stroke="{INK}" stroke-width="1.3"/>' + "".join(f'<line x1="-40" y1="{yy}" x2="-4" y2="{yy}" stroke="#3d4148" stroke-width="2"/>' for yy in range(-38, -6, 5))
    g += f'<rect x="4" y="-40" width="40" height="17" rx="8" fill="#80858c" stroke="{INK}" stroke-width="1.3"/>' + "".join(f'<rect x="{xx}" y="-36" width="3" height="9" fill="#4a4f56"/>' for xx in range(10, 40, 6))
    g += f'<rect x="4" y="-20" width="40" height="17" rx="2" fill="#2d3136" stroke="{INK}" stroke-width="1.2"/><circle cx="14" cy="-11.5" r="4.5" fill="#e9e2cf"/><circle cx="12.5" cy="-11.5" r=".9" fill="#222"/><circle cx="15.5" cy="-11.5" r=".9" fill="#222"/><rect x="26" y="-15" width="6" height="8" fill="#c0392b"/><circle cx="38" cy="-11.5" r="2.5" fill="#2e8b57"/>'
    g += f'<line x1="-56" y1="-30" x2="56" y2="-30" stroke="#1f1f1f" stroke-width="3"/>'
    if run:
        g += f'<path d="M60 -52 l12 -8 l-6 14 l12 -6" stroke="#f2b04a" stroke-width="3" fill="none"/>'
    if smoke:
        g += '<circle cx="50" cy="-48" r="9" fill="#555" fill-opacity=".7"/><circle cx="62" cy="-68" r="13" fill="#666" fill-opacity=".6"/><circle cx="80" cy="-92" r="17" fill="#777" fill-opacity=".5"/>'
    return g + "</g>"


def crates(y, n=6, missing=None):
    s = ""
    for i in range(n):
        x = 24 + i * 52
        if i == missing:
            s += f'<rect x="{x}" y="{y}" width="46" height="40" rx="3" fill="none" stroke="#e8553d" stroke-width="3" stroke-dasharray="6 5"/>'
            continue
        s += f'<rect x="{x}" y="{y}" width="46" height="40" rx="2" fill="#8b6f47" stroke="{INK}" stroke-width="1.4"/>'
        s += f'<rect x="{x}" y="{y}" width="6" height="40" fill="#6d5536"/><rect x="{x+40}" y="{y}" width="6" height="40" fill="#6d5536"/>'
        s += f'<line x1="{x}" y1="{y+13}" x2="{x+46}" y2="{y+13}" stroke="{INK}" stroke-width="1"/><line x1="{x}" y1="{y+27}" x2="{x+46}" y2="{y+27}" stroke="{INK}" stroke-width="1"/>'
        s += "".join(f'<path d="M{x+8} {y+5+k*13} q10 2 30 0" stroke="#5a4528" stroke-opacity=".5" fill="none"/>' for k in range(3))
        s += f'<text x="{x+23}" y="{y+23}" font-family="DejaVu Sans, Arial, sans-serif" font-size="6.5" font-weight="bold" fill="#3a2a18" fill-opacity=".75" text-anchor="middle">ТУШЁНКА</text>'
        s += "".join(f'<circle cx="{x+3}" cy="{y+yy}" r=".9" fill="#2a2018"/><circle cx="{x+43}" cy="{y+yy}" r=".9" fill="#2a2018"/>' for yy in (4, 36))
    return s


def bottle(x, y, h=90, level=1.0, cap=True):
    s = f'<path d="M{x+10} {y+10} h10 v6 q10 4 10 14 v{h-8} q0 6 -6 6 h-18 q-6 0 -6 -6 v{-(h-8)} q0 -10 10 -14 z" fill="#cfe3ef" fill-opacity=".35" stroke="{INK}" stroke-width="1.3"/>'
    lh = (h - 14) * level
    s += f'<rect x="{x+3}" y="{y+h+14-lh}" width="24" height="{lh}" rx="4" fill="#4aa3df" fill-opacity=".85"/>'
    s += f'<rect x="{x}" y="{y+h*0.45}" width="30" height="{h*0.28:.1f}" fill="#e7eef5" stroke="{INK}" stroke-width=".8"/><path d="M{x+4} {y+h*0.6:.1f} q5 -4 11 0 t11 0" stroke="#3a7ab8" stroke-width="2" fill="none"/>'
    s += "".join(f'<line x1="{x+1}" y1="{y+h*f:.1f}" x2="{x+29}" y2="{y+h*f:.1f}" stroke="{INK}" stroke-opacity=".25"/>' for f in (0.85, 0.95))
    s += f'<rect x="{x+4}" y="{y+22}" width="4" height="{h-10}" rx="2" fill="#fff" fill-opacity=".3"/>'
    if cap:
        s += f'<rect x="{x+8}" y="{y}" width="14" height="11" rx="2" fill="#3a7ab8" stroke="{INK}" stroke-width="1"/>' + "".join(f'<line x1="{x+10+k*3}" y1="{y+1}" x2="{x+10+k*3}" y2="{y+10}" stroke="#244e78"/>' for k in range(4))
    return s


def fvu(x=150, y=250, w=130, h=130):
    """Фильтровентиляционная установка: шкаф с решёткой, воздуховод в потолок, манометр, табличка."""
    s = f'<rect x="{x+w*0.35}" y="40" width="{w*0.3}" height="{y-40}" fill="#59606b" stroke="{INK}" stroke-width="1.3"/>' + "".join(f'<rect x="{x+w*0.33}" y="{yy}" width="{w*0.34}" height="6" fill="#3d434b"/>' for yy in range(70, int(y), 60))
    s += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="#4a525c" stroke="{INK}" stroke-width="1.8"/>'
    s += "".join(f'<rect x="{x+12}" y="{y+16+k*10}" width="{w*0.55}" height="5" rx="2" fill="#2f353d"/>' for k in range(7))
    s += f'<circle cx="{x+w-24}" cy="{y+28}" r="13" fill="#f4efe4" stroke="{INK}" stroke-width="1.5"/><line x1="{x+w-24}" y1="{y+28}" x2="{x+w-17}" y2="{y+21}" stroke="#c0392b" stroke-width="2"/>'
    s += f'<rect x="{x+w-38}" y="{y+52}" width="28" height="18" fill="#e2b13c" stroke="{INK}" stroke-width="1"/><text x="{x+w-24}" y="{y+64}" font-family="DejaVu Sans, Arial, sans-serif" font-size="7" font-weight="bold" fill="#222" text-anchor="middle">ФВУ</text>'
    s += "".join(f'<circle cx="{xx}" cy="{yy}" r="2" fill="#2a2f35"/>' for xx in (x + 6, x + w - 6) for yy in (y + 6, y + h - 6))
    s += f'<rect x="{x+w-10}" y="{y}" width="10" height="{h}" fill="#000" fill-opacity=".18"/>'
    return s
