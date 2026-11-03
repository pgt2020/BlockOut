import re, glob, os, sys

OLD_GUID = "e7d74714e2044a26bbdbbc2401c2ba01"
NEW_GUID = "15221c43fda64980a908947d5a7d4263"

small_ref = re.compile(r'\{fileID: (\d+)\}')
anchor_re = re.compile(r'&(\d+)\s*$')

base = "Assets/BlockOut/Resources/Prefabs"
prefabs = sorted(glob.glob(base + "/**/*.prefab", recursive=True))
scene = "Assets/BlockOut/Scenes/Launcher.unity"

def remap_small(text):
    anchors = set(int(m.group(1)) for m in anchor_re.finditer(text))
    misses = []
    def repl(m):
        n = int(m.group(1))
        if n == 0 or n >= 1000:
            return m.group(0)
        target = 1000000000000000 + n * 1000
        if target not in anchors:
            misses.append((n, target))
        return "{fileID: %d}" % target
    out = small_ref.sub(repl, text)
    return out, misses

total_changed = 0
problems = []
for f in prefabs:
    raw = open(f, 'rb').read().decode('utf-8')
    text, misses = remap_small(raw)
    guid_hits = raw.count(OLD_GUID)
    if guid_hits:
        text = text.replace(OLD_GUID, NEW_GUID)
    if text != raw:
        open(f, 'wb').write(text.encode('utf-8'))
        n_small = len([1 for m in small_ref.finditer(raw) if 0 < int(m.group(1)) < 1000])
        total_changed += 1
        print("%-40s small_fixed=%d guid_replaced=%d" % (os.path.basename(f), n_small, guid_hits))
    for n, t in misses:
        problems.append((f, n, t))

# scene appRootPrefab fix
sraw = open(scene, 'rb').read().decode('utf-8')
snew = sraw.replace(
    "appRootPrefab: {fileID: 1000000000000000, guid: 7f4a029d26f643c2898c7d62703effe4, type: 3}",
    "appRootPrefab: {fileID: 1000000000001000, guid: 7f4a029d26f643c2898c7d62703effe4, type: 3}")
if snew != sraw:
    open(scene, 'wb').write(snew.encode('utf-8'))
    print("Launcher.unity appRootPrefab fileID fixed")

print("prefabs changed:", total_changed)
if problems:
    print("!!! MISSING ANCHORS:", problems)
    sys.exit(1)
print("all remapped small fileIDs have matching anchors: OK")
