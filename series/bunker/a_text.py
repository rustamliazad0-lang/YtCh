#!/usr/bin/env python3
"""Бункер A: продолжение первой части без озвучки. Рассказ текстом на экране, темп по тексту, как в части 1.

python3 a_text.py                 -> video/bunker-A2-youtube-1440p.mp4 и -tiktok-1080p.mp4 (без звука, музыку ставят на площадке)
python3 a_text.py --frames 2,10   -> кадры в illus_out/
python3 a_text.py --range 0,6     -> быстрый кусок без кодирования звука
Сцены переиспользуют отрисовку из a_illus.py (бункер, магазины, техкомната, люк, деревня), поверх — свой текст, счётчик дней
как в части 1, плашки и иконки. Новые сцены: разрез «гараж и бункер» из части 1, стук и силуэт с фонарём, телефон Макса.
"""
import math, os, sys, json, subprocess, random
import illus as I, char as C
import a_illus as AI

HERE = os.path.dirname(os.path.abspath(__file__))
FPS, SCALE = 30, 4 / 3
M = AI.M
OUT = os.path.join(HERE, "video", "bunker-A2.mp4")
FONT = AI.FONT

# исходные помощники до отключения
PILL, CARD, WHIP, pop, esc, ss, kv = AI.pill, AI.card, AI.whip, AI.pop, AI.esc, AI.ss, AI.kv
# внутри старых сцен отключаем их собственные подписи, плашки, удары и наезды: всё рисуем по своему тексту
AI.caption = lambda t: ""
AI.pill = lambda *a, **k: ""
AI.card = lambda *a, **k: ""
AI.label_place = lambda *a, **k: ""
AI.whip = lambda svg, t: svg
AI.KNOCKS[:] = []
AI.KW[:] = []

# ---------- сценарий ----------
# (сцена, текст кусками через " / ", *красное*, опции)
BEATS = [
    ("cut_intro", "ДЕНЬ 365. / СИРЕНЫ *СТИХЛИ*. / СЕМЬЯ ВНИЗУ. / ЛЮК ЗАКРЫТ.", dict(hud="ДЕНЬ 365", tag=("ЛЮК ЗАКРЫТ", "y"), hold=0.3)),
    ("knock", "ТУК. / ТУК. / ТУК.", dict(hud="ДЕНЬ 365", hold=0.2)),
    ("knock2", "«ОТКРЫВАЙ.» / «Я ВСЁ *ЗНАЛ*.»", dict(hud="ДЕНЬ 365", hold=0.3)),
    ("hook", "ЕДЫ / НА ПЯТЕРЫХ. / А СТУЧИТ / *ШЕСТОЙ*.", dict(hud="ДЕНЬ 365", tag=("4. ЕДА", "r"))),
    ("phone", "ЭТО МАКС. / ТОТ САМЫЙ, / ЧТО ГОД НАЗАД / НАПИСАЛ *НОЧЬЮ*.", dict(hud="ДО ВОЙНЫ: 365 ДН.", hold=0.6)),
    ("count", "ТЫ СТОИШЬ / У ЛЮКА / И *СЧИТАЕШЬ*.", dict(hud="ДЕНЬ 365", tag=("4. ЕДА", "r"))),
    ("market", "ЦЕЛЫЙ ГОД / ТЫ ВОЗИЛ ЕДУ / ПО ОДНОМУ *ПАКЕТУ*", dict(hud="ДО ВОЙНЫ: 214 ДН.", tag=("4. ЕДА", "r"), place="РЫНОК")),
    ("super", "В РАЗНЫХ / МАГАЗИНАХ,", dict(hud="ДО ВОЙНЫ: 131 ДН.", tag=("4. ЕДА", "r"), place="СУПЕРМАРКЕТ")),
    ("pharm", "ЧТОБЫ НИКТО / НЕ *ЗАПОМНИЛ*.", dict(hud="ДО ВОЙНЫ: 58 ДН.", tag=("4. ЕДА", "r"), place="АПТЕКА")),
    ("calc", "11 000 ПОРЦИЙ / НА ШЕСТЕРЫХ — / ЭТО *20 МЕСЯЦЕВ*, / А НЕ 24.", dict(hud="ДЕНЬ 365", tag=("4. ЕДА", "r"))),
    ("tech", "ВОЗДУХ — ЕСТЬ. / ВОДА — ЕСТЬ. / СВЕТ — ЕСТЬ.", dict(hud="ДЕНЬ 365", tag=("ПРОВЕРКА", "y"))),
    ("food", "МИНУС / *4 МЕСЯЦА* ЕДЫ / ЗА ЖИЗНЬ ДРУГА. / ЭТО МОЖНО / ПЕРЕЖИТЬ.", dict(hud="ДЕНЬ 365", tag=("4. ЕДА", "r"))),
    ("climb", "ТЫ / *ОТКРЫВАЕШЬ*.", dict(hud="ДЕНЬ 365", tag=("ЛЮК ОТКРЫТ", "r"), hold=0.3)),
    ("friend", "МАКС / ЗАХОДИТ ОДИН / И ПОВТОРЯЕТ:", dict(hud="ДЕНЬ 365")),
    ("knew", "«Я ВСЁ ЗНАЛ.»", dict(hud="ДЕНЬ 365", hold=0.6)),
    ("shock", "И ТЫ ПОНИМАЕШЬ: / ЗНАЛ / *НЕ ОН ОДИН*.", dict(hud="ДЕНЬ 365")),
    ("up", "ЗА НИМ / В СВЕТЕ СИРЕН / СТОЯТ *ЛЮДИ*. / ЭТО СОСЕДИ.", dict(hud="ДЕНЬ 365", tag=("СОСЕДИ", "r"))),
    ("village", "ТЕ, КОМУ ТЫ / ЦЕЛЫЙ ГОД / *МАХАЛ* / ЧЕРЕЗ ЗАБОР.", dict(hud="ДО ВОЙНЫ: 300 ДН.")),
    ("calc2", "ТРОЕ. / ЕСЛИ ПУСТИТЬ / И ИХ, / ЕДЫ ХВАТИТ / НА *13 МЕСЯЦЕВ*.", dict(hud="ДЕНЬ 365", tag=("4. ЕДА", "r"))),
    ("end", "МАКСА / ТЫ ПУСТИЛ. / А ИХ? / ПИШИ: / ДА ИЛИ НЕТ.", dict(hud="ДЕНЬ 365", tag=("СОСЕДИ", "r"), hold=3.0)),
]


def chunk_dur(c):
    return max(0.72, 0.32 + 0.058 * len(c.replace("*", "")))


VOICE = os.path.join(HERE, "video", "voice-A2.mp3")
SPOKEN = {"365.": "триста шестьдесят пять", "11": "одиннадцать", "000": "тысяч", "*20": "двадцать", "24.": "двадцать четыре", "*4": "четыре", "*13": "тринадцать"}
VOW = "аеёиоуыэюя"


def syl_chunk(c):
    n = 0.0
    for w in c.replace("—", " ").split():
        w = SPOKEN.get(w, w)
        n += sum(max(1, sum(ch in VOW for ch in x.lower())) + 0.35 for x in w.split())
    return n


def voiced_intervals(audio):
    T = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", audio], capture_output=True, text=True).stdout)
    log = subprocess.run(["ffmpeg", "-hide_banner", "-i", audio, "-af", "silencedetect=noise=-35dB:d=0.18", "-f", "null", "-"], capture_output=True, text=True).stderr
    import re
    st_ = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]; en_ = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    voiced, cur = [], 0.0
    for a, b in zip(st_, en_ + [T] * (len(st_) - len(en_))):
        if a > cur + 0.02:
            voiced.append((cur, a))
        cur = max(cur, b)
    if cur < T - 0.02:
        voiced.append((cur, T))
    return T, voiced


def build_tl():
    """С голосом: куски текста раскладываются по звучащим участкам пропорционально слогам; начало фразы после точки/запятой
    притягивается к началу звучащего участка. Удары в люк (такт knock) стоят в паузе перед «Открывай». Без голоса — темп чтения."""
    tl = []
    if not os.path.exists(VOICE):
        t = 0.0
        for name, text, opt in BEATS:
            cs = []
            for p_ in [x.strip() for x in text.split("/")]:
                d = chunk_dur(p_); cs.append([t, t + d, p_]); t += d
            end = t + opt.get("hold", 0.25); tl.append((name, cs[0][0], end, opt, cs)); t = end
        return tl, t
    T, voiced = voiced_intervals(VOICE)
    chunks = [(bi, p_.strip()) for bi, (name, text, opt) in enumerate(BEATS) if name != "knock" for p_ in text.split("/")]
    # фразы: куски до знака препинания; каждой фразе — подряд идущие звучащие участки (динамика по длительности)
    phrases, cur = [], []
    for k, (bi, c) in enumerate(chunks):
        cur.append(k)
        if c.replace("*", "").rstrip("»").endswith((".", "?", "!")):   # фраза = предложение
            phrases.append(cur); cur = []
    if cur:
        phrases.append(cur)
    W = [sum(syl_chunk(chunks[k][1]) for k in ph) for ph in phrases]
    rate = sum(b - a for a, b in voiced) / sum(W)
    n, m = len(voiced), len(phrases); INF = 1e18
    # dp[j][e]: первые j фраз заняли первые e участков; шаг — группа из 1..4 фраз на 1..6 участков подряд
    dp = [[INF] * (n + 1) for _ in range(m + 1)]; bk = [[None] * (n + 1) for _ in range(m + 1)]; dp[0][0] = 0.0
    for j_ in range(m):
        for st in range(n):
            if dp[j_][st] >= INF:
                continue
            for g in range(1, 5):
                if j_ + g > m:
                    break
                wsum = sum(W[j_:j_ + g])
                for e in range(st + 1, min(n, st + 6) + 1):
                    dur = voiced[e - 1][1] - voiced[st][0]
                    c_ = dp[j_][st] + (dur - rate * wsum) ** 2 + 2.5 * (g - 1)
                    if c_ < dp[j_ + g][e]:
                        dp[j_ + g][e], bk[j_ + g][e] = c_, (j_, st)
    groups, j_, e = [], m, n
    while j_ > 0:
        pj, st = bk[j_][e]; groups.append((pj, j_, voiced[st][0], voiced[e - 1][1])); j_, e = pj, st
    groups.reverse()
    phrases2, spans = [], []
    for pj, j2, a, b in groups:
        phrases2.append([k for ph in phrases[pj:j2] for k in ph]); spans.append((a, b))
    phrases = phrases2
    starts = [0.0] * len(chunks)
    for ph, (a, b) in zip(phrases, spans):
        ws = [syl_chunk(chunks[k][1]) for k in ph]; acc = 0.0
        for k, w in zip(ph, ws):
            starts[k] = a + (b - a) * acc / sum(ws); acc += w
    vstarts = [a for a, b in voiced]
    for k in range(1, len(chunks)):  # начало предложения притягиваем к началу звучащего куска рядом
        if chunks[k - 1][1].replace("*", "").rstrip("»").endswith((".", "?", ":")):
            near = min(vstarts, key=lambda a: abs(a - starts[k]))
            if abs(near - starts[k]) < 1.0 and near > starts[k - 1] + 0.3:
                starts[k] = near
    for k in range(1, len(chunks)):
        starts[k] = max(starts[k], starts[k - 1] + 0.25)
    starts = [max(0.0, x - 0.05) for x in starts]
    kb = next(i for i, b in enumerate(BEATS) if b[0] == "knock")
    after = next(k for k, c in enumerate(chunks) if c[0] > kb)
    g0 = max(b for (a, b) in spans if b <= starts[after] + 0.1); g1 = starts[after] + 0.05
    knock_t = [g0 + 0.2 + k * (g1 - g0 - 0.45) / 3 for k in range(3)]
    flat = []
    ci = 0
    for bi, (name, text, opt) in enumerate(BEATS):
        parts = [x.strip() for x in text.split("/")]
        if name == "knock":
            flat += [[bi, knock_t[k], parts[k]] for k in range(3)]
        else:
            for p_ in parts:
                flat.append([bi, starts[ci], p_]); ci += 1
    flat.sort(key=lambda x: x[1])
    end_all = T + BEATS[-1][2].get("hold", 2.5) * 0.6
    for k, (bi, t0, p_) in enumerate(flat):
        t1 = flat[k + 1][1] if k + 1 < len(flat) else end_all
        flat[k] = [bi, t0, t1, p_]
    for bi, (name, text, opt) in enumerate(BEATS):
        cs = [[t0, t1, p_] for b_, t0, t1, p_ in flat if b_ == bi]
        tl.append((name, cs[0][0], cs[-1][1], opt, cs))
    tl = [(n, (0.0 if k == 0 else a), b, o, c) for k, (n, a, b, o, c) in enumerate(tl)]
    return tl, end_all


TL, _t = build_tl()
TOTAL = _t
CUTS = [b[1] for b in TL[1:]]
WHIPS = [TL[k][1] for k in range(1, len(TL)) if TL[k][0] in ("market", "super", "pharm", "calc", "phone", "count", "village", "calc2", "tech")]
KW = [c0 for b in TL for (c0, c1, p) in b[4] if "*" in p]


def beat_at(t):
    for b in TL:
        if t < b[2]:
            return b
    return TL[-1]


# ---------- оверлеи ----------
def caption(t, y=1200):
    for b in TL:
        for c0, c1, p in b[4]:
            if c0 <= t < (c1 if c1 < b[2] - 0.01 or p != b[4][-1][2] else b[2]):
                sc, op = pop(t, c0, 0.12)
                words = p.split(" "); out = []
                for w in words:
                    red = w.startswith("*") or w.endswith("*") or w.endswith("*.") or w.endswith("*,")
                    out.append(f'<tspan fill="{"#ff3b30" if "*" in w else "#ffffff"}">{esc(w.replace("*", ""))}</tspan>')
                tw = len(p.replace("*", "")) * 86 * 0.64
                sc *= min(1.0, 980 / max(1, tw))
                yy = {"phone": 1590, "up": 1500, "end": 1240, "cut_intro": 1420, "knock": 1420}.get(b[0], y)
                return (f'<g transform="translate(540 {yy}) scale({sc:.3f})"><text x="0" y="0" text-anchor="middle" font-family="{FONT}" font-weight="900" font-size="86" '
                        f'stroke="#0d0b0a" stroke-width="14" stroke-linejoin="round" paint-order="stroke">{" ".join(out)}</text></g>')
    return ""


def hud(t, b):
    o = b[3]; s = ""
    if o.get("hud"):
        txt = o["hud"]; w = len(txt) * 15 + 40
        s += (f'<g transform="translate(40 60)"><rect width="{w}" height="46" rx="10" fill="#0e0f14" opacity=".72" stroke="#3a3c46" stroke-width="2"/>'
              f'<text x="{w / 2}" y="31" text-anchor="middle" font-family="{FONT}" font-weight="700" font-size="24" fill="#c8ccd8">{esc(txt)}</text></g>')
        if o.get("tag"):
            tag, kind = o["tag"]; tw = len(tag) * 17 + 36
            fill = {"r": "#d8362b", "y": "#f2c94c"}[kind]; fg = {"r": "#ffffff", "y": "#1d1a17"}[kind]
            s += (f'<g transform="translate({40 + w + 14} 60)"><rect width="{tw}" height="46" rx="10" fill="{fill}" stroke="#14110f" stroke-width="3"/>'
                  f'<text x="{tw / 2}" y="32" text-anchor="middle" font-family="{FONT}" font-weight="900" font-size="26" fill="{fg}">{esc(tag)}</text></g>')
    if o.get("place"):
        s += PILL(t, b[1], b[2], o["place"], "y", 1)
    return s


def punch(t):
    v = 0.0
    for k in KW:
        d = t - k
        if 0 <= d < 0.5:
            v = max(v, math.sin(min(1, d / 0.18) * math.pi / 2) * (1 - max(0, d - 0.18) / 0.32))
    return v


def wrap(inner, t, roll=0.0, zoom=1.0, over=""):
    """Кадр сцены + динамика (наезд на ключевых словах, наклон камеры) + оверлеи поверх."""
    z = zoom * (1 + 0.06 * punch(t)); r = roll
    sc = z * (1 + abs(r) * 0.035)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920" viewBox="0 0 1080 1920"><rect width="1080" height="1920" fill="#0b0b0e"/>'
            f'<g transform="translate(540 960) rotate({r:.2f}) scale({sc:.4f}) translate(-540 -960)">{inner}</g>{over}</svg>')


def ai_map(t, b, a0, a1, ease=False):
    w = (t - b[1]) / (b[2] - b[1]); w = ss(w) * 0.3 + w * 0.7 if ease else w
    return a0 + (a1 - a0) * max(0.0, min(0.999, w))


S = AI.S


# ---------- новые сцены ----------
def sil_filter():
    return '<filter id="sil"><feColorMatrix values="0 0 0 0 .04  0 0 0 0 .03  0 0 0 0 .03  0 0 0 1 0"/></filter>'


def siren_sky(t):
    return I.mix("#160a0e", "#5a1218", 0.5 + 0.5 * math.sin(t * 3.2))


def cut_intro(t, b):
    w = (t - b[1]) / (b[2] - b[1])
    # почти плоский вид, как в части 1: камера далеко, длинный объектив; медленный наезд к гаражу
    c = I.Cam(x=0.2 + 0.6 * ss(w), y=-1.6 + 0.6 * ss(w), z=60, pitch=0.0, f=3900 * (1 + 0.35 * ss(w)))
    p = I.cutaway(c, t=t, red=1)
    for k, (n, x) in enumerate((("grandpa", -3.4), ("mom", -2.8), ("girl", -2.25), ("kid", -1.75))):
        AI.put(p, C.person(n, "side", face="worried", sit=1.0, blink=AI.blink(t, k), rim="#ffd59a"), x, -1.2, Y=-6.2)
    AI.put(p, C.person("hero", "front", face="worried", blink=AI.blink(t, 2), rim="#ffd59a"), 1.1, -0.9, Y=-6.2)
    p.defs.append(sil_filter())
    return p.svg(sky=siren_sky(t), particles=("dust", 30), vignette=0.55, grain=0, ptime=t)


def knock(t, b):
    cs = b[4]; e = 0.0; tk = None
    for c0, c1, p in cs:
        if c0 <= t < c0 + 0.35:
            e = max(e, (1 - (t - c0) / 0.35) ** 2); tk = c0
    w = (t - b[1]) / (b[2] - b[1])
    c = I.Cam(x=1.2, y=1.3 - 0.4 * w, z=60, pitch=0.0, f=11000 * (1 + 0.15 * w))
    c.vx += math.sin(t * 31) * 22 * e; c.vy += math.cos(t * 23) * 14 * e
    p = I.cutaway(c, t=t, red=1)
    p.defs.append(sil_filter())
    k = (t * 1.3) % 1.0
    svg = C.person("friend", "side", arms="money", rim="#ff8a6a")
    x, y, d = p.cam.p(1.0, 0, -1.6)
    sc = p.cam.f / d * M
    g = C.place(svg, x, y, sc)
    beam_from = p.cam.p(1.0 + 0.3, 1.0, -1.6); beam_to = p.cam.p(1.9, 0.02, -0.5)
    p.raw(d - 0.01, f'<g filter="url(#sil)">{g}</g>')
    p.top.append(f'<polygon points="{beam_from[0]:.1f},{beam_from[1]:.1f} {beam_to[0] - 120:.1f},{beam_to[1] + 30:.1f} {beam_to[0] + 120:.1f},{beam_to[1] + 30:.1f}" fill="#fff2c0" opacity=".22" style="mix-blend-mode:screen"/>'
                 f'<circle cx="{beam_from[0]:.1f}" cy="{beam_from[1]:.1f}" r="14" fill="#fffbe8"/>')
    ov = ""
    if e > 0:
        hx, hy, _ = p.cam.p(1.9, 0.05, -0.5)
        ov = "".join(f'<circle cx="{hx + (k * 41 % 140) - 70:.0f}" cy="{hy + 30 + (t - tk) * (260 + k * 30):.0f}" r="{2 + k % 3}" fill="#d8cdb8" opacity="{max(0, .8 - (t - tk) * 2):.2f}"/>' for k in range(12))
        if t - tk < 0.06:
            ov += '<rect width="1080" height="1920" fill="#ffffff" opacity=".35"/>'
    return p.svg(sky=siren_sky(t), particles=("dust", 40), vignette=0.62, grain=0, ptime=t, overlay=ov)


def phone(t, b):
    cs = b[4]
    shown = sum(1 for c0, c1, p in cs if t >= c0 + 0.1)
    msgs = [("Ты один? Слушай.", 1), ("Через год начнётся война.", 2), ("Никому.", 3)]
    rnd = random.Random(2)
    bok = "".join(f'<circle cx="{rnd.uniform(0, 1080):.0f}" cy="{rnd.uniform(0, 1920) + 30 * math.sin(t * 0.5 + i):.0f}" r="{rnd.uniform(20, 70):.0f}" fill="{rnd.choice(["#ffd870", "#ffb050", "#ffe8a0"])}" opacity="{rnd.uniform(.08, .25):.2f}"/>' for i in range(40))
    sway = 8 * math.sin(t * 1.4); w = (t - b[1]) / (b[2] - b[1]); z = 1.0 + 0.18 * ss(w)
    K = "#14110f"; SK = "#ecdcc0"; SL = "#b8322a"
    hand = ""
    for sg in (-1, 1):
        X = (lambda x: x) if sg < 0 else (lambda x: 1080 - x)
        hand += (f'<path d="M{X(60)} 2000 L{X(250)} 1560" stroke="{K}" stroke-width="222" stroke-linecap="round"/><path d="M{X(60)} 2000 L{X(250)} 1560" stroke="{SL}" stroke-width="210" stroke-linecap="round"/>'
                 f'<path d="M{X(330)} 1200 Q{X(205)} 1190 {X(196)} 1320 Q{X(190)} 1460 {X(250)} 1540 L{X(340)} 1560 Z" fill="{SK}" stroke="{K}" stroke-width="6"/>'
                 + "".join(f'<path d="M{X(262)} {y} Q{X(206)} {y - 8} {X(204)} {y + 30} Q{X(206)} {y + 58} {X(262)} {y + 56}" fill="{SK}" stroke="{K}" stroke-width="5"/>' for y in (1070, 1135, 1200, 1265)))
    ph = (f'<rect x="262" y="380" width="556" height="1110" rx="62" fill="#15181d" stroke="{K}" stroke-width="8"/><rect x="290" y="420" width="500" height="1030" rx="40" fill="#121820"/>'
          f'<rect x="290" y="420" width="500" height="120" rx="40" fill="#1c2632"/><rect x="290" y="490" width="500" height="50" fill="#1c2632"/>'
          f'<circle cx="356" cy="482" r="32" fill="#3a8a5a"/><text x="356" y="494" text-anchor="middle" font-family="{FONT}" font-weight="800" font-size="32" fill="#fff">М</text>'
          f'<text x="404" y="474" font-family="{FONT}" font-weight="800" font-size="32" fill="#fff">Макс (служба)</text><text x="404" y="508" font-family="{FONT}" font-weight="600" font-size="22" fill="#5ac87a">в сети</text>')
    y = 590
    for k, (m, need) in enumerate(msgs):
        if shown >= need:
            c0 = cs[min(need, len(cs) - 1) - 1][0] + 0.1
            sc, op = pop(t, c0)
            lines = [m] if len(m) < 16 else [m[:m.rfind(" ", 0, 16)], m[m.rfind(" ", 0, 16) + 1:]]
            hh = 40 + 52 * len(lines); ww = 420 if len(lines) > 1 else 40 + 24 * len(m)
            ph += (f'<g opacity="{op:.2f}" transform="translate(312 {y}) scale({sc:.3f})"><rect width="{ww}" height="{hh}" rx="24" fill="#26384c"/>'
                   + "".join(f'<text x="22" y="{56 + 52 * j}" font-family="{FONT}" font-weight="700" font-size="40" fill="#fff">{esc(l)}</text>' for j, l in enumerate(lines)) + "</g>")
            y += hh + 26
    thumbs = "".join(f'<path d="M{X(250)} 1520 Q{X(300)} 1420 {X(380)} 1330" fill="none" stroke="{K}" stroke-width="86" stroke-linecap="round"/><path d="M{X(250)} 1520 Q{X(300)} 1420 {X(380)} 1330" fill="none" stroke="{SK}" stroke-width="74" stroke-linecap="round"/>'
                     for X in ((lambda x: x), (lambda x: 1080 - x)))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920" viewBox="0 0 1080 1920"><defs><radialGradient id="pbg" cx="50%" cy="40%" r="80%"><stop offset="0" stop-color="#1c2232"/><stop offset="1" stop-color="#07080c"/></radialGradient>'
            f'<filter id="bk"><feGaussianBlur stdDeviation="12"/></filter></defs><rect width="1080" height="1920" fill="url(#pbg)"/><g filter="url(#bk)">{bok}</g>'
            f'<g transform="translate(540 900) scale({z:.3f}) translate(-540 -900) translate(0 {sway:.1f})">{hand}{ph}{thumbs}</g></svg>')


# ---------- кадр ----------
AIRANGE = {  # какую часть старой сцены (по её времени) показывать в такте
    "count": lambda: (S(2, 0.0), S(2, 0.2)), "market": lambda: (S(2, 0.2), S(2, 0.46)), "super": lambda: (S(2, 0.46), S(2, 0.72)),
    "pharm": lambda: (S(2, 0.72), S(2, 1.0)), "calc": lambda: (S(3, 0), S(3, 1)), "tech": lambda: (S(4, 0), AI.word_time(4, "четыре") - 0.16),
    "food": lambda: (AI.word_time(4, "четыре"), S(4, 1)), "climb": lambda: (S(5, 0), S(5, 1)), "friend": lambda: (S(6, 0), S(6, 0.4)),
    "knew": lambda: (S(6, 0.4), S(6, 0.75)), "shock": lambda: (S(6, 0.75), S(6, 1)), "up": lambda: (S(7, 0), S(7, 1)),
    "village": lambda: (S(8, 0), S(8, 1)), "calc2": lambda: (S(9, 0), S(9, 1)), "end": lambda: (S(10, 0), S(10, 1)),
    "hook": lambda: (S(0, 0.05), S(0, 0.5)), "knock2": lambda: (S(0, 0.72), S(0, 1.0)),
}
ROLL = {"knock2": -2.5, "shock": 3.0, "up": -2.0, "knew": 1.5, "hook": 1.0}


def overlays(t, b):
    name = b[0]; cs = b[4]; ov = hud(t, b)
    T1 = b[2]
    if name == "hook":
        ov += PILL(t, cs[0][0], T1, "ЕДА: ≈11 000 ПОРЦИЙ", "w", 1) + PILL(t, cs[1][0], T1, "НА 5 ЧЕЛОВЕК · 2 ГОДА", "y", 2)
        ov += CARD(t, cs[1][0], cs[3][0], "can", 230, 1560, .85) + CARD(t, cs[1][0] + .12, cs[3][0], "jar", 540, 1560, .85) + CARD(t, cs[1][0] + .24, cs[3][0], "mre", 850, 1560, .85)
        ov += PILL(t, cs[3][0], T1, "+1 = 6 ЧЕЛОВЕК", "r", 3)
    if name == "calc":
        ov += PILL(t, cs[0][0], T1, "≈11 000 ПОРЦИЙ", "w", 1) + PILL(t, cs[1][0], T1, "11 000 ÷ 6 ÷ 3 = 608 ДНЕЙ", "w", 2) + PILL(t, cs[2][0], T1, "НА 6 — 20 МЕС, НЕ 24", "r", 3)
    if name == "tech":
        ov += PILL(t, cs[0][0], T1, "ВОЗДУХ ✓", "w", 1) + PILL(t, cs[1][0], T1, "ВОДА ✓", "w", 2) + PILL(t, cs[2][0], T1, "СВЕТ ✓", "w", 3)
        ov += CARD(t, cs[0][0], cs[1][0], "fan", 540, 1560, 1.1) + CARD(t, cs[1][0], cs[2][0], "drop", 330, 1560) + CARD(t, cs[1][0] + .12, cs[2][0], "bottle", 750, 1560)
        ov += CARD(t, cs[2][0], T1 + .01, "bulb", 330, 1560) + CARD(t, cs[2][0] + .12, T1 + .01, "gen", 750, 1560)
    if name == "food":
        ov += PILL(t, cs[1][0], T1, "−4 МЕСЯЦА ЕДЫ", "r", 1)
        ov += CARD(t, cs[1][0], T1 + .01, "can", 230, 1560, .9, "−") + CARD(t, cs[1][0] + .15, T1 + .01, "mre", 540, 1560, .9, "−") + CARD(t, cs[1][0] + .3, T1 + .01, "meal", 850, 1560, .9, "−")
    if name == "calc2":
        ov += PILL(t, cs[0][0], T1, "+3 СОСЕДА = 9 ЧЕЛОВЕК", "w", 1) + PILL(t, cs[2][0], T1, "11 000 ÷ 9 ÷ 3 = 405 ДНЕЙ", "w", 2) + PILL(t, cs[3][0], T1, "≈ 13 МЕСЯЦЕВ", "r", 3)
    if name == "village":
        ov += '<rect width="1080" height="1920" fill="#e8c890" opacity=".14" style="mix-blend-mode:multiply"/>'
    if name == "end" and t > cs[-1][0]:
        sc, op = pop(t, cs[-1][0] + 0.3)
        ov += (f'<g opacity="{op:.2f}" transform="translate(540 430) scale({sc:.3f})"><rect x="-430" y="-150" width="860" height="300" rx="36" fill="#0e0f14" opacity=".82"/>'
               f'<text x="0" y="-80" text-anchor="middle" font-family="{FONT}" font-weight="700" font-size="34" fill="#9aa0b0">часть 3</text>'
               f'<text x="0" y="10" text-anchor="middle" font-family="{FONT}" font-weight="900" font-size="80" fill="#f2c94c">ПУСКАТЬ СОСЕДЕЙ?</text>'
               f'<text x="0" y="80" text-anchor="middle" font-family="{FONT}" font-weight="700" font-size="34" fill="#e8e8ee">ДА или НЕТ — пиши в комментах</text></g>')
    return ov + caption(t)


def frame(t):
    b = beat_at(t); name = b[0]
    if name == "cut_intro":
        inner = cut_intro(t, b)
    elif name == "knock":
        inner = knock(t, b)
    elif name == "phone":
        inner = phone(t, b)
    else:
        a0, a1 = AIRANGE[name]()
        inner = AI.frame(ai_map(t, b, a0, a1))
    w = (t - b[1]) / max(0.01, b[2] - b[1])
    roll = ROLL.get(name, 0.0) * (0.4 + 0.6 * ss(w))
    zoom = 1.0 + 0.04 * w   # лёгкий наезд в каждом плане
    svg = wrap(inner, t, roll, zoom, overlays(t, b))
    AI.WHIPS[:] = WHIPS
    return WHIP(svg, t)


# ---------- звуки (немного, только на важных движениях) ----------
def build_sfx(path, sr=48000):
    import numpy as np, wave
    n = int((TOTAL + 0.5) * sr); out = np.zeros(n)
    rng = np.random.default_rng(1)

    def add(t0, x, g=1.0):
        i = int(t0 * sr)
        if i >= n:
            return
        x = x[: n - i]; out[i:i + len(x)] += g * x

    def env(d, a=0.005, k=8.0):
        t = np.arange(int(d * sr)) / sr
        return t, np.minimum(1, t / a) * np.exp(-k * t)

    def lowpass(x, k=12):
        return np.convolve(x, np.ones(k) / k, mode="same")

    def thud():  # глухой удар по стальному люку
        t, e = env(0.6, 0.002, 9)
        x = 0.9 * np.sin(2 * np.pi * 58 * t) + 0.25 * np.sin(2 * np.pi * 116 * t)
        x += 0.18 * np.sin(2 * np.pi * 412 * t) * np.exp(-22 * t) + 0.12 * np.sin(2 * np.pi * 873 * t) * np.exp(-30 * t)
        x += 0.35 * lowpass(rng.normal(size=len(t)), 40) * np.exp(-40 * t)
        return x * e

    def clank():  # лязг запоров и тяжёлой крышки
        t, e = env(1.2, 0.002, 4)
        x = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-k * t) for f, a, k in ((523, .5, 5), (1187, .35, 7), (1840, .25, 9), (2550, .15, 12), (90, .6, 6)))
        return x * e + 0.3 * lowpass(rng.normal(size=len(t)), 6) * np.exp(-25 * t)

    def creak(d=0.8):  # скрип петли
        t = np.arange(int(d * sr)) / sr
        f = 180 + 120 * t / d + 15 * np.sin(2 * np.pi * 7 * t)
        x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / sr)) * 0.25 + 0.15 * np.sin(2 * np.pi * np.cumsum(f * 2.01) / sr)
        return lowpass(x, 8) * np.sin(np.pi * t / d) ** 1.5

    def ping():  # уведомление в мессенджере
        t, e = env(0.35, 0.003, 14)
        return (0.6 * np.sin(2 * np.pi * 1318 * t) + 0.4 * np.sin(2 * np.pi * 1760 * t) * (t > 0.07)) * e

    def whoosh(d=0.32):  # резкий переход
        t = np.arange(int(d * sr)) / sr
        x = rng.normal(size=len(t)); x = lowpass(x, 5) - lowpass(x, 60)
        return x * np.sin(np.pi * t / d) ** 2

    def boom(d=1.8):  # низкий удар на шоке и в финале
        t, e = env(d, 0.004, 2.6)
        return (np.sin(2 * np.pi * (46 - 8 * t) * t) + 0.3 * lowpass(rng.normal(size=len(t)), 60)) * e

    def drip():
        t, e = env(0.18, 0.001, 30)
        return np.sin(2 * np.pi * (900 + 1400 * np.exp(-30 * t)) * t) * e

    def hum(d, f0=50):  # ровный гул вентиляции/генератора
        t = np.arange(int(d * sr)) / sr
        x = 0.6 * np.sin(2 * np.pi * f0 * t) + 0.3 * np.sin(2 * np.pi * 2 * f0 * t) + 0.12 * lowpass(rng.normal(size=len(t)), 30)
        fade = np.minimum(1, np.minimum(t / 0.4, (d - t) / 0.5))
        return x * np.clip(fade, 0, 1)

    def siren_tail(d=1.4):  # сирена вдалеке затихает в самом начале
        t = np.arange(int(d * sr)) / sr
        f = 620 + 220 * np.sin(2 * np.pi * 0.7 * t)
        return np.sin(2 * np.pi * np.cumsum(f) / sr) * (1 - t / d) ** 2

    B = {b[0]: b for b in TL}
    add(0.0, siren_tail(), 0.08)
    for c0, c1, p_ in B["knock"][4]:
        add(c0, thud(), 0.9)
    for c0, c1, p_ in B["phone"][4][:3]:
        add(c0 + 0.1, ping(), 0.18)
    for w in WHIPS:
        add(w - 0.16, whoosh(), 0.12)
    tb = B["tech"]; cs = tb[4]
    add(cs[0][0], hum(tb[2] - cs[0][0], 62), 0.07)                 # вентилятор ФВУ
    for k in range(3):
        add(cs[1][0] + 0.1 + k * 0.33, drip(), 0.12)                # капли из скважины
    add(cs[2][0], hum(tb[2] - cs[2][0] + 0.2, 38), 0.1)            # генератор
    cb = B["climb"]; t_open = cb[1] + 0.45 * (cb[2] - cb[1])
    add(t_open - 0.35, clank(), 0.35); add(t_open, creak(), 0.18)
    add(B["shock"][4][-1][0], boom(), 0.35)
    add(B["end"][4][-1][0] + 0.3, boom(1.4), 0.22)
    peak = np.max(np.abs(out)) or 1.0
    out = out / max(1.0, peak) * 0.9
    with wave.open(path, "w") as wv:
        wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(sr)
        wv.writeframes((out * 32767).astype("<i2").tobytes())


def main():
    if "--frames" in sys.argv:
        ts = [float(x) for x in sys.argv[sys.argv.index("--frames") + 1].split(",")]
        fs = []
        for tt in ts:
            fn = os.path.join(HERE, "illus_out", f"x{tt:05.1f}.svg"); open(fn, "w").write(frame(tt)); fs.append(fn)
        subprocess.run(["node", os.path.join(HERE, "render_frames.js"), "--png", *fs], check=True)
        return
    k0, n = 0, int(TOTAL * FPS)
    rng = "--range" in sys.argv
    if rng:
        a, b = [float(x) for x in sys.argv[sys.argv.index("--range") + 1].split(",")]; k0, n = int(a * FPS), int(b * FPS)
    tmp = os.path.join(HERE, "video", "_a2.mp4")
    pr = subprocess.Popen(["node", os.path.join(HERE, "render_frames.js"), tmp, str(FPS), str(SCALE)], stdin=subprocess.PIPE)
    for k in range(k0, n):
        pr.stdin.write((json.dumps({"i": k - k0, "svg": frame(k / FPS)}) + "\n").encode())
        if k % 150 == 0:
            print(f"кадр {k}/{n}", flush=True)
    pr.stdin.close(); pr.wait()
    if rng:
        print(tmp); return
    common = ["-c:v", "libx264", "-preset", "slow", "-tune", "animation", "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", str(FPS), "-g", str(FPS * 2),
              "-x264-params", "aq-mode=3:aq-strength=0.9:deblock=-1,-1", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
              "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart"]
    yt = OUT.replace(".mp4", "-youtube-1440p.mp4"); tt = OUT.replace(".mp4", "-tiktok-1080p.mp4")
    fx = os.path.join(HERE, "video", "_sfx_a2.wav"); build_sfx(fx)
    if os.path.exists(VOICE):  # голос + звуки
        aud = ["-i", VOICE, "-i", fx]
        af = ["-filter_complex", "[1:a]loudnorm=I=-14:TP=-1.5:LRA=11,apad[v];[2:a]volume=1.0[f];[v][f]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]",
              "-map", "0:v", "-map", "[a]"]
    else:
        aud = ["-i", fx]; af = ["-map", "0:v", "-map", "1:a"]
    common = [c for c in common if c != "-shortest"] + ["-t", f"{TOTAL:.2f}"]
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, *aud, *af, "-crf", "16", "-maxrate", "40M", "-bufsize", "80M", "-b:a", "192k", *common, yt], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, *aud, *af, "-vf", "scale=1080:1920:flags=lanczos",
                    "-crf", "17", "-maxrate", "20M", "-bufsize", "40M", "-b:a", "192k", *common, tt], check=True)
    os.remove(tmp); print(yt, tt, f"{TOTAL:.1f} с")


if __name__ == "__main__":
    main()
