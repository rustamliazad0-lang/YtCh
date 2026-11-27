#!/usr/bin/env python3
"""Минутные ролики A-E с постановкой: что говорит голос, то и происходит в кадре.

Каждая сцена: (рисунок, текст диктора, кадр, звук, действия). Действия двигают помеченные элементы
(`data-a`): ходьба с шагом ног, вставание, открытие люка, стук, появление по очереди. Время действий
задано долями сцены (0..1), потому что длина сцены берётся из озвучки.
Правила постановки:
- кто снаружи бункера, рисуется в проёме люка (обрезка по кругу), а не в комнате;
- субтитр и картинка про одно и то же: «ты стоишь у люка» = герой у люка;
- в каждой сцене есть движение по смыслу: кто-то идёт, встаёт, берёт, считает, открывает.
"""
import itertools
from build_storyboard_3 import *  # noqa: F401,F403
import build_storyboard as B1
import build_storyboard_2 as B2
import build_storyboard_3 as B3
import art as A

_n = itertools.count()


# ---------- помощники постановки ----------
def g(aid, m, front=False):
    """Группа для анимации. front=True кладёт её в слой людей (поверх них), например лавку."""
    return f'<g data-a="{aid}"' + (' data-l="fg"' if front else "") + f'>{m}</g>'


def mv(a, t0, t1, f=None, to=None, e="io", org=None):
    d = {"k": "move", "a": a, "t0": t0, "t1": t1, "to": to or {}, "e": e}
    if f:
        d["f"] = f
    if org:
        d["org"] = org
    return d


def walk(a, t0, t1):
    return {"k": "walk", "a": a, "t0": t0, "t1": t1}


def shake(a, t0, t1, amp=4, hz=70):
    return {"k": "shake", "a": a, "t0": t0, "t1": t1, "amp": amp, "hz": hz}


def spin(a, t0, t1, rps=1.0, org="50% 50%"):
    return {"k": "spin", "a": a, "t0": t0, "t1": t1, "rps": rps, "org": org}


def bob(a, t0, t1, amp=6, hz=6):
    return {"k": "bob", "a": a, "t0": t0, "t1": t1, "amp": amp, "hz": hz}


def pulse(a, t0, t1, amp=0.08, hz=8):
    return {"k": "pulse", "a": a, "t0": t0, "t1": t1, "amp": amp, "hz": hz}


def appear(a, t0, t1=None, dy=24):
    return mv(a, t0, t1 or t0 + 0.12, {"o": 0, "y": dy}, {"o": 1, "y": 0}, "o")


def pop(a, t0, t1=None):
    return mv(a, t0, t1 or t0 + 0.1, {"o": 0, "s": 0.4}, {"o": 1, "s": 1}, "o")


def grow(a, t0, t1, fsx=0.0, tsx=1.0):
    return mv(a, t0, t1, {"sx": fsx}, {"sx": tsx}, "o", org="0% 50%")


def enter(a, t0, t1, dx):
    """Человек входит в кадр шагом: смещение dx -> 0 и работа ног."""
    return [mv(a, t0, t1, {"x": dx}, {"x": 0}, "lin"), walk(a, t0, t1)]


def stand_up(a, t0):
    return mv(a, t0, t0 + 0.08, {"y": 30}, {"y": 0}, "o")


def hatch(cx=262, cy=250, r=88, outside=(), open_=False, red=True):
    """Люк в стене. За ним проём со светом сирен; outside: [(dx, who, aid)] стоят снаружи, обрезаны кругом."""
    cid = f"dw{next(_n)}"
    s = f'<defs><clipPath id="{cid}"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath></defs>'
    s += f'<circle cx="{cx}" cy="{cy}" r="{r+16}" fill="#0b0d11"/><g clip-path="url(#{cid})">'
    s += f'<rect x="{cx-r}" y="{cy-r}" width="{2*r}" height="{2*r}" fill="{"#3a0e0e" if red else "#1c2638"}"/>'
    s += f'<circle cx="{cx-r*0.5}" cy="{cy-r*0.7}" r="{r*1.1}" fill="#ff3b30" fill-opacity="{0.35 if red else 0}"/>'
    s += "".join(f'<rect x="{cx-r}" y="{cy+r*0.15+k*14}" width="{2*r}" height="7" fill="#1a0606" fill-opacity=".7"/>' for k in range(5))
    for dx, who, aid in outside:
        s += g(aid, A.person(cx + dx, cy + r * 0.12, who, 0.42))
    s += f'</g><circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#5b6573" stroke-width="7"/>'
    return s


def hatch_door(cx=262, cy=250, r=88):
    return g("door", B1.door(cx, cy, r))


def wheel_spin(t0, t1):
    return []  # штурвал входит в рисунок люка; вращаем весь люк чуть-чуть при открытии


def bench(y=470):
    return g("bench", f'<rect x="10" y="{y}" width="340" height="22" rx="4" fill="#5a4630" stroke="{A.INK}" stroke-width="1.6"/>'
                      f'<rect x="10" y="{y}" width="340" height="6" fill="#fff" fill-opacity=".1"/><rect x="24" y="{y+22}" width="12" height="40" fill="#3e3020"/><rect x="324" y="{y+22}" width="12" height="40" fill="#3e3020"/>', front=True)


def thought(x, y, w, h, inner):
    s = f'<ellipse cx="{x+w/2}" cy="{y+h/2}" rx="{w/2}" ry="{h/2}" fill="#f4efe4" stroke="{A.INK}" stroke-width="2"/>'
    s += f'<circle cx="{x+w*0.75}" cy="{y+h+14}" r="9" fill="#f4efe4" stroke="{A.INK}" stroke-width="2"/><circle cx="{x+w*0.82}" cy="{y+h+34}" r="5" fill="#f4efe4" stroke="{A.INK}" stroke-width="2"/>'
    return s + inner


# ---------- люк в потолке (бункер под гаражом, вход сверху по лестнице) ----------
HX, HY, HRX, HRY = 230, 66, 62, 20  # центр проёма в потолке


def ladder(x=HX, top=HY + 8, bottom=420):
    s = f'<rect x="{x-26}" y="{top}" width="7" height="{bottom-top}" fill="#5b6370" stroke="{A.INK}"/><rect x="{x+19}" y="{top}" width="7" height="{bottom-top}" fill="#5b6370" stroke="{A.INK}"/>'
    return s + "".join(f'<rect x="{x-20}" y="{y}" width="40" height="5" fill="#6e7684" stroke="{A.INK}" stroke-width=".8"/>' for y in range(top + 20, bottom, 34))


def hatch_top(cx=HX, cy=HY, rx=HRX, ry=HRY, outside=(), with_ladder=True, red=True):
    """Проём в потолке. outside: [(dx, who, aid, scale)] стоят наверху, видны снизу в проёме."""
    cid = f"ht{next(_n)}"
    s = ladder(cx, cy + 8) if with_ladder else ""
    s += f'<defs><clipPath id="{cid}"><ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}"/></clipPath></defs>'
    s += f'<g clip-path="url(#{cid})"><rect x="{cx-rx}" y="{cy-ry-200}" width="{2*rx}" height="{2*ry+400}" fill="{"#3a0e0e" if red else "#1c2638"}"/>'
    s += f'<ellipse cx="{cx-rx*0.3}" cy="{cy-ry}" rx="{rx}" ry="{ry*2}" fill="#ff3b30" fill-opacity="{0.45 if red else 0}"/>'
    s += "".join(f'<rect x="{cx-rx+k*rx*0.5}" y="{cy-ry-200}" width="{rx*0.12}" height="400" fill="#1a0606" fill-opacity=".6"/>' for k in range(4))
    for dx, who, aid, sc in outside:
        feet = cy - ry * 0.25 + 132 * 1.3 * sc
        s += g(aid, A.person(cx + dx, feet - 70, who, sc))
    s += f'</g><ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="none" stroke="#5b6573" stroke-width="6"/>'
    return s


def lid(cx=HX, cy=HY, rx=HRX, ry=HRY, opened=False):
    m = (f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="#3b424c" stroke="{A.INK}" stroke-width="2"/>'
         f'<ellipse cx="{cx}" cy="{cy}" rx="{rx*0.7}" ry="{ry*0.7}" fill="none" stroke="#2a3038" stroke-width="3"/>'
         f'<ellipse cx="{cx}" cy="{cy}" rx="{rx*0.25}" ry="{ry*0.3}" fill="none" stroke="#9aa5b1" stroke-width="3"/><line x1="{cx-rx*0.35}" y1="{cy}" x2="{cx+rx*0.35}" y2="{cy}" stroke="#9aa5b1" stroke-width="3"/>'
         f'<rect x="{cx-rx*0.3}" y="{cy+ry*0.35}" width="{rx*0.6}" height="5" fill="#e2b13c"/>')
    if opened:  # откинута вверх: тонкая полоска у дальнего края
        m = f'<g transform="translate(0 {cy-ry}) scale(1 .15) translate(0 {-(cy-ry)})">{m}</g>'
        return g("door", m)
    return g("door", m)


def flood(cx=HX, cy=HY, rx=HRX):
    return g("flood", f'<polygon points="{cx-rx},{cy} {cx+rx},{cy} {cx+rx*2.2},420 {cx-rx*2.2},420" fill="#ff3b30" fill-opacity=".22"/>')


def knock_marks(cx=HX, cy=HY):
    return g("knk", f'<g stroke="{AMB}" stroke-width="4" stroke-linecap="round" fill="none"><path d="M{cx-80} {cy+6} q-10 14 0 28"/><path d="M{cx+80} {cy+6} q10 14 0 28"/><path d="M{cx-96} {cy} q-14 22 0 44"/><path d="M{cx+96} {cy} q14 22 0 44"/></g>')


def open_lid(t0, t1):
    return [mv("door", t0, t1, {"sy": 1, "y": 0}, {"sy": 0.15, "y": -HRY * 0.85}, "io", org="50% 0%"), mv("flood", t0 + (t1 - t0) * 0.4, t1, {"o": 0}, {"o": 1})]


def climb_down(a, t0, t1, dy=-300):
    return [mv(a, t0, t1, {"y": dy}, {"y": 0}, "lin"), walk(a, t0, t1)]


# ---------- A ----------
def A1():
    s = room(True) + lamp(110, 60, 120) + hatch_top() + lid() + knock_marks()
    s += t(108, 200, "≈11 000", 36, AMB) + t(110, 230, "порций на пятерых,", 14, "#cfd6de", "normal") + t(110, 248, "на 2 года", 14, "#cfd6de", "normal")
    s += person(150, 440, "hero", 1.0, mood="worried", pid="hero")
    return s + caption(["А в люк", "стучит шестой"])

A1_acts = [shake("door", 0.05, 0.25, 4), pulse("knk", 0.05, 0.25, 0.15, 30), shake("door", 0.55, 0.75, 4), pulse("knk", 0.55, 0.75, 0.15, 30),
           *enter("hero", 0.25, 0.7, -180)]


def A2():
    s = room(True) + hatch_top() + lid()
    s += g("phone", B2.card(30, 120, 150, 200, "#0d1117") + t(105, 148, "Друг · год назад", 13, "#9aa5b1")
           + g("m1", B2.bubble(42, 166, 126, 62, "Через год|начнётся война.", "#2d3b4e", "#fff", "l", 13))
           + g("m2", B2.bubble(42, 252, 126, 40, "Никому.", "#2d3b4e", "#fff", "l", 14)))
    s += person(110, 440, "hero", 1.0, mood="worried", pid="hero")
    return s + caption(["Тот самый друг,", "что писал ночью"])

A2_acts = [appear("phone", 0.05, 0.2, 40), appear("m1", 0.35), appear("m2", 0.7)]


def A3():
    s = room(True) + hatch_top() + lid()
    s += g("th", thought(10, 110, 200, 170, ""))
    s += g("r1", B3.receipt(20, 125, -10, "рынок")) + g("r2", B3.receipt(70, 118, 2, "супермаркет")) + g("r3", B3.receipt(120, 128, 10, "аптека"))
    s += person(180, 440, "hero", 1.0, mood="worried", pid="hero")
    return s + caption(["Понемногу,", "в разных магазинах"])

A3_acts = [mv("th", 0.05, 0.2, {"o": 0, "s": 0.3}, {"o": 1, "s": 1}, "o", org="90% 100%"),
           appear("r1", 0.3, 0.4, -30), appear("r2", 0.48, 0.58, -30), appear("r3", 0.66, 0.76, -30), bob("hero", 0.0, 1.0, 2, 3)]


def A4():
    s = room() + lamp()
    s += t(180, 92, "11 000 ÷ 6", 44, WAT)
    s += g("b1", bar(40, 130, 280, 1.0, "#2e8b57")) + t(40, 170, "на пятерых: 24 месяца", 14, "#9aa5b1", "normal", "start")
    s += g("b2", bar(40, 196, 280, 20 / 24, ACC)) + t(40, 236, "на шестерых: 20 месяцев", 14, "#ffb4a6", "normal", "start")
    for k, (x, who) in enumerate(((45, "grandpa"), (100, "mom"), (155, "hero"), (205, "kid"), (245, "kid"))):
        s += person(x, 430, who, 0.85, pid=f"f{k}")
    s += g("six", f'<g opacity=".8">{A.person(305, 430, "shadow", 0.85)}</g>' + t(305, 330, "?", 40, AMB))
    s += bench(480)
    return s + caption(["На четыре месяца", "меньше"])


A4_acts = [stand_up(f"f{k}", 0.08 + 0.09 * k) for k in range(5)] + [pop("six", 0.55), grow("b1", 0.62, 0.72), grow("b2", 0.75, 0.88, 0, 1)]


def A5():
    s = room() + lamp()
    for k, (x, kind, col, lab) in enumerate(((70, "drop", WAT, "скважина"), (180, "fan", "#2e8b57", "воздух"), (290, "bolt", AMB, "свет"))):
        s += g(f"i{k}", B2.icon(x, 230, kind, col) + t(x, 312, "✓", 30, "#2e8b57") + t(x, 340, lab, 15, "#9aa5b1", "normal"))
    s += g("bad", badge(180, 395, "−4 месяца еды", ACC, 230, 22))
    s += person(180, 470, "hero", 0.8, mood="worried", pid="hero")
    return s + caption(["Это можно", "пережить"])


A5_acts = [pop("i0", 0.05), pop("i1", 0.2), pop("i2", 0.35), appear("bad", 0.55), bob("hero", 0.8, 1.0, 3, 5)]


def A6():
    s = room(True) + hatch_top() + flood() + lid()
    s += person(HX, 440, "hero", 1.0, arm_up=True, mood="worried", pid="hero")
    return s + caption(["Ты открываешь"])

A6_acts = [mv("flood", 0.0, 0.01, {"o": 0}, {"o": 0}), mv("hero", 0.0, 0.4, {"y": 0}, {"y": -90}, "lin"), walk("hero", 0.0, 0.4), *open_lid(0.45, 0.95)]


def A7():
    s = room(True) + hatch_top() + flood() + lid(opened=True)
    s += person(70, 440, "hero", 1.0, mood="worried", pid="hero")
    s += person(HX, 440, "friend", 1.05, pid="fr")
    s += g("say", B2.bubble(40, 130, 200, 64, "Я всё знал.", "#fff", "#111", "r", 26))
    return s + caption(["Знал не он один"])

A7_acts = [*climb_down("fr", 0.0, 0.4, -330), appear("say", 0.45)]


def A8():
    s = room(True) + siren(0.25) + ladder(180, 300, 640)
    s += hatch_top(180, 210, 160, 90, outside=((-80, "n1", "n1", 0.62), (0, "n2", "n2", 0.62), (80, "n3", "n3", 0.62)), with_ladder=False)
    s += g("door", f'<g transform="translate(0 120) scale(1 .12) translate(0 -120)"><ellipse cx="180" cy="210" rx="160" ry="90" fill="#3b424c" stroke="{A.INK}" stroke-width="2"/></g>')
    s += t(180, 70, "наверху, у люка", 22, "#cfd6de", "normal")
    return s + caption(["За ним стоят", "соседи"])

A8_acts = [appear("n1", 0.1, 0.25, 10), appear("n2", 0.3, 0.45, 10), appear("n3", 0.5, 0.65, 10)]


def A9():
    s = f'<rect width="360" height="640" fill="#e9c98a"/><circle cx="290" cy="90" r="46" fill="#fff2b8"/><rect y="330" width="360" height="310" fill="#7d9a52"/>'
    s += person(80, 430, "hero", 1.0, arm_up=True, pid="hero") + person(270, 430, "n1", 1.0, arm_up=True, pid="nb")
    s += g("fence", "".join(f'<rect x="{x}" y="390" width="16" height="110" fill="#8a5a33" stroke="#4a2f1a" stroke-width="2"/>' for x in range(0, 360, 24))
           + '<rect x="0" y="420" width="360" height="10" fill="#4a2f1a"/>', front=True)
    s += t(180, 90, "год назад", 34, "#4a2f1a")
    return s + caption(["Те, кому ты", "махал через забор"])


A9_acts = [*enter("nb", 0.0, 0.45, 120), mv("hero", 0.5, 0.6, {"r": 0}, {"r": -4}), mv("hero", 0.6, 0.7, {"r": -4}, {"r": 4}), mv("hero", 0.7, 0.8, {"r": 4}, {"r": 0}),
           mv("nb", 0.55, 0.65, {"r": 0}, {"r": 4}), mv("nb", 0.65, 0.75, {"r": 4}, {"r": -4}), mv("nb", 0.75, 0.85, {"r": -4}, {"r": 0})]


def A10():
    s = room() + lamp() + t(180, 92, "11 000 ÷ 9", 44, WAT)
    s += g("bar", bar(40, 140, 280, 20 / 24, ACC)) + t(40, 182, "на девятерых: 13 месяцев", 15, "#ffb4a6", "normal", "start")
    for k in range(3):  # это «если», поэтому не люди в комнате, а силуэты
        s += g(f"n{k}", f'<g opacity=".5">{A.person(110 + k * 70, 430, "shadow", 0.8)}</g>' + t(110 + k * 70, 330, "?", 34, AMB))
    s += g("plus", t(180, 270, "+3", 50, ACC))
    return s + caption(["Если пустить и их:", "13 месяцев"])


A10_acts = [pop("plus", 0.05), *[pop(f"n{k}", 0.15 + 0.12 * k) for k in range(3)], mv("bar", 0.6, 0.85, {"sx": 1}, {"sx": 13 / 20}, "io", org="0% 50%")]


def A11():
    s = room(True) + siren(0.3) + ladder(180, 270, 640)
    s += hatch_top(180, 190, 140, 80, outside=((-70, "n1", "n1", 0.55), (0, "n2", "n2", 0.55), (70, "n3", "n3", 0.55)), with_ladder=False)
    s += t(180, 330, "Соседей", 50, "#fff") + t(180, 374, "пустил бы?", 34, ACC) + g("poll", poll(400))
    return s + caption(["Да или нет?"])

A11_acts = [pulse("poll", 0.3, 1.0, 0.05, 6)]


# ---------- E ----------
def E1():
    s = room(True)
    s += f'<rect x="100" y="260" width="160" height="110" rx="14" fill="#5b6573" stroke="{A.INK}" stroke-width="2"/><rect x="90" y="250" width="180" height="16" rx="6" fill="#8a95a3" stroke="{A.INK}"/>'
    s += g("steam", f'<g stroke="#cfd6de" stroke-width="5" fill="none" stroke-linecap="round" stroke-opacity=".7"><path d="M140 230 q10 -20 0 -40 t0 -40"/><path d="M180 230 q10 -20 0 -40 t0 -40"/><path d="M220 230 q10 -20 0 -40 t0 -40"/></g>')
    s += B2.trefoil(180, 315, 30, AMB) + t(180, 90, "КИПЯЧЕНИЕ", 46, AMB)
    s += g("x", f'<line x1="110" y1="240" x2="250" y2="390" stroke="{ACC}" stroke-width="12" stroke-linecap="round"/>')
    return s + caption(["Не убирает радиацию", "из воды"])


E1_acts = [bob("steam", 0.0, 1.0, 10, 3), grow("x", 0.45, 0.6)]


def E2():
    s = f'<rect width="360" height="640" fill="#2a2a1c"/><rect y="300" width="360" height="340" fill="#2a4a5a"/>'
    s += g("dust", B2.dust(40, -120, 300, 2)) + B2.dust(14, 300, 500, 5)
    s += f'<path d="M0 360 q60 -14 120 0 t120 0 t120 0" stroke="#4b7a8c" stroke-width="5" fill="none"/>'
    s += t(180, 110, "ПЫЛЬ", 60, "#d8c35a") + t(180, 148, "оседает на воде и земле", 19, "#cfd6de", "normal")
    return s + caption(["Оседает на всём", "открытом"])


E2_acts = [mv("dust", 0.0, 1.0, {"y": -60}, {"y": 120}, "lin")]


def E3():
    s = f'<rect width="360" height="640" fill="#1c2638"/><rect y="150" width="360" height="490" fill="#3a2e24"/><rect y="150" width="360" height="8" fill="#4f6b2f"/>'
    s += f'<rect x="40" y="95" width="130" height="55" fill="#6a717b"/><path d="M34 95 l71 -34 l71 34z" fill="#4a5058"/>'
    s += f'<rect x="96" y="158" width="12" height="320" fill="#2a2420"/>'
    s += g("drill", f'<rect x="95" y="160" width="14" height="300" fill="#7a8594"/><path d="M95 460 l7 18 l7 -18z" fill="#c9cfd6"/><rect x="82" y="470" width="40" height="26" rx="6" fill="{WAT}" fill-opacity=".9"/>')
    s += t(250, 310, "глубоко", 22, "#fff", "normal", "middle") + g("note", t(180, 540, "шанс лучше, но не гарантия", 19, AMB))
    return s + caption(["Скважина:", "закрытая и глубокая"])


E3_acts = [mv("drill", 0.0, 0.6, {"y": -300}, {"y": 0}, "o"), appear("note", 0.65)]


def E4():
    s = B2.e4()
    return s


E4_acts = []


def E5():
    s = room() + lamp() + f'<rect x="10" y="352" width="340" height="8" fill="#5a616a"/><rect x="10" y="472" width="340" height="8" fill="#5a616a"/>'
    for k in range(8):
        s += g(f"b{k}", A.bottle(24 + k * 40, 246, 100))
    s += t(180, 110, "закрытые", 46, WAT) + t(180, 148, "бутылки и ёмкости", 20, "#cfd6de", "normal")
    s += person(300, 470, "hero", 0.8, pid="hero")
    return s + caption(["Первые недели", "только запас"])


E5_acts = [appear(f"b{k}", 0.05 + 0.09 * k, 0.12 + 0.09 * k, -40) for k in range(8)] + [bob("hero", 0.0, 0.8, 4, 6)]


def E6():
    s = room() + lamp() + B2.dust(22, 120, 400, 4) + A.bottle(150, 250, 150, 1.0)
    s += g("cloth", f'<ellipse cx="205" cy="330" rx="44" ry="26" fill="#f4efe4" stroke="{A.INK}" transform="rotate(-25 205 330)"/>')
    s += person(300, 470, "hero", 0.8, pid="hero") + t(180, 100, "пыль и снаружи", 34, AMB)
    return s + caption(["Протираешь бутылку", "влажной тряпкой"])


E6_acts = [shake("cloth", 0.1, 0.9, 16, 9)]


def E7():
    s = B3.e_tank()
    return s


E7_acts = []


def E8():
    s = room() + lamp()
    for k in range(6):
        s += g(f"b{k}", A.bottle(28 + k * 52, 250, 110))
    s += t(180, 110, "6 × 2 л × 20 дней", 30, WAT) + g("res", t(180, 160, "= 240 литров", 34, "#fff"))
    return s + caption(["Двести сорок литров", "на двадцать дней"])


E8_acts = [appear(f"b{k}", 0.05 + 0.1 * k, 0.12 + 0.1 * k, -40) for k in range(6)] + [pop("res", 0.7)]


def E9():
    s = room() + lamp() + B2.calendar(180, 90, "20", None, 120) + t(180, 214, "дней запаса", 22, "#cfd6de", "normal")
    for k in range(5):
        s += g(f"b{k}", A.bottle(70 + k * 46, 270, 100))
    s += g("bar", bar(40, 430, 280, 1.0, ACC)) + t(40, 470, "день 1", 13, "#9aa5b1", "normal", "start") + t(320, 470, "день 20", 13, "#9aa5b1", "normal", "end")
    return s + caption(["Запас на", "двадцать дней"])


E9_acts = [mv(f"b{k}", 0.15 + 0.13 * k, 0.25 + 0.13 * k, {"o": 1}, {"o": 0.12}) for k in range(5)] + [mv("bar", 0.1, 0.9, {"sx": 1}, {"sx": 0.08}, "lin", org="0% 50%")]


def E10():
    s = B2.e8().replace(B2.icon(180, 300, "drop", WAT), g("drop", B2.icon(180, 300, "drop", WAT)))
    return s


E10_acts = [pulse("drop", 0.0, 1.0, 0.08, 5)]


# ---------- B ----------
def Bv1():
    s = room(True) + lamp()
    for i in range(3):
        for j in range(2):
            s += g(f"b{i}{j}", A.barrel(40 + i * 104, 250 + j * 100, 70, 84, 0.9))
    s += t(180, 100, "30 ТОНН", 58, WAT) + t(180, 138, "воды за два года", 19, "#cfd6de", "normal")
    return s + caption(["Куда она", "денется?"])


Bv1_acts = [appear(f"b{i}{j}", 0.05 + 0.08 * (i + 3 * j), 0.13 + 0.08 * (i + 3 * j), -40) for i in range(3) for j in range(2)]


def Bv2():
    s = B1.b2()
    return s


def Bv3():
    s = room(True) + lamp(110, 60, 110) + hatch_top() + lid()
    s += g("lock", f'<ellipse cx="{HX}" cy="{HY}" rx="30" ry="12" fill="none" stroke="{ACC}" stroke-width="6"/><line x1="{HX-22}" y1="{HY-9}" x2="{HX+22}" y2="{HY+9}" stroke="{ACC}" stroke-width="6"/>')
    s += t(112, 230, "несколько тонн", 22, AMB) + t(112, 256, "отходов за два года", 15, "#cfd6de", "normal")
    s += person(HX, 440, "hero", 0.9, mood="worried", pid="hero") + person(90, 445, "mom", 0.85, pid="mom")
    return s + caption(["Люк открывать", "нельзя"])

Bv3_acts = [mv("hero", 0.0, 0.35, {"y": 0}, {"y": -70}, "lin"), walk("hero", 0.0, 0.35), pop("lock", 0.4), pulse("lock", 0.5, 1.0, 0.06, 7),
            mv("mom", 0.45, 0.7, {"x": 0}, {"x": 60}), walk("mom", 0.45, 0.7), mv("hero", 0.7, 0.95, {"y": -70}, {"y": 0}, "lin"), walk("hero", 0.7, 0.95)]


def Bv4():
    s = B1.b4()
    s = s.replace('<rect x="262" y="338" width="92" height="48" rx="12" fill="#7a6a2a" stroke="{GAS}" stroke-width="3"/>'.replace("{GAS}", GAS),
                  "")
    s = s.replace(t(308, 369, "стоки", 15, "#fff"), "")
    s += g("tank", f'<rect x="262" y="338" width="92" height="48" rx="12" fill="#7a6a2a" stroke="{GAS}" stroke-width="3"/>' + t(308, 369, "стоки", 15, "#fff"))
    return s


Bv4_acts = [mv("tank", 0.1, 0.45, {"y": -230}, {"y": 0}, "o")]


def Bv5():
    s = room() + lamp() + B2.card(30, 120, 300, 80) + t(180, 170, "≈ 9 л в день на шестерых", 18, "#fff")
    s += f'<rect x="90" y="240" width="180" height="150" rx="24" fill="#3a3220" stroke="{A.INK}" stroke-width="2"/>'
    s += g("lvl", f'<rect x="100" y="250" width="160" height="130" rx="14" fill="#a8913c"/>')
    s += t(180, 300, "1000 л", 30, "#fff") + g("days", t(180, 440, "≈ 110 дней до полного", 22, AMB))
    return s + caption(["Бак на тысячу литров:", "сто десять дней"])


Bv5_acts = [mv("lvl", 0.1, 0.85, {"sy": 0.02}, {"sy": 1}, "lin", org="50% 100%"), appear("days", 0.75)]


def Bv6():
    s = f'<rect width="360" height="640" fill="#1c2638"/><rect y="150" width="360" height="490" fill="#3a2e24"/><rect y="150" width="360" height="8" fill="#4f6b2f"/>'
    s += f'<rect x="30" y="95" width="120" height="55" fill="#6a717b"/><path d="M24 95 l66 -32 l66 32z" fill="#4a5058"/><rect x="250" y="80" width="80" height="70" fill="#8b8f96"/><path d="M244 80 l46 -26 l46 26z" fill="#5b6068"/>'
    s += person(210, 80, "n1", 0.45, pid="nb")
    for k in range(7):
        x, y = 30 + (k % 4) * 80, 220 + (k // 4) * 90
        s += g(f"t{k}", f'<rect x="{x}" y="{y}" width="64" height="40" rx="10" fill="#7a6a2a" stroke="{GAS}" stroke-width="2"/>' + t(x + 32, y + 26, f"{k+1}", 18, "#fff"))
    s += t(180, 470, "6-7 баков за два года", 24, AMB)
    return s + caption(["Закопать так,", "чтобы соседи не заметили"])


Bv6_acts = [appear(f"t{k}", 0.05 + 0.1 * k, 0.12 + 0.1 * k, -30) for k in range(7)] + [*enter("nb", 0.3, 0.9, -160)]


def Bv7():
    s = room() + lamp()
    s += f'<path d="M100 330 h160 l-18 100 h-124 z" fill="#5b6573" stroke="{A.INK}" stroke-width="2"/>'
    s += g("scoop", f'<path d="M140 220 q40 -50 90 -10 l-20 70 h-60 z" fill="#d9b779" stroke="{A.INK}" stroke-width="1.5"/>')
    s += g("saw", "".join(f'<circle cx="{170+i*8}" cy="{300+(i%3)*8}" r="3" fill="#d9b779"/>' for i in range(9)))
    s += g("smell", f'<g stroke="{GAS}" stroke-width="4" fill="none" stroke-linecap="round" stroke-opacity=".6"><path d="M170 300 q10 -20 0 -40 t0 -40"/><path d="M210 300 q10 -20 0 -40 t0 -40"/></g>')
    s += t(180, 90, "ОПИЛКИ", 48, AMB)
    return s + caption(["Твёрдое отдельно,", "опилки держат запах"])


Bv7_acts = [mv("scoop", 0.1, 0.4, {"r": 0}, {"r": 35}, org="20% 80%"), mv("saw", 0.3, 0.7, {"y": -60, "o": 0}, {"y": 30, "o": 1}, "lin"),
            mv("smell", 0.5, 0.9, {"o": 1, "y": 0}, {"o": 0, "y": -40})]


def Bv8():
    s = f'<rect width="360" height="640" fill="#cdbb8a"/><rect y="340" width="360" height="300" fill="#7d9a52"/><rect x="30" y="250" width="130" height="90" fill="#8b8f96"/><path d="M24 250 l71 -36 l71 36z" fill="#5b6068"/>'
    s += f'<line x1="250" y1="340" x2="250" y2="190" stroke="#555" stroke-width="9"/><rect x="240" y="180" width="20" height="12" fill="#555"/>'
    s += g("gas", f'<g stroke="{GAS}" stroke-width="4" fill="none" stroke-opacity=".7"><path d="M250 170 q8 -14 0 -28 t0 -28"/></g>')
    s += person(330, 440, "n1", 1.0, pid="nb") + g("q", t(300, 190, "?", 60, ACC))
    return s + caption(["Труба выходит", "наружу"])


Bv8_acts = [bob("gas", 0.0, 1.0, 8, 3), *enter("nb", 0.05, 0.5, 120), pop("q", 0.6)]


def Bv9():
    s = f'<rect width="360" height="640" fill="#cdbb8a"/><rect y="420" width="360" height="220" fill="#7d9a52"/>'
    s += person(90, 480, "hero", 1.0, mood="worried", pid="hero") + person(270, 480, "n1", 1.0, pid="nb")
    s += g("s1", B2.bubble(20, 120, 150, 60, "Это септик", "#fff", "#111", "l", 20)) + g("s2", B2.bubble(190, 220, 150, 70, "Да, у нас|такой же", "#fff", "#111", "r", 18))
    return s + caption(["Соседи верят:", "у них такой же"])


Bv9_acts = [appear("s1", 0.1), appear("s2", 0.5), bob("nb", 0.55, 0.85, 4, 6)]


def Bv10():
    s = B1.b8() + g("dark", '<rect width="360" height="640" fill="#000"/>')
    return s


Bv10_acts = [mv("dark", 0.0, 0.3, {"o": 0.6}, {"o": 0.0}), mv("dark", 0.55, 0.65, {"o": 0}, {"o": 0.35})]


# ---------- C ----------
def Cv1():
    s = room() + lamp() + g("gen", B1.generator(180, 360, 1.9))
    s += g("smoke", '<circle cx="270" cy="230" r="14" fill="#666" fill-opacity=".6"/><circle cx="290" cy="200" r="18" fill="#777" fill-opacity=".5"/>')
    s += t(180, 100, "ЛОМАЕТСЯ", 46, ACC) + t(180, 138, "вопрос только когда", 19, "#cfd6de", "normal")
    return s + caption(["Он сломается"])


Cv1_acts = [shake("gen", 0.0, 0.7, 3, 50), mv("smoke", 0.0, 0.8, {"y": 20, "o": 0.9}, {"y": -80, "o": 0}, "lin")]


def Cv2():
    s = room() + lamp() + g("c1", B2.card(30, 120, 300, 90) + t(180, 175, "50 моточасов", 34, WAT) + t(180, 198, "замена масла (у многих малых моделей)", 12, "#9aa5b1", "normal"))
    s += g("c2", B2.card(30, 230, 300, 80) + t(180, 262, "6 часов в день", 21, "#fff") + t(180, 292, "= раз в 8 дней", 21, AMB))
    s += g("c3", B2.card(30, 330, 300, 80, "#1b2028", ACC) + t(180, 362, "≈ 90 замен", 30, ACC) + t(180, 394, "за два года", 18, "#cfd6de", "normal"))
    return s + caption(["Масло меняют", "каждые 50 часов"])


Cv2_acts = [appear("c1", 0.05), appear("c2", 0.35), appear("c3", 0.65)]


def Cv3():
    s = room() + B2.card(24, 110, 312, 150) + '<circle cx="62" cy="148" r="18" fill="#3a4452"/>' + t(92, 153, "зритель", 14, "#9aa5b1", "normal", "start")
    s += t(180, 190, "Генераторы нужно обслуживать,", 16, "#fff") + t(180, 214, "их нужно два или три", 16, "#fff") + t(180, 238, "+ масло на год", 16, "#fff")
    for k in range(3):
        s += g(f"g{k}", B1.generator(80 + k * 100, 400, 0.7))
    return s + caption(["Два или три", "и запас масла"])


Cv3_acts = [pop(f"g{k}", 0.3 + 0.15 * k) for k in range(3)]


def Cv4():
    s = room(True) + g("lamp", lamp()) + B2.calendar(180, 80, "40", None, 110) + B1.generator(180, 400, 1.6)
    s += g("silence", t(180, 260, "тишина", 54, ACC) + t(180, 300, "света нет", 22, "#cfd6de", "normal"))
    return s + caption(["Утро. Света нет"])


Cv4_acts = [mv("lamp", 0.0, 0.08, {"o": 1}, {"o": 0.2}), mv("lamp", 0.08, 0.14, {"o": 0.2}, {"o": 0.9}), mv("lamp", 0.14, 0.3, {"o": 0.9}, {"o": 0}), appear("silence", 0.4)]


def Cv5():
    s = room(True) + B2.gas(8, 250, 420, 4)
    s += f'<circle cx="180" cy="190" r="70" fill="none" stroke="#7a8594" stroke-width="8"/>'
    s += g("fan", "".join(f'<ellipse cx="180" cy="160" rx="12" ry="30" fill="#7a8594" transform="rotate({a} 180 190)"/>' for a in (0, 120, 240)))
    s += g("x", f'<line x1="120" y1="130" x2="240" y2="250" stroke="{ACC}" stroke-width="12"/><line x1="240" y1="130" x2="120" y2="250" stroke="{ACC}" stroke-width="12"/>')
    s += t(180, 90, "ВЕНТИЛЯЦИЯ", 34, "#fff")
    return s + caption(["Вентиляция встала"])


Cv5_acts = [mv("fan", 0.0, 0.55, {"r": 0}, {"r": 540}, "o", org="50% 50%"), pop("x", 0.6)]


def Cv6():
    s = room() + lamp() + A.fvu(150, 250, 130, 130)
    s += f'<line x1="280" y1="315" x2="320" y2="315" stroke="#aaa" stroke-width="8"/>'
    s += g("crank", f'<circle cx="320" cy="315" r="30" fill="none" stroke="{AMB}" stroke-width="6" stroke-dasharray="12 8"/><line x1="320" y1="315" x2="345" y2="315" stroke="#aaa" stroke-width="6"/><circle cx="345" cy="315" r="9" fill="{AMB}"/>')
    s += person(80, 500, "hero", 1.0, arm_up=True, mood="pain", pid="hero") + t(180, 110, "вручную", 56, AMB)
    return s + caption(["Крутишь фильтр", "вручную"])


Cv6_acts = [spin("crank", 0.0, 1.0, 0.7), bob("hero", 0.0, 1.0, 4, 4.4)]


def Cv7():
    s = room() + lamp() + A.fvu(150, 250, 130, 130)
    s += g("crank", f'<circle cx="320" cy="315" r="30" fill="none" stroke="{AMB}" stroke-width="6" stroke-dasharray="12 8"/><circle cx="345" cy="315" r="9" fill="{AMB}"/>')
    s += person(90, 500, "hero", 1.0, mood="pain", pid="hero") + person(250, 500, "mom", 1.0, pid="mom")
    s += t(180, 110, "смена", 50, "#fff")
    return s + caption(["Крутить по очереди,", "круглые сутки"])


Cv7_acts = [spin("crank", 0.0, 1.0, 0.6), mv("hero", 0.1, 0.6, {"x": 0}, {"x": -170}, "lin"), walk("hero", 0.1, 0.6),
            mv("mom", 0.3, 0.8, {"x": 160}, {"x": 0}, "lin"), walk("mom", 0.3, 0.8)]


def Cv8():
    s = B3.c_hours()
    for k in range(3):
        s = s  # шкалы ниже анимируются через обёртки
    return s


def Cv9():
    s = room(True) + hatch_top() + lid() + knock_marks()
    s += person(110, 440, "hero", 1.0, mood="worried", pid="hero") + person(50, 445, "mom", 0.85, pid="mom")
    s += t(120, 200, "Пустил бы", 34, "#fff") + t(120, 236, "соседей?", 34, ACC) + g("poll", poll(250))
    return s + caption(["Ради лишних рук"])

Cv9_acts = [shake("door", 0.0, 0.25, 4), pulse("knk", 0.0, 0.25, 0.15, 30), shake("door", 0.35, 0.55, 4), pulse("knk", 0.35, 0.55, 0.15, 30),
            mv("hero", 0.1, 0.4, {"x": -60}, {"x": 0}), walk("hero", 0.1, 0.4), pulse("poll", 0.6, 1.0, 0.05, 6)]


# ---------- D ----------
def Dv1():
    s = room() + lamp(110, 60, 120) + hatch_top(red=False) + lid(opened=True)
    xs = (28, 66, 104, 140, 172, 270, 205, 300, 336)
    ks = ("grandpa", "mom", "hero", "kid", "kid", "friend", "n1", "n2", "n3")
    for k, (x, w) in enumerate(zip(xs, ks)):
        s += person(x, 470, w, 0.55, pid=f"p{k}")
    s += t(110, 190, "9", 90, ACC) + t(110, 226, "человек в бункере на 5", 15, "#cfd6de", "normal")
    return s + caption(["Вас девять,", "еда на пятерых"])

Dv1_acts = [x for j, k in enumerate((6, 7, 8)) for x in [
    mv(f"p{k}", 0.05 + 0.28 * j, 0.2 + 0.28 * j, {"x": HX - (205, 300, 336)[j], "y": -260}, {"x": HX - (205, 300, 336)[j], "y": 0}, "lin"), walk(f"p{k}", 0.05 + 0.28 * j, 0.2 + 0.28 * j),
    mv(f"p{k}", 0.2 + 0.28 * j, 0.3 + 0.28 * j, {"x": HX - (205, 300, 336)[j]}, {"x": 0}, "lin"), walk(f"p{k}", 0.2 + 0.28 * j, 0.3 + 0.28 * j)]]


def Dv2():
    s = room() + lamp() + t(180, 100, "10 950 ÷ 9 ÷ 3", 34, WAT) + t(180, 138, "= 405 дней", 24, "#fff")
    s += bar(40, 200, 280, 1.0, "#2e8b57") + t(40, 242, "план: 24 месяца", 14, "#9aa5b1", "normal", "start")
    s += g("b2", bar(40, 272, 280, 13 / 24, ACC)) + t(40, 314, "теперь: 13 месяцев", 14, "#ffb4a6", "normal", "start")
    s += g("m", badge(180, 380, "минус 11", ACC, 160, 28))
    return s + caption(["Не 24 месяца,", "а 13"])


Dv2_acts = [mv("b2", 0.2, 0.6, {"sx": 24 / 13}, {"sx": 1}, "io", org="0% 50%"), pop("m", 0.65)]


def Dv3():
    s = room() + lamp()
    for k, x in enumerate((70, 180, 290)):
        s += g(f"pl{k}", B3.plate(x, 220, 40, True))
    s += g("x", f'<line x1="250" y1="170" x2="330" y2="270" stroke="{ACC}" stroke-width="10"/><line x1="330" y1="170" x2="250" y2="270" stroke="{ACC}" stroke-width="10"/>')
    s += t(180, 110, "2 приёма вместо 3", 30, AMB) + g("bar", bar(40, 340, 280, 20 / 24, "#2e8b57")) + t(180, 400, "те же 20 месяцев", 24, "#fff")
    return s + caption(["Два приёма", "вместо трёх"])


Dv3_acts = [appear("pl0", 0.0), appear("pl1", 0.08), appear("pl2", 0.16), pop("x", 0.35), mv("pl2", 0.45, 0.6, {"o": 1}, {"o": 0.3}), grow("bar", 0.6, 0.85, 13 / 20, 1)]


def Dv5():
    s = room() + lamp(180, 0, 110)
    s += person(80, 500, "hero", 1.0, mood="worried", pid="hero") + person(280, 500, "n1", 1.0, pid="nb")
    s += g("tn", f'<g stroke="{ACC}" stroke-width="5" fill="none"><path d="M130 300 l30 -14 l-30 -14"/><path d="M230 300 l-30 -14 l30 -14"/></g><path d="M150 330 l20 -22 l20 22 l20 -22" stroke="{ACC}" stroke-width="4" fill="none"/>')
    s += t(180, 110, "голодные", 46, ACC) + t(180, 146, "хуже терпят друг друга", 18, "#cfd6de", "normal")
    return s + caption(["Некуда уйти", "из бункера"])


Dv5_acts = [mv("hero", 0.1, 0.4, {"x": 0}, {"x": 25}), mv("nb", 0.1, 0.4, {"x": 0}, {"x": -25}), walk("hero", 0.1, 0.4), walk("nb", 0.1, 0.4), pulse("tn", 0.4, 1.0, 0.1, 9)]


def Dv6():
    s = room() + lamp() + f'<rect x="20" y="420" width="140" height="18" fill="#5a4630" stroke="{A.INK}"/>'
    s += B2.card(30, 300, 110, 110, "#f1ebdd", "#8b7a55") + "".join(f'<line x1="40" y1="{330+k*16}" x2="130" y2="{330+k*16}" stroke="#b7ab8a" stroke-width="2"/>' for k in range(5))
    s += g("pen", '<rect x="120" y="320" width="5" height="40" fill="#333" transform="rotate(30 122 340)"/>')
    s += person(60, 440, "hero", 0.8, pid="hero")
    for k, w in enumerate(("kid", "kid", "mom", "n2")):
        s += person(220 + k * 40, 440, w, 0.8, pid=f"q{k}")
    s += t(180, 110, "ВЫДАЧА", 40, AMB) + t(180, 150, "дети первыми", 20, "#cfd6de", "normal")
    return s + caption(["Выдаёшь ты,", "под запись"])


Dv6_acts = [shake("pen", 0.05, 0.95, 4, 18)] + [x for k in range(4) for x in [mv(f"q{k}", 0.08 + 0.2 * k, 0.24 + 0.2 * k, {"x": 0}, {"x": -40}, "lin"), walk(f"q{k}", 0.08 + 0.2 * k, 0.24 + 0.2 * k)]]


def Dv7():
    s = room() + lamp() + f'<rect x="90" y="140" width="180" height="280" rx="6" fill="#4a525c" stroke="{A.INK}" stroke-width="2"/>'
    s += "".join(f'<line x1="98" y1="{y}" x2="262" y2="{y}" stroke="#3a4048" stroke-width="2"/>' for y in range(170, 420, 30))
    s += f'<rect x="130" y="160" width="100" height="30" fill="#e2b13c" stroke="{A.INK}"/>' + t(180, 182, "СКЛАД", 18, "#222") + g("lock", B3.padlock(240, 290, 1.4))
    s += person(60, 520, "hero", 0.8, pid="hero")
    return s + caption(["Ключ один,", "он у тебя"])


Dv7_acts = [*enter("hero", 0.0, 0.4, -80), mv("lock", 0.45, 0.6, {"y": -14, "r": -10}, {"y": 0, "r": 0}, "o")]


def Dv8():
    s = room() + lamp() + A.crates(300, 6) + A.crates(350, 6) + B2.calendar(180, 90, "60", None, 110)
    for k in range(6):
        s += g(f"h{k}", f'<rect x="{22+k*52}" y="296" width="50" height="96" rx="4" fill="#f2b04a" fill-opacity=".35"/>')
    s += person(40, 520, "hero", 0.75, mood="worried", pid="hero")
    return s + caption(["Должно быть 240"])


Dv8_acts = [mv("hero", 0.05, 0.9, {"x": 0}, {"x": 270}, "lin"), walk("hero", 0.05, 0.9)] + [mv(f"h{k}", 0.08 + 0.14 * k, 0.16 + 0.14 * k, {"o": 0}, {"o": 1}) for k in range(6)]


def Dv9():
    s = room(True) + A.crates(300, 6) + A.crates(350, 6, missing=3)
    s += g("ring", f'<circle cx="{24+3*52+23}" cy="370" r="40" fill="none" stroke="{ACC}" stroke-width="4"/>')
    s += t(180, 130, "239", 64, ACC) + t(180, 175, "вместо 240", 30, "#fff")
    return s + caption(["Одной коробки", "не хватает"])


Dv9_acts = [pulse("ring", 0.0, 1.0, 0.12, 8)]


def Dv10():
    s = B3.d_key().replace(B3.key_shape(130, 230, 1.5), g("key", B3.key_shape(130, 230, 1.5)))
    s += g("key2", f'<g opacity=".5">{B3.key_shape(250, 300, 1.0)}</g>')
    return s


Dv10_acts = [pulse("key", 0.0, 0.6, 0.05, 5), appear("key2", 0.55, 0.7, 0)]


def Dv11():
    s = room(True) + A.crates(380, 6)
    s += g("beam", f'<polygon points="80,300 360,180 360,420" fill="#fff4d6" fill-opacity=".45"/>')
    s += person(60, 470, "shadow", 1.1, pid="thief")
    s += t(180, 110, "Кто ест", 54, "#fff") + t(180, 168, "ночью?", 54, ACC)
    return s + caption(["Пиши версии"])


Dv11_acts = [mv("thief", 0.0, 0.8, {"x": -120}, {"x": 60}, "lin"), walk("thief", 0.0, 0.8), mv("beam", 0.0, 0.8, {"x": -120, "r": -8}, {"x": 60, "r": 6}, "lin", org="20% 50%")]


def make(slug, title, thumb, hook, rows):
    scenes, t0 = [], 0.0
    for fn, narr, vis, sfx, acts in rows:
        d = max(2, round(len(narr) / B3.CPS))
        scenes.append((fn, f"{int(t0)}-{int(t0 + d)} с", narr, vis, sfx, acts)); t0 += d
    return dict(slug=slug, title=title, thumb=thumb, hook=hook, runtime=f"≈{int(t0)} с", scenes=scenes)


V3 = {v["slug"]: v for v in B3.VIDEOS60}
N = lambda slug: [sc[2] for sc in V3[slug]["scenes"]]  # тексты диктора те же, что в озвучке

VIDEOS60 = [
    make("A", V3["A"]["title"], V3["A"]["thumb"], V3["A"]["hook"], [
        (A1, N("A")[0], "Люк трясётся от стука, герой подходит.", "три удара по металлу", A1_acts),
        (A2, N("A")[1], "Телефон: сообщения друга появляются по одному. Друга в кадре нет, он за люком.", "уведомление", A2_acts),
        (A3, N("A")[2], "Герой стоит у люка, в облаке мыслей появляются чеки из разных магазинов.", "шорох бумаги", A3_acts),
        (A4, N("A")[3], "Семья на лавке встаёт по одному при пересчёте, шестым появляется силуэт друга, шкалы растут.", "тиканье", A4_acts),
        (A5, N("A")[4], "Значки по очереди, плашка «−4 месяца еды».", "три «дзынь»", A5_acts),
        (A6, N("A")[5], "Герой у люка, люк вздрагивает и открывается.", "скрип штурвала", A6_acts),
        (A7, N("A")[6], "Друг шагает из проёма в комнату, пузырь «Я всё знал».", "шаги", A7_acts),
        (A8, N("A")[7], "Крупно проём люка: снаружи в красном свете по одному появляются соседи.", "гул", A8_acts),
        (A9, N("A")[8], "Год назад: сосед подходит к забору, оба машут.", "птицы", A9_acts),
        (A10, N("A")[9], "+3, соседи входят в кадр, шкала сжимается до 13 месяцев.", "тиканье", A10_acts),
        (A11, N("A")[10], "Проём с соседями снаружи, «Соседей пустил бы?», ДА/НЕТ.", "удар", A11_acts),
    ]),
    make("E", V3["E"]["title"], V3["E"]["thumb"], V3["E"]["hook"], [
        (E1, N("E")[0], "Пар идёт, красная черта перечёркивает кастрюлю.", "кипение", E1_acts),
        (E2, N("E")[1], "Пыль падает на воду.", "шорох", E2_acts),
        (E3, N("E")[2], "Бур уходит в глубину.", "бурение", E3_acts),
        (E4, N("E")[3], "Колба, перечёркнуто.", "тиканье", E4_acts),
        (E5, N("E")[4], "Бутылки встают на полку по одной.", "звон", E5_acts),
        (E6, N("E")[5], "Тряпка ходит по бутылке.", "шорох ткани", E6_acts),
        (E7, N("E")[6], "Бачок (не чаша) и бойлер.", "журчание", E7_acts),
        (E8, N("E")[7], "Бутылки появляются по одной, итог 240 л.", "звон", E8_acts),
        (E9, N("E")[8], "Бутылки пустеют по одной, шкала тает.", "часы", E9_acts),
        (E10, N("E")[9], "Капля пульсирует, ДА/НЕТ.", "капля", E10_acts),
    ]),
    make("B", V3["B"]["title"], V3["B"]["thumb"], V3["B"]["hook"], [
        (Bv1, N("B")[0], "Бочки появляются по одной.", "вода", Bv1_acts),
        (Bv2, N("B")[1], "Комментарий.", "уведомление", []),
        (Bv3, N("B")[2], "Герой идёт к люку, на люке запрет, мама останавливает.", "гул", Bv3_acts),
        (Bv4, N("B")[3], "Бак «стоки» опускается в яму.", "лопата", Bv4_acts),
        (Bv5, N("B")[4], "Уровень в баке растёт, итог 110 дней.", "журчание", Bv5_acts),
        (Bv6, N("B")[5], "Баки появляются по одному, сосед проходит мимо.", "лопата", Bv6_acts),
        (Bv7, N("B")[6], "Совок наклоняется, опилки сыплются, запах уходит.", "шорох", Bv7_acts),
        (Bv8, N("B")[7], "Из трубы идёт газ, сосед подходит, «?».", "ветер", Bv8_acts),
        (Bv9, N("B")[8], "Диалог по очереди, сосед кивает.", "музыка", Bv9_acts),
        (Bv10, N("B")[9], "Утро, свет мигает, генератор молчит.", "тишина", Bv10_acts),
    ]),
    make("C", V3["C"]["title"], V3["C"]["thumb"], V3["C"]["hook"], [
        (Cv1, N("C")[0], "Генератор трясётся, дым уходит.", "кашель мотора", Cv1_acts),
        (Cv2, N("C")[1], "Карточки по очереди.", "счётчик", Cv2_acts),
        (Cv3, N("C")[2], "Комментарий, генераторы по одному.", "уведомление", Cv3_acts),
        (Cv4, N("C")[3], "Лампа мигает и гаснет.", "щелчок", Cv4_acts),
        (Cv5, N("C")[4], "Вентилятор замедляется и встаёт.", "затихающий гул", Cv5_acts),
        (Cv6, N("C")[5], "Герой крутит ручку ФВУ.", "скрип", Cv6_acts),
        (Cv7, N("C")[6], "Герой уходит, на смену встаёт мама.", "шаги", Cv7_acts),
        (Cv8, N("C")[7], "Три шкалы часов.", "удары", []),
        (Cv9, N("C")[8], "Люк трясётся от стука, герой подходит. Соседей не видно: они снаружи.", "стук", Cv9_acts),
    ]),
    make("D", V3["D"]["title"], V3["D"]["thumb"], V3["D"]["hook"], [
        (Dv1, N("D")[0], "Соседи по одному входят через люк и встают в ряд.", "шаги", Dv1_acts),
        (Dv2, N("D")[1], "Шкала сжимается до 13 месяцев.", "калькулятор", Dv2_acts),
        (Dv3, N("D")[2], "Три тарелки, третья убирается.", "звон", Dv3_acts),
        (Cv6, N("D")[3], "Герой крутит фильтр.", "скрип", Cv6_acts),
        (Dv5, N("D")[4], "Двое шагают друг на друга.", "низкий тон", Dv5_acts),
        (Dv6, N("D")[5], "Очередь за пайком: по одному подходят к столу, ты пишешь.", "карандаш", Dv6_acts),
        (Dv7, N("D")[6], "Герой подходит к складу, замок защёлкивается.", "щелчок", Dv7_acts),
        (Dv8, N("D")[7], "Герой идёт вдоль ящиков, они подсвечиваются при счёте.", "счёт шёпотом", Dv8_acts),
        (Dv9, N("D")[8], "239 вместо 240, пустой слот пульсирует.", "обрыв", Dv9_acts),
        (Dv10, N("D")[9], "Ключ блестит, рядом проступает второй.", "низкий тон", Dv10_acts),
        (Dv11, N("D")[10], "Ночью силуэт крадётся к складу, луч фонаря скользит.", "шаги", Dv11_acts),
    ]),
]

if __name__ == "__main__":
    B1.main(VIDEOS60)
