using System;
using UnityEngine;
using UnityEngine.UI;

namespace BlockOut.UI
{
    /// <summary>Real catalog progress on the garden path; never baked level numbers.</summary>
    public sealed class BlockOutGardenHomePath : MonoBehaviour
    {
        public Button[] Nodes;
        public Text[] Numbers;
        public Image[] Locks;
        public Sprite Available, Completed, Locked;

        public void Refresh(int target, int count, Func<int, bool> isCompleted, Action<int> enter)
        {
            for (int i = 0; i < Nodes.Length; i++)
            {
                int level = target + i - 1;
                var button = Nodes[i];
                bool exists = level >= 0 && level < count;
                button.gameObject.SetActive(exists);
                button.onClick.RemoveAllListeners();
                if (!exists) continue;
                bool done = isCompleted(level);
                bool playable = level == target || done;
                Numbers[i].text = (level + 1).ToString();
                Locks[i].gameObject.SetActive(!playable);
                var image = button.targetGraphic as Image;
                if (image != null)
                {
                    image.sprite = level == target ? Available : done ? Completed : Locked;
                    image.color = Color.white;
                }
                button.interactable = playable;
                if (playable) button.onClick.AddListener(() => enter(level));
            }
        }
    }
}
