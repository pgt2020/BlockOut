import os
import glob
import subprocess
import urllib.parse

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE = os.path.dirname(os.path.abspath(__file__))
SCREEN_DIR = os.path.join(BASE, "screens")
EXPORT_DIR = os.path.join(BASE, "exports")

os.makedirs(EXPORT_DIR, exist_ok=True)
files = sorted(glob.glob(os.path.join(SCREEN_DIR, "*.html")))

for f in files:
    name = os.path.splitext(os.path.basename(f))[0] + ".png"
    out = os.path.join(EXPORT_DIR, name)
    path = os.path.abspath(f)
    # encode Chinese characters in path for file URL
    url = "file:///" + urllib.parse.quote(path.replace("\\", "/"), safe="/:")
    cmd = [
        CHROME,
        "--headless",
        "--disable-gpu",
        f"--screenshot={out}",
        "--window-size=375,812",
        url,
    ]
    print(f"Rendering {name} ...")
    subprocess.run(cmd, check=True)

print(f"\nDone. {len(files)} screenshots saved to {EXPORT_DIR}")
