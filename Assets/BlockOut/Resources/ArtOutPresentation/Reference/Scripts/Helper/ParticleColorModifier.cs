using UnityEngine;

public class ParticleColorModifier : MonoBehaviour
{
    private ParticleSystemRenderer particleRenderer;
    private MaterialPropertyBlock propertyBlock;

    void Start()
    {
        // 获取粒子系统的渲染器
        particleRenderer = GetComponent<ParticleSystemRenderer>();
        if (particleRenderer == null)
        {
            Debug.LogError("未找到ParticleSystemRenderer组件");
            return;
        }

        propertyBlock = new MaterialPropertyBlock();
        
        // 设置材质颜色（例如设为红色）
        // SetColor(Color.red);
    }

    public void SetColor(Color color)
    {
        if (particleRenderer == null)
        {
            particleRenderer = GetComponent<ParticleSystemRenderer>();
            propertyBlock = new MaterialPropertyBlock();
        }
        // 获取当前材质属性块
        particleRenderer.GetPropertyBlock(propertyBlock);
        
        // 设置颜色属性（根据着色器不同，属性名可能为"_Color"、"_TintColor"等）
        propertyBlock.SetColor("_Color", color);
        
        // 应用修改后的属性块
        particleRenderer.SetPropertyBlock(propertyBlock);
    }
}