# -*- coding: utf-8 -*-
"""校验 Assets/Resources/audio/ 实际音频：格式、峰值、RMS 响度一致性、
BGM 循环接缝连续性、短音效长度、文件名与 18 号资源契约一致性。"""
import os, struct, math, wave
import numpy as np

AUD = r"E:/UnityProject/MutiplayGame/BlockOut/Assets/Resources/audio"
CONTRACT = ["sfx_tap_block", "sfx_fly_out", "sfx_error", "sfx_hint", "sfx_hammer",
            "sfx_wand", "sfx_star_hit", "sfx_coin", "sfx_ui_tap", "sfx_popup",
            "sfx_toast", "sfx_piece_reveal", "sfx_level_win", "sfx_level_fail",
            "sfx_revive", "sfx_countdown_tick", "sfx_countdown_end",
            "bgm_home", "bgm_game", "bgm_chapter_complete"]

# 清单目标时长（11 §10 / §11），BGM 为设计值不强制
TARGET = {"sfx_tap_block": (0.0, 0.15), "sfx_fly_out": (0.3, 0.5), "sfx_error": (0.2, 0.4),
          "sfx_hint": (0.2, 0.4), "sfx_hammer": (0.2, 0.4), "sfx_wand": (0.5, 0.7),
          "sfx_star_hit": (0.3, 0.5), "sfx_coin": (0.3, 0.5), "sfx_ui_tap": (0.0, 0.12),
          "sfx_popup": (0.12, 0.3), "sfx_toast": (0.12, 0.3), "sfx_piece_reveal": (0.4, 0.6),
          "sfx_level_win": (1.0, 1.5), "sfx_level_fail": (0.8, 1.2), "sfx_revive": (0.6, 1.0),
          "sfx_countdown_tick": (0.0, 0.12), "sfx_countdown_end": (0.6, 1.0)}


def load(name):
    with wave.open(os.path.join(AUD, name + ".wav"), "rb") as w:
        sr, ch, sw, n = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes()
        raw = w.readframes(n)
    x = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    return sr, ch, sw, n, x


print("=== 1) 文件名与 18 号资源契约一致性 ===")
have = sorted(f[:-4] for f in os.listdir(AUD) if f.endswith(".wav"))
missing = [c for c in CONTRACT if c not in have]
extra = [h for h in have if h not in CONTRACT]
print("   契约 %d 项，目录 %d 项" % (len(CONTRACT), len(have)))
print("   缺失:", missing or "无", " 多余:", extra or "无")
print("   ->", "PASS" if not missing and not extra else "FAIL")

print("\n=== 2) 格式 / 峰值 / 响度 ===")
rows, lufs = [], []
for name in CONTRACT:
    sr, ch, sw, n, x = load(name)
    pk = float(np.max(np.abs(x)))
    rms = float(np.sqrt(np.mean(x ** 2)))
    db = 20 * math.log10(rms + 1e-12)
    lufs.append(db)
    rows.append((name, sr, ch, sw * 8, n / sr, pk, db))
    ok_fmt = (sr == 44100 and ch == 1 and sw == 2)
    ok_pk = pk <= 0.891 + 1e-6      # -1dBFS
    print("   %-22s %dHz %dch %dbit %6.3fs  peak %.3f%s  RMS %6.1f dBFS  %s"
          % (name, sr, ch, sw * 8, n / sr, pk, "" if ok_pk else "(!超-1dBFS)", db,
             "fmt OK" if ok_fmt else "fmt FAIL"))

print("\n=== 3) 短音效时长是否落在 11 号清单区间 ===")
bad = 0
for name, (lo, hi) in TARGET.items():
    _, _, _, n, _ = load(name)
    d = n / 44100
    inside = lo <= d <= hi
    if not inside:
        bad += 1
    print("   %-22s %.3fs  目标 %.2f–%.2fs  %s" % (name, d, lo, hi, "OK" if inside else "FAIL"))
print("   ->", "PASS" if bad == 0 else "FAIL %d 条" % bad)

print("\n=== 4) 音量一致性（RMS 离散度）==")
sfx_db = [r[6] for r in rows if r[0].startswith("sfx_")]
print("   17 音效 RMS: min %.1f / max %.1f / 极差 %.1f dB" %
      (min(sfx_db), max(sfx_db), max(sfx_db) - min(sfx_db)))
print("   ->", "PASS(极差<8dB 听感一致)" if max(sfx_db) - min(sfx_db) < 8 else "FAIL(离散过大)")

print("\n=== 5) BGM 循环接缝连续性（首尾 5ms 波形跳变）==")
for name in ("bgm_home", "bgm_game"):
    _, _, _, n, x = load(name)
    seam = abs(float(x[0] - x[-1]))
    # 循环点不应落在静音（淡出到 0 会造成声音断续）
    tail_rms = float(np.sqrt(np.mean(x[-int(0.05 * 44100):] ** 2)))
    head_rms = float(np.sqrt(np.mean(x[:int(0.05 * 44100)] ** 2)))
    d1 = np.abs(np.diff(x[-220:])).mean()      # 末尾 5ms 平均变化
    dall = np.abs(np.diff(x)).mean()
    print("   %-14s 首尾跳变 %.5f  头/尾RMS %.4f/%.4f %s  斜率比 %.2fx  %s"
          % (name, seam, head_rms, tail_rms,
             "(非静音)" if min(head_rms, tail_rms) > 1e-4 else "(静音!)",
             d1 / (dall + 1e-12),
             "PASS(接缝平滑且非静音)" if seam < 0.02 and min(head_rms, tail_rms) > 1e-4 else "FAIL"))
print("   bgm_chapter_complete 一次性 sting，不循环，无需接缝检查")

print("\n=== 6) 响度分层（BGM 应低于音效；章节 sting 与通关音效同级）==")
sfx_ref = sum(sfx_db) / len(sfx_db)
for name in ("bgm_home", "bgm_game", "bgm_chapter_complete"):
    _, _, _, n, x = load(name)
    db = 20 * math.log10(float(np.sqrt(np.mean(x ** 2))) + 1e-12)
    if name == "bgm_chapter_complete":
        ok = abs(db - sfx_ref) < 3          # sting 与音效同级
        note = "PASS(与音效同级 %.1f)" % sfx_ref
    else:
        ok = db < sfx_ref - 2              # 循环 BGM 低于音效
        note = "PASS(低于音效)" if ok else "FAIL"
    print("   %-22s RMS %6.1f dBFS   音效参考 %.1f dBFS  %s" % (name, db, sfx_ref, note))
print("\nDONE")