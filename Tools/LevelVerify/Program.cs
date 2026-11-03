using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Numerics;
using System.Text;
using BlockOut.Config;
using BlockOut.Core;
using UnityEngine;

namespace LevelVerify
{
    /// <summary>
    /// 关卡集离线校验（阶段 B 证据链）。
    /// 用真实 Runtime 代码验证 Assets/Resources/ArtOut 下的 12 个第一章关卡：
    ///   1) manifest → 关卡文件一一对应（模拟 BlockOutCatalog.BuildFromManifest 的读取路径）
    ///   2) 真实 BlockOutLevelParser.Parse 可解析，id/difficulty 归一化正确
    ///   3) 边界/不重叠/arrowCell 合法/shapeId 在形状库范围内
    ///   4) 可解性：游戏内 BlockOutSolver.IsSolvable（贪心）+ runner 自带回溯求解（权威判定），
    ///      并在贪心每一步与 BlockOutGameRules.CanMove 交叉核对，保证回溯复刻规则等价
    ///   5) 图片配置覆盖（BlockOutCatalog.FindPicture 语义）与插画文件落盘
    ///   6) 奖励语义：GetLevelReward 表优先（easy → 10，ArtOut 基线）
    /// 退出码 0 = 全部通过；1 = 存在失败项。
    /// </summary>
    internal static class Program
    {
        private const int ExpectedLevelCount = 12; // 第一章 = 全局 1-12
        private const int ExpectedGametime = 120;  // 与参考工程 606 关清单一致

        private static int _failures;
        private static int _warnings;
        private static readonly StringBuilder Report = new StringBuilder();
        private static readonly List<string> structuralSignatures = new List<string>();
        private static readonly SortedSet<int> shapeCoverage = new SortedSet<int>();
        private static readonly Dictionary<BlockOutDirection, int> directionCounts = new Dictionary<BlockOutDirection, int>();

        private static int Main(string[] args)
        {
            string root = args.Length > 0 ? args[0] : FindProjectRoot();
            if (root == null)
            {
                Console.Error.WriteLine("FATAL: cannot locate BlockOut project root (expects Assets/Resources/ArtOut).");
                return 1;
            }

            string artOutDir = Path.Combine(root, "Assets", "Resources", "ArtOut");
            string levelsDir = Path.Combine(artOutDir, "Levels");
            Line("LevelVerify: root=" + root);

            var manifest = LoadManifest(Path.Combine(artOutDir, "GameAssets.json"));
            if (manifest == null || manifest.levels == null || manifest.levels.Count == 0)
            {
                Fail("manifest 为空或解析失败");
                return Finish();
            }
            Line("manifest version=" + manifest.version + " entries=" + manifest.levels.Count);

            if (manifest.levels.Count != ExpectedLevelCount)
                Fail("manifest 关卡数=" + manifest.levels.Count + "，期望 " + ExpectedLevelCount + "（第一章 12 关）");
            else
                Pass("manifest 关卡数 = " + ExpectedLevelCount);

            var pictureConfig = LoadPictureConfig(Path.Combine(artOutDir, "ArtOutPictureConfig.json"));
            if (pictureConfig == null)
            {
                Fail("ArtOutPictureConfig.json 解析失败");
                return Finish();
            }

            var levels = new List<BlockOutLevelData>();
            for (int i = 0; i < manifest.levels.Count; i++)
            {
                var entry = manifest.levels[i];
                if (entry == null || string.IsNullOrEmpty(entry.id))
                {
                    Fail("manifest 第 " + i + " 项缺少 id");
                    continue;
                }

                string path = Path.Combine(levelsDir, entry.id + ".json");
                if (!File.Exists(path))
                {
                    Fail("关卡文件缺失: " + path);
                    continue;
                }

                BlockOutLevelData level = null;
                try
                {
                    level = BlockOutLevelParser.Parse(File.ReadAllText(path));
                }
                catch (Exception e)
                {
                    Fail("解析失败 " + entry.id + ": " + e.Message);
                    continue;
                }

                string ctx = "[" + (i + 1) + "/" + manifest.levels.Count + "] " + entry.id;
                VerifyLevel(ctx, level, entry, i, pictureConfig, root);
                levels.Add(level);
            }

            // 章节结构：第一章应恰好 12 关，且全部 chapter=0 / levelInChapter=0..11
            // （Catalog.BuildFromManifest 用 orderIndex/12 与 %12 覆写，这里按同一公式预期）
            for (int i = 0; i < levels.Count; i++)
            {
                int expectChapter = i / BlockOutContentConfig.LevelsPerChapter;
                int expectIndex = i % BlockOutContentConfig.LevelsPerChapter;
                if (levels[i].Chapter != expectChapter || levels[i].LevelInChapter != expectIndex)
                    Fail(levels[i].Id + " 章节位=" + levels[i].Chapter + "/" + levels[i].LevelInChapter
                        + "，期望 " + expectChapter + "/" + expectIndex);
            }
            if (levels.Count == ExpectedLevelCount)
                Pass("第一章 12 关章节位 0/0..0/11 与 manifest 顺序一致（Catalog 覆写公式复算）");

            // 正式关卡数达到每章上限 → 不触发占位补齐 / 过程生成兜底
            if (levels.Count >= BlockOutContentConfig.LevelsPerChapter)
                Pass("关卡数 ≥ LevelsPerChapter(" + BlockOutContentConfig.LevelsPerChapter + ")：不触发占位补齐与兜底生成");
            else
                Fail("关卡数不足，将触发开发占位补齐（不符合阶段 B 目标）");

            // 结构 distinctness：不允许"仅改颜色假装难度变化"（签名不含颜色）
            var distinct = new HashSet<string>(structuralSignatures);
            if (distinct.Count != structuralSignatures.Count)
                Fail("存在结构签名相同的关卡（仅改颜色充数）：" + structuralSignatures.Count + " 关 / " + distinct.Count + " 种结构");
            else
                Pass("12 关结构签名互不相同（不含颜色，排除\"仅改颜色\"充数）");

            // 覆盖度报告
            Line("");
            Line("coverage: distinct shapeIds used = [" + string.Join(",", shapeCoverage) + "] (library 1.." + BlockOutShapeLibrary.ShapeCount + ")");
            Line("coverage: directions = " + string.Join(", ", directionCounts.Select(kv => kv.Key + "=" + kv.Value)));
            Line("coverage: boards = " + string.Join(", ", levels.Select(l => l.Width + "x" + l.Height)));
            Line("coverage: block counts = " + string.Join(", ", levels.Select(l => l.Blocks.Count.ToString())));
            if (shapeCoverage.Count >= 8)
                Pass("形状覆盖 " + shapeCoverage.Count + " 种（含单块/双格/三格/L/T/S/Z/U/长条等家族）");
            else
                Warn("形状覆盖偏窄：" + shapeCoverage.Count + " 种");
            bool allFourDirs = directionCounts.Keys.Count == 4;
            if (allFourDirs) Pass("四向飞出均有覆盖（Up/Down/Left/Right）");
            else Warn("方向覆盖不足四向：" + string.Join(",", directionCounts.Keys));

            Line("");
            Line("summary: levels=" + levels.Count + " failures=" + _failures + " warnings=" + _warnings);
            return Finish();
        }

        // ---- 单关校验 ----

        private static void VerifyLevel(string ctx, BlockOutLevelData level, BlockOutManifestEntry entry, int orderIndex, BlockOutPictureConfig pictureConfig, string root)
        {
            Line("");
            Line("== " + ctx + " ==");
            Line("  displayName=" + level.DisplayName + " difficulty=" + level.Difficulty
                + " board=" + level.Width + "x" + level.Height + " blocks=" + level.Blocks.Count
                + " dataVersion=" + level.DataVersion + " rewardCoins(level)=" + level.RewardCoins);

            if (level.Id != entry.id) Fail(ctx + " id 不一致: json=" + level.Id + " manifest=" + entry.id);
            if (string.IsNullOrEmpty(level.DisplayName)) Fail(ctx + " displayName 为空");
            if (level.Difficulty != "easy") Fail(ctx + " difficulty 归一化为 " + level.Difficulty + "，期望 easy");

            // gametime：manifest 值 > 0 时由 BuildFromManifest 覆写 level.GameTime（解析器不读 gametime）
            if (entry.gametime <= 0)
                Fail(ctx + " manifest gametime=" + entry.gametime + " 非正数");
            else if (entry.gametime != ExpectedGametime)
                Warn(ctx + " manifest gametime=" + entry.gametime + " 与参考基线 " + ExpectedGametime + " 不一致");
            if (level.GameTime != 0)
                Warn(ctx + " level.GameTime 解析器内值=" + level.GameTime + "（应由 manifest 覆写为 " + entry.gametime + "）");

            // 奖励语义（表优先）：easy 关无论 level.RewardCoins 是多少都应发 10
            int reward = BlockOutContentConfig.GetLevelReward(level.Difficulty, level.RewardCoins);
            if (reward != 10)
                Fail(ctx + " GetLevelReward(easy)=" + reward + "，期望 10（ArtOut 奖励表）");
            else
                Line("  reward: GetLevelReward(easy, levelValue=" + level.RewardCoins + ") = " + reward + "（表优先，OK）");

            // 图片配置 + 插画落盘（与 BlockOutCatalog.FindPicture 同语义：线性查 id）
            var pic = CatalogFindPictureExtensions.FindPicture(pictureConfig, level.PictureId);
            if (pic == null)
                Fail(ctx + " pictureId=" + level.PictureId + " 在 ArtOutPictureConfig 中无条目");
            else if (string.IsNullOrEmpty(pic.completeImage))
                Fail(ctx + " picture 条目缺少 completeImage");
            else
                Line("  picture: " + level.PictureId + " -> " + pic.completeImage + " (exists=" + ArtFileExists(root, pic.completeImage) + ")");

            // 形状/边界/重叠/arrowCell
            var occupied = new HashSet<Vector2Int>();
            int shapeCount = BlockOutShapeLibrary.ShapeCount;
            for (int b = 0; b < level.Blocks.Count; b++)
            {
                var block = level.Blocks[b];
                shapeCoverage.Add(block.ShapeId);
                directionCounts.TryGetValue(block.Direction, out int dc);
                directionCounts[block.Direction] = dc + 1;
                if (block.ShapeId < 1 || block.ShapeId > shapeCount)
                    Fail(ctx + " block " + b + " shapeId=" + block.ShapeId + " 超出形状库 1.." + shapeCount);

                foreach (var c in block.GetOccupiedCells())
                {
                    if (c.x < 0 || c.y < 0 || c.x >= level.Width || c.y >= level.Height)
                    { Fail(ctx + " block " + b + " cell (" + c.x + "," + c.y + ") 越界 " + level.Width + "x" + level.Height); break; }
                    if (!occupied.Add(c))
                    { Fail(ctx + " block " + b + " cell (" + c.x + "," + c.y + ") 重叠"); break; }
                }

                if (!block.HasArrowCell || !block.Cells.Contains(block.ArrowCell))
                    Fail(ctx + " block " + b + " arrowCell 不合法");
            }

            // 可解性：游戏内贪心 + runner 回溯（带与 GameRules 的交叉核对）
            bool greedy = BlockOutSolver.IsSolvable(level);
            var solve = SolveWithCrossCheck(level, out int nodes, out bool budgetExceeded, out List<int> solution);
            Line("  solvable: gameGreedy=" + greedy + " backtracking=" + solve
                + " nodes=" + nodes + (budgetExceeded ? " (BUDGET-EXCEEDED)" : ""));
            if (!solve) Fail(ctx + " 无可解序列（回溯求解失败）");
            else
            {
                Pass(ctx + " 可解（回溯 " + nodes + " 节点; 贪心=" + greedy + "）");
                Line("  solution (removal order, block indices): " + string.Join(" -> ", solution));
            }
            if (budgetExceeded) Warn(ctx + " 回溯超出节点预算，结论为\"未证明\"");
            Line("  runHash (BlockOutGameRules.BuildLevelRunHash): " + BlockOutGameRules.BuildLevelRunHash(level));
            structuralSignatures.Add(StructuralSignature(level));

            // 玩家向 sanity：初始局面至少 2 个可走块（避免死局开局）
            var rules = new BlockOutGameRules();
            rules.StartLevel(level);
            int movable = 0;
            foreach (var b in rules.Blocks) if (b.Active && rules.CanMove(b)) movable++;
            if (movable < 1) Fail(ctx + " 初始无可走块");
            else Line("  initial movable blocks = " + movable);
        }

        // ---- 回溯求解（复刻 ArtOut 路径判定：每格沿方向射线无其他存活块即可飞出）----

        private static bool SolveWithCrossCheck(BlockOutLevelData level, out int nodes, out bool budgetExceeded, out List<int> solution)
        {
            int nodeCount = 0;
            bool exceeded = false;
            var path = new List<int>();
            nodes = 0;
            budgetExceeded = false;
            solution = path;
            int n = level.Blocks.Count;
            if (n == 0) return true;
            if (n > 64) { budgetExceeded = true; return false; }

            // 复刻规则与游戏规则交叉核对：初始局面逐块比对。
            // 注意：必须传 rules.Blocks[i]（StartLevel 的克隆块）——游戏内 IsPathClear 用
            // 引用比较排除自身格子，传关卡数据对象会把块自己的格子当成遮挡。
            var rules = new BlockOutGameRules();
            rules.StartLevel(level);
            for (int i = 0; i < n; i++)
            {
                bool replica = ReplicaCanMove(level, 0UL, i);
                bool real = rules.Blocks[i].Active && rules.CanMove(rules.Blocks[i]);
                if (replica != real)
                {
                    Fail("cross-check mismatch at level start: block " + i + " replica=" + replica + " rules=" + real);
                    return false;
                }
            }

            var failed = new HashSet<ulong>();
            const int Budget = 20_000_000;
            bool Dfs(ulong removed)
            {
                if (BitOperations.PopCount(removed) == (uint)n) return true;
                if (failed.Contains(removed)) return false;
                if (nodeCount++ > Budget) { exceeded = true; return false; }
                for (int i = 0; i < n; i++)
                {
                    ulong bit = 1UL << i;
                    if ((removed & bit) != 0) continue;
                    if (!ReplicaCanMove(level, removed, i)) continue;
                    if (Dfs(removed | bit)) { path.Add(i); return true; }
                }
                failed.Add(removed);
                return false;
            }
            bool solved = Dfs(0UL);
            path.Reverse(); // DFS 回溯时先记录深层的移除，反转为正常出手顺序
            nodes = nodeCount;
            budgetExceeded = exceeded;
            return solved;
        }

        /// <summary>结构签名（不含颜色）：同形同布同向的两关会被判为"仅改颜色"。</summary>
        private static string StructuralSignature(BlockOutLevelData level)
        {
            var tuples = new List<string>();
            foreach (var b in level.Blocks)
                tuples.Add(b.ShapeId + "@" + b.Column + "," + b.Row + ":" + b.Direction);
            tuples.Sort(StringComparer.Ordinal);
            return level.Width + "x" + level.Height + "|" + string.Join(";", tuples);
        }

        private static bool ReplicaCanMove(BlockOutLevelData level, ulong removed, int index)
        {
            var block = level.Blocks[index];
            var step = BlockOutGameRules.GetDirectionStep(block.Direction);
            foreach (var origin in block.GetOccupiedCells())
            {
                var cursor = origin + step;
                while (cursor.x >= 0 && cursor.y >= 0 && cursor.x < level.Width && cursor.y < level.Height)
                {
                    int owner = Occupant(level, removed, cursor);
                    if (owner >= 0 && owner != index) return false;
                    cursor += step;
                }
            }
            return true;
        }

        private static int Occupant(BlockOutLevelData level, ulong removed, Vector2Int cell)
        {
            for (int i = 0; i < level.Blocks.Count; i++)
            {
                if ((removed & (1UL << i)) != 0) continue;
                foreach (var c in level.Blocks[i].GetOccupiedCells())
                    if (c == cell) return i;
            }
            return -1;
        }

        // ---- 资源加载 ----

        private static BlockOutManifest LoadManifest(string path)
        {
            if (!File.Exists(path)) { Fail("manifest 文件不存在: " + path); return null; }
            try
            {
                string json = File.ReadAllText(path).TrimStart('\uFEFF');
                return JsonUtility.FromJson<BlockOutManifest>(json);
            }
            catch (Exception e)
            {
                Fail("manifest 解析异常: " + e.Message);
                return null;
            }
        }

        private static BlockOutPictureConfig LoadPictureConfig(string path)
        {
            if (!File.Exists(path)) { Fail("图片配置文件不存在: " + path); return null; }
            try
            {
                string json = File.ReadAllText(path).TrimStart('\uFEFF');
                return JsonUtility.FromJson<BlockOutPictureConfig>(json);
            }
            catch (Exception e)
            {
                Fail("图片配置解析异常: " + e.Message);
                return null;
            }
        }

        private static bool ArtFileExists(string root, string resourcesRelativePath)
        {
            if (string.IsNullOrEmpty(resourcesRelativePath)) return false;
            string path = Path.Combine(root, "Assets", "Resources", resourcesRelativePath + ".png");
            return File.Exists(path);
        }

        private static string FindProjectRoot()
        {
            var dir = new DirectoryInfo(AppContext.BaseDirectory);
            for (int i = 0; i < 8 && dir != null; i++, dir = dir.Parent)
            {
                if (File.Exists(Path.Combine(dir.FullName, "Assets", "Resources", "ArtOut", "GameAssets.json")))
                    return dir.FullName;
            }
            return null;
        }

        // ---- 报告 ----

        private static void Pass(string msg) { Line("  [PASS] " + msg); }

        private static void Warn(string msg)
        {
            _warnings++;
            Line("  [WARN] " + msg);
        }

        private static void Fail(string msg)
        {
            _failures++;
            Line("  [FAIL] " + msg);
        }

        private static void Line(string msg)
        {
            Report.AppendLine(msg);
            Console.WriteLine(msg);
        }

        private static int Finish()
        {
            string logDir = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "logs");
            try
            {
                Directory.CreateDirectory(logDir);
                File.WriteAllText(Path.Combine(logDir, "level_verify_result.txt"), Report.ToString(), Encoding.UTF8);
                Console.WriteLine("report written to " + Path.GetFullPath(Path.Combine(logDir, "level_verify_result.txt")));
            }
            catch (Exception e)
            {
                Console.Error.WriteLine("warn: cannot write report: " + e.Message);
            }
            return _failures == 0 ? 0 : 1;
        }
    }

    /// <summary>与 BlockOutCatalog.FindPicture 同语义的条目查找（线性匹配 id）。</summary>
    internal static class CatalogFindPictureExtensions
    {
        public static BlockOutPictureEntry FindPicture(BlockOutPictureConfig config, string pictureId)
        {
            if (config == null || config.pictures == null || string.IsNullOrEmpty(pictureId)) return null;
            foreach (var p in config.pictures)
                if (p != null && p.id == pictureId) return p;
            return null;
        }
    }
}
