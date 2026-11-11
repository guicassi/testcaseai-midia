"""Renderiza um episódio da série (página HTML com window.render(t) e window.SCENES).
Uso: python3 serie/render.py <index.html> <pasta_saida> [indices de cena para refazer...]
Gera uma MP4 por cena (30 fps, H.264) e <pasta_saida>/video_mudo.mp4 (concat).
"""
import asyncio, subprocess, os, sys, pathlib
from playwright.async_api import async_playwright
import shutil
CHROME = next((str(x) for x in pathlib.Path("/opt/pw-browsers").glob("chromium-*/chrome-linux/chrome")), None) or shutil.which("google-chrome") or shutil.which("chromium")
FPS = 30
html = pathlib.Path(sys.argv[1]).resolve(); out = pathlib.Path(sys.argv[2]).resolve(); out.mkdir(parents=True, exist_ok=True)
only = [int(x) for x in sys.argv[3:]]
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 1080, "height": 1920})
        await pg.goto(html.as_uri()); await pg.wait_for_timeout(500)
        scenes = await pg.evaluate("SCENES"); files = []
        for i, (a, e) in enumerate(scenes):
            fin = out / f"s{i}.mp4"; files.append(fin)
            if only and i not in only: continue
            tmp = out / f"s{i}.tmp.mp4"; n = round((e - a) * FPS)
            ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
                                   "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), str(tmp)], stdin=subprocess.PIPE)
            for k in range(n):
                await pg.evaluate(f"render({a + k / FPS})")
                ff.stdin.write(await pg.screenshot(type="jpeg", quality=92))
            ff.stdin.close(); assert ff.wait() == 0
            os.rename(tmp, fin); print("cena", i, n, "quadros", flush=True)
        await b.close()
    lst = out / "list.txt"; lst.write_text("".join(f"file '{f}'\n" for f in files))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out / "video_mudo.mp4")], check=True)
asyncio.run(main())
