#!/usr/bin/env python3
"""Раскадровки D и E (после первых трёх). Запуск: python3 build_storyboard_2.py, затем скриншот HTML."""
from build_storyboard import *  # noqa: F401,F403
import build_storyboard as B


def plate(cx, cy, r=34, food=True):
    s = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#e9e6df" stroke="#9aa5b1" stroke-width="3"/><circle cx="{cx}" cy="{cy}" r="{r-10}" fill="none" stroke="#c9c5bb" stroke-width="2"/>'
    if food:
        s += f'<circle cx="{cx-6}" cy="{cy+2}" r="9" fill="#d9a04a"/><circle cx="{cx+9}" cy="{cy-6}" r="7" fill="#6b9a4a"/>'
    return s


def bottle(x, y, h=90, level=1.0, cap=True):
    s = f'<rect x="{x}" y="{y+16}" width="30" height="{h}" rx="9" fill="#1d232b" stroke="#6b7480" stroke-width="3"/><rect x="{x+4}" y="{y+16+(h-8)*(1-level)+4}" width="22" height="{(h-8)*level}" rx="5" fill="{WAT}"/>'
    if cap:
        s += f'<rect x="{x+7}" y="{y}" width="16" height="18" rx="3" fill="#cfd6de"/>'
    return s


def dust(n=24, y0=40, y1=380, seed=1, color="#d8c35a"):
    return "".join(f'<circle cx="{(i*53+seed*31)%340+10}" cy="{y0+(i*97+seed*17)%(y1-y0)}" r="{2+(i%3)}" fill="{color}" fill-opacity=".8"/>' for i in range(n))


def trefoil(cx, cy, r=40, color=AMB):
    s = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}"/><circle cx="{cx}" cy="{cy}" r="{r*0.18}" fill="#111"/>'
    for a in (90, 210, 330):
        s += f'<path d="M{cx} {cy} L{cx+r*0.85*math.cos(math.radians(a-30)):.1f} {cy-r*0.85*math.sin(math.radians(a-30)):.1f} A{r*0.85} {r*0.85} 0 0 0 {cx+r*0.85*math.cos(math.radians(a+30)):.1f} {cy-r*0.85*math.sin(math.radians(a+30)):.1f}Z" fill="#111"/>'
    return s


def crates(y, n=6, missing=None):
    s = ""
    for i in range(n):
        x = 24 + i * 52
        if i == missing:
            s += f'<rect x="{x}" y="{y}" width="46" height="40" rx="4" fill="none" stroke="{ACC}" stroke-width="3" stroke-dasharray="6 5"/>'
        else:
            s += f'<rect x="{x}" y="{y}" width="46" height="40" rx="4" fill="#8b6f47" stroke="#5a4528" stroke-width="2"/><line x1="{x}" y1="{y+14}" x2="{x+46}" y2="{y+14}" stroke="#5a4528" stroke-width="2"/>'
    return s


def d1():
    s = room() + lamp()
    xs = (28, 70, 112, 150, 186, 222, 258, 296, 332)
    ks = ("grandpa", "mom", "hero", "kid", "kid", "friend", "n1", "n2", "n3")
    for x, k in zip(xs, ks):
        s += person(x, 470, k, 0.55)
    s += t(180, 110, "9", 110, ACC) + t(180, 150, "человек в бункере на 5", 22, "#cfd6de", "normal")
    return s + caption(["Вас девять,", "еда на пятерых"])


def d2():
    s = room() + lamp() + t(180, 100, "10 950 ÷ 9 ÷ 3", 34, WAT) + t(180, 138, "= 405 дней", 24, "#fff")
    s += bar(40, 200, 280, 1.0, "#2e8b57") + t(40, 242, "план: 24 месяца", 14, "#9aa5b1", "normal", "start")
    s += bar(40, 272, 280, 13 / 24, ACC) + t(40, 314, "теперь: 13 месяцев", 14, "#ffb4a6", "normal", "start")
    s += badge(180, 380, "минус 11", ACC, 160, 28)
    return s + caption(["Не 24 месяца,", "а 13"])


def d3():
    s = room() + lamp()
    for i, x in enumerate((70, 180, 290)):
        s += plate(x, 220, 40, True)
    s += f'<line x1="250" y1="170" x2="330" y2="270" stroke="{ACC}" stroke-width="10"/><line x1="330" y1="170" x2="250" y2="270" stroke="{ACC}" stroke-width="10"/>'
    s += t(180, 110, "2 приёма вместо 3", 30, AMB) + bar(40, 340, 280, 20 / 24, "#2e8b57", None, None) + t(180, 400, "те же 20 месяцев", 24, "#fff")
    return s + caption(["Два приёма", "вместо трёх"])


def d4():
    s = room() + lamp(180, 0, 110)
    s += person(80, 500, "hero", 1.0, mood="worried") + person(280, 500, "n1", 1.0)
    s += f'<g stroke="{ACC}" stroke-width="5" fill="none"><path d="M130 300 l30 -14 l-30 -14"/><path d="M230 300 l-30 -14 l30 -14"/></g><path d="M150 330 l20 -22 l20 22 l20 -22" stroke="{ACC}" stroke-width="4" fill="none"/>'
    s += t(180, 110, "голодные", 46, ACC) + t(180, 146, "хуже терпят друг друга", 18, "#cfd6de", "normal")
    return s + caption(["Некуда уйти", "из бункера"])


def d5():
    s = room() + lamp() + card(60, 130, 240, 260, "#f1ebdd", "#8b7a55")
    for i in range(7):
        y = 170 + i * 30
        s += f'<line x1="80" y1="{y}" x2="280" y2="{y}" stroke="#b7ab8a" stroke-width="2"/>' + (f'<path d="M86 {y-6} l6 8 l12 -14" stroke="#2e8b57" stroke-width="4" fill="none"/>' if i < 5 else "")
    s += t(180, 160, "ВЫДАЧА", 22, "#5a4528") + person(310, 500, "hero", 0.7)
    return s + caption(["Выдаёшь ты,", "под запись"])


def d6():
    s = room() + lamp() + crates(300, 6) + crates(350, 6) + calendar(180, 100, "60", None, 110)
    s += person(60, 560, "hero", 0.7, mood="worried")
    return s + caption(["День 60.", "Считаешь коробки"])


def d7():
    s = room(True) + crates(300, 6) + crates(350, 6, missing=3)
    s += f'<circle cx="{24+3*52+23}" cy="370" r="40" fill="none" stroke="{ACC}" stroke-width="4"/>' + t(180, 130, "не хватает", 44, ACC) + t(180, 175, "одной коробки", 34, "#fff")
    return s + caption(["Одной коробки", "не хватает"])


def d8():
    s = room(True)
    s += f'<defs><linearGradient id="fl" x1="0" x2="1"><stop offset="0" stop-color="{LIGHT}" stop-opacity=".85"/><stop offset="1" stop-color="{LIGHT}" stop-opacity="0"/></linearGradient></defs><polygon points="80,300 360,180 360,420" fill="url(#fl)"/>'
    s += crates(380, 6) + person(60, 470, "shadow", 1.1)
    s += t(180, 110, "Кто ест", 54, "#fff") + t(180, 168, "ночью?", 54, ACC)
    return s + caption(["Пиши версии"])


def e1():
    s = room(True)
    s += f'<rect x="100" y="260" width="160" height="110" rx="14" fill="#5b6573" stroke="#8a95a3" stroke-width="4"/><rect x="90" y="250" width="180" height="16" rx="6" fill="#8a95a3"/>'
    s += f'<g stroke="#cfd6de" stroke-width="5" fill="none" stroke-linecap="round" stroke-opacity=".7"><path d="M140 230 q10 -20 0 -40 t0 -40"/><path d="M180 230 q10 -20 0 -40 t0 -40"/><path d="M220 230 q10 -20 0 -40 t0 -40"/></g>'
    s += trefoil(180, 315, 30, AMB) + t(180, 90, "КИПЯЧЕНИЕ", 46, AMB)
    s += f'<line x1="120" y1="240" x2="240" y2="390" stroke="{ACC}" stroke-width="12"/>'
    return s + caption(["Не убирает радиацию", "из воды"])


def e2():
    s = f'<rect width="{W}" height="{H}" fill="#2a2a1c"/><rect y="300" width="{W}" height="340" fill="#2a4a5a"/>' + dust(40, 30, 330, 2) + dust(14, 300, 500, 5)
    s += f'<path d="M0 360 q60 -14 120 0 t120 0 t120 0" stroke="#4b7a8c" stroke-width="5" fill="none"/>'
    s += t(180, 110, "ПЫЛЬ", 60, "#d8c35a") + t(180, 148, "осела на реках и озёрах", 19, "#cfd6de", "normal")
    return s + caption(["Оседает на всём", "открытом"])


def e3():
    s = f'<rect width="{W}" height="{H}" fill="#1c2638"/><rect y="150" width="{W}" height="490" fill="#3a2e24"/><rect y="150" width="{W}" height="8" fill="#4f6b2f"/>' + dust(18, 20, 150, 3)
    s += f'<rect x="40" y="95" width="130" height="55" fill="#6a717b"/><path d="M34 95 l71 -34 l71 34z" fill="#4a5058"/>'
    s += f'<rect x="95" y="158" width="14" height="300" fill="#7a8594"/><rect x="82" y="440" width="40" height="30" rx="6" fill="{WAT}"/>'
    s += f'<line x1="220" y1="160" x2="220" y2="450" stroke="#fff" stroke-width="2" stroke-dasharray="5 5"/><path d="M212 178 l8 -12 l8 12" stroke="#fff" fill="none" stroke-width="2"/><path d="M212 432 l8 12 l8 -12" stroke="#fff" fill="none" stroke-width="2"/>' + t(250, 310, "глубоко", 20, "#fff", "normal", "start")
    s += t(180, 500, "шанс лучше, но не гарантия", 19, AMB)
    return s + caption(["Скважина:", "закрытая и глубокая"])


def e4():
    s = room() + lamp()
    s += f'<path d="M150 190 h60 l-10 40 q40 50 10 110 h-60 q-30 -60 10 -110z" fill="#1d232b" stroke="#8a95a3" stroke-width="4"/><path d="M160 290 h40 l8 40 h-56z" fill="{WAT}"/>'
    s += t(180, 110, "?", 110, ACC) + f'<line x1="120" y1="180" x2="240" y2="360" stroke="{ACC}" stroke-width="10"/>'
    s += t(180, 440, "лаборатории нет", 22, "#cfd6de", "normal")
    return s + caption(["Проверить воду", "ты не можешь"])


def e5():
    s = room() + lamp()
    for i in range(8):
        s += bottle(24 + i * 40, 250, 100, 1.0, True)
    for i in range(8):
        s += bottle(24 + i * 40, 370, 100, 1.0, True)
    s += t(180, 110, "закрытые", 46, WAT) + t(180, 148, "бутылки и ёмкости", 20, "#cfd6de", "normal")
    return s + caption(["Первые недели", "только запас"])


def e6():
    s = room() + lamp() + dust(22, 120, 400, 4) + bottle(150, 250, 150, 1.0, True)
    s += f'<ellipse cx="205" cy="330" rx="44" ry="26" fill="#f4efe4" transform="rotate(-25 205 330)"/>'
    s += person(300, 520, "hero", 0.8) + t(180, 100, "пыль и снаружи", 34, AMB)
    return s + caption(["Протираешь бутылку", "влажной тряпкой"])


def e7():
    s = room() + lamp() + calendar(180, 90, "20", None, 120)
    s += t(180, 214, "дней запаса", 22, "#cfd6de", "normal")
    for i in range(3):
        s += bottle(110 + i * 60, 270, 100, 0.5 if i == 2 else 1.0, True)
    s += bar(40, 430, 280, 0.12, ACC, "день 1", "день 20")
    return s + caption(["Запас на", "двадцать дней"])


def e8():
    s = room(True) + door(180, 150, 70)
    s += icon(180, 300, "drop", WAT) + t(180, 410, "Пил бы воду", 38, "#fff") + t(180, 452, "из скважины?", 38, ACC) + poll(480)
    return s + caption(["Да или нет?"])


VIDEOS2 = [
    dict(slug="D", title="9 человек в бункере на 5: еды на 13 месяцев", thumb="КТО ВЗЯЛ?",
         hook="Вас стало девять, а еда рассчитана на пятерых. Хватит на тринадцать месяцев.", runtime="≈42 с",
         scenes=[
             (d1, "0-5 с", "Вас стало девять, а еда рассчитана на пятерых.", "Девять человек в ряд под лампой, цифра 9 крупно.", "гул, шаги по металлу"),
             (d2, "5-14 с", "Одиннадцать тысяч порций, по три в день на девятерых. Хватит на тринадцать месяцев, на одиннадцать меньше, чем планировал.", "Формула 10 950 ÷ 9 ÷ 3, две шкалы: 24 и 13 месяцев.", "быстрое тиканье калькулятора"),
             (d3, "14-21 с", "Выход один: два приёма пищи вместо трёх. Тогда снова двадцать месяцев.", "Три тарелки, одна зачёркнута, шкала на 20 месяцев.", "звон тарелки, одобрительная нота"),
             (d4, "21-26 с", "Но голодные люди хуже терпят друг друга, а из бункера некуда уйти.", "Двое друг против друга, красная ломаная между ними.", "нарастающий низкий тон"),
             (d5, "26-30 с", "Ты вводишь правила: еду выдаёшь ты, под запись.", "Тетрадь с отметками выдачи.", "шорох бумаги, карандаш"),
             (d6, "30-35 с", "На шестидесятый день ты считаешь банки.", "Два ряда коробок, календарь 60.", "счёт шёпотом"),
             (d7, "35-39 с", "Не хватает одной коробки.", "Один пустой слот красным пунктиром.", "резкий обрыв звука"),
             (d8, "39-43 с", "Кто-то ест ночью. Кто взял? Пиши версии.", "Тёмный бункер, конус фонаря, силуэт у полки, «Кто ест ночью?».", "шаги, шорох упаковки, обрыв"),
         ]),
    dict(slug="E", title="Кипячение не убирает радиацию из воды", thumb="ИЗ СКВАЖИНЫ?",
         hook="Кипячение не убирает радиацию из воды. А ты собирался пить из скважины.", runtime="≈43 с",
         scenes=[
             (e1, "0-6 с", "Кипячение не убирает радиацию из воды. А ты собирался пить из скважины.", "Кастрюля с паром, знак радиации, красная перекрестная черта.", "кипение, затем резкий удар"),
             (e2, "6-13 с", "Радиоактивная пыль оседает на всём открытом: на реках, озёрах, колодцах без крышки.", "Пыль падает на воду, мутный красный фон.", "шорох, тихий треск"),
             (e3, "13-20 с", "Скважина в гараже глубокая и закрытая, так что шансов у неё больше. Но больше не значит чисто.", "Разрез: гараж, скважина вниз, надпись «шанс лучше, но не гарантия».", "эхо падающей капли"),
             (e4, "20-24 с", "А проверить воду ты не можешь: лаборатории нет.", "Колба, красный перечёркнутый знак, вопрос.", "тиканье, пауза"),
             (e5, "24-29 с", "Поэтому первые недели вы пьёте только запас в закрытых бутылках: упаковка защищает воду от пыли.", "Ряды закрытых бутылок.", "звон бутылок"),
             (e6, "29-34 с", "Перед тем как открыть, бутылку протираешь влажной тряпкой: пыль сидит и снаружи.", "Бутылка, тряпка, пыль вокруг.", "шорох ткани"),
             (e7, "34-39 с", "Запас рассчитан на двадцать дней, а сирены только начались.", "Календарь «20», три бутылки, шкала почти пуста.", "тиканье часов"),
             (e8, "39-43 с", "Стал бы ты пить воду из скважины? Да или нет.", "Капля, кнопки ДА/НЕТ, закреплённый комментарий.", "капля, пауза"),
         ]),
]

if __name__ == "__main__":
    B.main(VIDEOS2)
