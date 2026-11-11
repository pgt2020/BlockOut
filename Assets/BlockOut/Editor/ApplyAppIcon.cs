#if UNITY_EDITOR
using UnityEditor;
using UnityEngine;

/// <summary>
/// BlockOut 上线图标应用工具。
/// 把生成好的一套 App 图标（位于 Assets/BlockOut/AppIcon/）应用到 PlayerSettings。
/// 用法：Unity 菜单 BlockOut -> Apply App Icon (master)，一键把 1024 master 设为
/// iOS / Android 的默认图标，Unity 在打包时据此自动生成各尺寸。
///
/// 如需像素级逐尺寸控制（iOS App Store 资产目录 / Android 自适应图标），
/// 可直接用 AppIcon/ios/AppIcon.appiconset 与 AppIcon/android/mipmap-* 下的成品，
/// 它们是按 Apple / Google 规范预切好的，可手动并入 Xcode / gradle res。
/// </summary>
public static class ApplyAppIcon
{
    private const string MasterPath = "Assets/BlockOut/AppIcon/master_1024_opaque.png";

    [MenuItem("BlockOut/Apply App Icon (master)")]
    public static void ApplyMaster()
    {
        var icon = AssetDatabase.LoadAssetAtPath<Texture2D>(MasterPath);
        if (icon == null)
        {
            Debug.LogError("[BlockOut] 找不到主图标：" + MasterPath);
            return;
        }

        PlayerSettings.SetIconsForTargetGroup(BuildTargetGroup.iOS, new[] { icon });
        PlayerSettings.SetIconsForTargetGroup(BuildTargetGroup.Android, new[] { icon });
        AssetDatabase.SaveAssets();

        Debug.Log("[BlockOut] 已将 " + MasterPath + " 设为 iOS / Android 默认图标（打包时自动派生各尺寸）。");
    }
}
#endif
