using System;
using System.Collections.Generic;
using BlockOut.Contracts;
using BlockOut.Core;
using UnityEngine;

namespace BlockOut.Infrastructure.Audio
{
    /// <summary>
    /// 音频预热 / 缓存 / 统一播放入口（R10）。
    /// 职责边界（明确记录，避免双实现互相遮蔽）：
    /// - 本类负责**预热与缓存**（启动期一次性装载，避免首次播放卡顿）与无主播放（UI 提示音等）；
    /// - 游戏内音乐/音效开关与即时生效仍由 <see cref="BlockOut.Gameplay.BlockOutSettings"/> 负责
    ///   （已交付且在用的实现，本轮不改其行为，避免回归）；
    /// - 两者尚未合并：合并需要把 Settings 的 AudioSource 生命周期交予本服务，属独立重构项，
    ///   未合并前不得让两条路径同时播放同一音效（调用方二选一）。
    /// </summary>
    public sealed class BlockOutAudioService : IAudioService
    {
        private readonly Dictionary<string, AudioClip> cache = new Dictionary<string, AudioClip>(StringComparer.Ordinal);
        private AudioSource musicSource;
        private string currentMusic;

        public int CachedClipCount => cache.Count;

        public void Warmup(IEnumerable<string> clipIds)
        {
            if (clipIds == null) return;
            foreach (var id in clipIds)
            {
                var clip = Load(id);
                if (clip == null)
                    Debug.LogWarning("[BlockOut][Audio] 预热失败，未找到音源：audio/" + id);
            }
        }

        public AudioClip Load(string clipId)
        {
            if (string.IsNullOrEmpty(clipId)) return null;
            if (cache.TryGetValue(clipId, out var hit) && hit != null) return hit;
            var clip = UnityEngine.Resources.Load<AudioClip>(BlockOutResourcePaths.BlockOutAudio + "/" + clipId);
            if (clip != null) cache[clipId] = clip;
            return clip;
        }

        public void Play(string clipId, float volumeScale = 1f)
        {
            var clip = Load(clipId);
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
            var clip = Load(clipId);
            if (clip == null) return;
            EnsureMusicSource();
            if (currentMusic == clipId && musicSource.isPlaying) return;
            currentMusic = clipId;
            musicSource.clip = clip;
            musicSource.loop = true;
            musicSource.Play();
        }

        public void StopMusic()
        {
            if (musicSource == null) return;
            musicSource.Stop();
            currentMusic = null;
        }

        public void Release(string clipId)
        {
            if (!string.IsNullOrEmpty(clipId)) cache.Remove(clipId);
        }

        public void ReleaseAll()
        {
            cache.Clear();
            currentMusic = null;
        }

        private void EnsureMusicSource()
        {
            if (musicSource != null) return;
            var existing = GameObject.Find("[BlockOut_MusicHost]");
            var go = existing ?? new GameObject("[BlockOut_MusicHost]");
            musicSource = go.GetComponent<AudioSource>() ?? go.AddComponent<AudioSource>();
            musicSource.loop = true;
            musicSource.spatialBlend = 0f;
            musicSource.playOnAwake = false;
        }
    }
}
