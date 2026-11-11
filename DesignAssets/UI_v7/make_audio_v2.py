# -*- coding: utf-8 -*-
"""
UI_v7 audio kit. Pure stdlib, no third-party assets, no deps.

Builds:
  audio/*.wav         10 original warm-wood / soft-light UI sounds
  audio/manifest.json durations, peak, rms, spectral centroid
  ui_audio.html       ui_final.html + audio bound to real controls (self-contained)
  UI_v7_audio.zip     everything above + this script

Design: marimba/xylophone inharmonic partials + wooden knock transient
+ short early-reflection room + gentle low-pass. No plain sine beeps.
Re-run after tuning any number below.
"""
import math
import os
import struct
import wave
import base64
import zipfile
import json
import random

SR = 44100
ROOT = os.path.dirname(os.path.abspath(__file__))
AUD = os.path.join(ROOT, "audio")
os.makedirs(AUD, exist_ok=True)
random.seed(20261110)

MARIMBA = [(1.0, 1.0, 1.0), (4.02, 0.20, 0.55), (9.30, 0.07, 0.32)]
XYLO = [(1.0, 1.0, 1.0), (3.01, 0.30, 0.48), (6.04, 0.11, 0.28)]
SOFT = [(1.0, 1.0, 1.0), (2.02, 0.16, 0.70), (4.06, 0.06, 0.45)]


def lp(buf, cutoff):
    rc = 1.0 / (2 * math.pi * cutoff)
    a = (1.0 / SR) / (rc + 1.0 / SR)
    v = 0.0
    out = [0.0] * len(buf)
    for i, x in enumerate(buf):
        v += a * (x - v)
        out[i] = v
    return out


def mallet(freq, dur, amp=0.5, partials=None, attack=0.008,
           decay=0.20, offset=0.0, detune=0.0):
    partials = partials or MARIMBA
    n = int(SR * dur)
    off = int(SR * offset)
    buf = [0.0] * (n + off)
    ph = [0.0] * len(partials)
    for i in range(n):
        t = i / SR
        f0 = freq * (1.0 + 0.0035 * math.exp(-t / 0.018)) * (1.0 + detune)
        v = 0.0
        for k, (ratio, pa, pd) in enumerate(partials):
            ph[k] += 2 * math.pi * f0 * ratio / SR
            v += math.sin(ph[k]) * pa * math.exp(-t / (decay * pd))
        atk = 1.0 - math.exp(-t / attack) if attack > 0 else 1.0
        tail = max(0.0, min(1.0, (dur - t) / 0.030))
        buf[off + i] = v * amp * atk * tail
    return buf


def knock(dur, amp=0.15, cutoff=2600, offset=0.0):
    n = int(SR * dur)
    off = int(SR * offset)
    buf = [0.0] * (n + off)
    rc = 1.0 / (2 * math.pi * cutoff)
    a = (1.0 / SR) / (rc + 1.0 / SR)
    v = 0.0
    for i in range(n):
        t = i / SR
        v += a * (random.uniform(-1, 1) - v)
        buf[off + i] = v * amp * math.exp(-t / 0.006)
    return buf


def sweep(f0, f1, dur, amp=0.3, offset=0.0):
    n = int(SR * dur)
    off = int(SR * offset)
    buf = [0.0] * (n + off)
    ph = 0.0
    for i in range(n):
        t = i / SR
        f = f0 * (f1 / f0) ** (t / dur)
        ph += 2 * math.pi * f / SR
        e = math.sin(math.pi * t / dur)
        buf[off + i] = math.sin(ph) * amp * e
    return buf


def room(buf, amount=0.22):
    n = len(buf)
    out = list(buf)
    for delay, gain in ((0.017, 0.34), (0.029, 0.25), (0.043, 0.18), (0.067, 0.11)):
        d = int(SR * delay)
        for i in range(d, n):
            out[i] += buf[i - d] * gain * amount
    return lp(out, 3900)


def mix(*bufs):
    n = max(len(b) for b in bufs)
    out = [0.0] * n
    for b in bufs:
        for i, v in enumerate(b):
            out[i] += v
    return out


def arp(freqs, step, dur, amp, partials, decay, offset=0.0):
    return mix(*[mallet(f, dur, amp, partials, decay=decay, offset=offset + i * step)
                 for i, f in enumerate(freqs)])


def finish(buf, target=0.72):
    buf = lp(buf, 5200)
    n = len(buf)
    fade = int(SR * 0.003)
    for i in range(min(fade, n)):
        buf[i] *= i / fade
        buf[n - 1 - i] *= i / fade
    peak = max(1e-9, max(abs(v) for v in buf))
    g = target / peak
    return [v * g for v in buf]


def pcm(buf):
    return struct.pack("<%dh" % len(buf),
                       *[int(max(-1.0, min(1.0, v)) * 32767) for v in buf])


def centroid(buf):
    x = buf[:8192]
    if not x:
        return 0.0
    num = den = 0.0
    for k in range(28):
        f = 180.0 * (9000.0 / 180.0) ** (k / 27.0)
        w = 2 * math.pi * f / SR
        c = 2 * math.cos(w)
        s1 = s2 = 0.0
        for v in x:
            s0 = v + c * s1 - s2
            s2, s1 = s1, s0
        mag = math.sqrt(max(0.0, s1 * s1 + s2 * s2 - c * s1 * s2))
        num += f * mag
        den += mag
    return num / den if den else 0.0


SOUNDS = [
    ("ui_hover", "悬停", "极轻的木质高点，默认关闭，验货条可开",
     mix(mallet(1568, 0.10, 0.30, SOFT, decay=0.055), knock(0.012, 0.05, 3400))),
    ("ui_tap", "按钮点击", "软木敲一下，暖、短、连点不糊",
     mix(mallet(784, 0.18, 0.58, MARIMBA, decay=0.13), knock(0.020, 0.17, 2300))),
    ("ui_back", "返回", "下行两音，方向感明确",
     mix(mallet(659, 0.16, 0.42, MARIMBA, decay=0.13),
         mallet(494, 0.22, 0.40, MARIMBA, decay=0.17, offset=0.075))),
    ("card_pick", "选卡", "木琴单音带一点亮泛音",
     mix(mallet(880, 0.24, 0.50, XYLO, decay=0.17), knock(0.015, 0.10, 3000))),
    ("tile_tap", "点方块", "清脆短击，比按钮更硬一点",
     mix(mallet(1046, 0.16, 0.54, XYLO, decay=0.10), knock(0.018, 0.19, 3100))),
    ("match", "消除", "三音上行琶音，每点满 3 个方块触发",
     mix(arp([659.25, 783.99, 987.77], 0.055, 0.20, 0.42, MARIMBA, 0.17),
         mallet(1318.5, 0.30, 0.20, SOFT, decay=0.22, offset=0.11))),
    ("combo", "连击", "四级上行 + 长亮尾，每 9 个方块触发",
     mix(arp([659.25, 783.99, 987.77, 1318.5], 0.048, 0.16, 0.40, XYLO, 0.13),
         mallet(1568, 0.42, 0.22, SOFT, decay=0.30, offset=0.192))),
    ("prop", "道具", "短促上扫 + 木质落点，不刺耳",
     mix(sweep(420, 1500, 0.22, 0.34), knock(0.020, 0.12, 2600),
         mallet(1318.5, 0.20, 0.24, SOFT, decay=0.15, offset=0.10))),
    ("win", "过关", "大调琶音 + 稍长房间尾音",
     mix(arp([523.25, 659.25, 783.99, 1046.5], 0.115, 0.28, 0.36, MARIMBA, 0.24),
         mallet(2093, 0.62, 0.16, SOFT, decay=0.40, offset=0.345))),
    ("lose", "失败", "小三度下行 + 闷木噪，挫败但不刺",
     mix(mallet(392, 0.24, 0.38, SOFT, decay=0.20),
         mallet(311.13, 0.30, 0.34, SOFT, decay=0.24, offset=0.135),
         knock(0.20, 0.07, 800, offset=0.06))),
]

items = []
for name, label, desc, raw in SOUNDS:
    buf = finish(room(raw, 0.30 if name == "win" else 0.22))
    path = os.path.join(AUD, name + ".wav")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm(buf))
    rms = math.sqrt(sum(v * v for v in buf) / len(buf))
    items.append({
        "name": name, "label": label, "desc": desc,
        "dur": round(len(buf) / SR, 3),
        "size": os.path.getsize(path),
        "peak": round(max(abs(v) for v in buf), 3),
        "rms": round(rms, 4),
        "centroid_hz": round(centroid(buf)),
        "b64": base64.b64encode(open(path, "rb").read()).decode("ascii"),
    })

with open(os.path.join(AUD, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump([{k: v for k, v in it.items() if k != "b64"} for it in items],
              f, ensure_ascii=False, indent=2)

INJECT = r"""
<style>
#sfxbar{position:fixed;right:10px;bottom:10px;z-index:99;display:none;width:262px;
background:rgba(255,247,231,.97);border:1px solid rgba(120,90,60,.24);border-radius:10px;
padding:11px 13px;font:12px/1.55 "Microsoft YaHei",sans-serif;color:#6b533c}
#sfxbar b{font-weight:500;font-size:12px}
#sfxbar .r{display:flex;flex-wrap:wrap;gap:5px;margin-top:9px}
#sfxbar button{font:inherit;font-size:11px;border:1px solid rgba(120,90,60,.24);
background:#fffaf0;color:#6b533c;border-radius:6px;padding:3px 7px;cursor:pointer}
#sfxbar button:hover{background:#f2e2c4}
#sfxbar .m{font-size:11px;color:#8b7458;margin-top:9px;line-height:1.6}
</style>
<div id="sfxbar"><b>音效验货 · 按 M 收起</b><div class="r">__BUTTONS__</div>
<div class="m">9 屏控件已按类别绑定：按钮 / 卡片 / 方块 / 道具 / 返回。<br>
方块每 3 次叠加「消除」、每 9 次叠加「连击」。<br>
H 悬停音 · S 静音 · W 过关 · L 失败 · 1–9 切屏</div></div>
<script>
(function(){
var SFX=__SFX__;
var muted=false,hoverOn=false,lastHover=0,tileN=0;
function play(n,vol){if(muted||!SFX[n])return;var a=new Audio(SFX[n]);a.volume=vol||1;a.play().catch(function(){});}
window.playSfx=play;
document.addEventListener('click',function(e){
  var t=e.target.closest('.ui');if(!t||t.closest('#sfxbar'))return;
  var cat=t.dataset.cat||'',nm=t.dataset.name||'';
  if(nm.indexOf('prop_')===0){play('prop');return}
  if(cat==='tile'){tileN++;play('tile_tap');
    if(tileN%3===0)setTimeout(function(){play('match',.8)},70);
    if(tileN%9===0)setTimeout(function(){play('combo',.8)},160);return}
  if(cat==='card'){play('card_pick');return}
  if(nm.indexOf('back')>=0){play('ui_back');return}
  if(cat==='panel'||cat==='decor'||cat==='artword'||cat==='text'||cat==='bar'||cat==='plate'||cat==='hud'){
    play('ui_hover',.45);return}
  play('ui_tap');
});
document.addEventListener('mouseover',function(e){
  if(!hoverOn||muted)return;var now=Date.now();if(now-lastHover<110)return;lastHover=now;
  if(e.target.closest('.ui'))play('ui_hover',.28);
});
document.addEventListener('keydown',function(e){
  var k=e.key.toLowerCase();
  if(k==='m'){var b=document.getElementById('sfxbar');b.style.display=b.style.display==='none'?'block':'none';return}
  if(k==='h'){hoverOn=!hoverOn;return}
  if(k==='s'){muted=!muted;return}
  if(k==='w'){play('win');return}
  if(k==='l'){play('lose');return}
  if(k>='1'&&k<='9'){location.hash='#s'+k}
});
})();
</script>
"""

buttons = "".join('<button onclick="playSfx(\'%s\')">%s</button>' % (it["name"], it["label"])
                  for it in items)
sfx_json = json.dumps({it["name"]: "data:audio/wav;base64," + it["b64"] for it in items})
inject = INJECT.replace("__BUTTONS__", buttons).replace("__SFX__", sfx_json)

src_path = os.path.join(ROOT, "ui_final.html")
with open(src_path, "r", encoding="utf-8") as f:
    src = f.read()
assert src.count("</body></html>") == 1, "unexpected ui_final.html structure"
out_html = src.replace("</body></html>", inject + "</body></html>")
out_html = out_html.replace("<title>点击画廊 · v7 控件级 UI（9 屏）</title>",
                            "<title>点击画廊 · v7 控件级 UI（9 屏）· 含音效</title>")

# Inline every slice so the HTML is a genuine single file: double-click works,
# and the preview panel works even when it only serves the .html itself.
import re
_img = {}


def _uri(rel):
    if rel not in _img:
        with open(os.path.join(ROOT, rel), "rb") as fh:
            _img[rel] = "data:image/png;base64," + base64.b64encode(fh.read()).decode("ascii")
    return _img[rel]


out_html = re.sub(r'src="((?:bg|assets|tilekit)/[^"]+)"',
                  lambda m: 'src="' + _uri(m.group(1)) + '"', out_html)
html_path = os.path.join(ROOT, "ui_audio.html")
with open(html_path, "w", encoding="utf-8") as f:
    f.write(out_html)

zip_path = os.path.join(ROOT, "UI_v7_audio.zip")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for it in items:
        z.write(os.path.join(AUD, it["name"] + ".wav"), "audio/" + it["name"] + ".wav")
    z.write(os.path.join(AUD, "manifest.json"), "audio/manifest.json")
    z.write(html_path, "ui_audio.html")
    z.write(os.path.abspath(__file__), "make_audio_v2.py")

# objective brightness check against the rejected v1 kit
v1 = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(ROOT))),
                  "outputs", "ui-sfx-kit", "sfx")
v1_c = []
if os.path.isdir(v1):
    for fn in os.listdir(v1):
        if fn.endswith(".wav"):
            with wave.open(os.path.join(v1, fn)) as w:
                s = struct.unpack("<%dh" % w.getnframes(), w.readframes(w.getnframes()))
                v1_c.append(centroid([v / 32768.0 for v in s]))

print("generated %d wav -> audio/" % len(items))
for it in items:
    print("  %-11s %5.2fs  %5.1fKB  peak %.2f  centroid %5dHz  %s"
          % (it["name"], it["dur"], it["size"] / 1024, it["peak"], it["centroid_hz"], it["label"]))
print("v2 mean centroid: %d Hz" % (sum(i["centroid_hz"] for i in items) / len(items)))
if v1_c:
    print("v1 mean centroid: %d Hz  (rejected beep kit)" % (sum(v1_c) / len(v1_c)))
print("ui_audio.html %.1f KB (self-contained, original ui_final.html untouched)"
      % (os.path.getsize(html_path) / 1024))
print("UI_v7_audio.zip %.1f KB" % (os.path.getsize(zip_path) / 1024))
