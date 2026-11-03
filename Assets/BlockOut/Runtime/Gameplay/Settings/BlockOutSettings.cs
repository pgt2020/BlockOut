using System;
using UnityEngine;
using BlockOut.Core;

namespace BlockOut.Gameplay
{
    /// <summary>
    /// Audio/vibration/settings manager. Wraps PlayerPrefs-stored toggles.
    /// Real audio clips are not included — this is the control layer only.
    /// </summary>
    public sealed class BlockOutSettings
    {
        // C06：Bootstrap 注入集中存档服务后需要重绑档案对象，去掉 readonly。
        private BlockOutPlayerProfile profile;
        private Func<System.Action, bool> commitChange;   // N07：统一存档入口（由 GM 注入 CommitProfileChange）
        private readonly AudioSource music;
        private readonly AudioSource effects;
        private string currentMusic;
        private readonly System.Collections.Generic.Dictionary<string, AudioClip> clips = new System.Collections.Generic.Dictionary<string, AudioClip>();

        /// <summary>服务注入后重新绑定档案（C06）：与 GameManager.Profile 保持同一对象，避免设置写到旧对象被覆写。</summary>
        public void BindProfile(BlockOutPlayerProfile p)
        {
            if (p != null) profile = p;
        }

        /// <summary>N07：注入统一存档入口（GM.CommitProfileChange）。设置变更经此提交，失败自动回滚内存档案。</summary>
        public void BindCommit(Func<System.Action, bool> commit)
        {
            commitChange = commit;
        }

        /// <summary>N07：经统一存档入口提交设置变更；无注入时退回档案直存（兼容旧装配）。返回是否提交成功。</summary>
        private bool Commit(Action mutate)
        {
            if (mutate == null) return false;
            if (commitChange != null) return commitChange(mutate);
            mutate();
            return profile != null && profile.TrySave();
        }

        public bool MusicOn
        {
            get => profile.MusicOn;
            set { Commit(() => profile.MusicOn = value); ApplyMusicSetting(); }
        }
        public bool SoundOn
        {
            get => profile.SoundOn;
            set { Commit(() => profile.SoundOn = value); if (!profile.SoundOn) effects.Stop(); }
        }
        public bool VibrationOn { get => profile.VibrationOn; set { Commit(() => profile.VibrationOn = value); } }

        public BlockOutSettings(BlockOutPlayerProfile p, Transform owner)
        {
            profile = p;
            var root = new GameObject("BlockOutAudio");
            root.transform.SetParent(owner, false);
            music = root.AddComponent<AudioSource>();
            music.playOnAwake = false;
            music.volume = .35f;
            music.loop = true;
            effects = root.AddComponent<AudioSource>();
            effects.playOnAwake = false;
            effects.volume = .7f;
        }

        private AudioClip FindClip(string id)
        {
            if (!clips.TryGetValue(id, out var clip))
            {
                clip = Resources.Load<AudioClip>("audio/" + id);
                clips.Add(id, clip);
            }
            return clip;
        }

        public void PlayMusic(string id)
        {
            if (currentMusic == id && music.clip != null) { ApplyMusicSetting(); return; }
            currentMusic = id;
            music.Stop();
            music.clip = FindClip(id);
            ApplyMusicSetting();
        }

        private void ApplyMusicSetting()
        {
            if (!MusicOn) { music.Pause(); return; }
            if (music.clip == null || music.isPlaying) return;
            music.UnPause();
            if (!music.isPlaying) music.Play();
        }

        public void PlaySound(string soundId)
        {
            if (!SoundOn) return;
            var clip = FindClip(soundId);
            if (clip != null) effects.PlayOneShot(clip);
        }

        public void PlayVibration()
        {
            if (!VibrationOn) return;
            Handheld.Vibrate(); // Simple cross-platform vibration
        }
    }

    /// <summary>
    /// New player guide / coach-mark system. Triggers on first level.
    /// </summary>
    public sealed class BlockOutGuideSystem
    {
        // C06：服务注入后需要重绑档案对象，去掉 readonly。
        private BlockOutPlayerProfile profile;
        private Func<System.Action, bool> commitChange;   // N07：统一存档入口
        public int StepCount = 1;
        public bool IsGuideActive => !profile.GuideCompleted;

        public event Action OnGuideStepStarted;
        public event Action OnGuideCompleted;

        public BlockOutGuideSystem(BlockOutPlayerProfile p) { profile = p; }

        /// <summary>服务注入后重新绑定档案（C06）。</summary>
        public void BindProfile(BlockOutPlayerProfile p)
        {
            if (p != null) profile = p;
        }

        /// <summary>N07：注入统一存档入口（GM.CommitProfileChange）。</summary>
        public void BindCommit(Func<System.Action, bool> commit)
        {
            commitChange = commit;
        }

        public void OnPlayerAction()
        {
            if (profile.GuideCompleted) return;
            // N07：引导完成经统一存档入口提交；失败回滚（GuideCompleted 复位），不触发完成事件
            bool ok = commitChange != null
                ? commitChange(() => profile.GuideCompleted = true)
                : (profile.GuideCompleted = true) == true && profile.TrySave();
            if (ok) OnGuideCompleted?.Invoke();
        }
    }
}
