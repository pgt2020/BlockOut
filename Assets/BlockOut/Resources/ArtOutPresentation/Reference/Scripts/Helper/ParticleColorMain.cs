using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class ParticleColorMain : MonoBehaviour
{
    [SerializeField] ParticleColorModifier[] needUpdateColors;
    // Start is called before the first frame update
    public void SetNeedColor(Color color)
    {
        foreach (ParticleColorModifier a in needUpdateColors)
        {
            a.SetColor(color);
        }
    }
}
