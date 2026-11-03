import re, glob, os, sys

pattern = re.compile(r'fileID[^0-9]*([0-9]+)')
base = "Assets/BlockOut/Resources/Prefabs"
files = sorted(glob.glob(base + "/**/*.prefab", recursive=True))
print("found files:", len(files))
total = {}
for f in files:
    data = open(f, 'rb').read().decode('utf-8')
    hits = {}
    for m in pattern.finditer(data):
        n = int(m.group(1))
        if n != 0 and n < 1000:
            hits[n] = hits.get(n, 0) + 1
    if hits:
        print(os.path.basename(f), "->", hits)
        for k, v in hits.items():
            total[k] = total.get(k, 0) + v
print("total small fileIDs:", total)
