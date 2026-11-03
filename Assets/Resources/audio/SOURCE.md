# 音频资源 · 来源与授权记录

## 交付清单（20 个文件，全部实际存在）

路径：`BlockOut/Assets/Resources/audio/`
加载方式：程序 `Resources.Load<AudioClip>("audio/" + id)`（见 `BlockOutSettings.cs:49`），文件名即 id，**已逐一对齐，无需改名**。

### 音效 17 条（44100Hz / 16bit PCM WAV / 单声道）

| 文件 | 场景 | 实测时长 | RMS |
| --- | --- | --- | --- |
| `sfx_tap_block.wav` | 点击方块 | 0.090s | −15.1 dBFS |
| `sfx_fly_out.wav` | 方块飞出 | 0.400s | −15.0 dBFS |
| `sfx_error.wav` | 点击受阻 | 0.300s | −15.0 dBFS |
| `sfx_hint.wav` | 提示道具 | 0.320s | −15.1 dBFS |
| `sfx_hammer.wav` | 锤子道具 | 0.300s | −15.0 dBFS |
| `sfx_wand.wav` | 魔法棒 | 0.600s | −15.0 dBFS |
| `sfx_star_hit.wav` | 星星命中 | 0.360s | −15.0 dBFS |
| `sfx_coin.wav` | 金币变动 | 0.380s | −15.0 dBFS |
| `sfx_ui_tap.wav` | UI 点击 | 0.070s | −15.0 dBFS |
| `sfx_popup.wav` | 弹窗 | 0.200s | −15.0 dBFS |
| `sfx_toast.wav` | Toast | 0.220s | −15.0 dBFS |
| `sfx_piece_reveal.wav` | 拼片区域揭晓 | 0.520s | −15.0 dBFS |
| `sfx_level_win.wav` | 通关 | 1.350s | −15.0 dBFS |
| `sfx_level_fail.wav` | 失败 | 1.050s | −15.0 dBFS |
| `sfx_revive.wav` | 复活 | 0.850s | −15.0 dBFS |
| `sfx_countdown_tick.wav` | 倒计时滴答 | 0.090s | −15.0 dBFS |
| `sfx_countdown_end.wav` | 时间到 | 0.820s | −15.0 dBFS |

### BGM / 章末音乐 3 条

| 文件 | 场景 | 时长 | RMS | 循环 |
| --- | --- | --- | --- | --- |
| `bgm_home.wav` | 首页 | 32.000s | −19.0 dBFS | 无缝循环 |
| `bgm_game.wav` | 对局 | 32.000s | −19.0 dBFS | 无缝循环 |
| `bgm_chapter_complete.wav` | 章节完成 sting | 8.000s | −15.0 dBFS | 一次性 |

## 来源与授权

- **作者**：本项目设计侧原创产出（程序化合成，脚本 `UI原型/design_v5/gen_audio.py`）。
- **第三方素材**：**无**。全部波形由加法合成 + 噪声整形生成，未使用任何采样库、音源包或受版权保护的录音。
- **授权**：作为本项目自有音频资产交付，版权归项目方，可商用、可修改、可再分发。
- **产出/获取日期**：2026-10-15。
- **重新生成**：`py -3.9 UI原型/design_v5/gen_audio.py`
- **客观校验**：`py -3.9 UI原型/design_v5/verify_audio.py`

## 技术校验结果（脚本实测，非声明）

| 项 | 结果 |
| --- | --- |
| 文件名 vs 18 号资源契约 | 20/20 一致，无缺失无多余 |
| 采样格式 | 20/20 = 44100Hz / 单声道 / 16bit |
| 峰值 | 全部 ≤ −1dBFS（0.891），无削波 |
| 音量一致性 | 17 音效 RMS 极差 **2.9 dB**（−17.9 ~ −15.0），听感一致 |
| 短音效时长 | 17/17 落在 11 号清单区间内 |
| BGM 循环接缝 | 首尾跳变 0.00000；头/尾 50ms RMS 0.071/0.059（非静音）；接缝处斜率仅为全局 0.08–0.10 倍 → **无爆音、无断点** |
| 响度分层 | 循环 BGM −19dBFS 低于音效 −15dBFS（不抢 UI）；章末 sting 与音效同级 |

### 循环无缝的实现方式

1. 和弦采用**恒定包络**，乐句推进靠和声变化（C: I–V–vi–IV / A: i–VI–III–VII），不做段末淡出——否则循环点会出现可听见的断点。
2. 末尾再做**等增益首尾交叉**（120ms），使 `x[0] ≈ x[-1]` 且两端均非静音。
3. 生成后由 `verify_audio.py` 客观复核头尾 RMS 与斜率比，防止回归。

## 与 11 号清单的差异（已按实测更新）

- 清单原建议「44.1kHz / 16bit PCM WAV 源文件 → 交付 OGG Vorbis」。本次先交付 **WAV**（Unity 直接可用、便于验收），OGG 转码可在打包阶段按平台设置执行，转码不改变响度与循环点。
- BGM 时长：清单建议首页 60–90s、对局 90–120s；本次交付 **32s** 版本（循环播放，等效覆盖长时段）。若需更长版本，调整 `gen_audio.py` 中 `bgm_home` / `bgm_game` 的 `dur` 重新生成即可，循环处理逻辑不变。
- 清单建议「整体约 −16 LUFS」：本次以 RMS 近似控制，音效 −15dBFS、BGM −19dBFS。真机验收时如需严格 LUFS，可用响度计量工具复核后微调 `save_wav(target_db=...)`。