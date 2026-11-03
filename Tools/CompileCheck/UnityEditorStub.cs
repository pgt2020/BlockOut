// BlockOut 离线编译校验用 UnityEditor 桩（仅编译期存在，不进入 Unity 工程）。
using System;
using System.Collections.Generic;
using UnityEngine;

namespace UnityEditor
{
    [AttributeUsage(AttributeTargets.Method)]
    public sealed class MenuItemAttribute : Attribute
    {
        public MenuItemAttribute(string item) { }
        public MenuItemAttribute(string item, bool isValidateFunction) { }
        public MenuItemAttribute(string item, bool isValidateFunction, int priority) { }
    }

    public static class AssetDatabase
    {
        public static T LoadAssetAtPath<T>(string assetPath) where T : UnityEngine.Object => default;
        public static UnityEngine.Object LoadAssetAtPath(string assetPath, Type type) => default;
        public static UnityEngine.Object LoadMainAssetAtPath(string assetPath) => default;
        public static string GUIDToAssetPath(string guid) => "";
        public static string AssetPathToGUID(string assetPath) => "";
        public static string[] FindAssets(string filter) => new string[0];
        public static string[] FindAssets(string filter, params string[] searchInFolders) => new string[0];
        public static void SaveAssets() { }
        public static void Refresh() { }
        public static bool IsValidFolder(string path) => false;
        public static void CreateAsset(UnityEngine.Object asset, string path) { }
        public static bool DeleteAsset(string path) => false;
        public static UnityEngine.Object CreateAsset(Type type, string path) => null;
        public static string CreateFolder(string parent, string name) => "";
        public static void ImportAsset(string path, ImportAssetOptions o = ImportAssetOptions.Default) { }
        public static bool Contains(UnityEngine.Object obj) => false;
        public static string GetAssetPath(UnityEngine.Object obj) => "";
        public static void MoveAsset(string oldPath, string newPath) { }
    }

    [Flags]
    public enum ImportAssetOptions { Default = 0, ForceUpdate = 1, ForceSynchronousImport = 8, SynchronousImportMode = 15 }

    public static class EditorUtility
    {
        public static bool DisplayDialog(string title, string message, string ok) => true;
        public static bool DisplayDialog(string title, string message, string ok, string cancel) => true;
        public static void DisplayProgressBar(string title, string info, float progress) { }
        public static void ClearProgressBar() { }
        public static void SetDirty(UnityEngine.Object o) { }
        public static UnityEngine.Object InstanceIDToObject(int id) => null;
        public static int GetObjectDirty(UnityEngine.Object o) => 0;
        public static string OpenFilePanel(string t, string d, string e) => "";
        public static string OpenFolderPanel(string t, string d, string d2) => "";
        public static string SaveFilePanel(string t, string d, string n, string e) => "";
    }

    public sealed class SerializedObject
    {
        public SerializedObject(UnityEngine.Object o) { }
        public UnityEngine.Object targetObject => null;
        public SerializedProperty FindProperty(string p) => null;
        public SerializedProperty GetIterator() => null;
        public bool Update() => false;
        public void ApplyModifiedProperties() { }
        public void ApplyModifiedPropertiesWithoutUndo() { }
        public void SetIsDifferentCacheDirty() { }
    }

    public sealed class SerializedProperty
    {
        public UnityEngine.Object objectReferenceValue { get; set; }
        public string stringValue { get; set; } = "";
        public int intValue { get; set; }
        public long longValue { get; set; }
        public bool boolValue { get; set; }
        public float floatValue { get; set; }
        public int enumValueIndex { get; set; }
        public SerializedProperty Copy() => this;
        public bool NextVisible(bool e = true) => false;
        public SerializedProperty FindPropertyRelative(string p) => null;
        public string name { get; }
        public string type { get; }
        public string propertyPath { get; }
        public int arraySize { get; set; }
        public SerializedProperty GetArrayElementAtIndex(int i) => null;
    }

    public static class PrefabUtility
    {
        public static UnityEngine.GameObject SaveAsPrefabAsset(UnityEngine.GameObject instanceRoot, string assetPath) => null;
        public static UnityEngine.GameObject SaveAsPrefabAssetAndConnect(UnityEngine.GameObject instanceRoot, string assetPath, InteractionMode m) => null;
        public static UnityEngine.Object InstantiatePrefab(UnityEngine.Object a) => null;
        public static bool IsPartOfPrefabInstance(UnityEngine.Object o) => false;
    }

    public enum InteractionMode { AutomatedAction, UserAction }

    public class AssetImporter : UnityEngine.Object
    {
        public string assetPath { get; set; }
        public void SaveAndReimport() { }
        public AssetImportContext2 GetAssetContext() => null;
    }

    public class AssetImportContext2 { }

    public class TextureImporter : AssetImporter
    {
        public TextureImporterType textureType { get; set; }
        public bool isReadable { get; set; }
        public bool alphaIsTransparency { get; set; }
        public void SaveAndReimport() { }
        public TextureImporterPlatformSettings GetDefaultPlatformTextureSettings() => null;
        public void SetPlatformTextureSettings(TextureImporterPlatformSettings s) { }
    }

    public enum TextureImporterType { Default, NormalMap, GUI, Sprite, Cursor, Cookie, Lightmap, SingleChannel }

    public sealed class TextureImporterPlatformSettings
    {
        public string name = "DefaultTexturePlatform";
        public int maxTextureSize = 2048;
        public TextureImporterFormat format = TextureImporterFormat.Automatic;
        public int compressionQuality = 50;
        public bool allowsAlphaSplitting;
    }

    public enum TextureImporterFormat { Automatic = -1, RGB24 = 3, RGBA32 = 4, ARGB32 = 5, RGB565 = 7, RGBAHalf = 12, DXT1 = 10, DXT5 = 12, BC7 = 26, ASTC_RGB_6x6 = 48 }
}

namespace UnityEditor.Build.Reporting
{
    public sealed class BuildReport
    {
        public BuildSummary summary { get; } = new BuildSummary();
        public BuildResult result => summary.result;
        public string Summary() => "";
        public BuildStep[] steps => new BuildStep[0];
    }

    public sealed class BuildSummary
    {
        public BuildResult result { get; set; }
        public int totalErrors { get; set; }
        public int totalWarnings { get; set; }
        public long totalSize { get; set; }
        public string outputPath { get; set; }
        public UnityEditor.BuildTarget target { get; set; }
        public string guid { get; set; }
    }

    public enum BuildResult { Unknown, Succeeded, Failed, Cancelled }

    public sealed class BuildStep
    {
        public string name { get; set; }
        public BuildStepResult result { get; set; }
        public int duration { get; set; }
    }

    public enum BuildStepResult { Succeeded, Failed, Cancelled, Warning }
}

namespace UnityEditor.Build
{
    public interface IPreprocessBuildWithReport
    {
        void OnPreprocessBuild(UnityEditor.Build.Reporting.BuildReport report);
    }

    public interface IPostprocessBuildWithReport
    {
        void OnPostprocessBuild(UnityEditor.Build.Reporting.BuildReport report);
    }

    public interface IProcessSceneWithReport
    {
        void OnProcessScene(UnityEngine.SceneManagement.Scene scene, UnityEditor.Build.Reporting.BuildReport report);
    }
}

namespace UnityEditor
{
    public enum BuildTarget { StandaloneWindows = 5, StandaloneWindows64 = 19, StandaloneOSX = 2, StandaloneLinux64 = 24, iOS = 9, Android = 13, WebGL = 20, WSAPlayer = 26, PS4 = 31, XboxOne = 37, Switch = 36, tvOS = 38, NoTarget = -2 }
    public enum BuildTargetGroup { Unknown = 0, Standalone = 1, iOS = 4, Android = 7, WebGL = 8, WSAPlayer = 9, PS4 = 10, XboxOne = 11, Switch = 12, tvOS = 13 }
}

namespace UnityEditor
{
    public class BuildFailedException : Exception
    {
        public BuildFailedException(string m) : base(m) { }
    }

    public static class Menu
    {
        public static void SetChecked(string menuPath, bool b) { }
        public static bool GetChecked(string menuPath) => false;
        public static void SetEnabled(string menuPath, bool b) { }
        public static bool GetEnabled(string menuPath) => false;
    }

    public sealed class EditorBuildSettingsScene
    {
        public string path { get; set; } = "";
        public bool enabled { get; set; } = true;
        public UnityEditor.Build.GUID guid { get; set; }
    }

    public static class EditorBuildSettings
    {
        public static EditorBuildSettingsScene[] scenes { get; set; } = new EditorBuildSettingsScene[0];
        public static void AddBuildScene(EditorBuildSettingsScene s) { }
    }

    public static class EditorApplication
    {
        public static bool isPlaying { get; set; }
        public static bool isCompiling { get; set; }
        public static bool isUpdating { get; set; }
        public static void SaveAssets() { }
        public static void EnterPlaymode() { }
        public static void ExitPlaymode() { }
    }

    public static class Selection
    {
        public static UnityEngine.Object activeObject { get; set; }
        public static GameObject activeGameObject { get; set; }
        public static void SetActiveObjectWithContext(UnityEngine.Object o, UnityEngine.Object c) { }
    }

    public class Editor : ScriptableObject
    {
        public virtual void OnInspectorGUI() { }
        public void DrawDefaultInspector() { }
        public void Repaint() { }
        public UnityEngine.Object target { get; }
    }

    public class EditorWindow : ScriptableObject
    {
        public void Show() { }
        public void Repaint() { }
        public void Close() { }
        public static T GetWindow<T>() where T : EditorWindow => null;
        public static T CreateWindow<T>() where T : EditorWindow => null;
    }

    public static class Undo
    {
        public static void RegisterCreatedObjectUndo(UnityEngine.Object o, string n) { }
        public static void RegisterCompleteObjectUndo(UnityEngine.Object o, string n) { }
        public static void RecordObject(UnityEngine.Object o, string n) { }
        public static void ClearUndo(UnityEngine.Object o) { }
        public static void PerformUndo() { }
        public static void PerformRedo() { }
    }
}

namespace UnityEditor.Build
{
    public struct GUID
    {
        public static GUID GenerateNew() => default;
        public bool Empty => true;
    }
}
