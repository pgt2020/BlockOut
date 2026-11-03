using System;
using System.Collections.Generic;
using UnityEngine;
using BlockOut.Core;

namespace BlockOut.Gameplay
{
    /// <summary>
    /// Chapter assembly meta-game: each completed level fills one puzzle piece
    /// on a chapter-wide artwork. Tracks progress per chapter.
    /// </summary>
    [Serializable]
    public class BlockOutChapterAssembly
    {
        public int ChapterId;
        public string ChapterName;
        public int TotalPieces;
        public int CompletedPieces;
        public bool IsComplete => CompletedPieces >= TotalPieces;

        public void AddPiece() { CompletedPieces = Mathf.Min(TotalPieces, CompletedPieces + 1); }
        public float Progress => TotalPieces > 0 ? (float)CompletedPieces / TotalPieces : 0f;
    }

    public sealed class BlockOutAssemblyManager
    {
        private readonly Dictionary<int, BlockOutChapterAssembly> chapters = new Dictionary<int, BlockOutChapterAssembly>();
        // C06：服务注入后需要重绑档案对象，去掉 readonly。
        private BlockOutPlayerProfile profile;

        public event Action<BlockOutChapterAssembly> OnChapterProgressChanged;

        public BlockOutAssemblyManager(BlockOutPlayerProfile p) { profile = p; }

        /// <summary>服务注入后重新绑定档案（C06）：收藏/解锁写入与 GameManager.Profile 保持同一对象。</summary>
        public void BindProfile(BlockOutPlayerProfile p)
        {
            if (p != null) profile = p;
        }

        public BlockOutChapterAssembly GetOrCreateChapter(int chapterId, string name, int totalPieces)
        {
            if (!chapters.TryGetValue(chapterId, out var ch))
            {
                ch = new BlockOutChapterAssembly { ChapterId = chapterId, ChapterName = name, TotalPieces = totalPieces };
                chapters[chapterId] = ch;
            }
            ch.TotalPieces=totalPieces;
            return ch;
        }

        public void OnLevelCompleted(int chapterId, int totalPieces)
        {
            var ch = GetOrCreateChapter(chapterId, $"Chapter {chapterId + 1}", totalPieces);
            ch.AddPiece();
            OnChapterProgressChanged?.Invoke(ch);
        }
    }
}
