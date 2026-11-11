"""Prévia: python3 serie/quadros.py <index.html> <pasta_saida> t1 t2 ... -> JPGs dos instantes pedidos."""
import asyncio, sys, pathlib
from playwright.async_api import async_playwright
import shutil
CHROME = next((str(x) for x in pathlib.Path("/opt/pw-browsers").glob("chromium-*/chrome-linux/chrome")), None) or shutil.which("google-chrome") or shutil.which("chromium")
html = pathlib.Path(sys.argv[1]).resolve(); out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"]); pg = await b.new_page(viewport={"width": 1080, "height": 1920})
        await pg.goto(html.as_uri()); await pg.wait_for_timeout(500)
        for t in sys.argv[3:]:
            await pg.evaluate(f"render({float(t)})"); await pg.screenshot(path=str(out / f"q_{float(t):05.2f}.jpg"), type="jpeg", quality=80)
        await b.close()
asyncio.run(main())
