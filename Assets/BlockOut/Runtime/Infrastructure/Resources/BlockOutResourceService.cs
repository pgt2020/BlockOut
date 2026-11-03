using System;
using System.Collections.Generic;
using BlockOut.Contracts;
using BlockOut.Core;
using UnityEngine;

namespace BlockOut.Infrastructure.Resources
{
    /// <summary>
    /// 资源加载 / 缓存 / 释放（R10）。
    /// 目标：区分首屏必需、进入关卡必需、延后特效三类；统一缓存；可整体释放。
    /// 当前实现基于 Resources（保持既有加载契约），缓存按"资源路径 + 类型"，
    /// 释放只释放本服务创建的缓存，不动静态引用（避免破坏已装配 UI）。
    /// </summary>
    public sealed class BlockOutResourceService : IAudioService
    {
        private readonly Dictionary<string, UnityEngine.Object> cache =
            new Dictionary<string, UnityEngine.Object>(StringComparer.Ordinal);

        /// <summary>已缓存资源数（检查工具与测试断言用）。</summary>
        public int CachedCount => cache.Count;

        public T Load<T>(string path) where T : UnityEngine.Object
        {
            if (string.IsNullOrEmpty(path)) return null;
            var key = typeof(T).FullName + "|" + path;
            if (cache.TryGetValue(key, out var hit) && hit != null) return (T)hit;

            var asset = UnityEngine.Resources.Load<T>(path);
            if (asset != null) cache[key] = asset;
            return asset;
        }

        public bool Exists<T>(string path) where T : UnityEngine.Object
        {
            return Load<T>(path) != null;
        }

        public void Preload<T>(IEnumerable<string> paths) where T : UnityEngine.Object
        {
            if (paths == null) return;
            foreach (var p in paths) Load<T>(p);
        }

        public void ReleasePath(string path)
        {
            if (string.IsNullOrEmpty(path)) return;
            var victims = new List<string>();
            foreach (var kv in cache)
                if (kv.Key.EndsWith("|" + path, StringComparison.Ordinal)) victims.Add(kv.Key);
            foreach (var k in victims) cache.Remove(k);
        }

        public void ReleaseAll()
        {
            cache.Clear();
        }

        // ---- IAudioService：预热 + 统一播放入口（开关仍由 BlockOutSettings 决定）----

        public void Warmup(IEnumerable<string> clipIds)
        {
            if (clipIds == null) return;
            foreach (var id in clipIds) Load<AudioClip>(BlockOutResourcePaths.BlockOutAudio + "/" + id);
        }

        public void Play(string clipId, float volumeScale = 1f)
        {
            var clip = Load<AudioClip>(BlockOutResourcePaths.BlockOutAudio + "/" + clipId);
            if (clip == null) return;
            var go = new GameObject("[BlockOut_Sfx] " + clipId, typeof(AudioSource));
            var src = go.GetComponent<AudioSource>();
            src.clip = clip;
            src.volume = Mathf.Clamp01(volumeScale);
            src.spatialBlend = 0f;
            src.Play();
            UnityEngine.Object.Destroy(go, clip.length + 0.05f);
        }

        public void PlayMusic(string clipId)
        {
            var clip = Load<AudioClip>(BlockOutResourcePaths.BlockOutAudio + "/" + clipId);
            if (clip == null) return;
            var go = GameObject.Find("[BlockOut_Music]");
            if (go == null)
            {
                go = new GameObject("[BlockOut_Music]", typeof(AudioSource));
                go.GetComponent<AudioSource>().loop = true;
                go.GetComponent<AudioSource>().spatialBlend = 0f;
            }
            var src = go.GetComponent<AudioSource>();
            if (src.clip == clip && src.isPlaying) return;
            src.clip = clip;
            src.Play();
        }

        public void StopMusic()
        {
            var go = GameObject.Find("[BlockOut_Music]");
            if (go != null) go.GetComponent<AudioSource>()?.Stop();
        }

        void IAudioService.Release(string clipId)
        {
            ReleasePath(BlockOutResourcePaths.BlockOutAudio + "/" + clipId);
        }
    }
}
