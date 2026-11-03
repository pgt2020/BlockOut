using System;
using System.Collections.Generic;
using UnityEngine;
using BlockOut.Core;

namespace BlockOut.Gameplay
{
    /// <summary>
    /// Combo system: tracks consecutive successful block removals within a time window.
    /// Error resets the combo. Pause/ad interrupts freeze the timer.
    /// </summary>
    public sealed class BlockOutComboSystem
    {
        public const float ComboWindowSeconds = 3.0f;
        public const float BaseScorePerBlock = 100f;

        public int CurrentCombo { get; private set; }
        public float ComboTimer { get; private set; }
        public float TotalScore { get; private set; }
        public int BestCombo { get; private set; }

        public event Action<int /*combo*/> OnComboChanged;
        public event Action<float /*score*/> OnScoreChanged;

        private bool timerRunning;

        public void OnSuccessfulRemove(bool isAutomaticChain = false)
        {
            if (!isAutomaticChain)
            {
                CurrentCombo++;
                ComboTimer = ComboWindowSeconds;
                timerRunning = true;
                BestCombo = Mathf.Max(BestCombo, CurrentCombo);
                OnComboChanged?.Invoke(CurrentCombo);
            }

            float multiplier = GetMultiplier();
            float score = BaseScorePerBlock * multiplier;
            TotalScore += score;
            OnScoreChanged?.Invoke(TotalScore);
        }

        public void OnError()
        {
            if (CurrentCombo > 0)
            {
                CurrentCombo = 0;
                timerRunning = false;
                OnComboChanged?.Invoke(0);
            }
        }

        public float GetMultiplier()
        {
            return Mathf.Min(1f + 0.25f * (CurrentCombo - 1), 3f);
        }

        public void Tick(float deltaTime)
        {
            if (!timerRunning || CurrentCombo <= 0) return;
            ComboTimer -= deltaTime;
            if (ComboTimer <= 0)
            {
                CurrentCombo = 0;
                timerRunning = false;
                OnComboChanged?.Invoke(0);
            }
        }

        public void FreezeTimer() => timerRunning = false;
        public void ResumeTimer() { if (CurrentCombo > 0) timerRunning = true; }

        public void Reset()
        {
            CurrentCombo = 0;
            ComboTimer = 0;
            TotalScore = 0;
            timerRunning = false;
            OnComboChanged?.Invoke(0);
        }
    }
}
