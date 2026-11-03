using System;
using BlockOut.Contracts;
using UnityEngine;

namespace BlockOut.Infrastructure.Persistence
{
    /// <summary>PlayerPrefs 存储实现（默认）。键名与旧版完全一致，保证旧存档可读。</summary>
    public sealed class PlayerPrefsProfileStore : IProfileStore
    {
        public bool Has(string key) { return PlayerPrefs.HasKey(key); }
        public string Get(string key) { return PlayerPrefs.GetString(key); }
        public void Set(string key, string value) { PlayerPrefs.SetString(key, value); }
        public void Delete(string key) { PlayerPrefs.DeleteKey(key); }
        public bool Commit() { try { PlayerPrefs.Save(); return true; } catch (Exception e) { Debug.LogWarning("[BlockOut] Commit failed: " + e.Message); return false; } }
    }

    /// <summary>内存存储实现：供测试与"保存失败"演练使用，不落任何持久介质。</summary>
    public sealed class InMemoryProfileStore : IProfileStore
    {
        public bool CommitShouldFail;
        private readonly System.Collections.Generic.Dictionary<string, string> map = new System.Collections.Generic.Dictionary<string, string>();

        public bool Has(string key) { return map.ContainsKey(key); }
        public string Get(string key) { return map.TryGetValue(key, out var v) ? v : null; }
        public void Set(string key, string value) { map[key] = value; }
        public void Delete(string key) { map.Remove(key); }
        public bool Commit() { return !CommitShouldFail; }
    }
}
