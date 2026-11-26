#!/usr/bin/env python3
"""Бункер A на сгенерированных иллюстрациях (стиль ролика про гаражи).

Картинки: img/A/*.jpg (vidIQ, 9:16). Камера ходит по нужным частям картинки: у каждой сцены
список планов (откуда -> куда): точка фокуса на картинке (x 0-360, y 0-640) и приближение z.
Поверх картинки движок кладёт пыль, мигание сирены, субтитры по словам и голос.
"""
import os
import build_storyboard as B1
import build_storyboard_3 as B3

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img", "A")
RED = "<!-- #ff2d2d -->"  # метка: в сцене мигает сирена


def pic(name, red=False, over=""):
    def fn():
        return (f'<image href="file://{IMG}/{name}" x="0" y="0" width="360" height="640" preserveAspectRatio="xMidYMid slice"/>'
                + (RED if red else "") + over)
    fn.__name__ = name
    return fn


def sprite(name, x, y, h, aid, flip=False):
    """2D-персонаж (PNG с прозрачным фоном) поверх 3D-фона: x, y = точка ступней на кадре 360x640,
    h = рост в единицах кадра. aid: метка для действий движка (шаг, подъём, появление, смена выражения)."""
    w = h  # ширину держим квадратной рамкой, картинка вписывается по высоте
    tr = f' transform="translate({2*x} 0) scale(-1 1)"' if flip else ""
    return (f'<g data-a="{aid}" data-l="fg"><image href="file://{IMG}/{name}" x="{x - w/2}" y="{y - h}" width="{w}" height="{h}" '
            f'preserveAspectRatio="xMidYMax meet"{tr}/></g>')


def cam(fx, fy, z):
    """Фокус камеры на точке картинки и приближение (z: 0 = весь кадр, 700 ≈ x1,5).
    Сдвиг ограничен так, чтобы картинка всегда закрывала кадр (края не видны)."""
    tz = z + 260                                  # базовый запас: картинка чуть больше кадра
    S = 1.008 * 1500 / (1680 - tz)                # видимый масштаб картинки
    mx, my = (S - 1) * 540 / S * 1.008 * 0.97, (S - 1) * 880 / S * 1.008 * 0.97
    cl = lambda v, m: max(-m, min(m, v))
    return {"tx": round(cl((180 - fx) * 3, mx), 1), "ty": round(cl((294 - fy) * 3, my), 1), "tz": tz}


def shot(a, b):
    return (cam(*a), cam(*b))


K1, K2, K3, K4 = "k1-hatch-hero.jpg", "k2-family.jpg", "k3-friend-ladder.jpg", "k4-neighbors-above.jpg"
N = [sc[2] for sc in {v["slug"]: v for v in B3.VIDEOS60}["A"]["scenes"]]
ROWS = [  # (картинка, сирена, планы)
    (K1, False, [shot((200, 110, 650), (200, 120, 720)), shot((120, 300, 600), (125, 310, 660))]),
    (K1, False, [shot((110, 290, 700), (110, 290, 780)), shot((150, 420, 450), (150, 380, 520))]),
    (K1, False, [shot((180, 330, 0), (180, 320, 160)), shot((260, 250, 450), (230, 200, 520))]),
    (K2, False, [shot((90, 330, 550), (150, 330, 560)), shot((210, 330, 560), (270, 330, 560))]),
    (K2, False, [shot((120, 220, 600), (140, 220, 650)), shot((290, 130, 550), (290, 110, 620))]),
    (K1, False, [shot((200, 110, 600), (200, 100, 820))]),
    (K3, True, [shot((120, 120, 500), (130, 160, 560)), shot((270, 330, 520), (270, 310, 600))]),
    (K4, True, [shot((180, 300, 100), (180, 260, 300)), shot((180, 200, 500), (180, 190, 580))]),
    (K4, True, [shot((180, 170, 650), (150, 170, 700))]),
    (K4, True, [shot((70, 190, 600), (180, 190, 600)), shot((180, 190, 600), (290, 190, 600))]),
    (K4, True, [shot((180, 320, 0), (180, 310, 120))]),
]
SCENES = []
for k, ((img, red, shots), narr) in enumerate(zip(ROWS, N)):
    over = B1.poll(470) if k == len(ROWS) - 1 else ""
    SCENES.append((pic(img, red, over), "0-1 с", narr, img, "", [], shots))

VIDEOS = [dict(slug="A", title="Шестой в бункере: еды на 20 месяцев", thumb="ОТКРЫТЬ?", hook=N[0], runtime="≈61 с", scenes=SCENES)]
