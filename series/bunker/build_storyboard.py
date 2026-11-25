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


def person(x, y, who="hero", s=1.0, pack=False, down=False, lie=False, mood="calm"):
    """Люди с одеждой. hero = инженер (куртка со светоотражающей полосой, простое лицо).
    friend = механик (комбинезон, кепка, лицо без черт). shadow = силуэт."""
    P = {"hero": dict(top="#2f5d8a", pants="#2b2f3a", boot="#14161a", skin="#d9a47e"),
         "friend": dict(top="#6b7a4a", pants="#58663c", boot="#14161a", skin="#c99a78"),
         "shadow": dict(top="#14181d", pants="#14181d", boot="#14181d", skin="#14181d")}[who]
    face = who == "hero"

    def head(hx, hy, show_face=True):
        h = f'<circle cx="{hx}" cy="{hy}" r="15" fill="{P["skin"]}"/>'
        if who == "hero":
            h += f'<path d="M{hx-15} {hy-2} a15 15 0 0 1 30 0 q-15 -9 -30 0z" fill="#2a1d14"/>'
        elif who == "friend":
            h += f'<path d="M{hx-16} {hy-3} a16 16 0 0 1 32 0z" fill="#a8412f"/><rect x="{hx-2}" y="{hy-5}" width="22" height="5" rx="2" fill="#a8412f"/>'
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
        g += f'<rect x="10" y="-22" width="64" height="22" rx="8" fill="{P["pants"]}"/><rect x="68" y="-22" width="14" height="22" rx="5" fill="{P["boot"]}"/>'
        g += f'<rect x="-54" y="-28" width="68" height="28" rx="12" fill="{P["top"]}"/>'
        if who == "hero":
            g += f'<rect x="-20" y="-28" width="6" height="28" fill="{AMB}"/>'
        return g + head(-68, -16, True) + "</g>"
    s, y = s * 1.4, min(y + 70, 600)
    hy, hx = (-122, 0) if not down else (-100, 10)
    g = f'<g transform="translate({x},{y}) scale({s})">'
    g += f'<rect x="-15" y="-56" width="13" height="46" rx="4" fill="{P["pants"]}"/><rect x="2" y="-56" width="13" height="46" rx="4" fill="{P["pants"]}"/>'
    g += f'<rect x="-17" y="-12" width="16" height="12" rx="4" fill="{P["boot"]}"/><rect x="1" y="-12" width="16" height="12" rx="4" fill="{P["boot"]}"/>'
    if pack:
        g += f'<rect x="-36" y="-104" width="18" height="50" rx="7" fill="#c4472f" stroke="#7d2a1a" stroke-width="2"/>'
    if down:
        g += f'<line x1="-18" y1="-98" x2="{hx-9}" y2="{hy+10}" stroke="{P["top"]}" stroke-width="10" stroke-linecap="round"/><line x1="18" y1="-98" x2="{hx+9}" y2="{hy+10}" stroke="{P["top"]}" stroke-width="10" stroke-linecap="round"/>'
    else:
        g += f'<rect x="-30" y="-108" width="11" height="52" rx="5" fill="{P["top"]}"/><rect x="19" y="-108" width="11" height="52" rx="5" fill="{P["top"]}"/>'
    g += f'<rect x="-22" y="-112" width="44" height="64" rx="14" fill="{P["top"]}"/>'
    if who == "hero":
        g += f'<rect x="-22" y="-80" width="44" height="7" fill="{AMB}"/><rect x="-22" y="-66" width="44" height="3" fill="{AMB}" fill-opacity=".7"/>'
    elif who == "friend":
        g += f'<rect x="-10" y="-96" width="20" height="16" rx="3" fill="#56633a" stroke="#3f4a2a" stroke-width="2"/>'
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


# ---------- ролик A ----------
def a1():
    s = room(True) + door(180, 270, 120)
    s += f'<g stroke="{AMB}" stroke-width="5" stroke-linecap="round" fill="none"><path d="M40 190 q-14 30 0 60"/><path d="M22 175 q-22 45 0 90"/><path d="M320 190 q14 30 0 60"/><path d="M338 175 q22 45 0 90"/></g>'
    s += t(180, 105, "1095 Л", 64, AMB) + t(180, 140, "вся вода на год", 18, "#cfd6de", "normal")
    return s + caption(["А друг уже", "стучит в дверь"])


def a2():
    s = room() + lamp()
    for i in range(5):
        s += barrel(26 + i * 62, 300, 52, 84, 1.0, "219 л" if i == 0 else None)
    s += person(300, 470, "hero", 1.0)
    s += t(180, 120, "3 Л × 365 = 1095 Л", 28, WAT) + t(180, 156, "на одного человека", 16, "#cfd6de", "normal")
    return s + caption(["Ты считал", "на одного"])


def a3():
    s = room() + lamp()
    for i in range(5):
        s += barrel(26 + i * 62, 300, 52, 84, 1.0 if i < 2 else 0.0)
    s += person(120, 480, "hero", 0.9) + person(230, 480, "friend", 0.9)
    s += t(180, 100, "182", 92, ACC) + t(180, 136, "ДНЯ НА ДВОИХ", 20, "#fff")
    s += bar(30, 230, 300, 0.5, ACC, "0", "365 дней")
    return s + caption(["На двоих воды", "на 182 дня"])


def a4():
    s = room(True) + door(180, 250, 120)
    s += f'<rect x="120" y="430" width="120" height="8" fill="{AMB}" fill-opacity=".8"/><rect x="146" y="430" width="18" height="8" fill="#000"/><rect x="198" y="430" width="18" height="8" fill="#000"/>'
    s += person(80, 560, "hero", 0.7, mood="worried")
    s += f'<circle cx="180" cy="250" r="9" fill="{AMB}"/>'
    return s + caption(["Он слышит,", "что ты за дверью"])


def a5():
    s = room(True)
    s += f'<defs><linearGradient id="lt" x1="0" x2="1"><stop offset="0" stop-color="{LIGHT}"/><stop offset="1" stop-color="{LIGHT}" stop-opacity="0"/></linearGradient></defs>'
    s += f'<polygon points="200,60 360,0 360,640 200,430" fill="url(#lt)" fill-opacity=".85"/><rect x="190" y="60" width="14" height="370" fill="{STEEL}"/>'
    s += person(300, 440, "shadow", 1.1, pack=True) + person(90, 470, "hero", 1.0, mood="worried")
    return s + caption(["Ты открываешь"])


def a6():
    s = room() + lamp()
    for i, x in enumerate((70, 220)):
        s += f'<rect x="{x}" y="260" width="70" height="86" rx="10" fill="#1d232b" stroke="#6b7480" stroke-width="3"/><rect x="{x+6}" y="{346-40}" width="58" height="34" rx="5" fill="{WAT}"/>'
        s += t(x + 35, 380, "1,5 Л", 18, WAT)
    s += t(180, 120, "1,5 Л", 70, WAT) + t(180, 156, "в день каждому", 18, "#cfd6de", "normal") + badge(180, 205, "вдвое меньше", ACC, 190, 20)
    s += bar(30, 440, 300, 1.0, "#2e8b57", "0", "365 дней: хватит")
    return s + caption(["По полтора литра", "каждому"])


def a7():
    s = room() + lamp(180, 0, 120)
    s += person(120, 500, "hero", 0.9, down=True) + person(250, 500, "friend", 0.9, down=True)
    s += f'<path d="M170 250 q14 -26 28 0 t28 0" stroke="{ACC}" stroke-width="5" fill="none"/>'
    s += t(180, 110, "голова болит", 24, "#cfd6de") + t(180, 142, "сил нет", 24, "#cfd6de")
    return s + caption(["Организм терпит,", "но плохо"])


def a8():
    s = room() + lamp()
    s += f'<path d="M130 300 h100 l-12 110 h-76 z" fill="#5b6573" stroke="#8a95a3" stroke-width="3"/><rect x="124" y="288" width="112" height="14" rx="6" fill="#8a95a3"/>'
    s += t(180, 250, "?", 120, AMB) + t(180, 130, "Куда это девать?", 26, "#fff")
    s += poll(470)
    return s + caption(["Открыл бы дверь?"])


# ---------- ролик B ----------
def b1():
    s = room(True) + door(180, 270, 110)
    s += barrel(30, 380, 54, 84, 0.8, None, "#c8b04a") + barrel(276, 380, 54, 84, 0.9, None, "#c8b04a")
    s += t(180, 100, "СОТНИ", 56, AMB) + t(180, 140, "литров отходов за год", 19, "#cfd6de", "normal")
    return s + caption(["Бункер закрыт.", "Выйти нельзя"])


def b2():
    s = room() + lamp()
    s += f'<circle cx="80" cy="260" r="46" fill="#1d232b" stroke="{WAT}" stroke-width="4"/><path d="M80 232 q20 30 0 48 q-20 -18 0 -48" fill="{WAT}"/>'
    s += f'<circle cx="180" cy="260" r="46" fill="#1d232b" stroke="{AMB}" stroke-width="4"/><rect x="156" y="244" width="48" height="32" rx="6" fill="{AMB}"/>'
    s += f'<circle cx="280" cy="260" r="46" fill="#1d232b" stroke="{ACC}" stroke-width="4"/>' + t(280, 290, "?", 80, ACC)
    s += t(80, 340, "✓", 36, "#2e8b57") + t(180, 340, "✓", 36, "#2e8b57") + t(80, 368, "вода", 16, "#9aa5b1", "normal") + t(180, 368, "еда", 16, "#9aa5b1", "normal") + t(280, 368, "туалет", 16, "#9aa5b1", "normal")
    s += person(180, 540, "hero", 0.7, mood="worried")
    return s + caption(["Про туалет", "ты не думал"])


def b3():
    s = room() + lamp()
    s += f'<path d="M110 250 h100 l-12 130 h-76 z" fill="#5b6573" stroke="#8a95a3" stroke-width="3"/><rect x="104" y="236" width="112" height="16" rx="6" fill="#8a95a3"/>'
    s += f'<rect x="250" y="190" width="26" height="190" rx="8" fill="#1d232b" stroke="#6b7480" stroke-width="3"/><rect x="254" y="{380-4-150}" width="18" height="150" rx="5" fill="{ACC}"/>' + t(263, 410, "полное", 12, "#9aa5b1", "normal")
    s += t(180, 110, "10 дней", 52, ACC) + t(180, 148, "и ведро полное", 19, "#cfd6de", "normal")
    s += bar(30, 470, 300, 0.03, ACC, "день 10", "осталось 355")
    return s + caption(["Ведро с крышкой", "на десять дней"])


def b4():
    s = room() + lamp()
    s += f'<rect x="30" y="250" width="120" height="130" rx="12" fill="#1d232b" stroke="{WAT}" stroke-width="4"/><rect x="40" y="300" width="100" height="70" rx="6" fill="#c8b04a"/>' + t(90, 410, "жидкое:", 15, "#9aa5b1") + t(90, 430, "закрытый бак", 15, "#9aa5b1")
    s += f'<rect x="210" y="270" width="120" height="110" rx="12" fill="#1d232b" stroke="{AMB}" stroke-width="4"/><rect x="220" y="320" width="100" height="50" rx="6" fill="#8b6f47"/>' + t(270, 410, "твёрдое:", 15, "#9aa5b1") + t(270, 430, "сухой туалет", 15, "#9aa5b1")
    s += t(180, 120, "СИСТЕМА", 44, AMB) + f'<path d="M160 320 h40" stroke="#666" stroke-width="3"/>'
    return s + caption(["Жидкое отдельно,", "твёрдое отдельно"])


def b5():
    s = room() + lamp()
    s += f'<path d="M100 330 h160 l-18 100 h-124 z" fill="#5b6573" stroke="#8a95a3" stroke-width="3"/>'
    s += f'<path d="M140 220 q40 -50 90 -10 l-20 70 h-60 z" fill="#d9b779"/>'
    for i in range(7):
        s += f'<circle cx="{170+i*8}" cy="{300+(i%3)*8}" r="3" fill="#d9b779"/>'
    s += f'<g stroke="{GAS}" stroke-width="4" fill="none" stroke-linecap="round" stroke-opacity=".5"><path d="M170 190 q10 -20 0 -40 t0 -40"/><path d="M200 190 q10 -20 0 -40 t0 -40"/></g>'
    s += t(180, 110, "ОПИЛКИ", 48, AMB)
    return s + caption(["Они держат запах"])


def b6():
    s = room() + lamp(180, 0, 110)
    s += person(90, 500, "hero", 1.0, mood="worried") + person(270, 500, "friend", 1.0)
    s += f'<g stroke="{ACC}" stroke-width="5" fill="none"><path d="M130 300 l30 -14 l-30 -14"/><path d="M230 300 l-30 -14 l30 -14"/></g>'
    s += f'<path d="M150 320 l20 -22 l20 22 l20 -22" stroke="{ACC}" stroke-width="4" fill="none"/>'
    s += t(180, 110, "ссора", 56, ACC) + t(180, 146, "из-за запаха", 19, "#cfd6de", "normal")
    return s + caption(["Люди ссорятся", "из-за меньшего"])


def b7():
    s = room() + lamp()
    s += generator(150, 440, 1.5, smoke=True) + calendar(280, 140, "40", None, 100)
    s += person(300, 470, "friend", 0.9)
    s += f'<g stroke="{AMB}" stroke-width="4" fill="none" stroke-linecap="round"><path d="M70 330 l-16 -10"/><path d="M60 358 l-22 0"/><path d="M70 384 l-16 10"/></g>'
    s += t(110, 160, "кхх…", 34, "#cfd6de")
    return s + caption(["Генератор кашляет,", "друг: «Включим тут»"])


def b8():
    s = room() + lamp()
    s += generator(180, 360, 1.7, smoke=True, run=True)
    s += t(180, 130, "Включил бы", 40, "#fff") + t(180, 172, "его внутри?", 40, "#fff")
    s += poll(470)
    return s + caption(["Пиши: да или нет"])


# ---------- ролик C ----------
def c1():
    s = room() + lamp() + generator(130, 440, 1.4, smoke=True, run=True)
    s += person(280, 470, "hero", 0.9, down=True)
    s += f'<rect x="196" y="120" width="130" height="60" rx="12" fill="#000" fill-opacity=".6"/>' + t(261, 160, "40:00", 36, ACC)
    s += f'<g stroke="{ACC}" stroke-width="4" fill="none" stroke-linecap="round"><path d="M262 330 l-12 -18"/><path d="M280 322 l0 -22"/><path d="M298 330 l12 -18"/></g>'
    return s + caption(["Через сорок минут", "болит голова"])


def c2():
    s = room() + lamp() + gas(9, 315, 410, 2) + generator(110, 470, 1.3, smoke=False, run=True)
    s += person(280, 480, "hero", 0.9, mood="pain")
    s += f'<circle cx="180" cy="190" r="44" fill="#000" fill-opacity=".55"/><circle cx="180" cy="190" r="26" fill="none" stroke="#fff" stroke-width="5"/><line x1="160" y1="210" x2="200" y2="170" stroke="{ACC}" stroke-width="6"/>'
    s += t(180, 120, "CO", 56, GAS) + t(180, 290, "без запаха и цвета", 18, "#cfd6de", "normal")
    return s + caption(["Угарный газ", "не пахнет и не виден"])


def c3():
    s = room(True) + gas(7, 205, 335, 3)
    s += f'<rect x="20" y="360" width="150" height="14" rx="5" fill="{STEEL}"/><rect x="190" y="360" width="150" height="14" rx="5" fill="{STEEL}"/>'
    s += person(100, 360, "hero", 1.0, lie=True) + person(270, 360, "friend", 1.0, lie=True)
    s += t(60, 270, "Z", 40, "#9aa5b1") + t(95, 235, "z", 28, "#9aa5b1") + t(240, 270, "Z", 40, "#9aa5b1") + t(275, 235, "z", 28, "#9aa5b1")
    s += t(180, 110, "во сне", 44, ACC) + t(180, 146, "организм не жалуется", 18, "#cfd6de", "normal")
    return s + caption(["Это самый", "опасный момент"])


def c4():
    s = room(True) + generator(180, 340, 1.8, smoke=True)
    s += f'<circle cx="180" cy="270" r="140" fill="none" stroke="{ACC}" stroke-width="22"/><line x1="82" y1="172" x2="278" y2="368" stroke="{ACC}" stroke-width="22"/>'
    s += t(180, 90, "НИКОГДА", 52, ACC) + t(180, 495, "даже на 10 минут", 22, "#fff")
    return s + caption(["В закрытом", "помещении"])


def c5():
    s = f'<rect width="{W}" height="{H}" fill="#1c2638"/><rect y="330" width="{W}" height="310" fill="#262e1e"/><rect x="0" y="330" width="{W}" height="6" fill="#2a3524"/>'
    s += generator(90, 420, 1.2, smoke=False, run=True)
    for r in (60, 110, 170, 240):
        s += f'<path d="M{90+r*0.35:.0f} {360-r*0.5:.0f} a{r} {r} 0 0 1 0 {r}" stroke="{AMB}" stroke-opacity="{0.9-r/320:.2f}" stroke-width="4" fill="none"/>'
    s += person(300, 440, "shadow", 0.9) + f'<circle cx="300" cy="333" r="30" fill="none" stroke="{ACC}" stroke-width="4" stroke-dasharray="6 6"/>'
    s += t(180, 110, "шум слышно далеко", 26, "#fff") + t(180, 146, "снаружи война", 20, ACC)
    return s + caption(["Снаружи", "ставить нельзя"])


def c6():
    s = room(True)
    s += f'<defs><radialGradient id="dk"><stop offset="0" stop-color="{AMB}" stop-opacity=".45"/><stop offset="1" stop-color="{AMB}" stop-opacity="0"/></radialGradient></defs><circle cx="180" cy="300" r="110" fill="url(#dk)"/>'
    s += person(110, 480, "hero", 0.9, down=True) + person(250, 480, "friend", 0.9, down=True)
    s += f'<rect x="130" y="130" width="100" height="56" rx="8" fill="#1d232b" stroke="{AMB}" stroke-width="4"/><rect x="230" y="148" width="10" height="20" fill="{AMB}"/><rect x="136" y="136" width="30" height="44" fill="{AMB}"/>'
    s += t(180, 230, "2 часа света в день", 20, AMB)
    return s + caption(["Панель, аккумуляторы", "и темнота"])


def c7():
    s = room(True) + calendar(180, 90, "230", None, 150)
    s += f'<rect x="100" y="260" width="160" height="200" rx="30" fill="#1b1f25"/><circle cx="180" cy="230" r="34" fill="#232a33"/><path d="M180 196 a34 34 0 0 1 0 68 z" fill="#0a0c10"/><path d="M144 226 a36 36 0 0 1 72 0z" fill="#a8412f"/><rect x="176" y="220" width="50" height="8" rx="3" fill="#a8412f"/><rect x="100" y="270" width="160" height="40" fill="#56633a"/>'
    s += t(180, 400, "?", 120, ACC)
    return s + caption(["Друг признаётся", "в том, о чём молчал"])


def c8():
    s = room(True)
    s += t(180, 170, "Что он", 64, "#fff") + t(180, 245, "скрывал?", 64, ACC)
    s += f'<rect x="40" y="320" width="280" height="90" rx="20" fill="#1d232b" stroke="{ACC}" stroke-width="3"/>' + t(180, 375, "версии в комментарии", 21, "#cfd6de", "normal")
    return s + caption(["Пиши версии"])


VIDEOS = [
    dict(slug="A", title="Пустил друга в бункер: воды на 182 дня", thumb="НЕ ОТКРЫВАЙ?",
         hook="Тысяча девяносто пять литров. Это вся твоя вода на год. А друг уже стучит в дверь.", runtime="≈40 с",
         scenes=[
             (a1, "0-6 с", "Тысяча девяносто пять литров. Вся твоя вода на год. А друг уже стучит.", "Люк, тряска от ударов, цифра 1095 бьёт в центр на первом кадре.", "глухие удары по металлу, тишина между ними"),
             (a2, "6-10 с", "Ты считал на одного: три литра в день, триста шестьдесят пять дней.", "Пять бочек, формула 3 × 365, один человек у стены.", "тихий гул вентиляции"),
             (a3, "10-14 с", "На двоих этого хватит на сто восемьдесят два дня.", "Два человека, три бочки пустеют, шкала на половине года.", "звук льющейся воды, затем пустой стук"),
             (a4, "14-17 с", "Можно не открывать. Но он слышит, что ты за дверью.", "Полоска света под дверью, две тени ног, жёлтый глазок.", "стук прекращается, слышно дыхание"),
             (a5, "17-19 с", "Ты открываешь.", "Люк открыт, контровой свет, силуэт друга с рюкзаком. Кадр короткий, 2 секунды.", "скрип засова, один низкий удар"),
             (a6, "19-25 с", "Выход один: по полтора литра в день каждому. Вдвое меньше, чем рассчитывал.", "Две кружки по 1,5 л, плашка «вдвое меньше», шкала на 365 дней зелёная.", "лёгкий звон кружки"),
             (a7, "25-29 с", "Организм терпит, только голова болит и сил нет.", "Двое сидят, голова в руках, тусклая лампа.", "ровный низкий гул, свет мигает"),
             (a8, "29-40 с", "Всё, что вы выпьете, придётся куда-то девать. Открыл бы дверь? Да или нет.", "Ведро со знаком вопроса, внизу кнопки ДА и НЕТ. Закреплённый комментарий с тем же вопросом.", "короткий звук «кап», обрыв"),
         ]),
    dict(slug="B", title="Что если в бункере нет туалета? 365 дней", thumb="КУДА ДЕВАТЬ?",
         hook="Двое людей за год производят сотни литров отходов. Бункер закрыт. Выйти нельзя.", runtime="≈41 с",
         scenes=[
             (b1, "0-6 с", "Двое людей за год производят сотни литров отходов. Бункер закрыт.", "Люк, слово СОТНИ крупно, два бака по бокам.", "гул, один низкий удар"),
             (b2, "6-10 с", "Ты думал про воду и про еду. Про туалет не думал.", "Три круга: вода ✓, еда ✓, туалет «?» красным.", "две галочки «дзинь», третий звук фальшивый"),
             (b3, "10-19 с", "Обычное ведро с крышкой заполняется меньше чем за десять дней. Остаётся триста пятьдесят пять.", "Ведро, шкала заполнения, календарь «355».", "щелчок крышки, затем тиканье"),
             (b4, "19-24 с", "Жидкое отдельно, в закрытый бак. Твёрдое отдельно, в сухой туалет.", "Два контейнера разного цвета, подписи.", "два разных глухих стука"),
             (b5, "24-28 с", "Сверху засыпают опилки. Они держат запах.", "Совок опилок, дымки запаха гаснут.", "шорох сыпучего"),
             (b6, "28-34 с", "Люди ссорятся из-за меньшего, а вас двое и дверь одна.", "Двое спинами друг к другу, красная ломаная между ними.", "гул нарастает"),
             (b7, "34-39 с", "На сороковой день генератор начинает кашлять, и друг предлагает включить его внутри.", "Календарь «40», генератор с дымом, друг показывает на него.", "кашель двигателя, обрыв"),
             (b8, "39-43 с", "Включил бы? Да или нет.", "Генератор крупно, внизу ДА/НЕТ, закреплённый комментарий.", "тишина, затем один удар"),
         ]),
    dict(slug="C", title="Генератор в бункере: через 40 минут", thumb="ГОЛОВА БОЛИТ",
         hook="Ты включил генератор в бункере. Через сорок минут у тебя болит голова.", runtime="≈43 с",
         scenes=[
             (c1, "0-6 с", "Ты включил генератор в бункере. Через сорок минут у тебя болит голова.", "Генератор работает, таймер 40:00, человек держится за голову.", "ровный рокот генератора"),
             (c2, "6-14 с", "Угарный газ не пахнет и не виден. А воздуху в бункере деваться некуда.", "Зелёные волны заполняют верх комнаты, перечёркнутый нос.", "рокот приглушается, звон в ушах"),
             (c3, "14-22 с", "Друг говорит, что устал. Вы ложитесь, и это самый опасный момент.", "Двое лежат, Z-значки, газ над ними.", "дыхание замедляется"),
             (c4, "22-28 с", "Правило одно: в закрытом помещении генератор не включают никогда, даже на десять минут.", "Перечёркнутый круг поверх генератора, красный.", "резкий удар, тишина"),
             (c5, "28-32 с", "Снаружи ставить нельзя: шум слышно далеко, а снаружи война.", "Генератор на поверхности, волны шума до силуэта вдалеке.", "рокот вдали, чьи-то шаги"),
             (c6, "32-37 с", "Остаются панель и аккумуляторы. Свет два часа в день, остальное темнота.", "Тёмный бункер, один аккумулятор светится, двое сидят.", "щелчок выключателя"),
             (c7, "37-41 с", "На двести тридцатый день друг признаётся в том, о чём молчал с первого дня.", "Календарь «230», лицо друга в тени, крупное «?».", "низкий нарастающий тон"),
             (c8, "41-44 с", "Как думаешь, что он скрывал? Пиши версии.", "Текст «Что он скрывал?», подпись «версии в комментарии».", "обрыв на полуслове"),
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


def main():
    os.makedirs(OUT, exist_ok=True)
    paths = []
    for v in VIDEOS:
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
