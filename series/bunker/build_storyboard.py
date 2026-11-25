#!/usr/bin/env python3
"""Раскадровка серии «Бункер»: рисует кадры 9:16 в SVG и собирает листы PNG.

    python3 build_storyboard.py          # пишет storyboard/*.html и *.png (нужен playwright)

Кадры плоские, тёмные, с одним акцентом. Текст на кадрах это субтитры и плашки, которые
монтажёр кладёт поверх картинки. Картинка здесь схема: по ней генерируют или снимают настоящую.
"""
import html, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "storyboard")
W, H = 360, 640
BG1, BG2, STEEL, ACC, AMB, WAT, LIGHT, GAS = "#12151a", "#242b34", "#3b424c", "#e8553d", "#f2b04a", "#4aa3df", "#fff4d6", "#b6d94c"
FONT = "DejaVu Sans, Arial, sans-serif"


def t(x, y, s, size=20, fill="#fff", weight="bold", anchor="middle", extra=""):
    return f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" {extra}>{html.escape(s)}</text>'


def caption(lines):
    h = 30 * len(lines) + 14
    y0 = 616 - h
    out = f'<rect x="14" y="{y0}" width="332" height="{h}" rx="12" fill="#000" fill-opacity=".62"/>'
    for i, ln in enumerate(lines):
        out += t(180, y0 + 30 + i * 30, ln, 21)
    return out


def room(dark=False):
    top = "#0b0d11" if dark else BG2
    s = f'<rect width="{W}" height="{H}" fill="{BG1}"/><rect y="0" width="{W}" height="420" fill="{top}"/>'
    for y in range(60, 420, 90):
        s += f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="#000" stroke-opacity=".25"/>'
    for x in range(40, W, 110):
        s += f'<line x1="{x}" y1="0" x2="{x}" y2="420" stroke="#000" stroke-opacity=".18"/>'
    s += f'<rect y="420" width="{W}" height="220" fill="#0e1014"/><line x1="0" y1="420" x2="{W}" y2="420" stroke="#000" stroke-width="3"/>'
    return s


def lamp(x=180, y=0, r=150, on=True):
    if not on:
        return ""
    return (f'<defs><radialGradient id="lg{x}{y}"><stop offset="0" stop-color="{AMB}" stop-opacity=".55"/><stop offset="1" stop-color="{AMB}" stop-opacity="0"/></radialGradient></defs>'
            f'<circle cx="{x}" cy="{y+40}" r="{r}" fill="url(#lg{x}{y})"/><line x1="{x}" y1="0" x2="{x}" y2="{y+18}" stroke="#888"/><circle cx="{x}" cy="{y+24}" r="8" fill="{LIGHT}"/>')


KINDS = {
    "hero": dict(top="#2f5d8a", pants="#2b2f3a", skin="#d9a47e", hair="#2a1d14", hat=None, stripe=True, face=True),
    "friend": dict(top="#4b5a3a", pants="#3a4530", skin="#c99a78", hair=None, hat="#2f3a26", pocket=True),
    "mom": dict(top="#d8a94a", pants="#5a3a4a", skin="#e0b090", hair="#4a2f1e", hat=None),
    "grandpa": dict(top="#8a8f98", pants="#4a4a50", skin="#d8b898", hair=None, hat="#6a5a48"),
    "kid": dict(top="#c24b4b", pants="#34506a", skin="#e0b090", hair="#3a2a1a", hat=None, k=0.66),
    "n1": dict(top="#7a5c8a", pants="#3a3a44", skin="#d0a080", hair="#777", hat=None),
    "n2": dict(top="#5c8a7a", pants="#3d3d3a", skin="#d8b090", hair=None, hat="#8a7a4a"),
    "n3": dict(top="#9a6a4a", pants="#34384a", skin="#c8a080", hair="#3a2a20", hat=None),
    "shadow": dict(top="#14181d", pants="#14181d", skin="#14181d", hair=None, hat=None),
}


def person(x, y, who="hero", s=1.0, pack=False, down=False, lie=False, mood="calm", arm_up=False):
    """Люди. hero = инженер (синяя куртка, светоотражающая полоса, простое лицо). Остальные без лица:
    friend = военный друг (камуфляж), mom/grandpa/kid = семья, n1-n3 = соседи, shadow = силуэт."""
    P = KINDS[who]
    face = P.get("face", False)
    s = s * P.get("k", 1.0)

    def head(hx, hy, show_face=True):
        h = f'<circle cx="{hx}" cy="{hy}" r="15" fill="{P["skin"]}"/>'
        if P.get("hair"):
            h += f'<path d="M{hx-15} {hy-1} a15 15 0 0 1 30 0 q-15 -9 -30 0z" fill="{P["hair"]}"/>'
            if who == "mom":
                h += f'<rect x="{hx-17}" y="{hy-3}" width="6" height="22" rx="3" fill="{P["hair"]}"/><rect x="{hx+11}" y="{hy-3}" width="6" height="22" rx="3" fill="{P["hair"]}"/>'
        if P.get("hat"):
            h += f'<path d="M{hx-16} {hy-3} a16 16 0 0 1 32 0z" fill="{P["hat"]}"/><rect x="{hx-2}" y="{hy-5}" width="22" height="5" rx="2" fill="{P["hat"]}"/>'
        if face and show_face:
            br = {"calm": 0, "worried": 2, "pain": 3}[mood]
            h += f'<circle cx="{hx-5}" cy="{hy+1}" r="1.9" fill="#1a1a1a"/><circle cx="{hx+5}" cy="{hy+1}" r="1.9" fill="#1a1a1a"/>'
            if br:
                h += f'<line x1="{hx-9}" y1="{hy-4-br+3}" x2="{hx-2}" y2="{hy-4}" stroke="#1a1a1a" stroke-width="1.6"/><line x1="{hx+9}" y1="{hy-4-br+3}" x2="{hx+2}" y2="{hy-4}" stroke="#1a1a1a" stroke-width="1.6"/>'
            mouth = {"calm": f"M{hx-4} {hy+8} h8", "worried": f"M{hx-4} {hy+10} q4 -4 8 0", "pain": f"M{hx-4} {hy+10} q4 -4 8 0"}[mood]
            h += f'<path d="{mouth}" stroke="#7a3b2b" stroke-width="1.8" fill="none" stroke-linecap="round"/>'
        return h

    if lie:
        g = f'<g transform="translate({x},{y}) scale({s})">'
        g += f'<rect x="10" y="-22" width="64" height="22" rx="8" fill="{P["pants"]}"/><rect x="68" y="-22" width="14" height="22" rx="5" fill="#14161a"/>'
        g += f'<rect x="-54" y="-28" width="68" height="28" rx="12" fill="{P["top"]}"/>'
        if P.get("stripe"):
            g += f'<rect x="-20" y="-28" width="6" height="28" fill="{AMB}"/>'
        return g + head(-68, -16, True) + "</g>"
    s, y = s * 1.4, min(y + 70, 600)
    hy, hx = (-122, 0) if not down else (-100, 10)
    g = f'<g transform="translate({x},{y}) scale({s})">'
    g += f'<rect x="-15" y="-56" width="13" height="46" rx="4" fill="{P["pants"]}"/><rect x="2" y="-56" width="13" height="46" rx="4" fill="{P["pants"]}"/>'
    g += f'<rect x="-17" y="-12" width="16" height="12" rx="4" fill="#14161a"/><rect x="1" y="-12" width="16" height="12" rx="4" fill="#14161a"/>'
    if pack:
        g += f'<rect x="-36" y="-104" width="18" height="50" rx="7" fill="#c4472f" stroke="#7d2a1a" stroke-width="2"/>'
    if down:
        g += f'<line x1="-18" y1="-98" x2="{hx-9}" y2="{hy+10}" stroke="{P["top"]}" stroke-width="10" stroke-linecap="round"/><line x1="18" y1="-98" x2="{hx+9}" y2="{hy+10}" stroke="{P["top"]}" stroke-width="10" stroke-linecap="round"/>'
    elif arm_up:
        g += f'<rect x="-30" y="-108" width="11" height="52" rx="5" fill="{P["top"]}"/><line x1="24" y1="-100" x2="44" y2="-150" stroke="{P["top"]}" stroke-width="11" stroke-linecap="round"/><circle cx="44" cy="-153" r="6" fill="{P["skin"]}"/>'
    else:
        g += f'<rect x="-30" y="-108" width="11" height="52" rx="5" fill="{P["top"]}"/><rect x="19" y="-108" width="11" height="52" rx="5" fill="{P["top"]}"/>'
    g += f'<rect x="-22" y="-112" width="44" height="64" rx="14" fill="{P["top"]}"/>'
    if P.get("stripe"):
        g += f'<rect x="-22" y="-80" width="44" height="7" fill="{AMB}"/><rect x="-22" y="-66" width="44" height="3" fill="{AMB}" fill-opacity=".7"/>'
    if P.get("pocket"):
        g += f'<rect x="-10" y="-96" width="20" height="16" rx="3" fill="#3f4a2a" stroke="#2c351d" stroke-width="2"/>'
    if down:
        g += f'<circle cx="{hx-9}" cy="{hy+10}" r="6" fill="{P["skin"]}"/><circle cx="{hx+9}" cy="{hy+10}" r="6" fill="{P["skin"]}"/>'
    g += head(hx, hy, not down)
    return g + "</g>"


def barrel(x, y, w=54, h=84, level=1.0, label=None, color=WAT):
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="#1d232b" stroke="#6b7480" stroke-width="3"/>'
    lh = (h - 10) * level
    if lh > 0:
        s += f'<rect x="{x+5}" y="{y+h-5-lh}" width="{w-10}" height="{lh}" rx="4" fill="{color}"/>'
    s += f'<line x1="{x}" y1="{y+22}" x2="{x+w}" y2="{y+22}" stroke="#6b7480" stroke-width="2"/><line x1="{x}" y1="{y+h-22}" x2="{x+w}" y2="{y+h-22}" stroke="#6b7480" stroke-width="2"/>'
    if label:
        s += t(x + w / 2, y + h + 20, label, 13, "#9fb3c8")
    return s


def door(cx=180, cy=250, r=130, open_=False):
    s = f'<circle cx="{cx}" cy="{cy}" r="{r+16}" fill="#0b0d11"/><circle cx="{cx}" cy="{cy}" r="{r}" fill="{STEEL}" stroke="#5b6573" stroke-width="6"/>'
    s += f'<circle cx="{cx}" cy="{cy}" r="{r-24}" fill="none" stroke="#2a3038" stroke-width="5"/>'
    for a in range(0, 360, 30):
        x, y = cx + (r - 10) * math.cos(math.radians(a)), cy + (r - 10) * math.sin(math.radians(a))
        s += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="#222830"/>'
    s += f'<circle cx="{cx}" cy="{cy}" r="34" fill="#2a3038" stroke="#7a8594" stroke-width="5"/>'
    for a in (0, 90):
        dx, dy = 46 * math.cos(math.radians(a)), 46 * math.sin(math.radians(a))
        s += f'<line x1="{cx-dx}" y1="{cy-dy}" x2="{cx+dx}" y2="{cy+dy}" stroke="#7a8594" stroke-width="9" stroke-linecap="round"/>'
    return s


def badge(x, y, text, fill=ACC, w=130, size=24, color="#fff"):
    return f'<rect x="{x-w/2}" y="{y-24}" width="{w}" height="40" rx="10" fill="{fill}"/>' + t(x, y + 5, text, size, color)


def bar(x, y, w, frac, fill=ACC, label_l=None, label_r=None):
    s = f'<rect x="{x}" y="{y}" width="{w}" height="16" rx="8" fill="#222a33"/><rect x="{x}" y="{y}" width="{w*frac:.1f}" height="16" rx="8" fill="{fill}"/>'
    if label_l:
        s += t(x, y + 36, label_l, 13, "#9aa5b1", "normal", "start")
    if label_r:
        s += t(x + w, y + 36, label_r, 13, "#9aa5b1", "normal", "end")
    return s


def generator(x, y, s=1.0, smoke=False, run=False):
    g = f'<g transform="translate({x},{y}) scale({s})"><rect x="-50" y="-60" width="100" height="60" rx="8" fill="#c9b037" stroke="#222" stroke-width="3"/><rect x="-40" y="-50" width="38" height="22" rx="4" fill="#222"/>'
    g += f'<circle cx="26" cy="-34" r="12" fill="#222"/><circle cx="-34" cy="4" r="8" fill="#222"/><circle cx="34" cy="4" r="8" fill="#222"/>'
    if run:
        g += f'<path d="M60 -50 l12 -8 l-6 14 l12 -6" stroke="{AMB}" stroke-width="3" fill="none"/>'
    if smoke:
        g += f'<circle cx="60" cy="-64" r="10" fill="#555" fill-opacity=".7"/><circle cx="72" cy="-84" r="14" fill="#666" fill-opacity=".6"/><circle cx="90" cy="-108" r="18" fill="#777" fill-opacity=".5"/>'
    return g + "</g>"


def gas(n=9, y0=60, y1=380, seed=1):
    s = ""
    for i in range(n):
        x = 30 + (i * 83 + seed * 37) % 300
        y = y0 + (i * 61 + seed * 29) % (y1 - y0)
        s += f'<path d="M{x} {y} q14 -16 28 0 t28 0 t28 0" stroke="{GAS}" stroke-width="5" fill="none" stroke-linecap="round" stroke-opacity=".75"/>'
    return s


def calendar(x, y, text, sub=None, w=118):
    s = f'<rect x="{x-w/2}" y="{y}" width="{w}" height="92" rx="10" fill="#f4efe4"/><rect x="{x-w/2}" y="{y}" width="{w}" height="26" rx="10" fill="{ACC}"/>'
    s += t(x, y + 19, "ДЕНЬ", 14, "#fff") + t(x, y + 68, text, 40, "#222")
    if sub:
        s += t(x, y + 112, sub, 14, "#9aa5b1", "normal")
    return s


def poll(y=500):
    return (f'<rect x="30" y="{y}" width="140" height="48" rx="24" fill="#2e8b57"/>{t(100,y+32,"ДА",22)}'
            f'<rect x="190" y="{y}" width="140" height="48" rx="24" fill="{ACC}"/>{t(260,y+32,"НЕТ",22)}')


def wrap(inner, num, tm):
    tag = f'<rect x="10" y="10" width="86" height="26" rx="8" fill="#000" fill-opacity=".7"/>' + t(53, 28, f"{num} · {tm}", 13, "#ddd")
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">{inner}{tag}</svg>'


def siren(op=0.35):
    return (f'<defs><radialGradient id="sr"><stop offset="0" stop-color="#ff2d2d" stop-opacity="{op}"/><stop offset="1" stop-color="#ff2d2d" stop-opacity="0"/></radialGradient></defs>'
            f'<circle cx="40" cy="60" r="260" fill="url(#sr)"/><circle cx="330" cy="460" r="240" fill="url(#sr)"/>')


def family(y=480, s=0.8, xs=(50, 110, 170, 222, 262)):
    kinds = ("grandpa", "mom", "hero", "kid", "kid")
    return "".join(person(x, y, k, s) for x, k in zip(xs, kinds))


def icon(cx, cy, kind, color):
    s = f'<circle cx="{cx}" cy="{cy}" r="46" fill="#1d232b" stroke="{color}" stroke-width="4"/>'
    if kind == "drop":
        s += f'<path d="M{cx} {cy-26} q22 30 0 48 q-22 -18 0 -48" fill="{color}"/>'
    elif kind == "fan":
        for a in (0, 120, 240):
            s += f'<ellipse cx="{cx}" cy="{cy-14}" rx="8" ry="16" fill="{color}" transform="rotate({a} {cx} {cy})"/>'
        s += f'<circle cx="{cx}" cy="{cy}" r="5" fill="#1d232b"/>'
    elif kind == "bolt":
        s += f'<path d="M{cx+6} {cy-28} l-20 32 h14 l-6 24 l24 -36 h-14z" fill="{color}"/>'
    return s


def card(x, y, w, h, fill="#1b2028", stroke="#3a4452"):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'


def bubble(x, y, w, h, text, fill="#fff", color="#111", tail="l", size=17):
    tx = x + 24 if tail == "l" else x + w - 24
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{fill}"/><path d="M{tx} {y+h} l{14 if tail=="l" else -14} 18 l-26 -18z" fill="{fill}"/>'
    lines = text.split("|")
    for i, ln in enumerate(lines):
        s += t(x + w / 2, y + h / 2 + 6 + (i - (len(lines) - 1) / 2) * 22, ln, size, color)
    return s


def a1():
    s = room(True) + siren() + door(180, 270, 115)
    s += f'<g stroke="{AMB}" stroke-width="5" stroke-linecap="round" fill="none"><path d="M44 190 q-14 30 0 60"/><path d="M26 175 q-22 45 0 90"/><path d="M316 190 q14 30 0 60"/><path d="M334 175 q22 45 0 90"/></g>'
    s += t(180, 100, "≈11 000", 62, AMB) + t(180, 136, "порций на пятерых, на 2 года", 17, "#cfd6de", "normal")
    return s + caption(["А в люк", "стучит шестой"])


def a2():
    s = room(True) + card(95, 110, 170, 280, "#0d1117")
    s += t(180, 145, "Друг", 17, "#9aa5b1") + bubble(108, 165, 144, 70, "Через год|начнётся война.", "#2d3b4e", "#fff", "l", 15) + bubble(108, 270, 144, 44, "Никому.", "#2d3b4e", "#fff", "l", 15)
    s += person(300, 470, "friend", 1.0)
    return s + caption(["Тот самый друг,", "что писал ночью"])


def a3():
    s = room() + lamp() + family(485, 0.8)
    s += t(180, 96, "11 000 ÷ 6", 48, WAT) + bar(40, 140, 280, 1.0, "#2e8b57", None, None) + t(40, 182, "на пятерых: 24 месяца", 14, "#9aa5b1", "normal", "start")
    s += bar(40, 212, 280, 20 / 24, ACC, None, None) + t(40, 254, "на шестерых: 20 месяцев", 14, "#ffb4a6", "normal", "start")
    return s + caption(["На четыре месяца", "меньше"])


def a4():
    s = room() + lamp()
    s += icon(70, 250, "drop", WAT) + icon(180, 250, "fan", "#2e8b57") + icon(290, 250, "bolt", AMB)
    for x, lab in ((70, "скважина"), (180, "воздух"), (290, "генератор")):
        s += t(x, 330, "✓", 34, "#2e8b57") + t(x, 360, lab, 15, "#9aa5b1", "normal")
    s += person(180, 540, "hero", 0.8, mood="worried")
    return s + caption(["Это переживаемо"])


def a5():
    s = room(True) + door(180, 240, 120)
    s += f'<defs><linearGradient id="lt5" x1="0" x2="1"><stop offset="0" stop-color="{LIGHT}" stop-opacity="0"/><stop offset="1" stop-color="{LIGHT}"/></linearGradient></defs><path d="M296 150 q40 90 0 190 l30 0 l0 -190z" fill="url(#lt5)"/>'
    s += person(70, 500, "hero", 1.0, arm_up=True, mood="worried")
    return s + caption(["Ты открываешь"])


def a6():
    s = room(True) + siren(0.45)
    s += person(250, 470, "n1", 0.95) + person(320, 470, "n2", 0.9) + person(180, 500, "n3", 0.9)
    s += person(120, 480, "friend", 1.1)
    return s + caption(["За ним стоят", "соседи"])


def a7():
    s = f'<rect width="{W}" height="{H}" fill="#e9c98a"/><circle cx="290" cy="90" r="46" fill="#fff2b8"/><rect y="330" width="{W}" height="310" fill="#7d9a52"/>'
    s += person(80, 430, "hero", 1.0, arm_up=True) + person(260, 430, "n1", 1.0, arm_up=True)
    for x in range(0, W, 24):
        s += f'<rect x="{x}" y="390" width="16" height="110" fill="#8a5a33" stroke="#4a2f1a" stroke-width="2"/>'
    s += f'<rect x="0" y="420" width="{W}" height="10" fill="#4a2f1a"/>' + t(180, 90, "год назад", 34, "#4a2f1a")
    return s + caption(["Те, кому ты", "махал через забор"])


def a8():
    s = room(True) + siren(0.3) + door(180, 190, 80)
    s += t(180, 330, "Соседей", 56, "#fff") + t(180, 380, "пустил бы?", 38, ACC) + poll(430)
    return s + caption(["Да или нет?"])


def b1():
    s = room(True) + lamp()
    for i in range(3):
        for j in range(2):
            s += barrel(40 + i * 104, 250 + j * 100, 70, 84, 0.9)
    s += t(180, 100, "30 ТОНН", 58, WAT) + t(180, 138, "воды за два года", 19, "#cfd6de", "normal")
    return s + caption(["Куда она", "денется?"])


def b2():
    s = room() + card(24, 130, 312, 120) + f'<circle cx="62" cy="168" r="18" fill="#3a4452"/>' + t(92, 173, "зритель", 14, "#9aa5b1", "normal", "start")
    s += t(180, 210, "А куда они будут ходить", 19, "#fff") + t(180, 236, "в туалет?", 19, "#fff")
    s += card(60, 290, 240, 80, "#1b2028", ACC) + t(180, 340, "А туалет?", 28, ACC)
    s += t(180, 440, "2 из 50 комментариев", 17, "#9aa5b1", "normal")
    return s + caption(["Под первым роликом", "спросили про туалет"])


def b3():
    s = room(True) + door(180, 190, 90) + family(420, 0.62, (60, 120, 180, 232, 270))
    s += t(180, 330, "несколько тонн", 36, AMB) + t(180, 366, "отходов за два года", 20, "#cfd6de", "normal")
    return s + caption(["Люк открывать", "нельзя"])


def b4():
    s = f'<rect width="{W}" height="{H}" fill="#1c2638"/><rect y="150" width="{W}" height="490" fill="#3a2e24"/><rect y="150" width="{W}" height="8" fill="#4f6b2f"/>'
    for y in (230, 330, 430):
        s += f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="#000" stroke-opacity=".18"/>'
    s += f'<rect x="40" y="95" width="130" height="55" fill="#6a717b"/><path d="M34 95 l71 -34 l71 34z" fill="#4a5058"/>' + t(105, 128, "гараж", 15, "#fff")
    s += f'<rect x="95" y="158" width="20" height="90" fill="#555e68"/><rect x="40" y="248" width="200" height="120" rx="8" fill="#242b34" stroke="#7a8594" stroke-width="3"/>' + t(140, 316, "бункер", 18, "#cfd6de")
    s += f'<rect x="262" y="205" width="92" height="48" rx="12" fill="{AMB}"/>' + t(308, 235, "солярка", 13, "#222")
    s += f'<rect x="262" y="338" width="92" height="48" rx="12" fill="#7a6a2a" stroke="{GAS}" stroke-width="3"/>' + t(308, 369, "стоки", 15, "#fff")
    s += f'<line x1="240" y1="300" x2="270" y2="362" stroke="#aaa" stroke-width="5"/><line x1="240" y1="270" x2="270" y2="230" stroke="#aaa" stroke-width="3"/>'
    s += f'<line x1="318" y1="338" x2="318" y2="120" stroke="#aaa" stroke-width="6"/><rect x="310" y="112" width="16" height="10" fill="#aaa"/>' + t(300, 100, "труба", 14, "#fff", "normal", "end")
    return s + caption(["Ещё один бак", "под гаражом, для стоков"])


def b5():
    s = room() + lamp()
    s += f'<path d="M100 330 h160 l-18 100 h-124 z" fill="#5b6573" stroke="#8a95a3" stroke-width="3"/><path d="M140 220 q40 -50 90 -10 l-20 70 h-60 z" fill="#d9b779"/>'
    for i in range(7):
        s += f'<circle cx="{170+i*8}" cy="{300+(i%3)*8}" r="3" fill="#d9b779"/>'
    s += f'<g stroke="{GAS}" stroke-width="4" fill="none" stroke-linecap="round" stroke-opacity=".5"><path d="M170 190 q10 -20 0 -40 t0 -40"/><path d="M200 190 q10 -20 0 -40 t0 -40"/></g>' + t(180, 90, "ОПИЛКИ", 48, AMB)
    return s + caption(["Твёрдое отдельно,", "опилки держат запах"])


def b6():
    s = f'<rect width="{W}" height="{H}" fill="#cdbb8a"/><rect y="340" width="{W}" height="300" fill="#7d9a52"/><rect x="30" y="250" width="130" height="90" fill="#8b8f96"/><path d="M24 250 l71 -36 l71 36z" fill="#5b6068"/>'
    s += f'<line x1="250" y1="340" x2="250" y2="190" stroke="#555" stroke-width="9"/><rect x="240" y="180" width="20" height="12" fill="#555"/><g stroke="{GAS}" stroke-width="4" fill="none" stroke-opacity=".7"><path d="M250 170 q8 -14 0 -28 t0 -28"/></g>'
    s += person(330, 440, "n1", 1.0) + t(300, 190, "?", 60, ACC)
    return s + caption(["Труба выходит", "наружу"])


def b7():
    s = f'<rect width="{W}" height="{H}" fill="#cdbb8a"/><rect y="420" width="{W}" height="220" fill="#7d9a52"/>'
    s += person(90, 480, "hero", 1.0, mood="worried") + person(270, 480, "n1", 1.0)
    s += bubble(20, 120, 150, 60, "Это септик", "#fff", "#111", "l", 20) + bubble(190, 220, 150, 70, "Да, у нас|такой же", "#fff", "#111", "r", 18)
    return s + caption(["Соседи верят:", "у них такой же"])


def b8():
    s = room(True) + calendar(300, 50, "40", None, 90)
    s += person(80, 350, "hero", 1.0, lie=True) + person(260, 350, "mom", 1.0, lie=True) + person(80, 430, "kid", 1.0, lie=True) + person(260, 430, "kid", 1.0, lie=True)
    s += generator(180, 280, 1.0) + t(150, 135, "тишина", 48, ACC) + t(180, 490, "Что сделаешь первым?", 22, AMB)
    return s + caption(["Утро.", "Генератор молчит"])


def c1():
    s = room() + lamp() + generator(180, 360, 1.9)
    s += f'<path d="M150 300 l16 -22 l-12 -14 l20 -22" stroke="{ACC}" stroke-width="5" fill="none"/>' + t(180, 100, "ЛОМАЕТСЯ", 46, ACC) + t(180, 138, "вопрос только когда", 19, "#cfd6de", "normal")
    return s + caption(["Он сломается"])


def c2():
    s = room() + lamp() + card(30, 120, 300, 90) + t(180, 175, "50 моточасов", 34, WAT) + t(180, 198, "замена масла (у многих малых моделей)", 12, "#9aa5b1", "normal")
    s += card(30, 230, 300, 80) + t(180, 262, "6 часов в день", 21, "#fff") + t(180, 292, "= раз в 8 дней", 21, AMB)
    s += card(30, 330, 300, 80, "#1b2028", ACC) + t(180, 362, "≈ 90 замен", 30, ACC) + t(180, 394, "за два года", 18, "#cfd6de", "normal")
    return s + caption(["Масло меняют", "каждые 50 часов"])


def c3():
    s = room(True) + calendar(180, 80, "40", None, 110) + generator(180, 400, 1.6)
    s += t(180, 260, "тишина", 54, ACC) + t(180, 300, "света нет", 22, "#cfd6de", "normal")
    return s + caption(["Утро. Света нет"])


def c4():
    s = room(True) + gas(8, 250, 420, 4)
    s += f'<circle cx="180" cy="190" r="70" fill="none" stroke="#7a8594" stroke-width="8"/>'
    for a in (0, 120, 240):
        s += f'<ellipse cx="180" cy="160" rx="12" ry="30" fill="#7a8594" transform="rotate({a} 180 190)"/>'
    s += f'<line x1="120" y1="130" x2="240" y2="250" stroke="{ACC}" stroke-width="12"/><line x1="240" y1="130" x2="120" y2="250" stroke="{ACC}" stroke-width="12"/>' + t(180, 90, "ВЕНТИЛЯЦИЯ", 34, "#fff")
    return s + caption(["Вентиляция встала"])


def c5():
    s = room() + lamp() + f'<rect x="150" y="250" width="130" height="130" rx="10" fill="#3b424c" stroke="#7a8594" stroke-width="4"/>' + t(215, 322, "фильтр", 18, "#cfd6de", "normal")
    s += f'<line x1="280" y1="315" x2="320" y2="315" stroke="#aaa" stroke-width="8"/><circle cx="320" cy="315" r="30" fill="none" stroke="{AMB}" stroke-width="6" stroke-dasharray="12 8"/><circle cx="345" cy="315" r="9" fill="{AMB}"/>'
    s += person(80, 500, "hero", 1.0, arm_up=True, mood="pain") + t(180, 110, "вручную", 56, AMB)
    return s + caption(["Крутишь фильтр", "вручную"])


def c6():
    s = room() + lamp(180, 0, 120)
    s += person(100, 500, "hero", 1.0, down=True) + person(260, 500, "mom", 1.0)
    s += f'<path d="M140 270 q40 -50 80 0" stroke="{AMB}" stroke-width="6" fill="none"/><path d="M212 258 l12 14 l-18 4" fill="{AMB}"/><path d="M220 300 q-40 50 -80 0" stroke="{AMB}" stroke-width="6" fill="none"/><path d="M148 312 l-12 -14 l18 -4" fill="{AMB}"/>'
    s += t(180, 110, "смена", 50, "#fff")
    return s + caption(["Нужны руки,", "чтобы меняться"])


def c7():
    s = room(True)
    for x, n, lab, col in ((70, "5", "семья", "#9aa5b1"), (180, "6", "+ друг", WAT), (290, "9", "+ соседи", ACC)):
        s += f'<circle cx="{x}" cy="260" r="46" fill="#1d232b" stroke="{col}" stroke-width="5"/>' + t(x, 278, n, 52, col) + t(x, 340, lab, 17, "#cfd6de", "normal")
    s += t(180, 130, "РУК ДЛЯ ФИЛЬТРА", 30, "#fff")
    return s + caption(["Считай руки"])


def c8():
    s = room(True) + siren(0.3) + door(180, 190, 80)
    s += person(300, 520, "n1", 0.7) + person(60, 520, "n2", 0.7)
    s += t(180, 330, "Пустил бы", 52, "#fff") + t(180, 380, "соседей?", 52, ACC) + poll(420)
    return s + caption(["Ради лишних рук"])


VIDEOS = [
    dict(slug="A", title="Шестой в бункере: еды на 20 месяцев", thumb="ОТКРЫТЬ?",
         hook="Почти одиннадцать тысяч порций. Это еда на пятерых на два года. А в люк стучит шестой.", runtime="≈40 с",
         scenes=[
             (a1, "0-6 с", "Почти одиннадцать тысяч порций. Это еда на пятерых на два года. А в люк стучит шестой.", "Люк в красном свете сирен, цифра ≈11 000 крупно, дрожь от ударов.", "сирена стихает, три глухих удара"),
             (a2, "6-12 с", "Сирены стихли. Это друг, тот самый, что год назад написал тебе ночью.", "Экран телефона: «Через год начнётся война. Никому.» Внизу силуэт друга в камуфляже.", "звук уведомления из первого ролика"),
             (a3, "12-22 с", "Ты считаешь быстро: одиннадцать тысяч порций на шестерых. Хватит на двадцать месяцев, а не на двадцать четыре.", "Семья из пяти под лампой, две шкалы: 24 и 20 месяцев.", "быстрое тиканье, как калькулятор"),
             (a4, "22-26 с", "Вода из скважины, воздух идёт. Это можно пережить.", "Три галочки: скважина, воздух, генератор.", "три коротких «дзынь»"),
             (a5, "26-29 с", "Ты открываешь.", "Рука на штурвале люка, щель света справа. Кадр короткий.", "скрип штурвала, тишина"),
             (a6, "29-35 с", "Друг заходит один. Но за ним в свете сирен стоят люди. Это соседи.", "Друг на первом плане, три соседа без лиц в красном свете.", "низкий нарастающий тон"),
             (a7, "35-39 с", "Те, кому ты целый год махал через забор.", "Возврат в день: солнце, забор, вы машете друг другу.", "птицы, затем резкий обрыв"),
             (a8, "39-42 с", "Друга ты пустил. А их? Пиши: да или нет.", "Люк, слово «Соседей», кнопки ДА/НЕТ. Закреплённый комментарий с тем же вопросом.", "один удар"),
         ]),
    dict(slug="B", title="Куда в бункере девать 30 тонн воды", thumb="А ТУАЛЕТ?",
         hook="Вы потратите тридцать тонн воды. Куда она денется?", runtime="≈42 с",
         scenes=[
             (b1, "0-5 с", "Вы потратите тридцать тонн воды. Куда она денется?", "Бочки с водой стопкой, «30 ТОНН» крупно.", "льющаяся вода, обрыв"),
             (b2, "5-11 с", "Под первым роликом спросили про туалет, и вопрос правильный.", "Карточка комментария «А куда они будут ходить в туалет?», ниже «А туалет?».", "звук пуш-уведомления"),
             (b3, "11-17 с", "Пятеро за два года оставят несколько тонн отходов, а люк открывать нельзя.", "Люк, пятеро внизу, надпись «несколько тонн».", "гул, удар"),
             (b4, "17-26 с", "Решение как с соляркой: под гаражом закапываешь ещё один бак, только для стоков. К нему труба с затвором, чтобы запах не шёл обратно.", "Разрез: гараж, бункер, бак с соляркой и новый бак «стоки», труба вверх.", "звук лопаты, гулкий стук по металлу"),
             (b5, "26-30 с", "Твёрдое отдельно, в сухой туалет с опилками. Опилки держат запах.", "Совок опилок в ведро, дымки запаха гаснут.", "шорох сыпучего"),
             (b6, "30-35 с", "Бак нужно проветривать, иначе газ пойдёт в бункер. Значит, труба выходит наружу.", "Двор в селе: труба торчит у гаража, сосед смотрит, над ним «?».", "ветер, шаги"),
             (b7, "35-38 с", "Соседям скажешь: это септик. У них такой же.", "Диалог пузырями: «Это септик» и «Да, у нас такой же».", "лёгкая музыка, тёплая"),
             (b8, "38-44 с", "На сороковой день все спят. Утром ты слышишь тишину. Генератор не работает. Что сделаешь первым? Пиши.", "Бункер, спящая семья, молчащий генератор, надпись «Что сделаешь первым?».", "гул стихает, остаётся тишина"),
         ]),
    dict(slug="C", title="Генератор бункера встал на 40-й день", thumb="КРУТИ РУКАМИ",
         hook="Генератор в твоём бункере сломается. Вопрос только когда.", runtime="≈44 с",
         scenes=[
             (c1, "0-5 с", "Генератор в твоём бункере сломается. Вопрос только когда.", "Генератор крупно, трещина, слово ЛОМАЕТСЯ.", "рокот, кашель мотора"),
             (c2, "5-14 с", "У многих малых генераторов масло меняют каждые пятьдесят моточасов. При шести часах в день это раз в восемь дней, за два года почти девяносто замен.", "Три карточки: 50 часов, раз в 8 дней, ≈90 замен. Подпись «у многих малых моделей».", "быстрое тиканье счётчика"),
             (c3, "14-19 с", "Сорокой день, утро. Тишина. Света нет.", "Тёмный бункер, календарь 40, молчащий генератор.", "тишина, затем щелчок реле"),
             (c4, "19-27 с", "Значит, встала и вентиляция. А в закрытом бункере, как ты помнишь, на второй день уже нечем дышать.", "Остановленный вентилятор, красный крест, зелёные волны газа.", "затихающий гул вентилятора"),
             (c5, "27-33 с", "Ты берёшь рукоятку и крутишь фильтр вручную. Это тяжёлая работа.", "Герой крутит ручку фильтра, лицо от напряжения.", "скрип рукоятки, дыхание"),
             (c6, "33-37 с", "Нужно меняться, и нужны люди.", "Герой выдохся, мама ждёт смены, стрелки по кругу.", "ритмичное скрипение"),
             (c7, "37-41 с", "Считай: рук для фильтра пять. Или шесть. Или девять.", "Три круга: 5, 6, 9 и подписи «семья», «+ друг», «+ соседи».", "три нарастающих удара"),
             (c8, "41-45 с", "Пустил бы соседей ради лишних рук? Да или нет.", "Люк, силуэты соседей, кнопки ДА/НЕТ.", "один удар, обрыв"),
         ]),
]


def sheet(v):
    cards = ""
    for i, (fn, tm, narr, vis, sfx) in enumerate(v["scenes"], 1):
        svg = wrap(fn(), f"{i:02d}", tm)
        cards += (f'<div class="card">{svg}<div class="n"><b>Диктор:</b> {html.escape(narr)}<br><b>Кадр:</b> {html.escape(vis)}<br><b>Звук:</b> {html.escape(sfx)}</div></div>')
    return f"""<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<style>
body{{margin:0;background:#0b0d11;color:#e8ecf1;font-family:{FONT};padding:24px}}
h1{{margin:0 0 6px;font-size:30px}} .m{{color:#9aa5b1;font-size:17px;line-height:1.5;margin-bottom:22px}}
.m b{{color:#f2b04a}} .g{{display:grid;grid-template-columns:repeat(2,360px);gap:22px;justify-content:center}}
.card{{background:#12151a;border-radius:14px;overflow:hidden;width:360px}} .card svg{{display:block}}
.n{{padding:12px 14px 14px;font-size:14px;line-height:1.45;color:#cfd6de}} .n b{{color:#f2b04a}}
</style><body><div style="width:742px;margin:0 auto">
<h1>Ролик {v['slug']}: {html.escape(v['title'])}</h1>
<div class="m"><b>Миниатюра:</b> {html.escape(v['thumb'])} · <b>Длина:</b> {v['runtime']}<br><b>Хук:</b> {html.escape(v['hook'])}</div>
<div class="g">{cards}</div></div></body></html>"""


def main(videos=None):
    os.makedirs(OUT, exist_ok=True)
    paths = []
    for v in (videos or VIDEOS):
        p = os.path.join(OUT, f"bunker-{v['slug']}.html")
        open(p, "w", encoding="utf8").write(sheet(v))
        paths.append(p)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright не найден: открой HTML в браузере"); return
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 790, "height": 900}, device_scale_factor=1.5)
        for p in paths:
            pg.goto("file://" + p)
            pg.screenshot(path=p.replace(".html", ".png"), full_page=True)
            print("ok", p.replace(".html", ".png"))
        b.close()


if __name__ == "__main__":
    main()
