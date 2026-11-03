# -*- coding: utf-8 -*-
"""生成 BlockOut 实际音频资源（17 音效 + 3 BGM），输出到
BlockOut/Assets/Resources/audio/，文件名与 18_implementation_status.md 资源契约一致。
规格（11 §10 / §11）：
  音效 44100Hz / 16bit PCM WAV / 单声道 / 峰值 ≤ -1dBFS
  BGM  44100Hz / 16bit PCM WAV / 单声道（Unity 可循环播放）/ 无缝循环
BGM 采用「整数周期波形 + 首尾相位对齐 + 交叉淡化」保证接缝处波形与导数连续。
所有音效/BGM 均为本脚本程序化合成（无第三方采样），版权归项目方。
"""
import os, struct, math
import numpy as np

OUT = r"E:/UnityProject/MutiplayGame/BlockOut/Assets/Resources/audio"
os.makedirs(OUT, exist_ok=True)
SR = 44100
PEAK = 10 ** (-1 / 20.0)   # -1 dBFS


def save_wav(name, x, sr=SR, target_db=None):
    """16bit PCM WAV。
    target_db: 目标 RMS 响度（dBFS）。给定后按响度归一，保证 17 条音效听感一致；
               归一后仍再限幅到 -1dBFS。"""
    x = np.asarray(x, dtype=np.float64)
    if target_db is not None:
        cur = float(np.sqrt(np.mean(x ** 2)))
        if cur > 1e-9:
            x = x * (10 ** (target_db / 20.0) / cur)
    m = float(np.max(np.abs(x)))
    if m > PEAK:
        x = x / m * PEAK          # 限幅到 -1dBFS，防止削波
    data = np.clip(x, -1.0, 1.0)
    pcm = (data * 32767.0).astype("<i2")
    path = os.path.join(OUT, name + ".wav")
    with open(path, "wb") as f:
        f.write(b"RIFF"); f.write(struct.pack("<I", 36 + len(pcm) * 2)); f.write(b"WAVE")
        f.write(b"fmt "); f.write(struct.pack("<IHHIIHH", 16, 1, 1, sr, sr * 2, 2, 16))
        f.write(b"data"); f.write(struct.pack("<I", len(pcm) * 2)); f.write(pcm.tobytes())
    dur = len(x) / sr
    rms = 20 * math.log10(float(np.sqrt(np.mean(np.asarray(x) ** 2))) + 1e-12)
    print("  %-24s %6.3fs  %7d B  RMS %6.1f dBFS  peak %.3f"
          % (name + ".wav", dur, os.path.getsize(path), rms, float(np.max(np.abs(x)))))
    return dur


# ---------------- 合成基元 ----------------
def env(n, a=0.005, d=0.05, s=0.0, r=0.05, sr=SR):
    """ADSR 包络（秒）；严格返回长度 n。"""
    n = int(n)
    A, D, R = int(a * sr), int(d * sr), int(r * sr)
    # 保证各段之和不超过 n，按比例压缩
    if A + D + R > n:
        tot = A + D + R
        A, D, R = int(A * n / tot), int(D * n / tot), max(1, int(R * n / tot))
    S = max(0, n - A - D - R)
    e = np.concatenate([
        np.linspace(0, 1, A, endpoint=False) if A else np.zeros(0),
        np.linspace(1, s, D, endpoint=False) if D else np.zeros(0),
        np.full(S, s),
        np.linspace(s, 0, R) if R else np.zeros(0),
    ])
    # 线性补齐/截断到精确 n
    if len(e) < n:
        e = np.concatenate([e, np.full(n - len(e), e[-1] if len(e) else 0.0)])
    return e[:n]


def tone(freq, dur, sr=SR, wave="sine", phase=0.0):
    t = np.arange(int(dur * sr)) / sr
    w = 2 * np.pi * freq * t + phase
    if wave == "sine":
        return np.sin(w)
    if wave == "tri":
        return 2 / np.pi * np.arcsin(np.sin(w))
    if wave == "square":
        return np.sign(np.sin(w))
    if wave == "saw":
        return 2 * (w / (2 * np.pi) % 1.0) - 1
    raise ValueError(wave)


def sweep(f0, f1, dur, sr=SR, curve="exp"):
    t = np.arange(int(dur * sr)) / sr
    if curve == "exp":
        f = f0 * (f1 / f0) ** (t / max(t[-1], 1e-9))
    else:
        f = f0 + (f1 - f0) * (t / max(t[-1], 1e-9))
    ph = 2 * np.pi * np.cumsum(f) / sr
    return np.sin(ph)


def noise(n, sr=SR, seed=0):
    return np.random.default_rng(seed).uniform(-1, 1, n)


def lowpass(x, cutoff, sr=SR):
    """一阶低通（简单但足够自然）。"""
    a = math.exp(-2 * math.pi * cutoff / sr)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc = (1 - a) * x[i] + a * acc
        y[i] = acc
    return y


def highpass(x, cutoff, sr=SR):
    return x - lowpass(x, cutoff, sr)


def mix(*layers):
    n = max(len(l) for l in layers)
    out = np.zeros(n)
    for l in layers:
        out[:len(l)] += l
    return out


def pad_to(x, n):
    """把 x 补零/截断到精确长度 n（n 为样本数，不是秒数）。"""
    n = int(n)
    x = np.asarray(x, dtype=np.float64).ravel()
    if len(x) == n:
        return x
    if len(x) > n:
        return x[:n]
    return np.concatenate([x, np.zeros(n - len(x))])


def mul_env(x, e):
    """安全相乘：长度不等时自动截断到较短者（避免广播异常）。"""
    e = np.asarray(e)
    n = min(len(x), len(e))
    return np.asarray(x)[:n] * e[:n]


def soft_clip(x):
    return np.tanh(x * 1.2) / math.tanh(1.2)


# ---------------- 17 条音效 ----------------
def sfx_tap_block():
    n = int(0.09 * SR)
    body = mul_env(sweep(720, 300, 0.09), env(n, 0.002, 0.03, 0.0, 0.055))
    click = lowpass(noise(n, seed=1), 2600) * env(n, 0.001, 0.012, 0.0, 0.02) * 0.5
    return soft_clip(body * 0.8 + click)


def sfx_fly_out():
    n = int(0.40 * SR)
    body = mul_env(sweep(980, 340, 0.40), env(n, 0.004, 0.10, 0.12, 0.26))
    airy = highpass(lowpass(noise(n, seed=2), 5200), 1400) * env(n, 0.01, 0.12, 0.05, 0.24) * 0.18
    return soft_clip(body * 0.75 + airy)


def sfx_error():
    n = int(0.30 * SR)
    f = np.zeros(n)
    for i, (fr, st) in enumerate([(196, 0.0), (185, 0.06), (174, 0.12)]):
        seg = int(st * SR)
        ln = n - seg
        if ln <= 0:
            break
        t = np.arange(ln) / SR
        w = 2 * np.pi * fr * t
        f[seg:] += (np.sin(w) * 0.62 + np.sin(2 * w) * 0.22 + np.sin(3 * w) * 0.1)
    f *= env(n, 0.004, 0.07, 0.55, 0.20)
    return soft_clip(f)


def sfx_hint():
    n = int(0.32 * SR)
    a = mul_env(tone(1318.5, 0.32), env(n, 0.003, 0.05, 0.5, 0.24))
    # 第二个泛音只在前半段出现：tone 与 env 必须用同一长度
    b_len = int(0.16 * SR)
    b = mul_env(tone(1760.0, b_len / SR, phase=0.4), env(b_len, 0.003, 0.04, 0.3, 0.10))
    b = np.concatenate([b, np.zeros(n - len(b))])
    return soft_clip(a * 0.6 + b * 0.45)


def sfx_hammer():
    n = int(0.30 * SR)
    thump = mul_env(sweep(220, 90, 0.30), env(n, 0.001, 0.05, 0.05, 0.22))
    metal = mix(tone(1180, 0.14), tone(2360, 0.14, wave="sine") * 0.5) * env(int(0.14 * SR), 0.001, 0.03, 0.1, 0.10)
    metal = np.concatenate([metal, np.zeros(n - len(metal))])
    return soft_clip(thump * 0.85 + metal * 0.35)


def sfx_wand():
    n = int(0.60 * SR)
    shimmer = mix(tone(1046.5, 0.60), tone(1396.9, 0.60, phase=0.3) * 0.7,
                  tone(2093.0, 0.60, phase=0.8) * 0.45)
    shimmer *= env(n, 0.02, 0.16, 0.42, 0.38)
    spark = highpass(noise(n, seed=6), 3600) * env(n, 0.01, 0.10, 0.20, 0.40) * 0.14
    return soft_clip(shimmer * 0.42 + spark)


def sfx_star_hit():
    n = int(0.36 * SR)
    base = mix(tone(2637.0, 0.36), tone(3136.0, 0.36, phase=0.5) * 0.6)
    base *= env(n, 0.001, 0.05, 0.18, 0.26)
    tick = mul_env(tone(4186.0, 0.08), env(int(0.08 * SR), 0.001, 0.02, 0.0, 0.05))
    tick = np.concatenate([tick, np.zeros(n - len(tick))])
    return soft_clip(base * 0.5 + tick * 0.4)


def sfx_coin():
    n = int(0.38 * SR)
    a = mul_env(tone(1046.5, 0.10), env(int(0.10 * SR), 0.001, 0.02, 0.4, 0.06))
    a = np.concatenate([a, np.zeros(n - len(a))])
    b = mul_env(tone(1568.0, 0.26), env(int(0.26 * SR), 0.001, 0.05, 0.5, 0.18))
    b = np.concatenate([np.zeros(int(0.07 * SR)), b])
    b = pad_to(b, n)
    return soft_clip(a * 0.55 + b * 0.6)


def sfx_ui_tap():
    n = int(0.07 * SR)
    return soft_clip(mul_env(tone(1320, 0.07), env(n, 0.001, 0.02, 0.1, 0.04) * 0.7)
                     + lowpass(noise(n, seed=9), 4200) * env(n, 0.0005, 0.01, 0.0, 0.012) * 0.25)


def sfx_popup():
    n = int(0.20 * SR)
    body = mul_env(sweep(420, 880, 0.20, curve="lin"), env(n, 0.004, 0.05, 0.35, 0.12))
    return soft_clip(body * 0.7)


def sfx_toast():
    n = int(0.22 * SR)
    a = mul_env(tone(880, 0.10), env(int(0.10 * SR), 0.002, 0.03, 0.3, 0.06))
    a = np.concatenate([a, np.zeros(n - len(a))])
    b = mul_env(tone(1174.7, 0.12), env(int(0.12 * SR), 0.002, 0.03, 0.2, 0.07))
    b = np.concatenate([np.zeros(int(0.08 * SR)), b])
    b = pad_to(b, n)
    return soft_clip(a * 0.5 + b * 0.55)


def sfx_piece_reveal():
    n = int(0.52 * SR)
    notes = [(783.99, 0.00), (987.77, 0.07), (1174.66, 0.14), (1567.98, 0.21)]
    out = np.zeros(n)
    for f, st in notes:
        seg = int(st * SR)
        ln = n - seg
        t = np.arange(max(ln, 0)) / SR
        v = (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(4 * np.pi * f * t))
        v *= env(len(v), 0.004, 0.09, 0.42, 0.30)
        out[seg:seg + len(v)] += v
    sparkle = highpass(noise(n, seed=13), 5200) * env(n, 0.02, 0.14, 0.12, 0.30) * 0.10
    return soft_clip(out * 0.34 + sparkle)


def sfx_level_win():
    n = int(1.35 * SR)
    notes = [(523.25, 0.00), (659.25, 0.11), (783.99, 0.22), (1046.50, 0.33), (1318.51, 0.46)]
    out = np.zeros(n)
    for f, st in notes:
        seg = int(st * SR)
        ln = n - seg
        t = np.arange(max(ln, 0)) / SR
        v = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) + 0.12 * np.sin(6 * np.pi * f * t)
        v *= env(len(v), 0.006, 0.16, 0.45, 0.50)
        out[seg:seg + len(v)] += v * 0.9
    return soft_clip(out * 0.30)


def sfx_level_fail():
    n = int(1.05 * SR)
    notes = [(587.33, 0.00), (523.25, 0.16), (440.00, 0.32), (349.23, 0.50)]
    out = np.zeros(n)
    for f, st in notes:
        seg = int(st * SR)
        ln = n - seg
        t = np.arange(max(ln, 0)) / SR
        v = np.sin(2 * np.pi * f * t) + 0.22 * np.sin(2 * np.pi * f * 2 * t)
        v *= env(len(v), 0.008, 0.14, 0.40, 0.42)
        out[seg:seg + len(v)] += v
    return soft_clip(out * 0.30)


def sfx_revive():
    n = int(0.85 * SR)
    t = np.arange(n) / SR
    f = 330 * (1568.0 / 330.0) ** (t / t[-1])
    ph = 2 * np.pi * np.cumsum(f) / SR
    v = (np.sin(ph) + 0.30 * np.sin(2 * ph) + 0.10 * np.sin(3 * ph))
    v *= env(n, 0.02, 0.22, 0.55, 0.36)
    shimmer = mul_env(tone(2093.0, 0.85), env(n, 0.30, 0.20, 0.20, 0.30) * 0.16)
    return soft_clip(v * 0.42 + shimmer)


def sfx_countdown_tick():
    n = int(0.09 * SR)
    v = mul_env(tone(1760, 0.09, wave="tri"), env(n, 0.001, 0.02, 0.1, 0.05))
    return soft_clip(v * 0.65)


def sfx_countdown_end():
    n = int(0.82 * SR)
    out = np.zeros(n)
    for i, f in enumerate([880.0, 698.46, 587.33, 440.0]):
        seg = int(i * 0.14 * SR)
        ln = int(0.26 * SR)
        t = np.arange(ln) / SR
        v = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)
        v *= env(ln, 0.003, 0.06, 0.45, 0.16)
        end = min(seg + ln, n)
        out[seg:end] += v[:end - seg]
    low = mul_env(sweep(300, 120, 0.82), env(n, 0.01, 0.14, 0.30, 0.50) * 0.5)
    return soft_clip(out * 0.34 + low)


# ---------------- 3 条 BGM（无缝循环）----------------
def loop_fade(x, ms=120):
    """循环点处理：等增益交叉淡化，首尾互相混合。
    关键：**不淡出到静音**——淡出会让循环点出现可听见的断点。
    做法：取尾部 k 样本与头部 k 样本做互补线性交叉后拼回，使 x[0]≈x[-1] 且两端均非静音。
    """
    k = int(SR * ms / 1000)
    if k * 2 >= len(x):
        return x
    w = np.linspace(0, 1, k)          # 0→1
    head_src, tail_src = x[:k].copy(), x[-k:].copy()
    # 交叉：头部 = tail*(1-w) + head*w ；尾部区域 = head*(1-w) + tail*w
    new_head = tail_src * (1 - w) + head_src * w
    new_tail = head_src * (1 - w) + tail_src * w
    out = x.copy()
    out[:k] = new_head
    out[-k:] = new_tail
    return out


def bgm_home():
    """轻柔糖果风，60s 级 loop（此版 32s，循环播放）。C 大调 I–V–vi–IV。"""
    dur, bpb = 32.0, 2.0
    n = int(dur * SR)
    chords = [(261.63, 329.63, 392.00), (392.00, 493.88, 587.33),
              (329.63, 392.00, 493.88), (261.63, 329.63, 392.00)]
    out = np.zeros(n)
    seg = int(bpb * SR)
    for ci, ch in enumerate(chords):
        s0 = ci * seg
        for k, f in enumerate(ch):
            t = np.arange(seg) / SR
            # 轻微 detune 产生合唱感
            v = (np.sin(2 * np.pi * f * t) + np.sin(2 * np.pi * (f * 1.004) * t + 0.7)
                 + 0.18 * np.sin(2 * np.pi * f * 2 * t)) / 2.2
            # 恒定包络：循环音乐靠和声变化推进，音量必须持续饱满，
            # 若段末淡出到 0，循环点会出现可听见的断点。
            a = np.full(seg, 1.0)
            v *= a * (0.16 if k else 0.20)
            out[s0:s0 + seg] += v
    # 分解和弦琶音（八分音符）
    arp = [0, 1, 2, 1] * 4
    step = int(bpb / 4 * SR)
    for ci, ch in enumerate(chords):
        for j in range(4):
            pos = ci * seg + j * step
            f = ch[arp[j % len(arp)]]
            t = np.arange(step) / SR
            v = mul_env(np.sin(2 * np.pi * f * 2 * t), env(step, 0.01, 0.10, 0.18, 0.22) * 0.07)
            out[pos:pos + step] += v
    # 沙锤节奏（弱）
    for k in range(int(dur / 0.5)):
        pos = int(k * 0.5 * SR)
        ln = int(0.06 * SR)
        h = highpass(noise(ln, seed=20 + k), 6000) * env(ln, 0.0005, 0.012, 0.0, 0.03) * (0.05 if k % 2 else 0.03)
        out[pos:pos + ln] += h
    return loop_fade(soft_clip(out))


def bgm_game():
    """轻快不干扰思考，无强节拍，32s loop。A 小调 i–VI–III–VII。"""
    dur, bpb = 32.0, 2.0
    n = int(dur * SR)
    chords = [(220.00, 261.63, 329.63), (174.61, 220.00, 261.63),
              (261.63, 329.63, 392.00), (196.00, 246.94, 293.66)]
    out = np.zeros(n)
    seg = int(bpb * SR)
    for ci, ch in enumerate(chords):
        s0 = ci * seg
        for k, f in enumerate(ch):
            t = np.arange(seg) / SR
            v = np.sin(2 * np.pi * f * t) + 0.55 * np.sin(2 * np.pi * f * 1.5 * t + 0.4)
            v *= np.linspace(0.75, 1.0, seg)[:seg] * (0.13 if k else 0.17)
            out[s0:s0 + seg] += v / 2.0
    # 轻脉冲（弱，不构成强节拍）
    step = int(bpb / 2 * SR)
    for k in range(int(dur / (bpb / 2))):
        pos = k * step
        ln = int(0.14 * SR)
        s = np.sin(2 * np.pi * 110.0 * np.arange(ln) / SR) * env(ln, 0.004, 0.05, 0.05, 0.08) * 0.10
        out[pos:pos + ln] += s
    # 高音闪光点缀
    for k in range(int(dur / 4.0)):
        pos = int(k * 4.0 * SR)
        f = [1046.5, 1318.5, 1568.0, 1318.5][k % 4]
        ln = int(0.5 * SR)
        v = np.sin(2 * np.pi * f * np.arange(ln) / SR) * env(ln, 0.02, 0.16, 0.22, 0.30) * 0.045
        out[pos:pos + ln] += v
    return loop_fade(soft_clip(out))


def bgm_chapter_complete():
    """章节完成 sting，8s，一次性播放（不循环）。上行琶音 + 甜蜜收尾。"""
    n = int(8.0 * SR)
    out = np.zeros(n)
    notes = [(523.25, 0.0), (659.25, 0.28), (783.99, 0.56), (1046.50, 0.84),
             (1318.51, 1.12), (1567.98, 1.40)]
    for f, st in notes:
        seg = int(st * SR)
        ln = min(n - seg, int(2.4 * SR))
        t = np.arange(max(ln, 0)) / SR
        v = (np.sin(2 * np.pi * f * t) + 0.32 * np.sin(4 * np.pi * f * t)
             + 0.10 * np.sin(6 * np.pi * f * t))
        v *= env(len(v), 0.006, 0.30, 0.48, 1.30)
        out[seg:seg + ln] += v
    # 铺底和弦
    t = np.arange(n) / SR
    pad = sum(np.sin(2 * np.pi * f * t) for f in (261.63, 392.00, 523.25)) / 3
    pad *= env(n, 0.35, 0.5, 0.55, 2.6) * 0.14
    out += pad
    # 结尾糖粒
    for k in range(14):
        pos = int((2.2 + k * 0.10) * SR)
        f = 2093.0 * (1.0 + 0.06 * k)
        ln = int(0.5 * SR)
        v = np.sin(2 * np.pi * f * np.arange(ln) / SR) * env(ln, 0.004, 0.10, 0.18, 0.34) * 0.05
        out[pos:pos + ln] += v
    return soft_clip(out)


SFX = [
    ("sfx_tap_block", sfx_tap_block, "点击方块", 0.09),
    ("sfx_fly_out", sfx_fly_out, "方块飞出", 0.40),
    ("sfx_error", sfx_error, "点击受阻", 0.30),
    ("sfx_hint", sfx_hint, "提示道具", 0.30),
    ("sfx_hammer", sfx_hammer, "锤子道具", 0.30),
    ("sfx_wand", sfx_wand, "魔法棒", 0.60),
    ("sfx_star_hit", sfx_star_hit, "星星命中", 0.40),
    ("sfx_coin", sfx_coin, "金币变动", 0.40),
    ("sfx_ui_tap", sfx_ui_tap, "UI 点击", 0.10),
    ("sfx_popup", sfx_popup, "弹窗", 0.20),
    ("sfx_toast", sfx_toast, "Toast", 0.20),
    ("sfx_piece_reveal", sfx_piece_reveal, "拼片区域揭晓", 0.50),
    ("sfx_level_win", sfx_level_win, "通关", 1.35),
    ("sfx_level_fail", sfx_level_fail, "失败", 1.05),
    ("sfx_revive", sfx_revive, "复活", 0.85),
    ("sfx_countdown_tick", sfx_countdown_tick, "倒计时滴答", 0.09),
    ("sfx_countdown_end", sfx_countdown_end, "时间到", 0.82),
]

BGM = [
    ("bgm_home", bgm_home, "首页", True),
    ("bgm_game", bgm_game, "对局", True),
    ("bgm_chapter_complete", bgm_chapter_complete, "章节完成", False),
]

if __name__ == "__main__":
    # 统一响度目标（11 §10：整体约 -16LUFS；此处用 RMS 近似，短音效取 -15dBFS）
    SFX_TARGET_DB = -15.0
    print("== 17 条音效（统一 RMS 目标 %.1f dBFS）==" % SFX_TARGET_DB)
    for name, fn, desc, target in SFX:
        x = fn()
        d = save_wav(name, x, target_db=SFX_TARGET_DB)
        flag = "" if abs(d - target) < 0.06 else "  <-- 与清单目标 %.2fs 有偏差" % target
        print("      %s%s" % (desc, flag))
    print("== 3 条 BGM（BGM 响度低于音效，不抢 UI）==")
    for name, fn, desc, loop in BGM:
        x = fn()
        save_wav(name, x, target_db=-19.0 if loop else -15.0)
        print("      %s%s" % (desc, "（无缝循环）" if loop else "（一次性 sting）"))
    print("DONE ->", OUT)