#!/usr/bin/env python3
"""Бункер A в 3D-движке (стиль референса): python3 a_3d.py [--stills 1,5,9]

Время сцен и субтитров берётся из озвучки video/voice-A.mp3 (по словам). В каждой сцене: план камеры,
действия персонажей (шаг, лестница, вставание, взмах), мимика, таблички как в референсе.
Координаты: пол y=0, потолок 2.8; люк (1.0, 2.8, -3.0), лестница перед ним на z≈-3.2; лавка у задней стены z≈-3.8.
"""
import json, os, subprocess, sys
import motion
import build_storyboard_3 as B3

HERE = os.path.dirname(os.path.abspath(__file__))
VOICE = os.path.join(HERE, "video", "voice-A.mp3")
V = {v["slug"]: v for v in B3.VIDEOS60}["A"]
al = motion.align(V, VOICE if os.path.exists(VOICE) else None)
T0 = [sum(al["d"][:i]) for i in range(len(al["d"]))]
D = al["d"]
HX, HZ, LZ = 1.0, -3.0, -3.2


def at(i, f):  # абсолютное время: доля f сцены i
    return round(T0[i] + f * D[i], 3)


def cam(*keys):
    return [[k[0], {"x": k[1], "y": k[2], "z": k[3], "tx": k[4], "ty": k[5], "tz": k[6], **(k[7] if len(k) > 7 else {})}] for k in keys]


shots, chars, ui, knocks, crank = [], [], [], [], []
pill_slot = {}


def pill(i, f0, text, kind="pill-y", f1=1.0, slot=None):
    top = 140 + 112 * (slot if slot is not None else 0)
    ui.append({"t0": at(i, f0), "t1": at(i, f1), "kind": kind, "html": text, "css": {"top": f"{top}px"}})


def char(look, i, path, faces, **kw):
    """path: [(доля, {x,z,...})], faces: [(доля, имя)] внутри сцены i."""
    c = {"look": look, "vis": [[at(i, 0), at(i, 1) + 0.001]], "blinkOff": round(0.37 * len(chars), 2),
         "path": [[at(i, f), p] for f, p in path], "faces": [[at(i, f), n] for f, n in faces]}
    for k in ("climb", "talk"):
        if k in kw:
            c[k] = [[at(i, a), at(i, b)] for a, b in kw.pop(k)]
    c.update(kw); chars.append(c); return len(chars) - 1


# 1. Стук: герой входит под люк, смотрит вверх, лицо спокойное -> тревога -> испуг
i = 0
shots.append({"t0": at(i, 0), "t1": at(i, 1), "cam": cam((at(i, 0), -0.3, 1.0, 1.3, 0.8, 2.0, -3.0), (at(i, 1), 0.1, 0.9, 0.4, 0.8, 2.2, -3.0))})
knocks += [[at(i, 0.04), at(i, 0.13)], [at(i, 0.58), at(i, 0.68)]]
char("hero", i, [(0, {"x": -2.6, "z": -1.2}), (0.12, {"x": -2.6, "z": -1.2}), (0.5, {"x": 0.35, "z": -2.6, "lin": 1}), (0.56, {"x": 0.35, "z": -2.6, "head": -8, "gazeY": 3}), (1, {"x": 0.35, "z": -2.6, "head": -8, "gazeY": 3})],
     [(0, "neutral"), (0.15, "worried"), (0.6, "scared")])
pill(i, 0.08, "ЕДА: ≈11 000 ПОРЦИЙ", slot=0); pill(i, 0.35, "5 ЧЕЛОВЕК · 2 ГОДА", slot=1)

# 2. Сообщение: вид от первого лица, руки держат телефон, бункер размыт
i = 1
shots.append({"t0": at(i, 0), "t1": at(i, 1), "blur": 9, "cam": cam((at(i, 0), 0.2, 1.4, -1.0, -2.0, 1.2, -2.6), (at(i, 1), 0.1, 1.4, -1.2, -2.0, 1.25, -2.8))})
phone = ('<svg width="900" height="1400" viewBox="0 0 900 1400"><g stroke="#14110f" stroke-width="10" stroke-linejoin="round">'
         '<path d="M-40 1400 L120 1000 L300 1060 L230 1400 Z" fill="#2d5584"/><path d="M940 1400 L780 1000 L600 1060 L670 1400 Z" fill="#2d5584"/>'
         '<rect x="190" y="150" width="520" height="980" rx="60" fill="#15181d"/><rect x="225" y="215" width="450" height="860" rx="24" fill="#1d2633"/>'
         '<ellipse cx="205" cy="980" rx="95" ry="120" fill="#1c1f24"/><ellipse cx="695" cy="980" rx="95" ry="120" fill="#1c1f24"/>'
         '<path d="M110 1080 L270 1120" stroke="#f08a2a" stroke-width="22"/><path d="M790 1080 L630 1120" stroke="#f08a2a" stroke-width="22"/></g></svg>'
         '<div style="position:absolute;left:250px;top:240px;width:400px;font:700 34px DejaVu Sans;color:#9fb0c4;text-align:center">Друг · год назад</div>'
         f'<div data-t="{at(i, 0.25)}" style="position:absolute;left:255px;top:330px;width:340px;padding:24px;background:#2f4a6a;color:#fff;font:700 44px/1.2 DejaVu Sans;border-radius:26px">Через год начнётся война.</div>'
         f'<div data-t="{at(i, 0.6)}" style="position:absolute;left:255px;top:560px;width:220px;padding:24px;background:#2f4a6a;color:#fff;font:700 44px/1.2 DejaVu Sans;border-radius:26px">Никому.</div>')
ui.append({"t0": at(i, 0), "t1": at(i, 1), "kind": "phone", "html": phone})

# 3. «Ты стоишь у люка и считаешь. Целый год ты возил еду понемногу и в разных магазинах»:
#    у люка, затем три коротких плана покупок (рынок, супермаркет, аптека), как в референсе
i = 2
def sub(f0, f1, world, cams, **kw):
    shots.append({"t0": at(i, f0), "t1": at(i, f1), "world": world, "cam": cam(*[(at(i, f),) + k for f, k in cams]), **kw})
sub(0, 0.22, "bunker", [(0, (-1.3, 1.3, 0.2, 0.5, 1.25, -3.0)), (0.22, (-1.0, 1.3, -0.3, 0.5, 1.3, -3.0))])
char("hero", i, [(0, {"x": 0.45, "z": -2.85, "head": -5, "gazeY": 2}), (0.22, {"x": 0.45, "z": -2.85, "head": -3, "gazeY": 1})], [(0, "thinking")])
chars[-1]["vis"] = [[at(i, 0), at(i, 0.22)]]
# рынок
sub(0.22, 0.48, "town", [(0.22, (1.2, 1.4, 2.6, 0.0, 1.0, -1.4)), (0.48, (0.7, 1.35, 2.2, 0.0, 1.0, -1.4))], charFilter="brightness(.95)")
char("hero", i, [(0.22, {"x": 2.2, "z": -0.6}), (0.36, {"x": 0.35, "z": -0.6, "lin": 1}), (0.4, {"x": 0.35, "z": -0.6, "armR": -55, "bag": 0}), (0.43, {"x": 0.35, "z": -0.6, "armR": 0, "bag": 1}), (0.48, {"x": 0.0, "z": -0.6, "bag": 1})], [(0.22, "neutral")], world="town")
chars[-1]["vis"] = [[at(i, 0.22), at(i, 0.48)]]
char("vendor", i, [(0.22, {"x": 0.25, "z": -2.0, "armR": 0}), (0.38, {"x": 0.25, "z": -2.0, "armR": -60}), (0.44, {"x": 0.25, "z": -2.0, "armR": 0}), (0.48, {"x": 0.25, "z": -2.0})], [(0.22, "happy")], world="town")
chars[-1]["vis"] = [[at(i, 0.22), at(i, 0.48)]]
ui.append({"t0": at(i, 0.24), "t1": at(i, 0.48), "kind": "pill-w", "html": "<b></b>РЫНОК", "css": {"top": "240px"}})
# супермаркет
sub(0.48, 0.74, "town", [(0.48, (35.6, 1.5, -1.6, 42.0, 1.0, -1.6)), (0.74, (36.4, 1.45, -1.6, 42.0, 1.0, -1.6))])
char("hero", i, [(0.48, {"x": 37.4, "z": -1.6, "bag": 1}), (0.64, {"x": 39.6, "z": -1.6, "lin": 1, "bag": 1}), (0.66, {"x": 39.6, "z": -1.6, "armL": 70, "bag": 1}), (0.7, {"x": 39.6, "z": -1.6, "armL": 0, "bag": 1}), (0.74, {"x": 40.4, "z": -1.6, "bag": 1})], [(0.48, "neutral"), (0.62, "thinking")], world="town")
chars[-1]["vis"] = [[at(i, 0.48), at(i, 0.74)]]
ui.append({"t0": at(i, 0.5), "t1": at(i, 0.74), "kind": "pill-w", "html": "<b></b>СУПЕРМАРКЕТ", "css": {"top": "240px"}})
# аптека
sub(0.74, 1.0, "town", [(0.74, (81.3, 1.4, 1.3, 80.0, 1.15, -2.4)), (1.0, (80.9, 1.4, 0.9, 80.0, 1.15, -2.4))])
char("hero", i, [(0.74, {"x": 81.4, "z": -1.1, "bag": 1}), (0.86, {"x": 80.25, "z": -1.25, "lin": 1, "bag": 1}), (0.9, {"x": 80.25, "z": -1.25, "armR": -50, "bag": 0}), (1.0, {"x": 80.25, "z": -1.25, "armR": 0, "bag": 1})], [(0.74, "neutral")], world="town")
chars[-1]["vis"] = [[at(i, 0.74), at(i, 1.0) + 0.001]]
char("pharm", i, [(0.74, {"x": 79.9, "z": -2.8, "armR": 0}), (0.88, {"x": 79.9, "z": -2.8, "armR": -55}), (0.95, {"x": 79.9, "z": -2.8, "armR": 0}), (1.0, {"x": 79.9, "z": -2.8})], [(0.74, "neutral")], world="town")
chars[-1]["vis"] = [[at(i, 0.74), at(i, 1.0) + 0.001]]
ui.append({"t0": at(i, 0.76), "t1": at(i, 1.0), "kind": "pill-w", "html": "<b></b>АПТЕКА", "css": {"top": "240px"}})

# 4. Пересчёт: герой идёт вдоль стеллажей и показывает на банки (камера едет за ним),
#    потом обратно вдоль лавки — семья встаёт по одному, когда он проходит мимо (камера едет в другую сторону)
i = 3
h1 = char("hero", i, [(0, {"x": -2.0, "z": 0.4, "armR": -70}), (0.42, {"x": -2.0, "z": -2.6, "lin": 1, "armR": -70}), (0.45, {"x": 0.4, "z": -3.15}),
                     (0.95, {"x": -2.9, "z": -3.15, "lin": 1}), (1, {"x": -2.9, "z": -3.15})], [(0, "thinking"), (0.5, "worried")])
shots.append({"t0": at(i, 0), "t1": at(i, 0.44), "cam": cam((at(i, 0), 0, 0, 0, 0, 0, 0)), "follow": {"c": h1, "off": [1.9, 0.45, 1.5], "look": [-0.5, 0.95, -0.6]}})
shots.append({"t0": at(i, 0.44), "t1": at(i, 1), "cam": cam((at(i, 0.44), 0, 0, 0, 0, 0, 0)), "follow": {"c": h1, "off": [0.4, 0.35, 3.0], "look": [0.2, 0.85, -0.7]}})
for look, x, face in (("grandpa", -2.45, "tired"), ("mom", -2.0, "worried"), ("kid", -1.4, "scared"), ("girl", -0.95, "scared")):
    f = 0.45 + (0.4 - x) / 3.3 * 0.5
    char(look, i, [(0, {"x": x, "z": -3.78, "sit": 1}), (f, {"x": x, "z": -3.78, "sit": 1}), (f + 0.05, {"x": x, "z": -3.78, "sit": 0}), (1, {"x": x, "z": -3.78, "sit": 0})], [(0, face)])
    chars[-1]["vis"] = [[at(i, 0.44), at(i, 1) + 0.001]]
pill(i, 0.1, "ЕДА: ≈11 000 ПОРЦИЙ", slot=0, f1=0.44)
pill(i, 0.62, "НА 5 — 24 МЕСЯЦА", slot=0); pill(i, 0.8, "НА 6 — 20 МЕСЯЦЕВ", "pill-r", slot=1)

# 5. Вода, воздух, свет: герой проходит через проём в техкомнату и останавливается у каждой вещи
i = 4
h2 = char("hero", i, [(0, {"x": 1.8, "z": -0.4}), (0.3, {"x": 3.9, "z": -1.85, "lin": 1}), (0.36, {"x": 4.4, "z": -1.0, "lin": 1}), (0.45, {"x": 4.95, "z": -0.8, "lin": 1}),
                      (0.55, {"x": 4.95, "z": -0.8}), (0.63, {"x": 5.0, "z": -1.95, "lin": 1}), (0.72, {"x": 5.0, "z": -1.95}), (0.8, {"x": 4.9, "z": -3.0, "lin": 1}), (1, {"x": 4.9, "z": -3.0})],
          [(0, "neutral"), (0.5, "relieved")])
shots.append({"t0": at(i, 0), "t1": at(i, 0.34), "cam": cam((at(i, 0), 0, 0, 0, 0, 0, 0)), "follow": {"c": h2, "off": [-1.9, 0.55, 1.8], "look": [0.6, 0.9, -0.8]}})
shots.append({"t0": at(i, 0.34), "t1": at(i, 1), "cam": cam((at(i, 0.34), 3.55, 1.45, 0.9, 5.6, 0.9, -1.0), (at(i, 1), 3.55, 1.4, -0.4, 5.6, 0.9, -2.8))})
pill(i, 0.46, "ВОДА — ЕСТЬ", slot=0); pill(i, 0.64, "ВОЗДУХ — ЕСТЬ", slot=1); pill(i, 0.81, "СВЕТ — ЕСТЬ", slot=2); pill(i, 0.9, "−4 МЕСЯЦА ЕДЫ", "pill-r", slot=3)

# 6. «Ты открываешь»: герой лезет по лестнице, крышка откидывается, сверху красный свет
i = 5
shots.append({"t0": at(i, 0), "t1": at(i, 1), "cam": cam((at(i, 0), 2.3, 0.8, -0.5, 1.0, 1.9, -3.1), (at(i, 1), 2.2, 0.75, -0.8, 1.0, 2.1, -3.1))})
char("hero", i, [(0, {"x": HX, "z": LZ, "y": 0.0}), (0.7, {"x": HX, "z": LZ, "y": 0.9, "lin": 1}), (1, {"x": HX, "z": LZ, "y": 0.9})], [(0, "serious")], climb=[(0, 0.7)])
LID = [at(i, 0.45), at(i, 1.0)]; RED = at(i, 0.6); TORCH = at(i, 0.6)

# 7. Друг спускается в красном свете, «я всё знал»; герой в шоке
i = 6
shots.append({"t0": at(i, 0), "t1": at(i, 1), "red": True, "cam": cam((at(i, 0), -0.9, 1.35, 0.5, 0.35, 1.25, -3.0), (at(i, 1), -0.7, 1.3, 0.0, 0.3, 1.2, -3.0))})
fr = char("friend", i, [(0, {"x": HX, "z": LZ, "y": 2.2}), (0.38, {"x": HX, "z": LZ, "y": 0.0, "lin": 1}), (0.4, {"x": HX, "z": LZ, "y": 0}), (0.55, {"x": 0.65, "z": -2.6, "lin": 1}), (1, {"x": 0.65, "z": -2.6})],
           [(0, "serious")], climb=[(0, 0.38)], talk=[(0.56, 0.78)])
char("hero", i, [(0, {"x": -0.55, "z": -2.75}), (0.6, {"x": -0.55, "z": -2.75}), (0.72, {"x": -0.9, "z": -2.5}), (1, {"x": -0.9, "z": -2.5})], [(0, "worried"), (0.58, "shocked")])
ui.append({"t0": at(i, 0.56), "t1": at(i, 1), "kind": "bubble", "html": "Я всё знал.", "anchor": fr})

# 8. Соседи наверху, видны в проёме люка, появляются по одному
i = 7
shots.append({"t0": at(i, 0), "t1": at(i, 1), "red": True, "cam": cam((at(i, 0), 1.0, 2.05, -2.75, 1.0, 4.4, -3.05, {"fov": 74}), (at(i, 1), 1.0, 2.1, -2.8, 1.0, 4.5, -3.05, {"fov": 70}))})
for k, (look, dx, dz, face) in enumerate((("n1", -0.42, -0.12, "anxious"), ("n2", 0.0, -0.46, "serious"), ("n3", 0.42, -0.12, "sad"))):
    f = 0.08 + 0.17 * k
    char(look, i, [(0, {"x": HX + dx, "z": HZ + dz, "y": 3.15}), (1, {"x": HX + dx, "z": HZ + dz, "y": 3.15})], [(0, face)], clip=True, onFloorAbove=True)
    chars[-1]["vis"] = [[at(i, f), at(i, 1) + 0.001]]

# 9. Год назад: улица, забор, оба машут
i = 8
shots.append({"t0": at(i, 0), "t1": at(i, 1), "world": "village", "charFilter": "sepia(.18) saturate(1.1)", "cam": cam((at(i, 0), 1.3, 1.4, 4.2, 1.3, 1.0, -1.0), (at(i, 1), 1.1, 1.35, 3.6, 1.2, 1.0, -1.0))})
char("hero", i, [(0, {"x": 0.6, "z": 0.6, "wave": 0}), (0.25, {"x": 0.6, "z": 0.6, "wave": 1}), (1, {"x": 0.6, "z": 0.6, "wave": 1})], [(0, "happy")], world="village")
char("n1", i, [(0, {"x": 4.2, "z": -1.4, "wave": 0}), (0.4, {"x": 2.0, "z": -1.4, "lin": 1, "wave": 0}), (0.5, {"x": 2.0, "z": -1.4, "wave": 1}), (1, {"x": 2.0, "z": -1.4, "wave": 1})], [(0, "happy")], world="village")

# 10. «Трое. Если пустить и их...»: у полок с едой, расчёт
i = 9
shots.append({"t0": at(i, 0), "t1": at(i, 1), "cam": cam((at(i, 0), 0.4, 1.3, 0.8, -2.3, 1.0, -1.3), (at(i, 1), 0.2, 1.3, 0.3, -2.3, 1.0, -1.5))})
char("hero", i, [(0, {"x": -1.9, "z": 0.2}), (0.7, {"x": -1.9, "z": -1.4, "lin": 1}), (1, {"x": -1.9, "z": -1.4})], [(0, "worried"), (0.6, "sad")])
pill(i, 0.08, "+3 СОСЕДА", slot=0); pill(i, 0.3, "11 000 ÷ 9 ÷ 3", slot=1); pill(i, 0.55, "= 13 МЕСЯЦЕВ", "pill-r", slot=2)

# 11. Вопрос: проём люка с соседями, кнопки ДА/НЕТ
i = 10
shots.append({"t0": at(i, 0), "t1": at(i, 1) + 1, "red": True, "cam": cam((at(i, 0), 1.05, 1.9, -2.6, 1.0, 4.3, -3.05, {"fov": 78}), (at(i, 1), 1.05, 1.95, -2.65, 1.0, 4.4, -3.05, {"fov": 76}))})
for look, dx, dz, face in (("n1", -0.42, -0.12, "anxious"), ("n2", 0.0, -0.46, "serious"), ("n3", 0.42, -0.12, "sad")):
    char(look, i, [(0, {"x": HX + dx, "z": HZ + dz, "y": 3.15}), (1, {"x": HX + dx, "z": HZ + dz, "y": 3.15})], [(0, face)], clip=True, onFloorAbove=True)
ui.append({"t0": at(i, 0.1), "t1": at(i, 1) + 1, "kind": "pill-w", "html": "СОСЕДЕЙ ПУСТИЛ БЫ?", "css": {"top": "260px", "width": "640px", "marginLeft": "-320px"}})
ui.append({"t0": at(i, 0.2), "t1": at(i, 1) + 1, "kind": "poll pulse", "html": '<span style="background:#2e8b57">ДА</span><span style="background:#e8443a">НЕТ</span>'})

caps = []
for i, cs in enumerate(al["caps"]):
    for c in cs:
        caps.append({"t0": round(T0[i] + c["t0"], 3), "t1": round(T0[i] + c["t1"], 3), "w": c["w"], "top": {1: 1530, 7: 1480, 10: 1180}.get(i, 1150)})
spec = {"duration": round(sum(D), 2), "shots": shots, "chars": chars, "ui": ui, "caps": caps, "knocks": knocks,
        "lidOpen": LID, "redFrom": RED, "torchFrom": TORCH, "crank": crank}
out = os.path.join(HERE, "engine3d", "spec_A.json")
json.dump(spec, open(out, "w", encoding="utf8"), ensure_ascii=False)
print("сцены:", [round(x, 1) for x in D], "итого", spec["duration"], "с")
if "--stills" in sys.argv:
    ts = sys.argv[sys.argv.index("--stills") + 1]
    subprocess.run(["node", os.path.join(HERE, "engine3d", "render3d.js"), out, "--stills", ts], check=True)
elif "--norender" not in sys.argv:
    subprocess.run(["node", os.path.join(HERE, "engine3d", "render3d.js"), out, os.path.join(HERE, "video", "bunker-A.mp4"), VOICE], check=True)
