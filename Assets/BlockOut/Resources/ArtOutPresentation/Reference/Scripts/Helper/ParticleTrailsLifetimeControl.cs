using UnityEngine;
using static UnityEngine.ParticleSystem;

public class ParticleTrailsLifetimeControl : MonoBehaviour
{
    private ParticleSystem particleSystemComp;
    private ParticleSystem.TrailModule trailsModule;

    void Start()
    {
        // 获取 ParticleSystem 组件
        particleSystemComp = GetComponent<ParticleSystem>();
        if (particleSystemComp == null)
        {
            Debug.LogError("当前游戏对象上没有 ParticleSystem 组件，请检查！");
            return;
        }

        // 获取 Trails 模块
        trailsModule = particleSystemComp.trails;
    }

    // 获取 Trails 模块中 Lifetime 的值
    public float GetTrailsLifetime()
    {
        particleSystemComp = GetComponent<ParticleSystem>();
        if (particleSystemComp == null)
        {
            Debug.LogError("当前游戏对象上没有 ParticleSystem 组件，请检查！");
            return 0;
        }

        // 获取 Trails 模块
        trailsModule = particleSystemComp.trails;

        return trailsModule.lifetime.constant;
    }

    // 设置 Trails 模块中 Lifetime 的值
    public void SetTrailsLifetime(float newLifetime)
    {
        particleSystemComp = GetComponent<ParticleSystem>();
        if (particleSystemComp == null)
        {
            Debug.LogError("当前游戏对象上没有 ParticleSystem 组件，请检查！");
            return;
        }
        trailsModule = particleSystemComp.trails;
        // 先获取当前的 MinMaxCurve（因为 Lifetime 是 MinMaxCurve 类型）
        MinMaxCurve curve = trailsModule.lifetime;
        // 设置为固定值（如果需要范围，可以设置 curve.min 和 curve.max 等）
        curve.mode = ParticleSystemCurveMode.Constant;
        curve.constant = newLifetime;

        trailsModule.lifetime = curve;
    }

    // void Update()
    // {
    //     // 示例：在 Update 中演示获取和设置
    //     if (Input.GetKeyDown(KeyCode.Alpha1))
    //     {
    //         float currentLifetime = GetTrailsLifetime();
    //         Debug.Log("当前 Trails Lifetime 值：" + currentLifetime);
    //     }

    //     if (Input.GetKeyDown(KeyCode.Alpha2))
    //     {
    //         SetTrailsLifetime(1.0f);  // 设置新的 Lifetime 值为 1.0
    //         Debug.Log("已设置 Trails Lifetime 值为 1.0");
    //     }
    // }
}