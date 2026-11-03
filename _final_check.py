import re, os, collections

BS = chr(92)  # backslash

def strip_comments(s):
    out = []; i = 0; n = len(s); ins = None; lc = False; bc = False
    while i < n:
        c = s[i]; nx = s[i+1] if i+1 < n else ''
        if lc:
            if c == '\n': lc = False
            i += 1; continue
        if bc:
            if c == '*' and nx == '/': bc = False; i += 2; continue
            i += 1; continue
        if ins:
            if ins == '@"':
                if c == '"':
                    if nx == '"': i += 2; continue
                    ins = None; i += 1; continue
                i += 1; continue
            else:
                if c == BS: i += 2; continue
                if c == ins: ins = None
                i += 1; continue
        if c == '/' and nx == '/': lc = True; i += 2; continue
        if c == '/' and nx == '*': bc = True; i += 2; continue
        if c == '@' and nx == '"': ins = '@"'; i += 2; continue
        if c == '"' or c == "'": ins = c; i += 1; continue
        out.append(c); i += 1
    return ''.join(out)

files = [os.path.join(r, f) for r, _, fs in os.walk(".") for f in fs if f.endswith(".cs")]
allok = True
for p in sorted(files):
    s = strip_comments(open(p, encoding='utf-8').read())
    st = []; pr = {')': '(', ']': '[', '}': '{'}; ok = True
    for i, c in enumerate(s):
        if c in '([{': st.append((c, i))
        elif c in pr:
            if not st or st[-1][0] != pr[c]:
                print("MISMATCH %s line %d" % (p, s[:i].count('\n')+1)); ok = False; break
            st.pop()
    if ok and st:
        print("UNCLOSED %s : %s" % (p, [(x[0], s[:x[1]].count('\n')+1) for x in st[-3:]])); ok = False
    if not ok: allok = False
print("BRACKETS:", "ALL OK" if allok else "FAILURES", "(%d files)" % len(files))

src = {}
for r, _, fs in os.walk("."):
    for f in fs:
        if f.endswith(".cs"):
            src[os.path.normpath(os.path.join(r, f))] = open(os.path.join(r, f), encoding='utf-8').read()
def get(n):
    for k in src:
        if k.endswith(n): return src[k]
    raise KeyError(n)

decl = collections.defaultdict(set)
for p, s in src.items():
    s2 = strip_comments(s)
    for m in re.finditer(r'(?:public|internal)\s+(?:static\s+|sealed\s+|abstract\s+|partial\s+)*(?:class|struct)\s+(\w+)', s2):
        cn = m.group(1); i = s2.find('{', m.end()); d = 0; j = i; body = []
        while j < len(s2):
            if s2[j] == '{': d += 1
            elif s2[j] == '}':
                d -= 1
                if d == 0: break
            body.append(s2[j]); j += 1
        b = ''.join(body)
        for mm in re.finditer(r'\b(?:public|private|protected|internal)\s+(?:static\s+|readonly\s+|const\s+|new\s+|override\s+|virtual\s+|sealed\s+)*[\w<>\[\],\.\?]+\s+(\w+)\s*(?:=|;|\(|\{|=>)', b):
            decl[cn].add(mm.group(1))
        for mm in re.finditer(r'\bpublic\s+event\s+[\w<>\.]+\s+(\w+)', b):
            decl[cn].add(mm.group(1))

ctrl = get("BlockOutUIController.cs")
bad = 0
for owner, pref in [("BlockOutUIManager", "UI"), ("BlockOutGameManager", "GM"),
                    ("BlockOutToolController", "Tools"), ("BlockOutPlayerProfile", "Profile"),
                    ("BlockOutCatalog", "Catalog"), ("BlockOutChapterArtProvider", "artProvider"),
                    ("BlockOutContentConfig", "ContentConfig"), ("BlockOutDesignTokens", "BlockOutDesignTokens"),
                    ("BlockOutIconFactory", "BlockOutIconFactory"), ("BlockOutWidgets", "BlockOutWidgets")]:
    f = set(decl.get(owner, set())); u = set(re.findall(r'\b' + pref + r'\.(\w+)', ctrl))
    miss = sorted(x for x in u if x not in f)
    if miss:
        print("MISSING %s.%s -> %s" % (pref, owner, miss)); bad += len(miss)
print("CROSS-REF:", "ALL OK" if bad == 0 else "%d missing" % bad)
