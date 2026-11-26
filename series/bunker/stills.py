#!/usr/bin/env python3
"""Ключевые кадры ролика A: нарисованный фон (illus) + 2D-персонажи (char). Только кадры, на утверждение."""
import math, os, sys
import illus as I, char as C

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "illus_out")
M = 1.75 / 1000  # локальная единица персонажа в метрах


def put(pic, svg, X, Z, Y=0.0, flip=False, dz=0.0):
    """Ставит персонажа ступнями в мировую точку (X,Y,Z)."""
    x, y, d = pic.cam.p(X, Y, Z)
    pic.raw(d + dz, C.place(svg, x, y, pic.cam.f / d * M, flip))


def save(name, pic, **kw):
    open(f"{OUT}/{name}.svg", "w").write(pic.svg(**kw))


def frames():
    # 1. Герой в бункере у стеллажа с банками, тревога
    cam = I.Cam(x=0.1, y=1.15, z=1.5, pitch=0.05, f=760)
    p = I.bunker(cam)
    put(p, C.person("hero", "front", face="worried", arms="down", gaze=-3, light=(1, 1)), -0.25, 0.25)
    save("k1_bunker", p, sky="#101014", particles=("dust", 50), vignette=0.7)

    # 2. Семья на лавке у стеллажа, герой считает в блокноте
    cam = I.Cam(x=-1.3, y=1.0, z=-0.5, pitch=0.03, f=900)
    p = I.bunker(cam)
    put(p, C.person("grandpa", "side", face="serious", sit=True), -2.25, -3.3)
    put(p, C.person("mom", "side", face="worried", sit=True), -1.65, -3.3)
    put(p, C.person("girl", "side", face="scared", sit=True), -1.1, -3.3)
    put(p, C.person("kid", "front", face="sad", arms="down"), -2.55, -2.95)
    put(p, C.person("hero", "front", face="thinking", arms="count", prop="notebook"), -0.45, -2.5)
    save("k2_family", p, sky="#101014", particles=("dust", 40), vignette=0.7)

    # 3. Рынок: продавщица за прилавком, герой в профиль протягивает деньги
    cam = I.Cam(x=0.2, y=1.15, z=1.4, pitch=0.04, f=820)
    p = I.market(cam)
    put(p, C.person("vendor", "front", face="happy", talk=0.4, light=(-1, 1), rim="#ffc890"), 0.45, -2.0)
    put(p, C.person("hero", "side", face="neutral", arms="money", prop=None, light=(1, 1), rim="#ffc890"), -0.5, -0.55)
    save("k3_market", p, sky="#2c2c4a", particles=("snow", 140), vignette=0.6)

    # 4. Супермаркет сбоку: герой идёт с тележкой вдоль полки (походка в профиль)
    cam = I.Cam(x=-0.85, y=1.15, z=-3.0, yaw=math.pi / 2, pitch=-0.14, f=700)
    p = I.supermarket(cam)
    hero = C.person("hero", "side", face="serious", phase=0.9, arms="push", light=(-1, 1), rim="#ffffff")
    put(p, C.cart_side(300, 0) + hero, 0.45, -3.55)
    save("k4_super", p, sky="#d8d0c0", vignette=0.45)

    # 5. Аптека: герой со спины у прилавка, фармацевт лицом
    cam = I.Cam(x=0.3, y=1.3, z=0.5, pitch=-0.06, f=820)
    p = I.pharmacy(cam)
    put(p, C.person("pharm", "front", face="neutral", talk=0.3, light=(-1, 1), rim="#ffffff"), 0.2, -2.95)
    put(p, C.person("hero", "back", arms="down", prop=None, light=(-1, 1), rim="#ffffff"), -0.15, -1.55)
    save("k5_pharm", p, sky="#dfe9e2", vignette=0.55)

    # 6. Вид снизу в открытый люк: темнота, фонарик, над ним соседи
    cam = I.Cam(x=1.0, y=1.4, z=-2.35, pitch=1.3, f=1000)
    Hc, hx, hz, r = 2.8, 1.0, -3.0, 0.42
    ring = [cam.p(hx + math.cos(a) * r, Hc, hz + math.sin(a) * r) for a in [k / 48 * math.tau for k in range(48)]]
    cx = sum(q[0] for q in ring) / 48; cy = sum(q[1] for q in ring) / 48; rad = (max(q[0] for q in ring) - min(q[0] for q in ring)) / 2
    ppl = ""
    for name, dx, dy, face, flip, sc in (("n2", -0.55, -0.15, "angry", False, .58), ("n3", 0.58, -0.2, "serious", True, .58), ("n1", 0.0, -0.42, "angry", False, .66)):
        s_ = sc * rad / 152
        ppl += C.place(C.person(name, "front", face=face, arms="down" if name != "n1" else "flashlight", prop="flashlight" if name == "n1" else None, rim="#ff9a7a"),
                       cx + dx * rad, cy + dy * rad + 924 * s_, s_, flip)
    p = I.bunker_up(cam, people_svg=ppl)
    save("k6_up", p, sky="#0c0a0a", particles=("dust", 40), vignette=0.7)


def walk_test(n=48, fps=24):
    """Проверка походки: 2 секунды, герой идёт вправо по рынку."""
    import subprocess
    d = f"{OUT}/walk"; os.makedirs(d, exist_ok=True)
    cam = I.Cam(x=0.2, y=1.15, z=1.4, pitch=0.04, f=820)
    stride = 0.42 * 2 * 412 * 2 * M * 0.98  # метров за цикл: ноги не скользят
    for i in range(n):
        ph = i / n * math.tau * 2
        p = I.market(cam)
        put(p, C.person("hero", "side", face="neutral", phase=ph, prop="bags", rim="#ffc890"), -1.2 + stride * ph / math.tau, -0.55)
        open(f"{d}/f{i:03d}.svg", "w").write(p.svg(sky="#2c2c4a", particles=("snow", 140), vignette=0.6))
    return d


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if "walk" in sys.argv:
        print(walk_test())
    else:
        frames()
