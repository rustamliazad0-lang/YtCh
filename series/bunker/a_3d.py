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

# 3. «Ты стоишь у люка и считаешь»: герой у лестницы, думает; таблички магазинов
i = 2
shots.append({"t0": at(i, 0), "t1": at(i, 1), "cam": cam((at(i, 0), -1.4, 1.3, 0.3, 0.5, 1.25, -3.0), (at(i, 1), -1.1, 1.3, -0.2, 0.5, 1.3, -3.0))})
char("hero", i, [(0, {"x": 0.45, "z": -2.85, "head": -5, "gazeY": 2}), (1, {"x": 0.45, "z": -2.85, "head": -3, "gazeY": 1})], [(0, "thinking")])
pill(i, 0.32, "<b></b>РЫНОК", "pill-w", slot=None); ui[-1]["css"] = {"top": "260px"}
pill(i, 0.48, "<b></b>СУПЕРМАРКЕТ", "pill-w"); ui[-1]["css"] = {"top": "370px"}
pill(i, 0.64, "<b></b>АПТЕКА", "pill-w"); ui[-1]["css"] = {"top": "480px"}

# 4. Семья на лавке: при пересчёте встают по одному, шестое место пустое
i = 3
shots.append({"t0": at(i, 0), "t1": at(i, 1), "cam": cam((at(i, 0), -1.5, 1.3, 0.8, -1.55, 0.85, -4.0), (at(i, 1), -1.55, 1.3, 0.3, -1.6, 0.85, -4.0))})
for k, (look, x, face) in enumerate((("grandpa", -2.45, "tired"), ("mom", -2.0, "worried"), ("hero", -1.55, "thinking"), ("kid", -1.12, "scared"), ("girl", -0.78, "scared"))):
    f = 0.1 + 0.11 * k
    char(look, i, [(0, {"x": x, "z": -3.78, "sit": 1}), (f, {"x": x, "z": -3.78, "sit": 1}), (f + 0.06, {"x": x, "z": -3.78, "sit": 0}), (1, {"x": x, "z": -3.78, "sit": 0})], [(0, face)])
pill(i, 0.58, "НА 5 — 24 МЕСЯЦА", slot=0); pill(i, 0.76, "НА 6 — 20 МЕСЯЦЕВ", "pill-r", slot=1)

# 5. Вода, воздух, свет: камера едет вдоль техники, герой проходит рядом
i = 4
shots.append({"t0": at(i, 0), "t1": at(i, 1), "cam": cam((at(i, 0), -0.7, 1.3, 1.3, 2.6, 0.95, -0.2), (at(i, 1), -0.6, 1.3, -0.4, 2.6, 0.95, -2.4))})
char("hero", i, [(0, {"x": 1.75, "z": 0.7}), (0.9, {"x": 1.85, "z": -1.9, "lin": 1}), (1, {"x": 1.85, "z": -1.9})], [(0, "neutral"), (0.5, "relieved")])
pill(i, 0.08, "ВОДА — ЕСТЬ", slot=0); pill(i, 0.28, "ВОЗДУХ — ЕСТЬ", slot=1); pill(i, 0.48, "СВЕТ — ЕСТЬ", slot=2); pill(i, 0.7, "−4 МЕСЯЦА ЕДЫ", "pill-r", slot=3)

# 6. «Ты открываешь»: герой лезет по лестнице, крышка откидывается, сверху красный свет
i = 5
shots.append({"t0": at(i, 0), "t1": at(i, 1), "cam": cam((at(i, 0), 2.3, 0.8, -0.5, 1.0, 1.9, -3.1), (at(i, 1), 2.2, 0.75, -0.8, 1.0, 2.1, -3.1))})
char("hero", i, [(0, {"x": HX, "z": LZ, "y": 0.0}), (0.7, {"x": HX, "z": LZ, "y": 0.9, "lin": 1}), (1, {"x": HX, "z": LZ, "y": 0.9})], [(0, "serious")], climb=[(0, 0.7)])
LID = [at(i, 0.45), at(i, 1.0)]; RED = at(i, 0.6)

# 7. Друг спускается в красном свете, «я всё знал»; герой в шоке
i = 6
shots.append({"t0": at(i, 0), "t1": at(i, 1), "red": True, "cam": cam((at(i, 0), -0.9, 1.35, 0.5, 0.35, 1.25, -3.0), (at(i, 1), -0.7, 1.3, 0.0, 0.3, 1.2, -3.0))})
fr = char("friend", i, [(0, {"x": HX, "z": LZ, "y": 2.2}), (0.38, {"x": HX, "z": LZ, "y": 0.0, "lin": 1}), (0.4, {"x": HX, "z": LZ, "y": 0}), (0.55, {"x": 0.65, "z": -2.6, "lin": 1}), (1, {"x": 0.65, "z": -2.6})],
           [(0, "serious")], climb=[(0, 0.38)], talk=[(0.56, 0.78)])
char("hero", i, [(0, {"x": -0.55, "z": -2.75}), (1, {"x": -0.55, "z": -2.75})], [(0, "worried"), (0.58, "shocked")])
ui.append({"t0": at(i, 0.56), "t1": at(i, 1), "kind": "bubble", "html": "Я всё знал.", "anchor": fr})

# 8. Соседи наверху, видны в проёме люка, появляются по одному
i = 7
shots.append({"t0": at(i, 0), "t1": at(i, 1), "red": True, "cam": cam((at(i, 0), 1.0, 2.3, -2.85, 1.0, 4.8, -3.05, {"fov": 72}), (at(i, 1), 1.0, 2.35, -2.88, 1.0, 4.9, -3.05, {"fov": 68}))})
for k, (look, dx, dz, face) in enumerate((("n1", -0.33, -0.2, "anxious"), ("n2", 0.0, -0.36, "serious"), ("n3", 0.33, -0.2, "sad"))):
    f = 0.08 + 0.17 * k
    char(look, i, [(0, {"x": HX + dx, "z": HZ + dz, "y": 3.7}), (1, {"x": HX + dx, "z": HZ + dz, "y": 3.7})], [(0, face)], clip=True, onFloorAbove=True)
    chars[-1]["vis"] = [[at(i, f), at(i, 1) + 0.001]]

# 9. Год назад: улица, забор, оба машут
i = 8
shots.append({"t0": at(i, 0), "t1": at(i, 1), "world": "village", "charFilter": "sepia(.18) saturate(1.1)", "cam": cam((at(i, 0), 1.3, 1.4, 4.2, 1.3, 1.0, -1.0), (at(i, 1), 1.1, 1.35, 3.6, 1.2, 1.0, -1.0))})
char("hero", i, [(0, {"x": 0.6, "z": 0.6, "wave": 0}), (0.25, {"x": 0.6, "z": 0.6, "wave": 1}), (1, {"x": 0.6, "z": 0.6, "wave": 1})], [(0, "happy")], world="village")
char("n1", i, [(0, {"x": 4.2, "z": -1.4, "wave": 0}), (0.4, {"x": 2.0, "z": -1.4, "lin": 1, "wave": 0}), (0.5, {"x": 2.0, "z": -1.4, "wave": 1}), (1, {"x": 2.0, "z": -1.4, "wave": 1})], [(0, "happy")], world="village")

# 10. «Трое. Если пустить и их...»: у полок с едой, расчёт
i = 9
shots.append({"t0": at(i, 0), "t1": at(i, 1), "cam": cam((at(i, 0), 0.4, 1.3, 0.8, -2.3, 1.0, -1.3), (at(i, 1), 0.2, 1.3, 0.3, -2.3, 1.0, -1.5))})
char("hero", i, [(0, {"x": -1.85, "z": -0.9, "head": 0}), (1, {"x": -1.85, "z": -0.9})], [(0, "worried"), (0.6, "sad")])
pill(i, 0.08, "+3 СОСЕДА", slot=0); pill(i, 0.3, "11 000 ÷ 9 ÷ 3", slot=1); pill(i, 0.55, "= 13 МЕСЯЦЕВ", "pill-r", slot=2)

# 11. Вопрос: проём люка с соседями, кнопки ДА/НЕТ
i = 10
shots.append({"t0": at(i, 0), "t1": at(i, 1) + 1, "red": True, "cam": cam((at(i, 0), 1.05, 2.1, -2.7, 1.0, 4.6, -3.05, {"fov": 76}), (at(i, 1), 1.05, 2.15, -2.75, 1.0, 4.7, -3.05, {"fov": 74}))})
for look, dx, dz, face in (("n1", -0.33, -0.2, "anxious"), ("n2", 0.0, -0.36, "serious"), ("n3", 0.33, -0.2, "sad")):
    char(look, i, [(0, {"x": HX + dx, "z": HZ + dz, "y": 3.7}), (1, {"x": HX + dx, "z": HZ + dz, "y": 3.7})], [(0, face)], clip=True, onFloorAbove=True)
ui.append({"t0": at(i, 0.1), "t1": at(i, 1) + 1, "kind": "pill-w", "html": "СОСЕДЕЙ ПУСТИЛ БЫ?", "css": {"top": "260px", "width": "640px", "marginLeft": "-320px"}})
ui.append({"t0": at(i, 0.2), "t1": at(i, 1) + 1, "kind": "poll pulse", "html": '<span style="background:#2e8b57">ДА</span><span style="background:#e8443a">НЕТ</span>'})

caps = []
for i, cs in enumerate(al["caps"]):
    for c in cs:
        caps.append({"t0": round(T0[i] + c["t0"], 3), "t1": round(T0[i] + c["t1"], 3), "w": c["w"], "top": {1: 1530, 7: 1480, 10: 1180}.get(i, 1150)})
spec = {"duration": round(sum(D), 2), "shots": shots, "chars": chars, "ui": ui, "caps": caps, "knocks": knocks,
        "lidOpen": LID, "redFrom": RED, "crank": crank}
out = os.path.join(HERE, "engine3d", "spec_A.json")
json.dump(spec, open(out, "w", encoding="utf8"), ensure_ascii=False)
print("сцены:", [round(x, 1) for x in D], "итого", spec["duration"], "с")
if "--stills" in sys.argv:
    ts = sys.argv[sys.argv.index("--stills") + 1]
    subprocess.run(["node", os.path.join(HERE, "engine3d", "render3d.js"), out, "--stills", ts], check=True)
elif "--norender" not in sys.argv:
    subprocess.run(["node", os.path.join(HERE, "engine3d", "render3d.js"), out, os.path.join(HERE, "video", "bunker-A.mp4"), VOICE], check=True)
