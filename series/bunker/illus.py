#!/usr/bin/env python3
"""Нарисованные фоны в стиле референса (векторная иллюстрация с настоящей перспективой).

Каждый предмет задаётся в мировых координатах (метры) и проецируется камерой в кадр 1080x1920,
поэтому перспектива верная и камеру потом можно двигать. Рисовка: плоские цвета с мягкими градиентами,
тонкий тёмный контур, тёплый свет ламп со свечением, холодные тени, зерно, пыль/снег, виньетка.
"""
import math, random

W, H = 1080, 1920
INK = "#2a221c"


class Cam:
    def __init__(self, x=0.0, y=1.4, z=0.0, yaw=0.0, pitch=0.0, f=900, vx=540, vy=960):
        self.x, self.y, self.z, self.yaw, self.pitch, self.f, self.vx, self.vy = x, y, z, yaw, pitch, f, vx, vy

    def p(self, X, Y, Z):
        """Камера смотрит в сторону -Z (вглубь сцены). yaw > 0: поворот вправо, pitch > 0: взгляд вверх."""
        dx, dy, fw = X - self.x, Y - self.y, self.z - Z
        cy, sy = math.cos(self.yaw), math.sin(self.yaw)
        dx, fw = dx * cy - fw * sy, dx * sy + fw * cy
        cp, sp = math.cos(self.pitch), math.sin(self.pitch)
        dy, fw = dy * cp - fw * sp, dy * sp + fw * cp
        fw = max(fw, 0.05)
        return (self.vx + self.f * dx / fw, self.vy - self.f * dy / fw, fw)

    def cs(self, X, Y, Z):
        dx, dy, fw = X - self.x, Y - self.y, self.z - Z
        cy, sy = math.cos(self.yaw), math.sin(self.yaw)
        dx, fw = dx * cy - fw * sy, dx * sy + fw * cy
        cp, sp = math.cos(self.pitch), math.sin(self.pitch)
        return (dx, dy * cp - fw * sp, dy * sp + fw * cp)

    def proj(self, c):
        return (self.vx + self.f * c[0] / c[2], self.vy - self.f * c[1] / c[2], c[2])


def clip_near(C, near=0.12):
    """Обрезка многоугольника по ближней плоскости камеры (Сазерленд — Ходжман)."""
    out = []
    for i in range(len(C)):
        a, b = C[i], C[(i + 1) % len(C)]
        ina, inb = a[2] >= near, b[2] >= near
        if ina:
            out.append(a)
        if ina != inb:
            t = (near - a[2]) / (b[2] - a[2]); out.append(tuple(a[k] + (b[k] - a[k]) * t for k in range(3)))
    return out


def hexrgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def shade(c, k):
    r, g, b = hexrgb(c); return "#%02x%02x%02x" % tuple(max(0, min(255, int(v * k))) for v in (r, g, b))


def mix(a, b, u):
    A, B = hexrgb(a), hexrgb(b); return "#%02x%02x%02x" % tuple(int(A[i] + (B[i] - A[i]) * u) for i in range(3))


class Pic:
    """Сборщик кадра: полигоны с глубиной (рисуются от дальних к ближним), градиенты, свечения."""
    def __init__(self, cam, lights=(), soft=True, base=0.42):
        self.cam, self.items, self.defs, self.top, self.n = cam, [], [], [], 0
        self.lights, self.soft, self.base = lights, soft, base  # lights: [(X,Y,Z, радиус, цвет)]

    def lit(self, color, X, Y, Z, base=None):
        base = self.base if base is None else base
        k = base
        for lx, ly, lz, r, _c in self.lights:
            d = math.dist((X, Y, Z), (lx, ly, lz)); k += (1 - base) * max(0.0, 1 - d / r) ** 1.4
        return shade(color, min(1.25, k))

    def gid(self):
        self.n += 1; return f"g{self.n}"

    def poly(self, pts3, color, stroke=True, grad=None, op=1.0, depth=None, lw=1.6, emissive=False):
        C = clip_near([self.cam.cs(*q) for q in pts3])
        if len(C) < 3:
            return
        P = [self.cam.proj(c) for c in C]
        cx = sum(q[0] for q in pts3) / len(pts3); cy = sum(q[1] for q in pts3) / len(pts3); cz = sum(q[2] for q in pts3) / len(pts3)
        fill = color if emissive else self.lit(color, cx, cy, cz)
        d = " ".join(f"{x:.1f},{y:.1f}" for x, y, _ in P)
        fs = f'fill="{fill}"'
        if self.lights and not emissive and grad is None and self.soft:
            lx, ly, lz, lr, lc = max(self.lights, key=lambda L: L[3] / (1 + math.dist((cx, cy, cz), L[:3])))
            q = self.cam.p(lx, ly, lz); dep = max(0.3, sum(p[2] for p in P) / len(P))
            R = lr * self.cam.f / dep * 1.15; g = self.gid()
            warm = mix(color, lc, 0.25)
            self.defs.append(f'<radialGradient id="{g}" gradientUnits="userSpaceOnUse" cx="{q[0]:.1f}" cy="{q[1]:.1f}" r="{R:.1f}"><stop offset="0" stop-color="{shade(warm, 1.22)}"/>'
                             f'<stop offset=".45" stop-color="{shade(mix(color, lc, 0.12), 0.85)}"/><stop offset="1" stop-color="{shade(mix(color, "#1a2030", 0.25), self.base * 0.8)}"/></radialGradient>')
            fs = f'fill="url(#{g})"'
        if grad:  # вертикальный градиент: низ темнее/светлее
            g = self.gid(); top, bot = self.lit(grad[0], cx, cy, cz), self.lit(grad[1], cx, cy, cz)
            ys = [p[1] for p in P]
            self.defs.append(f'<linearGradient id="{g}" gradientUnits="userSpaceOnUse" x1="0" y1="{min(ys):.1f}" x2="0" y2="{max(ys):.1f}"><stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bot}"/></linearGradient>')
            fs = f'fill="url(#{g})"'
        st = f' stroke="{INK}" stroke-width="{lw * min(2.5, 3.0 / max(0.8, min(p[2] for p in P))):.2f}" stroke-linejoin="round"' if stroke else ""
        self.items.append((depth if depth is not None else max(p[2] for p in P), f'<polygon points="{d}" {fs}{st} opacity="{op}"/>'))

    def raw(self, depth, svg):
        self.items.append((depth, svg))

    def box(self, x0, x1, y0, y1, z0, z1, color, top=None, side=None, stroke=True, emissive=False):
        """Ящик: рисуем видимые грани (перед, верх/низ, бок к камере)."""
        c = self.cam
        faces = []
        if c.z < z0: faces.append(([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)], color))
        if c.z > z1: faces.append(([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], color))
        if c.y > y1: faces.append(([(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], top or shade(color, 1.15)))
        if c.y < y0: faces.append(([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], shade(color, 0.7)))
        if c.x < x0: faces.append(([(x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1)], side or shade(color, 0.8)))
        if c.x > x1: faces.append(([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], side or shade(color, 0.8)))
        dmax = max(c.p(x, y, z)[2] for x in (x0, x1) for y in (y0, y1) for z in (z0, z1))
        for pts, col in faces:
            self.poly(pts, col, stroke, depth=dmax, emissive=emissive)

    def jar(self, X, Y, Z, r, h, body, lid="#c8a03a", label="#e8dcc0", fill=None):
        """Банка/бутылка: тело-прямоугольник по проекции, крышка-эллипс, этикетка, блик."""
        c = self.cam; xl, yb, d = c.p(X - r, Y, Z); xr, _, _ = c.p(X + r, Y, Z); _, yt, _ = c.p(X, Y + h, Z)
        w = xr - xl; ry = max(1.5, w * 0.18); col = self.lit(body, X, Y, Z); lc = self.lit(lid, X, Y + h, Z); lab = self.lit(label or body, X, Y, Z)
        lw = max(0.6, 1.4 / d * 1.8)
        s = (f'<path d="M{xl:.1f} {yb:.1f} L{xl:.1f} {yt + ry:.1f} Q{xl:.1f} {yt:.1f} {xl + w / 2:.1f} {yt:.1f} Q{xr:.1f} {yt:.1f} {xr:.1f} {yt + ry:.1f} L{xr:.1f} {yb:.1f} Q{xl + w / 2:.1f} {yb + ry:.1f} {xl:.1f} {yb:.1f} Z" fill="{col}" stroke="{INK}" stroke-width="{lw:.2f}"/>'
             f'<rect x="{xl:.1f}" y="{yt + (yb - yt) * 0.38:.1f}" width="{w:.1f}" height="{(yb - yt) * 0.3:.1f}" fill="{lab}" opacity=".9"/>'
             f'<ellipse cx="{xl + w / 2:.1f}" cy="{yt:.1f}" rx="{w / 2 * 0.9:.1f}" ry="{ry * 0.8:.1f}" fill="{lc}" stroke="{INK}" stroke-width="{lw:.2f}"/>'
             f'<rect x="{xl + w * 0.16:.1f}" y="{yt + ry * 1.5:.1f}" width="{max(1, w * 0.1):.1f}" height="{(yb - yt) * 0.55:.1f}" fill="#fff" opacity=".28"/>')
        if label is None:
            s = s.replace(f'fill="{lab}" opacity=".9"', 'fill="none" opacity="0"')
        if fill:
            hh = yb - yt; c2 = shade(col, 1.35); c3 = shade(col, .7)
            if fill == "pickle":
                s += "".join(f'<ellipse cx="{xl + w * u:.1f}" cy="{yt + hh * .58:.1f}" rx="{w * .11:.1f}" ry="{hh * .3:.1f}" fill="{c2}" stroke="{c3}" stroke-width="{lw * .6:.2f}"/>' for u in (.28, .52, .74))
            elif fill == "tomato":
                s += "".join(f'<circle cx="{xl + w * u:.1f}" cy="{yt + hh * v:.1f}" r="{w * .17:.1f}" fill="{c2}" stroke="{c3}" stroke-width="{lw * .6:.2f}"/>' for u, v in ((.3, .4), (.68, .45), (.45, .72), (.75, .8), (.25, .82)))
            else:
                s += f'<rect x="{xl + w * .1:.1f}" y="{yt + hh * .5:.1f}" width="{w * .8:.1f}" height="{hh * .2:.1f}" fill="{c3}" opacity=".5"/>'
            s += f'<rect x="{xl + w * 0.14:.1f}" y="{yt + ry * 1.5:.1f}" width="{max(1, w * 0.08):.1f}" height="{hh * 0.6:.1f}" fill="#fff" opacity=".35"/>'
        self.raw(d, s)

    def glow(self, X, Y, Z, r, color, op=0.55):
        x, y, d = self.cam.p(X, Y, Z); g = self.gid(); R = r * self.cam.f / d
        op *= getattr(self, "glow_k", 1.0)
        if R > 650:  # камера вплотную к лампе: не заливать весь кадр
            op *= 650 / R; R = 650 + (R - 650) * 0.3
        self.defs.append(f'<radialGradient id="{g}"><stop offset="0" stop-color="{color}" stop-opacity="{op}"/><stop offset=".45" stop-color="{color}" stop-opacity="{op * 0.35}"/><stop offset="1" stop-color="{color}" stop-opacity="0"/></radialGradient>')
        self.top.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{R:.1f}" fill="url(#{g})" style="mix-blend-mode:screen"/>')

    def svg(self, sky="#101014", grade=("#2a3550", "#ffb060"), grain=0.07, vignette=0.55, particles=None, ptime=0.0, overlay="", dof=None):
        items = sorted(self.items, key=lambda t: -t[0])
        if dof:  # (фокус в метрах, сила): чем дальше за фокусом, тем сильнее размытие; группы идут подряд, т.к. отсортированы по глубине
            focus, k = dof; parts_, cur, buf, used = [], None, [], set()
            for d_, s_ in items:
                lv = round(min(9.0, max(0.0, (d_ - focus - 0.5) * k)) * 2) / 2
                if lv != cur and buf:
                    parts_.append(f'<g filter="url(#dof{str(cur).replace(".", "_")})">{"".join(buf)}</g>' if cur else "".join(buf)); buf = []
                cur = lv; buf.append(s_); used.add(lv)
            if buf:
                parts_.append(f'<g filter="url(#dof{str(cur).replace(".", "_")})">{"".join(buf)}</g>' if cur else "".join(buf))
            body = "".join(parts_)
            self.defs += [f'<filter id="dof{str(lv).replace(".", "_")}" x="-5%" y="-5%" width="110%" height="110%"><feGaussianBlur stdDeviation="{lv}" edgeMode="duplicate"/></filter>' for lv in used if lv]
        else:
            body = "".join(s for _, s in items)
        defs = "".join(self.defs)
        rnd = random.Random(7)
        parts = ""
        if particles:
            kind, n = particles
            for _ in range(n):
                x, y, r = rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(1.5, 5) if kind == "snow" else rnd.uniform(0.8, 2.6)
                v = r * (38 if kind == "snow" else 6); ph = rnd.uniform(0, 6.3)
                y = (y + v * ptime) % H; x = (x + (18 if kind == "snow" else 10) * math.sin(ptime * 0.8 + ph)) % W
                parts += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{"#ffffff" if kind == "snow" else "#ffe6b8"}" opacity="{rnd.uniform(0.35, 0.9) if kind == "snow" else rnd.uniform(0.15, 0.5):.2f}"/>'
        gr = f'<rect width="{W}" height="{H}" filter="url(#grain)" opacity="{grain}" style="mix-blend-mode:overlay"/>' if grain else ""
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><defs>{defs}'
                f'<filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="3"/><feColorMatrix values="0 0 0 0 .5  0 0 0 0 .5  0 0 0 0 .5  0 0 0 1.2 -.35"/></filter>'
                f'<radialGradient id="vig" cx="50%" cy="48%" r="72%"><stop offset=".55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="{vignette}"/></radialGradient>'
                f'<linearGradient id="grade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{grade[0]}" stop-opacity=".18"/><stop offset="1" stop-color="{grade[1]}" stop-opacity=".08"/></linearGradient></defs>'
                f'<rect width="{W}" height="{H}" fill="{sky}"/>{body}{"".join(self.top)}'
                f'<rect width="{W}" height="{H}" fill="url(#grade)" style="mix-blend-mode:soft-light"/>{gr}{parts}'
                f'<rect width="{W}" height="{H}" fill="url(#vig)"/>{overlay}</svg>')


# ---------- материалы ----------
CONC, CONC_D, METAL, WOOD, BRICK = "#7d7a6e", "#4f4c45", "#6c737a", "#7a5534", "#8a4a38"
JAR_COLS = ["#c0602a", "#7a8a2a", "#a8322a", "#d8a03a", "#6a8a4a", "#b84a3a"]


def concrete_wall(pic, pts, seams_u=(), seams_v=(), col=CONC, plane="z", at=0.0, bolts=True):
    pic.poly(pts, col)
    # стыки плит и болты рисуем отдельными линиями в мировых координатах
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; zs = [p[2] for p in pts]
    for u in seams_u:
        a = (u, min(ys), at) if plane == "z" else (at, min(ys), u); b = (u, max(ys), at) if plane == "z" else (at, max(ys), u)
        A, B = pic.cam.p(*a), pic.cam.p(*b); pic.raw(max(A[2], B[2]) - 0.01, f'<line x1="{A[0]:.1f}" y1="{A[1]:.1f}" x2="{B[0]:.1f}" y2="{B[1]:.1f}" stroke="#3a342c" stroke-width="{3.2 / max(A[2], B[2]) * 1.6:.2f}" opacity=".7"/>')
    for v in seams_v:
        a = (min(xs), v, at) if plane == "z" else (at, v, min(zs)); b = (max(xs), v, at) if plane == "z" else (at, v, max(zs))
        A, B = pic.cam.p(*a), pic.cam.p(*b); pic.raw(max(A[2], B[2]) - 0.01, f'<line x1="{A[0]:.1f}" y1="{A[1]:.1f}" x2="{B[0]:.1f}" y2="{B[1]:.1f}" stroke="#3a342c" stroke-width="{3.2 / max(A[2], B[2]) * 1.6:.2f}" opacity=".7"/>')
    if bolts:
        for u in seams_u:
            for v in [ys[0] + (max(ys) - min(ys)) * k for k in (0.15, 0.85)]:
                for du in (-0.12, 0.12):
                    q = (u + du, v, at) if plane == "z" else (at, v, u + du); x, y, d = pic.cam.p(*q)
                    pic.raw(d - 0.02, f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{5 / d:.1f}" fill="#3e3a34"/>')


def shelf_unit(pic, x, z0, z1, side=-1, levels=(0.35, 0.85, 1.35, 1.85), seed=1, kind="pantry"):
    """Стеллаж вдоль стены: стойки, полки, банки/консервы/коробки."""
    rnd = random.Random(seed); depth = 0.45; xin = x - side * depth
    for z in (z0, z1):
        pic.box(min(x, xin) - 0.02, min(x, xin) + 0.02 if side < 0 else max(x, xin) + 0.02, 0, levels[-1] + 0.15, z - 0.02, z + 0.02, METAL)
        pic.box(max(x, xin) - 0.02, max(x, xin) + 0.02, 0, levels[-1] + 0.15, z - 0.02, z + 0.02, METAL)
    for y in levels:
        pic.box(min(x, xin), max(x, xin), y - 0.025, y, z0, z1, "#6d747b", top="#8a9198")
        z = z0 + 0.06
        while z < z1 - 0.08:
            t = rnd.random()
            cx = xin + side * 0.18
            if kind == "pantry":
                if t < 0.55:
                    r = rnd.uniform(0.045, 0.06); pic.jar(cx + side * rnd.uniform(-0.05, 0.05), y, z, r, rnd.uniform(0.12, 0.2), rnd.choice(JAR_COLS)); z += r * 2 + 0.02
                elif t < 0.85:
                    r = 0.04; pic.jar(cx, y, z, r, 0.1, "#a8b0b6", lid="#c8ccd0", label=rnd.choice(["#c0392b", "#2c6aa0", "#d8a03a"])); z += 0.1
                else:
                    pic.box(cx - 0.14, cx + 0.14, y, y + 0.2, z, z + 0.26, "#b08a5a", top="#c8a070"); z += 0.3
            else:
                col = rnd.choice(["#c0392b", "#2c6aa0", "#e0a72a", "#3a9a5a", "#e07030", "#7a3aa0", "#f0f0e8"])
                if t < 0.6:
                    h = rnd.uniform(0.18, 0.3); pic.box(cx - 0.1, cx + 0.1, y, y + h, z, z + 0.14, col, top=shade(col, 1.2)); z += 0.16
                else:
                    r = 0.04; pic.jar(cx, y, z, r, rnd.uniform(0.18, 0.28), col, lid="#e8e8e8", label="#ffffff"); z += 0.1


def wall_rack(pic, x0, x1, zb, levels=(0.3, 0.75, 1.2, 1.65, 2.1), seed=2):
    """Стеллаж у задней стены лицом к камере, полный банок с соленьями (как в референсе)."""
    rnd = random.Random(seed); dz = 0.42
    for x in (x0, x1, (x0 + x1) / 2):
        pic.box(x - 0.025, x + 0.025, 0, levels[-1] + 0.2, zb + dz - 0.03, zb + dz + 0.02, "#5a4632")
    for y in levels:
        pic.box(x0, x1, y - 0.035, y, zb, zb + dz, "#7a5a3a", top="#8e6c48")
        x = x0 + 0.07
        while x < x1 - 0.07:
            t = rnd.random()
            if t < 0.4:
                r = rnd.uniform(.055, .07); pic.jar(x + r, y, zb + 0.24, r, rnd.uniform(.17, .24), rnd.choice(["#6a8a2a", "#7a9a3a", "#5a7a2a"]), lid=rnd.choice(["#e8e4d8", "#c8a03a"]), label=None, fill="pickle")
            elif t < 0.7:
                r = rnd.uniform(.055, .07); pic.jar(x + r, y, zb + 0.24, r, rnd.uniform(.15, .22), rnd.choice(["#b8321e", "#c8422a", "#a82a1a"]), lid=rnd.choice(["#e8e4d8", "#c8a03a"]), label=None, fill="tomato")
            elif t < 0.85:
                r = .05; pic.jar(x + r, y, zb + 0.24, r, .13, rnd.choice(["#d89a2a", "#8a2a3a", "#c86a2a"]), lid="#e8e4d8", label=None, fill="jam")
            else:
                r = .042; pic.jar(x + r, y, zb + 0.26, r, .11, "#a8b0b6", lid="#c8ccd0", label=rnd.choice(["#c0392b", "#2c6aa0", "#d8a03a"]))
            x += 2 * r + 0.025


# ---------- детали ----------
def ftext(pic, X, Y, Z, text, size, col="#2a221c", depth_bias=-0.03, weight=800, anchor="middle"):
    """Надпись на передней грани (размер в метрах, масштаб по глубине)."""
    x, y, d = pic.cam.p(X, Y, Z)
    pic.raw(d + depth_bias, f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-family="Inter, DejaVu Sans" font-weight="{weight}" font-size="{size * pic.cam.f / d:.1f}" fill="{col}">{text}</text>')


def sack(pic, X, Z, label="МУКА", col="#d8c8a0", w=0.5, h=0.55):
    pic.box(X - w / 2, X + w / 2, 0, h, Z - 0.18, Z + 0.18, col, top=shade(col, 1.08))
    x, y, d = pic.cam.p(X, h, Z); r = 0.12 * pic.cam.f / d
    pic.raw(d - 0.05, f'<path d="M{x - r:.1f} {y:.1f} Q{x} {y - r * 1.6:.1f} {x + r:.1f} {y:.1f}" fill="{col}" stroke="{INK}" stroke-width="{max(.6, 3 / d):.1f}"/><line x1="{x - r * .5:.1f}" y1="{y - r * .4:.1f}" x2="{x + r * .5:.1f}" y2="{y - r * .4:.1f}" stroke="#6a4a2a" stroke-width="{max(.6, 4 / d):.1f}"/>')
    ftext(pic, X, h * 0.45, Z + 0.19, label, 0.09, "#4a3a28")


def water_pack(pic, X, Z, n=3, rows=2):
    for j in range(rows):
        for k in range(n):
            pic.jar(X + k * 0.2, 0, Z - j * 0.2, 0.09, 0.34, "#5aa0d0", lid="#2c6aa0", label="#e8f0f4")


def crate_text(pic, x0, x1, y0, y1, z0, z1, text, col="#94693e"):
    pic.box(x0, x1, y0, y1, z0, z1, WOOD, top=col)
    ftext(pic, (x0 + x1) / 2, (y0 + y1) / 2 - 0.03, z1 + 0.005, text, 0.075, "#2a1a0c")


def calendar(pic, X, Y, Z, marks=22):
    c = pic.cam; w, h = 0.5, 0.62
    pic.box(X - w / 2, X + w / 2, Y - h, Y, Z, Z + 0.01, "#f2ecdc", top="#f2ecdc")
    pic.box(X - w / 2, X + w / 2, Y - 0.12, Y, Z + 0.01, Z + 0.015, "#b8321e")
    ftext(pic, X, Y - 0.08, Z + 0.02, "2026", 0.06, "#ffffff")
    for k in range(35):
        cx_, cy_ = X - w / 2 + 0.05 + (k % 7) * 0.065, Y - 0.19 - (k // 7) * 0.085
        A = c.p(cx_, cy_, Z + 0.02); r = 0.022 * c.f / A[2]
        if k < marks:
            pic.raw(A[2] - 0.05, f'<path d="M{A[0] - r:.1f} {A[1] - r:.1f} L{A[0] + r:.1f} {A[1] + r:.1f} M{A[0] + r:.1f} {A[1] - r:.1f} L{A[0] - r:.1f} {A[1] + r:.1f}" stroke="#c0302a" stroke-width="{max(.8, r * .35):.1f}"/>')
        else:
            pic.raw(A[2] - 0.05, f'<rect x="{A[0] - r:.1f}" y="{A[1] - r:.1f}" width="{2 * r:.1f}" height="{2 * r:.1f}" fill="none" stroke="#8a8478" stroke-width="{max(.5, r * .12):.1f}"/>')


def wall_clock(pic, X, Y, Z):
    x, y, d = pic.cam.p(X, Y, Z); r = 0.16 * pic.cam.f / d
    pic.raw(d - 0.05, f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="#f4f0e4" stroke="{INK}" stroke-width="{r * .12:.1f}"/><line x1="{x:.1f}" y1="{y:.1f}" x2="{x:.1f}" y2="{y - r * .6:.1f}" stroke="{INK}" stroke-width="{r * .1:.1f}"/><line x1="{x:.1f}" y1="{y:.1f}" x2="{x + r * .45:.1f}" y2="{y + r * .2:.1f}" stroke="{INK}" stroke-width="{r * .1:.1f}"/>')


def radio_table(pic, X, Z):
    pic.box(X - 0.5, X + 0.5, 0.72, 0.78, Z - 0.35, Z + 0.35, WOOD, top="#94693e")
    for dx in (-0.45, 0.42):
        for dz in (-0.3, 0.27):
            pic.box(X + dx, X + dx + 0.05, 0, 0.72, Z + dz, Z + dz + 0.05, shade(WOOD, .8))
    pic.box(X - 0.28, X + 0.12, 0.78, 1.02, Z - 0.15, Z + 0.1, "#4a5a3a", top="#5c6c4a")
    x, y, d = pic.cam.p(X - 0.12, 0.9, Z + 0.11); r = 0.05 * pic.cam.f / d
    pic.raw(d - 0.05, f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="#d8c890" stroke="{INK}" stroke-width="{max(.6, r * .15):.1f}"/>')
    a, b = pic.cam.p(X + 0.08, 1.02, Z), pic.cam.p(X + 0.3, 1.5, Z - 0.05)
    pic.raw(a[2] - 0.05, f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="#222" stroke-width="{max(1, 6 / a[2]):.1f}"/>')
    pic.jar(X + 0.3, 0.78, Z, 0.05, 0.12, "#e8e4d8", lid="#e8e4d8", label="#c0392b")
    pic.box(X - 0.45, X - 0.3, 0.78, 0.8, Z - 0.1, Z + 0.15, "#f2ecdc")


def sag(pic, a3, b3, col="#151210", w=4, drop=0.18, depth=None):
    a, b = pic.cam.p(*a3), pic.cam.p(*b3); m = pic.cam.p((a3[0] + b3[0]) / 2, (a3[1] + b3[1]) / 2 - drop, (a3[2] + b3[2]) / 2)
    pic.raw(depth if depth is not None else max(a[2], b[2]) - 0.05, f'<path d="M{a[0]:.1f} {a[1]:.1f} Q{2 * m[0] - (a[0] + b[0]) / 2:.1f} {2 * m[1] - (a[1] + b[1]) / 2:.1f} {b[0]:.1f} {b[1]:.1f}" fill="none" stroke="{col}" stroke-width="{max(1.2, w * 3 / m[2]):.1f}"/>')


def bunker_details(pic):
    """Обжитость бункера: мешки, вода, ящики с надписями, календарь с крестиками, часы, стол с рацией, коврик, провода."""
    for k, (x, lab, col) in enumerate(((1.75, "МУКА", "#e0d4b4"), (2.3, "РИС", "#d8ccb0"), (2.85, "САХАР", "#e8e0cc"))):
        sack(pic, x, -3.6, lab, col)
    water_pack(pic, -0.15, -3.75, n=2, rows=2)
    crate_text(pic, 1.8, 2.22, 0, 0.34, -4.35, -3.95, "ТУШЁНКА")
    crate_text(pic, 2.25, 2.67, 0, 0.34, -4.35, -3.95, "ГРЕЧКА")
    crate_text(pic, 2.0, 2.42, 0.34, 0.68, -4.35, -3.95, "ИРП")
    calendar(pic, 0.15, 2.05, -4.39)
    wall_clock(pic, 0.15, 2.45, -4.39)
    radio_table(pic, 2.55, -1.0)
    x0, x1, z0, z1 = -1.4, 0.6, -2.4, -0.8
    pic.poly([(x0, 0.005, z1), (x1, 0.005, z1), (x1, 0.005, z0), (x0, 0.005, z0)], "#7a3a2a", depth=96)
    pic.poly([(x0 + 0.12, 0.006, z1 - 0.12), (x1 - 0.12, 0.006, z1 - 0.12), (x1 - 0.12, 0.006, z0 + 0.12), (x0 + 0.12, 0.006, z0 + 0.12)], "#9a5a3a", depth=95.9)
    for k in range(4):
        sag(pic, (-3.1 + k * 1.5, 2.6, -4.38), (-1.6 + k * 1.5, 2.6, -4.38), drop=0.12)
    sag(pic, (2.9, 2.5, -4.38), (3.15, 1.0, -1.0), col="#2a2a2a", drop=0.3)
    ftext(pic, -1.6, 2.35, -4.38, "ГРАФИК ДЕЖУРСТВ", 0.07, "#e8e2d0")


def hanging_lamp(pic, X, Y, Z, color="#ffcf8a"):
    a, b = pic.cam.p(X, Y + 0.45, Z), pic.cam.p(X, Y, Z)
    pic.raw(b[2] - 0.05, f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="#1c1916" stroke-width="{3 / b[2] * 1.5:.1f}"/>')
    x, y, d = pic.cam.p(X, Y - 0.08, Z); r = 0.085 * pic.cam.f / d
    pic.raw(d - 0.05, f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{r:.1f}" ry="{r * 1.2:.1f}" fill="#fff4dc"/>'
                      f'<g stroke="#2a2420" stroke-width="{r * 0.12:.1f}" fill="none"><ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{r * 1.15:.1f}" ry="{r * 1.35:.1f}"/><line x1="{x:.1f}" y1="{y - r * 1.35:.1f}" x2="{x:.1f}" y2="{y + r * 1.35:.1f}"/><line x1="{x - r * 1.15:.1f}" y1="{y:.1f}" x2="{x + r * 1.15:.1f}" y2="{y:.1f}"/></g>'
                      f'<rect x="{x - r * 0.6:.1f}" y="{y - r * 1.6:.1f}" width="{r * 1.2:.1f}" height="{r * 0.4:.1f}" fill="#3a3530"/>')
    pic.glow(X, Y - 0.08, Z, 1.0, color, 0.5)


# ---------- сцены ----------
def bunker(cam, hatch_open=False, torch=False, red=False):
    """Бункер: бетон, стеллажи с банками слева, короб вентиляции, люк в потолке с лестницей, лампа, проём в техкомнату справа."""
    L = [(-0.4, 2.35, -1.6, 4.2, "#ffb860")] + ([(1.0, 2.7, -3.0, 3.5, "#ff5030")] if red else [])
    pic = Pic(cam, L, base=0.32)
    Wl, Wr, Hc, Zb, Zf = -3.2, 3.2, 2.8, -4.4, 2.0
    concrete_wall(pic, [(Wl, 0, Zb), (Wr, 0, Zb), (Wr, Hc, Zb), (Wl, Hc, Zb)], seams_u=(-1.6, 0, 1.6), seams_v=(1.4,), at=Zb)
    concrete_wall(pic, [(Wl, 0, Zf), (Wl, 0, Zb), (Wl, Hc, Zb), (Wl, Hc, Zf)], seams_u=(-0.4, -2.4), seams_v=(1.4,), plane="x", at=Wl)
    # правая стена с проёмом
    for z0, z1 in ((Zf, -1.3), (-2.4, Zb)):
        concrete_wall(pic, [(Wr, 0, z0), (Wr, 0, z1), (Wr, Hc, z1), (Wr, Hc, z0)], seams_u=((z0 + z1) / 2,), seams_v=(1.4,), plane="x", at=Wr)
    pic.poly([(Wr, 2.1, -1.3), (Wr, 2.1, -2.4), (Wr, Hc, -2.4), (Wr, Hc, -1.3)], CONC)
    pic.poly([(Wr + 0.01, 0, -1.3), (Wr + 0.01, 0, -2.4), (Wr + 0.01, 2.1, -2.4), (Wr + 0.01, 2.1, -1.3)], "#c89858", stroke=False, depth=8)
    pic.glow(Wr + 0.5, 1.4, -1.85, 1.2, "#ffc070", 0.35)
    # пол и потолок
    pic.poly([(Wl, 0, Zf), (Wr, 0, Zf), (Wr, 0, Zb), (Wl, 0, Zb)], CONC_D, depth=99)
    for x in (-1.6, 0, 1.6):
        A, B = cam.p(x, 0, Zf), cam.p(x, 0, Zb); pic.raw(98, f'<line x1="{A[0]:.1f}" y1="{A[1]:.1f}" x2="{B[0]:.1f}" y2="{B[1]:.1f}" stroke="#2e2a24" stroke-width="2.5" opacity=".6"/>')
    for z in (0.0, -1.6, -3.0):
        A, B = cam.p(Wl, 0, z), cam.p(Wr, 0, z); pic.raw(98, f'<line x1="{A[0]:.1f}" y1="{A[1]:.1f}" x2="{B[0]:.1f}" y2="{B[1]:.1f}" stroke="#2e2a24" stroke-width="2.5" opacity=".6"/>')
    x, y, d = cam.p(0.6, 0, -0.6); pic.raw(97, f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{1.0 * cam.f / d:.1f}" ry="{0.25 * cam.f / d:.1f}" fill="#4a4a50" opacity=".35"/>')
    pic.poly([(Wl, Hc, Zf), (Wr, Hc, Zf), (Wr, Hc, Zb), (Wl, Hc, Zb)], "#6e675d", depth=99)
    # короб вентиляции вдоль левого угла потолка
    for z in [Zf - k * 0.5 for k in range(13)]:
        pic.box(-2.75, -2.25, 2.35, 2.75, z - 0.5, z, "#9aa1a8", top="#b8bec4", side="#7e858c")
    # кабели
    for dx, col in ((-1.5, "#141210"), (-1.38, "#5a2420")):
        A, B = cam.p(dx, Hc - 0.06, Zf), cam.p(dx, Hc - 0.06, Zb); pic.raw(50, f'<line x1="{A[0]:.1f}" y1="{A[1]:.1f}" x2="{B[0]:.1f}" y2="{B[1]:.1f}" stroke="{col}" stroke-width="5"/>')
    # стеллажи слева
    shelf_unit(pic, Wl, -0.9, 0.7, side=-1, seed=3); shelf_unit(pic, Wl, -2.8, -1.2, side=-1, seed=5)
    # ящики и канистры у задней стены справа
    for x0, y0 in ((1.8, 0), (2.25, 0), (2.0, 0.34)):
        pic.box(x0, x0 + 0.42, y0, y0 + 0.34, -4.35, -3.95, WOOD, top="#94693e")
    pic.box(2.75, 3.05, 0, 0.42, -3.5, -3.3, "#4a5a3a", top="#5c6c4a")
    # огнетушитель и щиток на правой стене
    pic.box(3.05, 3.2, 0.65, 1.15, 0.1, 0.25, "#a8281e", top="#c03a2a")
    pic.box(3.12, 3.2, 1.45, 1.95, -3.7, -3.2, "#6a7076")
    wall_rack(pic, -3.0, -0.3, -4.4)
    # лавка
    pic.box(-2.7, -0.4, 0.42, 0.48, -3.75, -3.35, WOOD, top="#94693e")
    for x0 in (-2.6, -0.6):
        pic.box(x0, x0 + 0.08, 0, 0.42, -3.7, -3.4, shade(WOOD, 0.8))
    # люк в потолке и лестница
    hx, hz, r = 1.0, -3.0, 0.42
    ring = [cam.p(hx + math.cos(a) * r, Hc - 0.005, hz + math.sin(a) * r) for a in [k / 40 * math.tau for k in range(40)]]
    dring = max(q[2] for q in ring)
    inner = "#2a0e0a" if (hatch_open and red) else ("#0a0908" if hatch_open else "#3d434a")
    pic.raw(dring - 0.1, f'<polygon points="{" ".join(f"{q[0]:.1f},{q[1]:.1f}" for q in ring)}" fill="{inner}" stroke="#20242a" stroke-width="{14 / dring:.1f}"/>')
    if not hatch_open:
        ring2 = [cam.p(hx + math.cos(a) * r * 0.55, Hc - 0.01, hz + math.sin(a) * r * 0.55) for a in [k / 32 * math.tau for k in range(32)]]
        pic.raw(dring - 0.11, f'<polygon points="{" ".join(f"{q[0]:.1f},{q[1]:.1f}" for q in ring2)}" fill="none" stroke="#9aa3ac" stroke-width="{9 / dring:.1f}"/>')
        a, b = cam.p(hx - r * 0.6, Hc - 0.01, hz), cam.p(hx + r * 0.6, Hc - 0.01, hz)
        pic.raw(dring - 0.11, f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="#9aa3ac" stroke-width="{9 / dring:.1f}"/>')
    for dx in (-0.24, 0.24):
        pic.box(hx + dx - 0.025, hx + dx + 0.025, 0, Hc, hz - r + 0.03, hz - r + 0.08, "#5d6670", side="#4a525a")
    for y in [0.3 + k * 0.32 for k in range(8)]:
        pic.box(hx - 0.24, hx + 0.24, y, y + 0.035, hz - r + 0.04, hz - r + 0.075, "#717a84")
    pic.box(1.5, 2.9, 1.15, 1.95, -4.39, -4.36, "#8a6a44", top="#9a7a54")          # щит с инструментами
    for k, (dx, h, col) in enumerate(((-0.75, 0.5, "#555c64"), (-0.55, 0.38, "#a83a2a"), (-0.35, 0.45, "#555c64"), (-0.12, 0.3, "#c8a03a"), (0.1, 0.42, "#555c64"), (0.32, 0.35, "#3a5a8a"))):
        pic.box(dx + 2.4, dx + 2.47, 1.85 - h, 1.85, -4.35, -4.33, col)
    for x0, col in ((-3.0, "#3c5a34"), (-2.7, "#a8321e")):                          # канистры
        pic.box(x0, x0 + 0.25, 0, 0.42, 1.0, 1.15, col, top=shade(col, 1.2))
    for x0 in (2.2, 2.6):                                                          # вёдра
        pic.jar(x0, 0, 0.9, 0.16, 0.32, "#8c949c", lid="#5c636a", label="#8c949c")
    for z in [1.8 - k * 0.25 for k in range(26)]:                                  # труба по правой стене
        pic.box(3.05, 3.15, 2.45, 2.55, z - 0.25, z, "#7a6a5a", top="#8a7a6a")
    bunker_details(pic)
    hanging_lamp(pic, -0.4, 2.35, -1.6)
    if torch:
        x, y, d = cam.p(hx + 0.1, Hc + 0.6, hz + 0.1)
        pic.top.append(f'<polygon points="{x - 18:.1f},{y:.1f} {x + 18:.1f},{y:.1f} {x + 420:.1f},1920 {x - 380:.1f},1920" fill="#fff2cc" opacity=".08" style="mix-blend-mode:screen"/>')
    return pic


def bunker_up(cam, people_svg=""):
    """Вид снизу в открытый люк: темнота, красный отсвет сирены, фонарик светит вниз, люди наверху."""
    pic = Pic(cam, [(1.0, 3.6, -2.9, 1.2, "#ff5a3a")], base=0.3)
    Hc, hx, hz, r = 2.8, 1.0, -3.0, 0.42
    pic.poly([(-3.2, Hc, 2), (3.2, Hc, 2), (3.2, Hc, -4.4), (-3.2, Hc, -4.4)], "#3e3a35", depth=90)
    for z in (-1.6, -3.0):
        A, B = cam.p(-3.2, Hc, z), cam.p(3.2, Hc, z); pic.raw(89, f'<line x1="{A[0]:.1f}" y1="{A[1]:.1f}" x2="{B[0]:.1f}" y2="{B[1]:.1f}" stroke="#2e2a24" stroke-width="4" opacity=".6"/>')
    ring = [cam.p(hx + math.cos(a) * r, Hc, hz + math.sin(a) * r) for a in [k / 48 * math.tau for k in range(48)]]
    pts = " ".join(f"{q[0]:.1f},{q[1]:.1f}" for q in ring)
    g = pic.gid()
    pic.defs.append(f'<radialGradient id="{g}" cx="45%" cy="40%" r="65%"><stop offset="0" stop-color="#5a1410"/><stop offset=".6" stop-color="#1e0806"/><stop offset="1" stop-color="#080404"/></radialGradient>'
                    f'<clipPath id="hc"><polygon points="{pts}"/></clipPath>')
    pic.raw(50, f'<polygon points="{pts}" fill="url(#{g})"/>')
    cx = sum(q[0] for q in ring) / len(ring); cy = sum(q[1] for q in ring) / len(ring)
    pic.raw(49, f'<g clip-path="url(#hc)">{people_svg}<circle cx="{cx + 20:.1f}" cy="{cy + 10:.1f}" r="26" fill="#fffbe8"/><circle cx="{cx + 20:.1f}" cy="{cy + 10:.1f}" r="120" fill="#fff3d0" opacity=".25"/></g>')
    pic.raw(48, f'<polygon points="{pts}" fill="none" stroke="#7a838c" stroke-width="22"/><polygon points="{pts}" fill="none" stroke="#3a3e44" stroke-width="8"/>')
    pic.top.append(f'<polygon points="{cx + 2:.1f},{cy + 10:.1f} {cx + 38:.1f},{cy + 10:.1f} {cx + 520:.1f},1920 {cx - 420:.1f},1920" fill="#fff2cc" opacity=".12" style="mix-blend-mode:screen"/>')
    for dx in (-0.24, 0.24):
        pic.box(hx + dx - 0.025, hx + dx + 0.025, 0, Hc, hz - r + 0.03, hz - r + 0.08, "#6a4a48")
    for y in [0.3 + k * 0.32 for k in range(8)]:
        pic.box(hx - 0.24, hx + 0.24, y, y + 0.035, hz - r + 0.04, hz - r + 0.075, "#7a5654")
    return pic


def market(cam):
    """Рынок в сумерках: снег, прилавок под навесом, ящики с овощами, мешки, кирпичная стена, фонарь."""
    pic = Pic(cam, [(0.0, 2.1, -1.2, 4.0, "#ffb070"), (-3.5, 3.2, -3.0, 5.0, "#ffd090")], base=0.4)
    sky = Pic(cam)
    pic.poly([(-8, 0, 4), (8, 0, 4), (8, 0, -6), (-8, 0, -6)], "#d8dde6", grad=("#b8c0d0", "#eef0f4"), stroke=False, depth=99)
    for k in range(-3, 4):
        pic.box(k * 2.2 - 1.1, k * 2.2 + 1.1, 0, 3.2, -4.4, -4.0, BRICK, top="#e8ecf2")
        for v in (0.8, 1.6, 2.4):
            A, B = cam.p(k * 2.2 - 1.1, v, -4.0), cam.p(k * 2.2 + 1.1, v, -4.0)
            pic.raw(A[2] - 0.05, f'<line x1="{A[0]:.1f}" y1="{A[1]:.1f}" x2="{B[0]:.1f}" y2="{B[1]:.1f}" stroke="#5a3022" stroke-width="2" opacity=".5"/>')
    pic.box(-3.0, -1.9, 0, 2.2, -3.95, -3.9, "#3a5a6a")
    pic.box(-1.3, 1.3, 0, 0.85, -1.9, -1.1, WOOD, top="#946a42")
    for x in (-1.25, 1.25):
        pic.box(x - 0.04, x + 0.04, 0, 2.3, -1.15, -1.07, shade(WOOD, 0.8))
    pic.poly([(-1.5, 2.3, -0.9), (1.5, 2.3, -0.9), (1.5, 2.55, -2.1), (-1.5, 2.55, -2.1)], "#b03a2a")
    for k in range(6):
        pic.poly([(-1.5 + k * 0.5, 2.3, -0.9), (-1.25 + k * 0.5, 2.3, -0.9), (-1.25 + k * 0.5, 2.55, -2.1), (-1.5 + k * 0.5, 2.55, -2.1)], "#e8dcc8", stroke=False)
    veg = ["#d06828", "#7a9a3a", "#a8322a", "#d8b04a"]
    for k in range(4):
        x0 = -1.15 + k * 0.58
        pic.box(x0, x0 + 0.5, 0.85, 1.0, -1.8, -1.35, shade(WOOD, 1.1), top="#a8804e")
        for j in range(8):
            pic.jar(x0 + 0.07 + (j % 4) * 0.11, 0.98, -1.75 + (j // 4) * 0.18, 0.05, 0.08, veg[k], lid=veg[k], label=veg[k])
    for x in (-1.9, -1.45):
        pic.box(x - 0.2, x + 0.2, 0, 0.6, -0.9, -0.55, "#b8a27a", top="#ccb88e")
    for sx0, col in ((-4.2, "#3a6a8a"), (3.6, "#6a3a7a")):                       # соседние прилавки
        pic.box(sx0 - 0.9, sx0 + 0.9, 0, 0.85, -2.6, -1.9, WOOD, top="#946a42")
        pic.poly([(sx0 - 1.1, 2.2, -1.7), (sx0 + 1.1, 2.2, -1.7), (sx0 + 1.1, 2.45, -2.8), (sx0 - 1.1, 2.45, -2.8)], col)
        pic.poly([(sx0 - 1.1, 2.45, -2.8), (sx0 + 1.1, 2.45, -2.8), (sx0 + 1.1, 2.5, -2.75), (sx0 - 1.1, 2.5, -2.75)], "#f0f2f6", stroke=False)
    pic.poly([(-1.5, 2.55, -2.1), (1.5, 2.55, -2.1), (1.5, 2.6, -2.05), (-1.5, 2.6, -2.05)], "#f2f4f8", stroke=False)   # снег на навесе
    for k in range(14):                                                            # гирлянда
        x = -1.5 + k * 3.0 / 13; yy = 2.28 - 0.08 * math.sin(k / 13 * math.pi)
        q = cam.p(x, yy, -0.92); pic.raw(q[2] - 0.2, f'<circle cx="{q[0]:.1f}" cy="{q[1]:.1f}" r="{7 / q[2] * 1.6:.1f}" fill="#ffd070"/>'); pic.glow(x, yy, -0.92, 0.25, "#ffc860", 0.5)
    pic.box(0.6, 1.0, 1.0, 1.08, -1.6, -1.35, "#c8ccd0", top="#e0e4e8")
    pic.box(0.7, 0.9, 1.08, 1.3, -1.5, -1.45, "#c0392b")
    for k, (x, txt) in enumerate(((-0.9, "45₽"), (-0.32, "60₽"), (0.26, "80₽"), (0.84, "35₽"))):
        pic.box(x - 0.12, x + 0.12, 1.05, 1.2, -1.34, -1.33, "#d8c090")
        ftext(pic, x, 1.09, -1.32, txt, 0.08, "#2a1a0c")
    for k in range(3):
        sack(pic, -2.0 + k * 0.55, -1.0, ("КАРТОШКА", "ЛУК", "МОРКОВЬ")[k], "#c8a878", w=0.45, h=0.6)
    lx, ly, d = cam.p(-3.5, 3.4, -3.0)
    pic.box(-3.55, -3.45, 0, 3.4, -3.05, -2.95, "#2a2a2e")
    pic.glow(-3.5, 3.4, -3.0, 2.6, "#ffcf8a", 0.65)
    pic.glow(0.0, 2.1, -1.4, 2.2, "#ffb070", 0.45)
    return pic


def supermarket(cam):
    """Супермаркет: плитка, ряды полок с подписанными товарами и ценниками, лампы дневного света."""
    pic = Pic(cam, [(0, 3.1, -2.0, 7.0, "#eef4ff"), (0, 3.1, -6.0, 7.0, "#eef4ff")], base=0.55)
    pic.poly([(-3, 0, 3), (3, 0, 3), (3, 0, -12), (-3, 0, -12)], "#cfc8bc", depth=99)
    for z in [3 - k * 0.6 for k in range(26)]:
        A, B = cam.p(-3, 0, z), cam.p(3, 0, z); pic.raw(98, f'<line x1="{A[0]:.1f}" y1="{A[1]:.1f}" x2="{B[0]:.1f}" y2="{B[1]:.1f}" stroke="#a8a094" stroke-width="2"/>')
    for x in (-1.8, -0.6, 0.6, 1.8):
        A, B = cam.p(x, 0, 3), cam.p(x, 0, -12); pic.raw(98, f'<line x1="{A[0]:.1f}" y1="{A[1]:.1f}" x2="{B[0]:.1f}" y2="{B[1]:.1f}" stroke="#a8a094" stroke-width="2"/>')
    pic.poly([(-3, 3.2, 3), (3, 3.2, 3), (3, 3.2, -12), (-3, 3.2, -12)], "#e8e6e0", stroke=False, depth=99)
    pic.poly([(-3, 0, -12), (3, 0, -12), (3, 3.2, -12), (-3, 3.2, -12)], "#d8d0c0", depth=98)
    for side in (-1, 1):
        x = side * 1.0
        pic.box(min(x, x + side * 0.6) - 0.0, max(x, x + side * 0.6), 0, 0.15, -11, 2.5, "#3a3d44")
        shelf_unit(pic, x + side * 0.55, -10.5, 2.4, side=side, levels=(0.3, 0.75, 1.2, 1.65, 2.1), seed=11 + side, kind="store")
        for z in range(-10, 3, 2):  # ценники
            xx, yy, d = cam.p(x + side * 0.02, 0.62, z); pic.raw(d - 0.05, f'<rect x="{xx - 22 / d:.1f}" y="{yy:.1f}" width="{44 / d:.1f}" height="{22 / d:.1f}" fill="#f6d84a" stroke="{INK}" stroke-width="{1 / d:.1f}"/>')
    for z, col in ((-3.5, "#c0392b"), (-7.5, "#2c6aa0")):                          # подвесные указатели
        pic.box(-0.5, 0.5, 2.55, 2.8, z - 0.02, z + 0.02, col, top=col)
        for xx in (-0.3, 0.3):
            a, b = cam.p(xx, 2.8, z), cam.p(xx, 3.2, z); pic.raw(a[2], f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="#555" stroke-width="2"/>')
    for z in (0.5, -2.5, -5.5, -8.5):
        pic.box(-0.9, 0.9, 3.08, 3.14, z - 0.1, z + 0.1, "#fbfdff", stroke=False, emissive=True)
        pic.glow(0, 3.0, z, 2.2, "#f0f6ff", 0.45)
    return pic


def pharmacy(cam):
    """Аптека: светлая плитка, прилавок, стена с ячейками и коробками лекарств, зелёный светящийся крест."""
    pic = Pic(cam, [(0, 2.9, -1.0, 5.0, "#f4fff8")], base=0.46)
    pic.poly([(-3, 0, 3), (3, 0, 3), (3, 0, -4), (-3, 0, -4)], "#d8dcd4", depth=99)
    for z in [3 - k * 0.5 for k in range(15)]:
        A, B = cam.p(-3, 0, z), cam.p(3, 0, z); pic.raw(98, f'<line x1="{A[0]:.1f}" y1="{A[1]:.1f}" x2="{B[0]:.1f}" y2="{B[1]:.1f}" stroke="#b0b6ac" stroke-width="2"/>')
    pic.poly([(-3, 0, -4), (3, 0, -4), (3, 3.1, -4), (-3, 3.1, -4)], "#b8d4c4", depth=98)
    pic.poly([(-3, 0, -3.99), (3, 0, -3.99), (3, 1.0, -3.99), (-3, 1.0, -3.99)], "#5a8a74", depth=97.5)
    pic.poly([(-3, 0, 3), (-3, 0, -4), (-3, 3.1, -4), (-3, 3.1, 3)], "#a8c4b4", depth=97)
    rnd = random.Random(4); meds = ["#e8e8f0", "#3a7ac0", "#e05a4a", "#4ab07a", "#f0c040", "#9a6ac0"]
    for row in range(5):
        y = 0.55 + row * 0.42
        pic.box(-2.2, 2.2, y - 0.03, y, -3.95, -3.6, "#f4f2ec")
        x = -2.15
        while x < 2.1:
            w = rnd.uniform(0.12, 0.22); h = rnd.uniform(0.18, 0.3); c = rnd.choice(meds)
            pic.box(x, x + w, y, y + h, -3.9, -3.75, c, top=shade(c, 1.15)); x += w + 0.03
    pic.poly([(-3, 3.1, 3), (3, 3.1, 3), (3, 3.1, -4), (-3, 3.1, -4)], "#b4c2ba", depth=99)
    for z in (-0.5, -2.5):
        pic.box(-0.8, 0.8, 3.04, 3.09, z - 0.15, z + 0.15, "#fbfdff", stroke=False, emissive=True)
    pic.box(-2.0, 2.0, 0, 1.0, -2.6, -2.0, "#f2f0ea", top="#e2e0d8")
    pic.box(-2.0, 2.0, 1.0, 1.05, -2.65, -1.95, "#b8c8c0")
    pic.box(0.9, 1.4, 1.05, 1.35, -2.4, -2.1, "#3a3d44", top="#50545c")
    for (x0, x1, y0, y1) in ((-0.25, 0.25, 2.65, 2.8), (-0.075, 0.075, 2.48, 2.97)):
        pic.box(x0, x1, y0, y1, -3.98, -3.94, "#2ab060", stroke=False)
    pic.glow(0, 2.72, -3.9, 1.0, "#3aff8a", 0.5)
    for x0, col, txt in ((-2.7, "#e8f0f4", "ВИТАМИНЫ"), (2.0, "#fdf0e0", "СКИДКИ")):
        pic.box(x0, x0 + 0.7, 1.6, 2.5, -3.99, -3.97, col)
        ftext(pic, x0 + 0.35, 2.3, -3.96, txt, 0.08, "#2c6aa0")
        x, y, d = cam.p(x0 + 0.35, 1.95, -3.96); r = 0.18 * cam.f / d
        pic.raw(d - 0.05, f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="#f0a030" stroke="{INK}" stroke-width="2"/>')
    pic.jar(-2.4, 0, -1.6, 0.18, 0.35, "#8a5a3a", lid="#6a4a2a", label="#8a5a3a")
    for k in range(7):
        x, y, d = cam.p(-2.4 + 0.25 * math.cos(k), 0.75 + 0.25 * math.sin(k * 1.7), -1.6); r = 0.16 * cam.f / d
        pic.raw(d - 0.3, f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{r * .5:.1f}" ry="{r:.1f}" transform="rotate({k * 50} {x:.1f} {y:.1f})" fill="#4a8a4a" stroke="{INK}" stroke-width="1.5"/>')
    pic.box(-1.6, -1.55, 0, 1.0, -1.2, -1.15, "#c8a040"); pic.box(-0.6, -0.55, 0, 1.0, -1.2, -1.15, "#c8a040")
    pic.box(-1.6, -0.55, 0.92, 0.96, -1.19, -1.16, "#b8321e")
    return pic


def techroom(cam, red=False, t=0.0, fx=None):
    """Техкомната: скважина с насосом, ФВУ с ручкой, генератор, бак солярки, трубы, лампа."""
    pic = Pic(cam, [(0.0, 2.4, -1.2, 4.0, "#ffbe70")], base=0.32)
    Wl, Wr, Hc, Zb, Zf = -3.0, 3.0, 2.6, -3.0, 2.0
    concrete_wall(pic, [(Wl, 0, Zb), (Wr, 0, Zb), (Wr, Hc, Zb), (Wl, Hc, Zb)], seams_u=(-1.5, 0, 1.5), seams_v=(1.3,), at=Zb)
    concrete_wall(pic, [(Wl, 0, Zf), (Wl, 0, Zb), (Wl, Hc, Zb), (Wl, Hc, Zf)], seams_u=(-1.0,), plane="x", at=Wl)
    concrete_wall(pic, [(Wr, 0, Zf), (Wr, 0, Zb), (Wr, Hc, Zb), (Wr, Hc, Zf)], seams_u=(-1.0,), plane="x", at=Wr)
    pic.poly([(Wl, 0, Zf), (Wr, 0, Zf), (Wr, 0, Zb), (Wl, 0, Zb)], CONC_D, depth=99)
    pic.poly([(Wl, Hc, Zf), (Wr, Hc, Zf), (Wr, Hc, Zb), (Wl, Hc, Zb)], "#5e584f", depth=99)
    # скважина: оголовок, синий бак-гидроаккумулятор, труба с вентилем
    pic.box(-2.0, -1.6, 0, 0.35, -2.6, -2.2, "#7a838c", top="#9aa3ac")
    pic.jar(-1.2, 0, -2.55, 0.28, 0.75, "#2c6aa0", lid="#3a7ac0", label="#2c6aa0")
    for y in [0.35 + k * 0.1 for k in range(18)]:
        pic.box(-1.84, -1.76, y, y + 0.1, -2.44, -2.36, "#8a9198")
    pic.box(-1.84, -0.9, 2.1, 2.18, -2.44, -2.36, "#8a9198")
    x, y, d = cam.p(-1.8, 1.2, -2.35); r = 0.12 * cam.f / d
    pic.raw(d - 0.3, f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="none" stroke="#b8321e" stroke-width="{r * 0.25:.1f}"/><line x1="{x - r:.1f}" y1="{y:.1f}" x2="{x + r:.1f}" y2="{y:.1f}" stroke="#b8321e" stroke-width="{r * 0.2:.1f}"/>')
    # ФВУ: серый короб, воздуховоды вверх, ручка-штурвал
    pic.box(-0.45, 0.45, 0, 1.1, -2.9, -2.4, "#6f7a72", top="#86918a")
    pic.box(-0.15, 0.15, 1.1, 2.6, -2.75, -2.55, "#9aa1a8", top="#b8bec4")
    pic.box(-0.3, 0.3, 0.75, 0.95, -2.39, -2.37, "#3a3e44")
    x, y, d = cam.p(0.3, 0.55, -2.35); r = 0.14 * cam.f / d
    pic.raw(d - 0.3, f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="none" stroke="#2a2a2e" stroke-width="{r * 0.18:.1f}"/><line x1="{x:.1f}" y1="{y:.1f}" x2="{x + r * 1.3:.1f}" y2="{y + r * 0.4:.1f}" stroke="#2a2a2e" stroke-width="{r * 0.2:.1f}"/>')
    # генератор и бак солярки
    pic.box(1.2, 2.1, 0, 0.75, -2.8, -2.3, "#c8a03a", top="#d8b44a")
    pic.box(1.3, 2.0, 0.2, 0.55, -2.29, -2.27, "#2a2a2e")
    pic.box(1.75, 1.85, 0.75, 2.6, -2.7, -2.6, "#4a4a4e")
    pic.box(2.2, 2.9, 0, 1.2, -2.95, -1.6, "#4a6a3a", top="#5c7c4a")
    pic.box(2.18, 2.2, 0.5, 0.75, -2.3, -2.0, "#e8e4d8")
    water_pack(pic, -2.7, -2.1, n=2, rows=3)
    x, y, d = cam.p(-1.8, 1.65, -2.35); r = 0.08 * cam.f / d
    pic.raw(d - 0.3, f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="#f4f0e4" stroke="{INK}" stroke-width="{r * .15:.1f}"/><line x1="{x:.1f}" y1="{y:.1f}" x2="{x + r * .6:.1f}" y2="{y - r * .4:.1f}" stroke="#c0302a" stroke-width="{r * .12:.1f}"/>')
    pic.box(0.7, 1.1, 1.3, 1.9, -2.99, -2.93, "#8a9198", top="#9aa1a8")
    for k in range(3):
        pic.box(0.76 + k * 0.12, 0.84 + k * 0.12, 1.55, 1.7, -2.93, -2.92, "#2a2a2e")
    sag(pic, (1.8, 0.6, -2.29), (0.9, 1.3, -2.93), col="#1a1a1a", drop=0.25)
    sag(pic, (0.9, 1.9, -2.95), (0.0, 2.55, -1.2), col="#1a1a1a", drop=0.2)
    for x0, col in ((-2.85, "#a8321e"), (-2.55, "#a8321e")):
        pic.box(x0, x0 + 0.24, 0, 0.42, -0.4, -0.25, col, top=shade(col, 1.2))
    pic.box(2.85, 2.98, 0.6, 1.1, -0.9, -0.75, "#a8281e", top="#c03a2a")
    pic.box(-2.99, -2.6, 1.4, 1.43, -1.6, -0.6, WOOD, top="#94693e")
    for k, col in enumerate(("#555c64", "#c8a03a", "#3a5a8a", "#a83a2a")):
        pic.box(-2.9, -2.7, 1.43, 1.43 + 0.1 + 0.05 * k, -1.5 + k * 0.22, -1.38 + k * 0.22, col)
    hanging_lamp(pic, 0.0, 2.2, -1.2)
    fx = fx or {}
    if fx.get("water", 0) > 0:
        a = fx["water"]
        for k in range(3):
            ph = (t * 1.6 + k / 3) % 1.0
            x, y, d = cam.p(-0.95, 2.05 - ph * 1.25, -2.4); r = 0.04 * cam.f / d
            pic.raw(d - 0.4, f'<path d="M{x:.1f} {y - r * 1.6:.1f} Q{x + r:.1f} {y:.1f} {x:.1f} {y + r:.1f} Q{x - r:.1f} {y:.1f} {x:.1f} {y - r * 1.6:.1f} Z" fill="#7ac8f0" stroke="{INK}" stroke-width="{max(.6, r * .15):.1f}" opacity="{a:.2f}"/>')
        x, y, d = cam.p(-0.95, 0.76, -2.4); pic.raw(d - 0.35, f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{0.12 * cam.f / d * a:.1f}" ry="{0.03 * cam.f / d * a:.1f}" fill="none" stroke="#7ac8f0" stroke-width="3"/>')
    if fx.get("air", 0) > 0:
        a = fx["air"]
        for k in range(5):
            ph = (t * 0.9 + k / 5) % 1.0
            x0, y0, d = cam.p(0.0, 2.45 - k * 0.08, -2.5); r = (0.3 + ph * 1.4) * cam.f / d
            pic.top.append(f'<path d="M{x0 + r * 0.2:.1f} {y0 + r * .1:.1f} q{r * .5:.1f} {-r * .25:.1f} {r:.1f} 0 t{r * .6:.1f} {r * .1:.1f}" fill="none" stroke="#e8f4ff" stroke-width="5" stroke-linecap="round" opacity="{a * (1 - ph) * .8:.2f}"/>')
        x, y, d = cam.p(0.0, 0.85, -2.39); r = 0.2 * cam.f / d; ang = t * 600
        pic.raw(d - 0.4, f'<g transform="rotate({ang:.1f} {x:.1f} {y:.1f})">' + "".join(f'<ellipse cx="{x:.1f}" cy="{y - r * .5:.1f}" rx="{r * .22:.1f}" ry="{r * .5:.1f}" transform="rotate({k * 120} {x:.1f} {y:.1f})" fill="#b8c0c8" stroke="{INK}" stroke-width="2"/>' for k in range(3)) + f'</g><circle cx="{x:.1f}" cy="{y:.1f}" r="{r * .15:.1f}" fill="#3a3e44"/>')
    if fx.get("light", 0) > 0:
        a = fx["light"]
        for k in range(4):
            ph = (t * 0.7 + k / 4) % 1.0
            x, y, d = cam.p(1.8 + ph * 0.3, 2.6 + ph * 0.6, -2.65); r = (0.1 + ph * 0.35) * cam.f / d
            pic.top.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="#8a8a8a" opacity="{a * (1 - ph) * .5:.2f}"/>')
        pic.glow(0.0, 2.1, -1.2, 2.2, "#ffd890", 0.35 * a + 0.12 * a * math.sin(t * 40))
        pic.glow(1.65, 0.4, -2.28, 0.6, "#7aff8a", 0.5 * a)
    return pic


def gable_house(pic, x0, x1, z0, z1, h, wall, roof, rh=1.3, seed=0, porch=True):
    """Дачный домик: стены, двускатная крыша (конёк вдоль x), окна с рамами и ставнями, труба, крыльцо."""
    c = pic.cam; zm = (z0 + z1) / 2
    pic.box(x0, x1, 0, h, z0, z1, wall, top=wall)
    # доски обшивки на фасаде
    for k in range(1, int(h / 0.22)):
        y = k * 0.22; A, B = c.p(x0, y, z1), c.p(x1, y, z1)
        pic.raw(max(A[2], B[2]) - 0.02, f'<line x1="{A[0]:.1f}" y1="{A[1]:.1f}" x2="{B[0]:.1f}" y2="{B[1]:.1f}" stroke="{shade(wall, .75)}" stroke-width="{2.2 / max(A[2], B[2]) * 3:.2f}" opacity=".6"/>')
    if c.x > x1:
        pic.poly([(x1, h, z1), (x1, h, z0), (x1, h + rh, zm)], shade(wall, .88))
    if c.x < x0:
        pic.poly([(x0, h, z1), (x0, h, z0), (x0, h + rh, zm)], shade(wall, .88))
    pic.poly([(x0 - 0.25, h - 0.05, z1 + 0.35), (x1 + 0.25, h - 0.05, z1 + 0.35), (x1 + 0.25, h + rh, zm), (x0 - 0.25, h + rh, zm)], roof)
    for k in range(1, 6):  # волны шифера
        u = k / 6; A = c.p(x0 - 0.25 + (x1 - x0 + 0.5) * u, h - 0.05, z1 + 0.35); B = c.p(x0 - 0.25 + (x1 - x0 + 0.5) * u, h + rh, zm)
        pic.raw(max(A[2], B[2]) - 0.03, f'<line x1="{A[0]:.1f}" y1="{A[1]:.1f}" x2="{B[0]:.1f}" y2="{B[1]:.1f}" stroke="{shade(roof, .7)}" stroke-width="{2 / A[2] * 3:.2f}"/>')
    pic.box(x1 - 0.9, x1 - 0.6, h + rh * 0.4, h + rh + 0.4, zm + 0.1, zm + 0.4, "#8a4a38", top="#6a3a2a")
    n = max(1, int((x1 - x0) / 1.6))
    for k in range(n):
        wx = x0 + (x1 - x0) * (k + 0.5) / n - 0.35
        pic.box(wx - 0.12, wx, h * 0.38, h * 0.38 + 0.8, z1, z1 + 0.03, "#3a6a4a")
        pic.box(wx + 0.7, wx + 0.82, h * 0.38, h * 0.38 + 0.8, z1, z1 + 0.03, "#3a6a4a")
        pic.box(wx, wx + 0.7, h * 0.38, h * 0.38 + 0.8, z1, z1 + 0.02, "#9ac4dc", top="#f0ece0")
        A, B = c.p(wx + 0.35, h * 0.38, z1 + 0.025), c.p(wx + 0.35, h * 0.38 + 0.8, z1 + 0.025)
        pic.raw(A[2] - 0.04, f'<line x1="{A[0]:.1f}" y1="{A[1]:.1f}" x2="{B[0]:.1f}" y2="{B[1]:.1f}" stroke="#f0ece0" stroke-width="{3 / A[2] * 3:.1f}"/>')
        pic.box(wx - 0.05, wx + 0.75, h * 0.38 - 0.06, h * 0.38, z1, z1 + 0.1, "#f0ece0")
    if porch:
        px = x0 + 0.5
        pic.box(px, px + 1.2, 0, 0.35, z1, z1 + 0.8, "#8a6a44", top="#a8845a")
        pic.box(px + 0.3, px + 0.95, 0.35, 2.0, z1 - 0.02, z1 + 0.01, "#6a4a2a")


def birch(pic, X, Z, h=5.0, seed=1):
    rnd = random.Random(seed); c = pic.cam
    pic.box(X - 0.09, X + 0.09, 0, h * 0.75, Z - 0.09, Z + 0.09, "#ece8e0", top="#ece8e0")
    for k in range(7):
        y = rnd.uniform(0.3, h * 0.7); A = c.p(X - 0.09, y, Z + 0.1); B = c.p(X + rnd.uniform(-0.02, 0.06), y + 0.03, Z + 0.1)
        pic.raw(A[2] - 0.05, f'<line x1="{A[0]:.1f}" y1="{A[1]:.1f}" x2="{B[0]:.1f}" y2="{B[1]:.1f}" stroke="#2a2420" stroke-width="{3 / A[2] * 3:.1f}"/>')
    for k in range(26):
        cx_, cy_, cz_ = X + rnd.uniform(-0.9, 0.9), h * rnd.uniform(0.55, 1.0), Z + rnd.uniform(-0.5, 0.5)
        x, y, d = c.p(cx_, cy_, cz_); r = rnd.uniform(0.25, 0.45) * c.f / d
        col = rnd.choice(["#d8a03a", "#c8a03a", "#e0b84a", "#a8a03a", "#8a9a3a"])
        pic.raw(d - 0.2, f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{r:.1f}" ry="{r * 0.8:.1f}" fill="{col}" stroke="{INK}" stroke-width="{max(0.6, 4 / d):.1f}"/><ellipse cx="{x - r * .25:.1f}" cy="{y - r * .25:.1f}" rx="{r * .45:.1f}" ry="{r * .3:.1f}" fill="{shade(col, 1.18)}"/>')


def pine(pic, X, Z, h=6.0, col="#3a5a3a"):
    c = pic.cam
    pic.box(X - 0.1, X + 0.1, 0, h * 0.3, Z - 0.1, Z + 0.1, "#5a3a24")
    for k in range(4):
        y0 = h * (0.22 + k * 0.18); w = 1.3 * (1 - k * 0.2)
        A, B, T = c.p(X - w, y0, Z), c.p(X + w, y0, Z), c.p(X, y0 + h * 0.32, Z)
        pic.raw(A[2] - 0.1 - k * 0.01, f'<polygon points="{A[0]:.1f},{A[1]:.1f} {B[0]:.1f},{B[1]:.1f} {T[0]:.1f},{T[1]:.1f}" fill="{shade(col, 1 + k * .06)}" stroke="{INK}" stroke-width="{max(.6, 4 / A[2]):.1f}" stroke-linejoin="round"/>')


def village(cam):
    """Год назад: дачный посёлок за городом. Дорога и забор уходят по диагонали, вдали справа город."""
    pic = Pic(cam, [(-3.0, 8.0, 3.0, 30.0, "#fff2d0")], base=0.92, soft=False)
    rnd = random.Random(9)
    # город на горизонте (справа по диагонали), в дымке
    for k in range(40):
        x0 = 140 + k * 8 + rnd.uniform(-2, 2); w = rnd.uniform(7, 12); h = rnd.uniform(18, 55); z = -260 - rnd.uniform(0, 40)
        col = mix("#8a9ab0", "#b4c6da", rnd.uniform(0.35, 0.75))
        pic.box(x0, x0 + w, 0, h, z - 4, z, col, top=col, side=shade(col, .92), stroke=False)
        for j in range(int(h / 6)):
            A = cam.p(x0 + w * 0.2, 3 + j * 6, z + 0.05); B = cam.p(x0 + w * 0.8, 3 + j * 6, z + 0.05)
            pic.raw(A[2] - 0.5, f'<line x1="{A[0]:.1f}" y1="{A[1]:.1f}" x2="{B[0]:.1f}" y2="{B[1]:.1f}" stroke="{shade(col, .85)}" stroke-width="1.2"/>')
    for k in range(3):  # трубы ТЭЦ
        x0 = 200 + k * 45; pic.box(x0, x0 + 5, 0, 70, -300, -295, "#a8b4c4", top="#a8b4c4", stroke=False)
        pic.box(x0, x0 + 5, 52, 58, -300.1, -295, "#c89a9a", stroke=False)
    # лес вдали слева
    for k in range(40):
        x = -60 + k * 2.2; z = -45 - rnd.uniform(0, 8)
        pine(pic, x, z, h=rnd.uniform(7, 11), col=rnd.choice(["#3a5a3a", "#4a6a3a", "#2e4e34"]))
    # земля, трава, дорога вдоль забора
    pic.poly([(-80, 0, 12), (200, 0, 12), (200, 0, -160), (-80, 0, -160)], "#8a9a5a", grad=("#9aa86a", "#7a8a4a"), stroke=False, depth=999)
    pic.poly([(-30, 0.01, 2.2), (120, 0.01, 2.2), (120, 0.01, -0.3), (-30, 0.01, -0.3)], "#b8a888", stroke=False, depth=998)
    for k in range(60):  # колея и камешки
        x = -10 + k * 1.3; q = cam.p(x, 0.01, 0.9 + 0.4 * math.sin(k)); pic.raw(q[2], f'<ellipse cx="{q[0]:.1f}" cy="{q[1]:.1f}" rx="{14 / q[2] * 3:.1f}" ry="{4 / q[2] * 3:.1f}" fill="#9a8a6a"/>')
    # столбы ЛЭП вдоль дороги
    tops = []
    for k in range(10):
        x = -4 + k * 9; pic.box(x - 0.08, x + 0.08, 0, 6.5, 2.6, 2.76, "#6a5038"); pic.box(x - 0.7, x + 0.7, 6.0, 6.12, 2.62, 2.74, "#6a5038")
        tops.append(cam.p(x, 6.0, 2.68))
    for a, b in zip(tops, tops[1:]):
        if a[2] > 0.3 and b[2] > 0.3:
            pic.raw(max(a[2], b[2]), f'<path d="M{a[0]:.1f} {a[1]:.1f} Q{(a[0] + b[0]) / 2:.1f} {(a[1] + b[1]) / 2 + 30:.1f} {b[0]:.1f} {b[1]:.1f}" fill="none" stroke="#2a2420" stroke-width="2"/>')
    # дачи соседей за забором, уходят вдаль
    houses = [(-5.0, -0.6, -7.0, -3.6, 2.7, "#d8c8a0", "#7a8a94"), (9.0, 12.5, -9.5, -6.4, 2.5, "#a8c4b0", "#8a3a2a"),
              (19.0, 22.5, -10.0, -7.0, 2.6, "#e0b878", "#5a6a74"), (29.0, 32.0, -10.0, -7.2, 2.4, "#c8a8b8", "#8a4a38")]
    for k, (x0, x1, z0, z1, h, wall, roof) in enumerate(houses):
        gable_house(pic, x0, x1, z0, z1, h, wall, roof, seed=k)
    # заборы участков: штакетник вдоль дороги
    x = -12.0
    while x < 60:
        pic.box(x, x + 0.1, 0, 1.2, -1.2, -1.17, "#a8845a", top="#b8946a"); x += 0.17
    pic.box(-12, 60, 0.85, 0.93, -1.25, -1.2, "#8a6a44"); pic.box(-12, 60, 0.25, 0.33, -1.25, -1.2, "#8a6a44")
    for xg in (6.5, 16.5):  # калитки
        pic.box(xg, xg + 1.0, 0, 1.3, -1.19, -1.16, "#4a6a8a")
    # деревья и кусты
    birch(pic, -7.0, -2.6, 5.2, 1); birch(pic, 15.0, -4.0, 6.0, 2); birch(pic, 25.0, -5.0, 5.6, 3)
    pine(pic, -6.0, -6.0, 7.5); pine(pic, 27.0, -9.5, 8.0)
    for k in range(14):
        x = -8 + k * 4.3 + rnd.uniform(-0.5, 0.5); q = cam.p(x, 0.3, -1.5); r = 0.5 * cam.f / q[2]
        pic.raw(q[2] + 0.1, f'<ellipse cx="{q[0]:.1f}" cy="{q[1]:.1f}" rx="{r:.1f}" ry="{r * .6:.1f}" fill="#5a7a3a" stroke="{INK}" stroke-width="{max(.6, 4 / q[2]):.1f}"/>')
    return pic


def cutaway(cam, red=0.0, t=0.0, open_hatch=False):
    """Разрез в пропорциях первой части (вид почти плоский, длиннофокусная камера).
    Сверху: два дома по бокам, гараж между ними, фонарь, заборы. Под гаражом длинный низкий бункер 14.5 x 2.9 м:
    слева две ФВУ и труба воздуха наверх, справа стеллажи с едой и отдельная комната с дизелем, выхлоп трубой наверх.
    Лестница из гаража справа от центра. Бак закопан между землёй и потолком бункера. Под полом синий водоносный слой.
    Пол бункера y=-6.2, потолок y=-3.3, земля y=0."""
    pic = Pic(cam, [(0.0, -3.6, -1.0, 9.0, "#ffd08a")], base=0.5, soft=False)
    pic.glow_k = min(1.0, 4200 / cam.f)   # при сильном приближении свечения не заливают кадр
    Z0 = 0.0; XL, XR, YB, YT, ZB = -7.25, 7.25, -6.2, -3.3, -2.2
    pic.poly([(-60, 0, Z0), (60, 0, Z0), (60, -60, Z0), (-60, -60, Z0)], "#3a2e26", stroke=False, depth=300)
    pic.poly([(-60, 0, Z0 + .001), (60, 0, Z0 + .001), (60, -0.6, Z0 + .001), (-60, -0.6, Z0 + .001)], "#4a3a2c", stroke=False, depth=299)
    rnd = random.Random(5)
    for _ in range(260):
        x, y = rnd.uniform(-14, 14), rnd.uniform(-26, -0.3)
        if XL - 0.2 < x < XR + 0.2 and YB - 0.2 < y < YT + 0.2:
            continue
        q = cam.p(x, y, Z0 + 0.002); r_ = rnd.uniform(0.03, 0.08) * cam.f / q[2]
        pic.raw(298, f'<ellipse cx="{q[0]:.1f}" cy="{q[1]:.1f}" rx="{r_:.1f}" ry="{r_ * .7:.1f}" fill="#54443a" opacity=".8"/>')
    # вода под бункером
    pic.poly([(-4.6, -6.6, Z0 + .003), (4.6, -6.6, Z0 + .003), (4.6, -7.15, Z0 + .003), (-4.6, -7.15, Z0 + .003)], "#2c7ad0", depth=297, emissive=True)
    pic.glow(0, -6.9, 0.2, 3.5, "#4aa0ff", 0.3)
    # бункер: задняя стена, пол, потолок (видна небольшая глубина)
    pic.poly([(XL, YB, ZB), (XR, YB, ZB), (XR, YT, ZB), (XL, YT, ZB)], "#2e3440", depth=200)
    pic.poly([(XL, YB, Z0), (XR, YB, Z0), (XR, YB, ZB), (XL, YB, ZB)], "#3a404c", depth=199)
    pic.poly([(XL, YT, Z0), (XR, YT, Z0), (XR, YT, ZB), (XL, YT, ZB)], "#262a32", depth=199)
    pic.box(XL - 0.25, XL, YB - 0.25, YT + 0.25, ZB, Z0, "#5a606a"); pic.box(XR, XR + 0.25, YB - 0.25, YT + 0.25, ZB, Z0, "#5a606a")
    pic.box(XL - 0.25, XR + 0.25, YT, YT + 0.25, ZB, Z0, "#5a606a"); pic.box(XL - 0.25, XR + 0.25, YB - 0.25, YB, ZB, Z0, "#5a606a")
    for k in range(14):  # пунктир светильников под потолком
        x = XL + 0.4 + k * 1.03
        pic.box(x, x + 0.6, YT - 0.1, YT - 0.05, ZB + 0.6, ZB + 1.2, "#f4f2ea", stroke=False, emissive=True)
    for x in (-5.0, -1.6, 1.8, 5.2):
        pic.glow(x, YT - 0.25, -0.8, 1.3, "#ffe0a0", 0.55)
    # слева: ФВУ-1 (зелёная, работает) и ФВУ-2, труба воздуха наверх
    for k, (x0, col) in enumerate(((-7.0, "#2e9a5a"), (-6.2, "#5a6470"))):
        pic.box(x0, x0 + 0.7, YB, YB + 1.1, ZB + 0.2, ZB + 0.8, col, top=shade(col, 1.2))
        x, y, d = cam.p(x0 + 0.35, YB + 0.65, ZB + 0.81); r_ = 0.24 * cam.f / d
        pic.raw(d - 0.05, f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r_:.1f}" fill="{shade(col, .6)}"/><g transform="rotate({t * (520 if k == 0 else 0):.0f} {x:.1f} {y:.1f})">'
                          + "".join(f'<ellipse cx="{x:.1f}" cy="{y - r_ * .5:.1f}" rx="{r_ * .25:.1f}" ry="{r_ * .5:.1f}" transform="rotate({j * 120} {x:.1f} {y:.1f})" fill="#eef4ee"/>' for j in range(3)) + "</g>")
        ftext(pic, x0 + 0.35, YB + 0.12, ZB + 0.82, f"ФВУ-{k + 1}", 0.13, "#ffffff")
    pic.box(-6.7, -6.55, YT, 1.4, -0.6, -0.45, "#7a828c")
    pic.box(-6.85, -6.4, 1.4, 1.55, -0.65, -0.4, "#7a828c")
    # справа: стеллажи с едой, перегородка, отдельная комната с дизелем, выхлоп наверх
    for row in range(4):
        y = YB + 0.25 + row * 0.6
        pic.box(4.4, 5.4, y - 0.04, y, ZB + 0.1, ZB + 0.6, "#7a5a3a", top="#8e6c48")
        for k in range(7):
            pic.jar(4.5 + k * 0.13, y, ZB + 0.35, 0.05, 0.17, ["#d8a03a", "#c0602a", "#7a9a3a", "#a8322a"][(k + row) % 4], lid="#e8e4d8", label=None, fill="pickle" if k % 2 else "tomato")
    pic.box(5.7, 5.85, YB, YT, ZB, Z0 - 0.2, "#4a505a")
    pic.box(6.2, 7.0, YB, YB + 1.0, ZB + 0.2, ZB + 0.8, "#d8a030", top="#e8b040")
    ftext(pic, 6.6, YB + 0.45, ZB + 0.82, "ДИЗЕЛЬ", 0.14, "#2a1a08")
    pic.box(6.85, 6.97, YB + 1.0, 1.8, -0.6, -0.48, "#d86a3a", emissive=True)
    pic.glow(6.9, -1.0, 0.0, 0.8, "#ff7a3a", 0.25)
    # лестница из гаража (справа от центра)
    LX = 1.9
    pic.poly([(LX - 0.45, YT, -0.5), (LX + 0.45, YT, -0.5), (LX + 0.45, 0, -0.5), (LX - 0.45, 0, -0.5)], "#1e1a18", depth=190)
    for dx in (-0.26, 0.26):
        pic.box(LX + dx - 0.04, LX + dx + 0.04, YB, 0.25, -0.4, -0.32, "#c8ccd0")
    y = YB + 0.3
    while y < 0.2:
        pic.box(LX - 0.26, LX + 0.26, y, y + 0.05, -0.4, -0.34, "#e0e4e8"); y += 0.38
    pic.box(LX - 0.55, LX + 0.55, -0.03, 0.06, -0.8, -0.2, "#f2c94c" if not open_hatch else "#1a1210")
    # бак с соляркой в грунте над бункером
    pic.box(-1.4, 1.2, -2.35, -1.45, -0.6, -0.2, "#f0c830", top="#f8d850", emissive=True)
    for xx in (-1.4, 1.2):
        x, y, d = cam.p(xx, -1.9, -0.19); r_ = 0.45 * cam.f / d
        pic.raw(d - 0.02, f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r_:.1f}" fill="#f0c830"/>')
    pic.glow(-0.1, -1.9, 0.1, 2.2, "#ffd84a", 0.35)
    ftext(pic, -0.1, -2.0, -0.15, "БАК", 0.32, "#4a3a10")
    pic.box(-0.15, -0.05, -1.45, 0.15, -0.45, -0.38, "#8a9198")
    # поверхность: дорога, гараж между двумя домами, фонарь, заборы
    pic.poly([(-60, 0, 0), (60, 0, 0), (60, 0, -40), (-60, 0, -40)], "#22232a", stroke=False, depth=400)
    GX0, GX1, GH = -1.0, 3.4, 3.0
    pic.poly([(GX0, 0, -3.5), (GX1, 0, -3.5), (GX1, GH, -3.5), (GX0, GH, -3.5)], "#383c46", depth=150)        # гараж в разрезе
    pic.box(GX0 - 0.15, GX1 + 0.15, GH, GH + 0.25, -3.6, 0.0, "#2a2d34", top="#34383f")
    pic.box(GX0 - 0.15, GX0, 0, GH, -3.5, 0.0, "#30343b"); pic.box(GX1, GX1 + 0.15, 0, GH, -3.5, 0.0, "#30343b")
    for k in range(9):
        y = 0.35 + k * 0.28
        A, B = cam.p(GX0 + 0.1, y, -3.48), cam.p(GX1 - 0.1, y, -3.48)
        pic.raw(min(A[2], B[2]) - 0.01, f'<line x1="{A[0]:.1f}" y1="{A[1]:.1f}" x2="{B[0]:.1f}" y2="{B[1]:.1f}" stroke="#2a2e36" stroke-width="2"/>')
    pic.box(GX0 + 0.2, GX0 + 1.0, 1.0, 1.05, -3.45, -3.1, WOOD, top="#94693e")
    hanging_lamp(pic, (GX0 + GX1) / 2, GH - 0.15, -1.8, color="#ffe0a0")
    for (hx0, hx1, wall, roofc) in ((-8.6, -2.4, "#3a3e4c", "#2a2c36"), (5.0, 11.0, "#3e3a48", "#2c2a34")):        # два дома
        pic.box(hx0, hx1, 0, 4.0, -6.0, -2.5, wall, top=shade(wall, 1.1))
        pic.poly([(hx0 - 0.3, 4.0, -2.4), (hx1 + 0.3, 4.0, -2.4), ((hx0 + hx1) / 2, 5.8, -2.4)], roofc)
        for wx in (hx0 + 0.8, hx0 + 2.6, hx1 - 1.6):
            for wy, lit in ((0.9, (wx * 7) % 3 > 1), (2.5, (wx * 5) % 3 > 0.8)):
                pic.box(wx, wx + 0.9, wy, wy + 0.9, -2.52, -2.49, "#ffd870" if lit else "#1a1c22", stroke=False, emissive=lit)
                if lit:
                    pic.glow(wx + 0.45, wy + 0.45, -2.4, 0.9, "#ffcf70", 0.3)
        pic.box(hx0 + 4.2 if hx0 < 0 else hx0 + 3.6, (hx0 + 5.0) if hx0 < 0 else hx0 + 4.4, 0, 2.0, -2.53, -2.5, "#2a2c34")
    for x0, x1 in ((-2.4, -1.15), (3.55, 5.0), (-14, -8.6), (11, 16)):        # заборы
        x = x0
        while x < x1:
            pic.box(x, x + 0.07, 0, 1.0, -1.6, -1.57, "#5a4a3a"); x += 0.17
        pic.box(x0, x1, 0.7, 0.76, -1.62, -1.58, "#5a4a3a")
    pic.box(4.2, 4.3, 0, 4.2, -0.9, -0.8, "#2a2a2e"); pic.box(3.8, 4.3, 4.1, 4.2, -0.9, -0.8, "#2a2a2e")
    pic.glow(3.85, 4.0, -0.7, 1.6, "#ffcf8a", 0.55)
    if red:
        x, y, d = cam.p(8.5, 9.5, -8.0)
        pic.top.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{0.9 * cam.f / d * (0.85 + 0.15 * math.sin(t * 6)):.1f}" fill="#ff3a2a" opacity=".9"/>')
        pic.glow(8.5, 9.5, -8.0, 3.0, "#ff3a2a", 0.6)
    return pic
