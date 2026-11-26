#!/usr/bin/env python3
"""Аниматик в 1080x1920 из раскадровки: python3 render_video.py A B C D E [--nograin]

Против пережатия YouTube/TikTok:
- сцены рисуются как вектор и снимаются в 2160x3840, потом ужимаются в 1080x1920 (чёткие края, без «лесенки»);
- кадр лежит в безопасной зоне (сверху 130 px, снизу 480 px, по бокам 171 px), чтобы интерфейс не закрывал субтитры;
- тёмные градиенты прикрыты зерном (noise): без него платформа режет их в блоки и ступеньки;
- x264 с aq-mode=3 (больше бит на тёмные области), crf 16, bt709, yuv420p, faststart.
"""
import os, re, subprocess, sys
import build_storyboard as B1
import build_storyboard_2 as B2

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "video")
ALL = {v["slug"]: v for v in B1.VIDEOS + B2.VIDEOS2}
FPS = 30


def svg(fn):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {B1.W} {B1.H}" width="{B1.W}" height="{B1.H}">{fn()}</svg>'


def page(svg_markup):
    return f"""<!doctype html><meta charset="utf-8"><style>
html,body{{margin:0;width:1080px;height:1920px;overflow:hidden;background:#0b0d11}}
.bg{{position:absolute;left:-200px;top:-340px;width:1480px;height:2631px;filter:blur(60px) brightness(.5) saturate(1.1)}}
.fg{{position:absolute;left:171px;top:130px;width:737px;height:1310px;border-radius:26px;overflow:hidden}}
svg{{display:block;width:100%;height:100%}}
</style><div class="bg">{svg_markup}</div><div class="fg">{svg_markup}</div>"""


def durations(v):
    out = []
    for _, tm, *_ in v["scenes"]:
        a, b = re.match(r"(\d+)-(\d+)", tm).groups()
        out.append(int(b) - int(a))
    return out


def render(slug, grain=True):
    v = ALL[slug]
    fr = os.path.join(OUT, f"frames_{slug}")
    os.makedirs(fr, exist_ok=True)
    for f in os.listdir(fr):
        os.remove(os.path.join(fr, f))
    for i, (fn, *_rest) in enumerate(v["scenes"], 1):
        open(os.path.join(fr, f"s{i:02d}.html"), "w", encoding="utf8").write(page(svg(fn)))
    subprocess.run(["node", os.path.join(HERE, "shot_frames.js"), fr], check=True)
    durs = durations(v)
    cmd, graph = ["ffmpeg", "-y", "-loglevel", "error"], []
    for i, d in enumerate(durs):
        cmd += ["-i", os.path.join(fr, f"s{i+1:02d}.png")]
        n = d * FPS
        z = f"1+0.05*on/{n}" if i % 2 == 0 else f"1.05-0.05*on/{n}"
        graph.append(f"[{i}:v]zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s=1080x1920:fps={FPS}[v{i}]")
    graph.append("".join(f"[v{i}]" for i in range(len(durs))) + f"concat=n={len(durs)}:v=1:a=0[c]")
    post = "scale=out_color_matrix=bt709:flags=lanczos"
    if grain:
        post = "noise=alls=3:allf=t," + post
    graph.append(f"[c]{post},format=yuv420p[o]")
    name = f"bunker-{slug}{'' if grain else '-nograin'}.mp4"
    cmd += ["-filter_complex", ";".join(graph), "-map", "[o]", "-c:v", "libx264", "-preset", "slow", "-crf", "18",
            "-profile:v", "high", "-level", "4.2", "-g", "60", "-bf", "2", "-x264-params", "aq-mode=3:aq-strength=1.1:deblock=-1,-1",
            "-maxrate", "18M", "-bufsize", "36M", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
            "-movflags", "+faststart", os.path.join(OUT, name)]
    subprocess.run(cmd, check=True)
    print("ok", name, round(os.path.getsize(os.path.join(OUT, name)) / 1e6, 1), "МБ")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    for s in args or ["A"]:
        render(s, "--nograin" not in sys.argv)
