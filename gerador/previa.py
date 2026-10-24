import sys, json, pathlib
from playwright.sync_api import sync_playwright
html, cfgp, prefix = sys.argv[1], sys.argv[2], sys.argv[3]; times = [float(x) for x in sys.argv[4:]]
cfg = json.loads(pathlib.Path(cfgp).read_text())
chrome = next((str(p) for p in pathlib.Path("/opt/pw-browsers").glob("chromium-*/chrome-linux/chrome")), None)
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=chrome); pg = b.new_page(viewport={"width":1080,"height":1920})
    pg.goto(pathlib.Path(html).resolve().as_uri()); pg.evaluate("c => build(c)", cfg); print("TOTAL", pg.evaluate("TOTAL"))
    t = 0; i = 0
    for target in times:
        while t < target: pg.evaluate(f"render({t})"); t += 1/30
        pg.screenshot(path=f"{prefix}_{i}.jpg", type="jpeg", quality=70); i += 1
    b.close()
