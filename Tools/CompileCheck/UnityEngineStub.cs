// BlockOut 离线编译校验用 UnityEngine 桩（仅编译期存在，不进入 Unity 工程）。
// 目标：在无 Unity 编辑器环境下对 Assets/BlockOut/Runtime 做全量编译检查。
// 只提供签名与最小行为；不追求与 Unity 运行时语义一致。
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Text.Json;
using UnityEngine.EventSystems;

namespace UnityEngine
{
    [AttributeUsage(AttributeTargets.All)]
    public sealed class SerializeFieldAttribute : Attribute { public string Name; }

    [AttributeUsage(AttributeTargets.All)]
    public sealed class HeaderAttribute : Attribute { public HeaderAttribute(string h) { } }

    [AttributeUsage(AttributeTargets.Field)]
    public sealed class RangeAttribute : Attribute { public RangeAttribute(float a, float b) { } }

    [AttributeUsage(AttributeTargets.Field)]
    public sealed class TooltipAttribute : Attribute { public TooltipAttribute(string t) { } }

    [AttributeUsage(AttributeTargets.Field)]
    public sealed class SpaceAttribute : Attribute { public SpaceAttribute() { } public SpaceAttribute(float h) { } }

    [AttributeUsage(AttributeTargets.Field)]
    public sealed class MultilineAttribute : Attribute { public MultilineAttribute(int l = 3) { } }

    [AttributeUsage(AttributeTargets.Field)]
    public sealed class TextAreaAttribute : Attribute { public TextAreaAttribute(int a, int b) { } }

    [AttributeUsage(AttributeTargets.Field)]
    public sealed class HideInInspectorAttribute : Attribute { }

    [AttributeUsage(AttributeTargets.Field)]
    public sealed class MinAttribute : Attribute { public MinAttribute(float v) { } }

    [AttributeUsage(AttributeTargets.Field)]
    public sealed class NonReentrantAttribute : Attribute { }

    [AttributeUsage(AttributeTargets.Class)]
    public sealed class RequireComponentAttribute : Attribute { public Type m_Type0; public RequireComponentAttribute(Type t) { m_Type0 = t; } }

    [AttributeUsage(AttributeTargets.Class)]
    public sealed class DisallowMultipleComponentAttribute : Attribute { }

    [AttributeUsage(AttributeTargets.Class)]
    public sealed class ExecuteAlwaysAttribute : Attribute { }

    [AttributeUsage(AttributeTargets.Class)]
    public sealed class ExecuteInEditModeAttribute : Attribute { }

    [AttributeUsage(AttributeTargets.Class)]
    public sealed class AddComponentMenuAttribute : Attribute { public AddComponentMenuAttribute(string s) { } }

    [AttributeUsage(AttributeTargets.Class)]
    public sealed class SelectionBaseAttribute : Attribute { }

    [AttributeUsage(AttributeTargets.Class)]
    public sealed class ContextMenuAttribute : Attribute { public ContextMenuAttribute(string s) { } }

    [AttributeUsage(AttributeTargets.Method)]
    public sealed class ContextMenuItemAttribute : Attribute { public ContextMenuItemAttribute(string n, string m) { } }

    [AttributeUsage(AttributeTargets.Class | AttributeTargets.Struct)]
    public sealed class SerializeReferenceAttribute : Attribute { }

    [AttributeUsage(AttributeTargets.Field)]
    public sealed class FormerlySerializedAsAttribute : Attribute { public FormerlySerializedAsAttribute(string n) { } }

    [AttributeUsage(AttributeTargets.Method)]
    public sealed class RuntimeInitializeOnLoadMethodAttribute : Attribute
    { public RuntimeInitializeOnLoadMethodAttribute() { } public RuntimeInitializeOnLoadMethodAttribute(RuntimeInitializeLoadType t) { } }

    public enum RuntimeInitializeLoadType { BeforeSceneLoad, AfterSceneLoad, BeforeSplashScreen, AfterAssembliesLoaded }

    public class Object
    {
        public string name { get; set; }
        public HideFlags hideFlags { get; set; }
        public static void Destroy(Object o) { }
        public static void Destroy(Object o, float t) { }
        public static void DestroyImmediate(Object o) { }
        public static void DestroyImmediate(Object o, bool a) { }
        public static void DontDestroyOnLoad(Object target) { }
        public static T Instantiate<T>(T original) where T : Object => original;
        public static T Instantiate<T>(T original, Transform parent) where T : Object => original;
        public static T Instantiate<T>(T original, Transform parent, bool worldSpace) where T : Object => original;
        public static Object Instantiate(Object original, Vector3 p, Quaternion q) => original;
        public static Object Instantiate(Object original, Transform parent) => original;
        public static Object Instantiate(Object original, Transform parent, bool worldSpace) => original;
        public static Object Instantiate(Object original, Vector3 p, Quaternion q, Transform parent) => original;
        public static T FindObjectOfType<T>() where T : Object => default;
        public static Object FindObjectOfType(Type t) => default;
        public static T FindFirstObjectByType<T>() where T : Object => default;
        public static T FindAnyObjectByType<T>() where T : Object => default;
        public static T[] FindObjectsByType<T>(FindObjectsSortMode sortMode) where T : Object => new T[0];
        public static T[] FindObjectsByType<T>() where T : Object => new T[0];
        public static T[] FindObjectsOfType<T>() where T : Object => new T[0];
        public static Object[] FindObjectsOfType(Type t) => new Object[0];
        public static bool operator ==(Object a, Object b) { return ReferenceEquals(a, b) || (a is null && b is null); }
        public static bool operator !=(Object a, Object b) { return !(a == b); }
        public int GetInstanceID() => 0;
        public override bool Equals(object o) { return ReferenceEquals(this, o); }
        public override int GetHashCode() { return 0; }
        public override string ToString() { return name ?? base.ToString(); }
    }

    public enum HideFlags { None = 0, HideInHierarchy = 1, HideInInspector = 2, DontSaveInEditor = 4, NotEditable = 8, DontSaveInBuild = 16, DontUnloadUnusedAsset = 32 }

    public enum FindObjectsSortMode { None, InstanceID, Path, Name }

    public class Component : Object
    {
        public GameObject gameObject { get; internal set; }
        public Transform transform { get; internal set; }
        public string tag { get; set; }
        public T GetComponent<T>() => default;
        public Component GetComponent(Type t) => default;
        public T GetComponentInChildren<T>() => default;
        public T GetComponentInParent<T>() => default;
        public T[] GetComponents<T>() => new T[0];
        public T[] GetComponentsInChildren<T>() => new T[0];
        public T[] GetComponentsInParent<T>() => new T[0];
        public void GetComponents<T>(List<T> r) { }
        public bool TryGetComponent<T>(out T c) { c = default; return false; }
    }

    public class Behaviour : Component { public bool enabled { get; set; } = true; public bool isActiveAndEnabled => enabled; }

    public class MonoBehaviour : Behaviour
    {
        public Coroutine StartCoroutine(IEnumerator r) => new Coroutine();
        public Coroutine StartCoroutine(string m) => new Coroutine();
        public Coroutine StartCoroutine_AutoMethod(IEnumerator r) => new Coroutine();
        public void StopCoroutine(IEnumerator r) { }
        public void StopCoroutine(Coroutine c) { }
        public void StopCoroutine(string m) { }
        public void StopAllCoroutines() { }
        public void Invoke(string m, float t) { }
        public void InvokeRepeating(string m, float t, float r) { }
        public void CancelInvoke() { }
        public void CancelInvoke(string m) { }
        public bool IsInvoking() => false;
        public bool IsInvoking(string m) => false;
        public bool useGUILayout { get; set; }
        public bool runInEditMode { get; set; }
    }

    public sealed class Coroutine : YieldInstruction { }

    public class YieldInstruction
    {
        internal IEnumerator routine;
        public object Current => routine != null ? routine.Current : null;
        public bool MoveNext() => routine != null && routine.MoveNext();
    }

    public sealed class WaitForSeconds : YieldInstruction { public WaitForSeconds(float s) { } }
    public sealed class WaitForSecondsRealtime : YieldInstruction { public WaitForSecondsRealtime(float s) { } }
    public sealed class WaitForEndOfFrame : YieldInstruction { }
    public sealed class WaitForFixedUpdate : YieldInstruction { }
    public sealed class WaitUntil : YieldInstruction { public WaitUntil(Func<bool> p) { } }
    public sealed class WaitWhile : YieldInstruction { public WaitWhile(Func<bool> p) { } }

    public sealed class GameObject : Object
    {
        public GameObject() { }
        public GameObject(string n) { name = n; }
        public GameObject(string n, params Type[] components) { name = n; }
        public Transform transform { get; } = new Transform();
        public bool activeSelf { get; private set; } = true;
        public bool activeInHierarchy => activeSelf;
        public int layer { get; set; }
        public string tag { get; set; }
        public void SetActive(bool v) { activeSelf = v; }
        public bool CompareTag(string t) => tag == t;
        public T AddComponent<T>() where T : Component => (T)Activator.CreateInstance(typeof(T));
        public Component AddComponent(Type t) => (Component)Activator.CreateInstance(t);
        public T GetComponent<T>() => default;
        public Component GetComponent(Type t) => default;
        public T GetComponentInChildren<T>() => default;
        public T GetComponentInParent<T>() => default;
        public T[] GetComponents<T>() => new T[0];
        public T[] GetComponentsInChildren<T>() => new T[0];
        public T[] GetComponentsInParent<T>() => new T[0];
        public void GetComponents<T>(List<T> r) { }
        public bool TryGetComponent<T>(out T c) { c = default; return false; }
        public void SendMessage(string m) { }
        public void SendMessage(string m, object v) { }
        public void SendMessageUpwards(string m) { }
        public void BroadcastMessage(string m) { }
        public void SetActiveRecursively(bool v) { }
        public static GameObject Find(string n) => null;
        public static GameObject FindWithTag(string t) => null;
        public static GameObject[] FindGameObjectsWithTag(string t) => new GameObject[0];
    }

    public class Transform : Component
    {
        public Vector3 position { get; set; }
        public Vector3 localPosition { get; set; }
        public Quaternion rotation { get; set; } = Quaternion.identity;
        public Quaternion localRotation { get; set; } = Quaternion.identity;
        public Vector3 eulerAngles { get; set; }
        public Vector3 localEulerAngles { get; set; }
        public Vector3 localScale { get; set; } = Vector3.one;
        public Vector3 lossyScale => Vector3.one;
        public Transform parent { get; set; }
        public int childCount { get; private set; }
        public Vector3 forward => Vector3.forward;
        public Vector3 right => Vector3.right;
        public Vector3 up => Vector3.up;
        public Transform root => this;
        public Matrix4x4 worldToLocalMatrix => Matrix4x4.identity;
        public Matrix4x4 localToWorldMatrix => Matrix4x4.identity;
        public System.Collections.IEnumerator GetEnumerator() => new List<object>().GetEnumerator();
        public Transform GetChild(int i) => null;
        public Transform Find(string n) => null;
        public void SetParent(Transform p) { }
        public void SetParent(Transform p, bool wp) { }
        public void SetAsFirstSibling() { }
        public void SetAsLastSibling() { }
        public void SetSiblingIndex(int i) { }
        public int GetSiblingIndex() => 0;
        public void Rotate(Vector3 e) { }
        public void Rotate(Vector3 axis, float a) { }
        public void RotateAround(Vector3 p, Vector3 a, float d) { }
        public void LookAt(Transform t) { }
        public void LookAt(Vector3 w) { }
        public Vector3 TransformPoint(Vector3 p) => p;
        public Vector3 InverseTransformPoint(Vector3 p) => p;
        public Vector3 TransformDirection(Vector3 d) => d;
        public Vector3 InverseTransformDirection(Vector3 d) => d;
        public Vector3 TransformVector(Vector3 v) => v;
    }

    public sealed class RectTransform : Transform
    {
        public Vector2 anchorMin { get; set; }
        public Vector2 anchorMax { get; set; } = Vector2.one;
        public Vector2 anchoredPosition { get; set; }
        public Vector2 sizeDelta { get; set; }
        public Vector2 pivot { get; set; } = new Vector2(0.5f, 0.5f);
        public Vector2 offsetMin { get; set; }
        public Vector2 offsetMax { get; set; }
        public Rect rect { get; set; }
        public void ForceUpdateRectTransforms() { }
    }

    public static class Debug
    {
        public static ILogger unityLogger { get; } = new DefaultLogger();
        public static void Log(object msg) { Console.WriteLine("[LOG] " + msg); }
        public static void Log(string tag, object msg) { Console.WriteLine("[" + tag + "] " + msg); }
        public static void LogWarning(object msg) { Console.WriteLine("[WARN] " + msg); }
        public static void LogError(object msg) { Console.WriteLine("[ERR] " + msg); }
        public static void LogException(Exception e) { Console.WriteLine(e); }
        public static void Assert(bool c) { }
        public static void Assert(bool c, object m) { }
        public static void DrawLine(Vector3 a, Vector3 b, Color c, float t = 0f) { }
        public static void DrawRay(Vector3 a, Vector3 b, Color c, float t = 0f) { }
        public static void Break() { }
        public static bool isDebugBuild { get; set; }
    }

    public interface ILogger
    {
        void Log(LogType t, object m);
        void LogFormat(LogType t, string f, params object[] a);
        void LogError(string tag, object m);
        void LogException(Exception e);
        void LogWarning(string tag, object m);
        bool logEnabled { get; set; }
        LogType filterLogType { get; set; }
    }

    internal sealed class DefaultLogger : ILogger
    {
        public bool logEnabled { get; set; } = true;
        public LogType filterLogType { get; set; } = LogType.Log;
        public void Log(LogType t, object m) { if (logEnabled) Console.WriteLine("[" + t + "] " + m); }
        public void LogFormat(LogType t, string f, params object[] a) { if (logEnabled) Console.WriteLine("[" + t + "] " + string.Format(f, a)); }
        public void LogError(string tag, object m) { if (logEnabled) Console.WriteLine("[ERR][" + tag + "] " + m); }
        public void LogException(Exception e) { if (logEnabled) Console.WriteLine(e); }
        public void LogWarning(string tag, object m) { if (logEnabled) Console.WriteLine("[WARN][" + tag + "] " + m); }
    }

    public enum LogType { Error, Assert, Warning, Log, Exception }

    public static class Mathf
    {
        public const float PI = 3.14159274f;
        public const float Infinity = float.PositiveInfinity;
        public const float NegativeInfinity = float.NegativeInfinity;
        public const float Deg2Rad = 0.0174532924f;
        public const float Rad2Deg = 57.29578f;
        public const float Epsilon = 1.401298E-45f;
        public static float Sqrt(float v) => (float)Math.Sqrt(v);
        public static float Pow(float a, float b) => (float)Math.Pow(a, b);
        public static float Exp(float p) => (float)Math.Exp(p);
        public static float Log(float p) => (float)Math.Log(p);
        public static float Log(float p, float b) => (float)Math.Log(p, b);
        public static float Sin(float v) => (float)Math.Sin(v);
        public static float Cos(float v) => (float)Math.Cos(v);
        public static float Tan(float v) => (float)Math.Tan(v);
        public static float Asin(float v) => (float)Math.Asin(v);
        public static float Acos(float v) => (float)Math.Acos(v);
        public static float Atan(float v) => (float)Math.Atan(v);
        public static float Atan2(float y, float x) => (float)Math.Atan2(y, x);
        public static float Abs(float v) => Math.Abs(v);
        public static int Abs(int v) => Math.Abs(v);
        public static float Min(float a, float b) => Math.Min(a, b);
        public static int Min(int a, int b) => Math.Min(a, b);
        public static float Min(params float[] v) { float m = float.MaxValue; foreach (var x in v) m = Math.Min(m, x); return m; }
        public static float Max(float a, float b) => Math.Max(a, b);
        public static int Max(int a, int b) => Math.Max(a, b);
        public static float Max(params float[] v) { float m = float.MinValue; foreach (var x in v) m = Math.Max(m, x); return m; }
        public static float Clamp(float v, float a, float b) => Math.Min(Math.Max(v, a), b);
        public static int Clamp(int v, int a, int b) => Math.Min(Math.Max(v, a), b);
        public static float Clamp01(float v) => Math.Min(Math.Max(v, 0f), 1f);
        public static float Ceil(float v) => (float)Math.Ceiling(v);
        public static float Floor(float v) => (float)Math.Floor(v);
        public static float Round(float v) => (float)Math.Round(v);
        public static int CeilToInt(float v) => (int)Math.Ceiling(v);
        public static int FloorToInt(float v) => (int)Math.Floor(v);
        public static int RoundToInt(float v) => (int)Math.Round(v);
        public static float Sign(float v) => Math.Sign(v);
        public static bool Approximately(float a, float b) => Math.Abs(a - b) < 1e-6f;
        public static float Lerp(float a, float b, float t) => a + (b - a) * Clamp01(t);
        public static float LerpUnclamped(float a, float b, float t) => a + (b - a) * t;
        public static float InverseLerp(float a, float b, float v) => a == b ? 0f : Clamp01((v - a) / (b - a));
        public static float MoveTowards(float c, float t, float md) { float d = t - c; return Math.Abs(d) <= md ? t : c + Math.Sign(d) * md; }
        public static float MoveTowardsAngle(float c, float t, float md) => MoveTowards(c, t, md);
        public static float SmoothStep(float a, float b, float t) { t = Clamp01(t); t = t * t * (3f - 2f * t); return a + (b - a) * t; }
        public static float SmoothDamp(float c, float t, ref float cv, float st, float mt = float.PositiveInfinity, float dt = -1f) { cv = 0f; return t; }
        public static float SmoothDampAngle(float c, float t, ref float cv, float st, float mt = float.PositiveInfinity, float dt = -1f) { cv = 0f; return t; }
        public static float PingPong(float t, float l) => l == 0f ? 0f : (float)Math.Abs(Math.IEEERemainder(t, l * 2f) - l);
        public static float Repeat(float t, float l) => l == 0f ? 0f : t - (float)Math.Floor(t / l) * l;
        public static float DeltaAngle(float c, float t) => Mathf.Repeat(t - c + 180f, 360f) - 180f;
        public static float Gamma(float v, float a, float b) => v;
    }

    public struct Vector2
    {
        public float x, y;
        public Vector2(float x, float y) { this.x = x; this.y = y; }
        public static Vector2 zero => new Vector2(0f, 0f);
        public static Vector2 one => new Vector2(1f, 1f);
        public static Vector2 up => new Vector2(0f, 1f);
        public static Vector2 down => new Vector2(0f, -1f);
        public static Vector2 left => new Vector2(-1f, 0f);
        public static Vector2 right => new Vector2(1f, 0f);
        public static Vector2 positiveInfinity => new Vector2(float.PositiveInfinity, float.PositiveInfinity);
        public float magnitude => (float)Math.Sqrt(x * x + y * y);
        public float sqrMagnitude => x * x + y * y;
        public Vector2 normalized { get { float m = magnitude; return m > 1e-9f ? new Vector2(x / m, y / m) : zero; } }
        public void Normalize() { var n = normalized; x = n.x; y = n.y; }
        public static float Distance(Vector2 a, Vector2 b) => (a - b).magnitude;
        public static float Dot(Vector2 a, Vector2 b) => a.x * b.x + a.y * b.y;
        public static float Angle(Vector2 a, Vector2 b) => 0f;
        public static Vector2 Lerp(Vector2 a, Vector2 b, float t) => a + (b - a) * Mathf.Clamp01(t);
        public static Vector2 LerpUnclamped(Vector2 a, Vector2 b, float t) => a + (b - a) * t;
        public static Vector2 Max(Vector2 a, Vector2 b) => new Vector2(Mathf.Max(a.x, b.x), Mathf.Max(a.y, b.y));
        public static Vector2 Min(Vector2 a, Vector2 b) => new Vector2(Mathf.Min(a.x, b.x), Mathf.Min(a.y, b.y));
        public static Vector2 Scale(Vector2 a, Vector2 b) => new Vector2(a.x * b.x, a.y * b.y);
        public static Vector2 operator +(Vector2 a, Vector2 b) => new Vector2(a.x + b.x, a.y + b.y);
        public static Vector2 operator -(Vector2 a, Vector2 b) => new Vector2(a.x - b.x, a.y - b.y);
        public static Vector2 operator -(Vector2 a) => new Vector2(-a.x, -a.y);
        public static Vector2 operator *(Vector2 a, float d) => new Vector2(a.x * d, a.y * d);
        public static Vector2 operator *(float d, Vector2 a) => new Vector2(a.x * d, a.y * d);
        public static Vector2 operator /(Vector2 a, float d) => new Vector2(a.x / d, a.y / d);
        public static bool operator ==(Vector2 a, Vector2 b) => a.x == b.x && a.y == b.y;
        public static bool operator !=(Vector2 a, Vector2 b) => !(a == b);
        // 注意：Unity 的 Vector2 没有到 Vector3 的隐式转换（与真实行为一致）。
        public override bool Equals(object o) => o is Vector2 v && v == this;
        public override int GetHashCode() => x.GetHashCode() ^ (y.GetHashCode() << 2);
        public override string ToString() => "(" + x + "," + y + ")";
    }

    public struct Vector2Int
    {
        public int x, y;
        public Vector2Int(int x, int y) { this.x = x; this.y = y; }
        public static Vector2Int zero => new Vector2Int(0, 0);
        public static Vector2Int one => new Vector2Int(1, 1);
        public static Vector2Int up => new Vector2Int(0, 1);
        public static Vector2Int down => new Vector2Int(0, -1);
        public static Vector2Int left => new Vector2Int(-1, 0);
        public static Vector2Int right => new Vector2Int(1, 0);
        public static Vector2Int Min(Vector2Int a, Vector2Int b) => new Vector2Int(Mathf.Min(a.x, b.x), Mathf.Min(a.y, b.y));
        public static Vector2Int Max(Vector2Int a, Vector2Int b) => new Vector2Int(Mathf.Max(a.x, b.x), Mathf.Max(a.y, b.y));
        public static Vector2Int Scale(Vector2Int a, Vector2Int b) => new Vector2Int(a.x * b.x, a.y * b.y);
        public static Vector2Int FloorToInt(Vector2 v) => new Vector2Int(Mathf.FloorToInt(v.x), Mathf.FloorToInt(v.y));
        public static Vector2Int CeilToInt(Vector2 v) => new Vector2Int(Mathf.CeilToInt(v.x), Mathf.CeilToInt(v.y));
        public static Vector2Int RoundToInt(Vector2 v) => new Vector2Int(Mathf.RoundToInt(v.x), Mathf.RoundToInt(v.y));
        public float magnitude => (float)Math.Sqrt(x * x + y * y);
        public int sqrMagnitude => x * x + y * y;
        public static Vector2Int operator +(Vector2Int a, Vector2Int b) => new Vector2Int(a.x + b.x, a.y + b.y);
        public static Vector2Int operator -(Vector2Int a, Vector2Int b) => new Vector2Int(a.x - b.x, a.y - b.y);
        public static Vector2Int operator *(Vector2Int a, int d) => new Vector2Int(a.x * d, a.y * d);
        public static Vector2Int operator *(int d, Vector2Int a) => new Vector2Int(a.x * d, a.y * d);
        public static bool operator ==(Vector2Int a, Vector2Int b) => a.x == b.x && a.y == b.y;
        public static bool operator !=(Vector2Int a, Vector2Int b) => !(a == b);
        public static implicit operator Vector2(Vector2Int v) => new Vector2(v.x, v.y);
        public override bool Equals(object o) => o is Vector2Int v && v == this;
        public override int GetHashCode() => x ^ (y << 16);
        public override string ToString() => "(" + x + "," + y + ")";
    }

    public struct Vector3
    {
        public float x, y, z;
        public Vector3(float x, float y, float z) { this.x = x; this.y = y; this.z = z; }
        public Vector3(float x, float y) { this.x = x; this.y = y; z = 0f; }
        public static Vector3 zero => new Vector3(0f, 0f, 0f);
        public static Vector3 one => new Vector3(1f, 1f, 1f);
        public static Vector3 up => new Vector3(0f, 1f, 0f);
        public static Vector3 down => new Vector3(0f, -1f, 0f);
        public static Vector3 left => new Vector3(-1f, 0f, 0f);
        public static Vector3 right => new Vector3(1f, 0f, 0f);
        public static Vector3 forward => new Vector3(0f, 0f, 1f);
        public static Vector3 back => new Vector3(0f, 0f, -1f);
        public static Vector3 positiveInfinity => new Vector3(float.PositiveInfinity, float.PositiveInfinity, float.PositiveInfinity);
        public float magnitude => (float)Math.Sqrt(x * x + y * y + z * z);
        public float sqrMagnitude => x * x + y * y + z * z;
        public Vector3 normalized { get { float m = magnitude; return m > 1e-9f ? new Vector3(x / m, y / m, z / m) : zero; } }
        public void Normalize() { var n = normalized; x = n.x; y = n.y; z = n.z; }
        public static float Distance(Vector3 a, Vector3 b) => (a - b).magnitude;
        public static float Dot(Vector3 a, Vector3 b) => a.x * b.x + a.y * b.y + a.z * b.z;
        public static Vector3 Cross(Vector3 a, Vector3 b) => new Vector3(a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x);
        public static Vector3 Lerp(Vector3 a, Vector3 b, float t) => a + (b - a) * Mathf.Clamp01(t);
        public static Vector3 LerpUnclamped(Vector3 a, Vector3 b, float t) => a + (b - a) * t;
        public static Vector3 Max(Vector3 a, Vector3 b) => new Vector3(Mathf.Max(a.x, b.x), Mathf.Max(a.y, b.y), Mathf.Max(a.z, b.z));
        public static Vector3 Min(Vector3 a, Vector3 b) => new Vector3(Mathf.Min(a.x, b.x), Mathf.Min(a.y, b.y), Mathf.Min(a.z, b.z));
        public static Vector3 Scale(Vector3 a, Vector3 b) => new Vector3(a.x * b.x, a.y * b.y, a.z * b.z);
        public static Vector3 Project(Vector3 v, Vector3 n) => v - n * Vector3.Dot(n, v);
        public static Vector3 operator +(Vector3 a, Vector3 b) => new Vector3(a.x + b.x, a.y + b.y, a.z + b.z);
        public static Vector3 operator -(Vector3 a, Vector3 b) => new Vector3(a.x - b.x, a.y - b.y, a.z - b.z);
        public static Vector3 operator -(Vector3 a) => new Vector3(-a.x, -a.y, -a.z);
        public static Vector3 operator *(Vector3 a, float d) => new Vector3(a.x * d, a.y * d, a.z * d);
        public static Vector3 operator *(float d, Vector3 a) => new Vector3(a.x * d, a.y * d, a.z * d);
        public static Vector3 operator /(Vector3 a, float d) => new Vector3(a.x / d, a.y / d, a.z / d);
        public static bool operator ==(Vector3 a, Vector3 b) => a.x == b.x && a.y == b.y && a.z == b.z;
        public static bool operator !=(Vector3 a, Vector3 b) => !(a == b);
        public static implicit operator Vector2(Vector3 v) => new Vector2(v.x, v.y);
        public override bool Equals(object o) => o is Vector3 v && v == this;
        public override int GetHashCode() => x.GetHashCode() ^ (y.GetHashCode() << 2) ^ (z.GetHashCode() >> 2);
        public override string ToString() => "(" + x + "," + y + "," + z + ")";
    }

    public struct Quaternion
    {
        public float x, y, z, w;
        public Quaternion(float x, float y, float z, float w) { this.x = x; this.y = y; this.z = z; this.w = w; }
        public static Quaternion identity => new Quaternion(0f, 0f, 0f, 1f);
        public static Quaternion Euler(float x, float y, float z) => new Quaternion(0f, 0f, 0f, 1f);
        public static Quaternion Euler(Vector3 e) => identity;
        public static Quaternion AngleAxis(float a, Vector3 axis) => identity;
        public static Quaternion LookRotation(Vector3 f) => identity;
        public static Quaternion LookRotation(Vector3 f, Vector3 u) => identity;
        public static Quaternion Slerp(Quaternion a, Quaternion b, float t) => a;
        public static Quaternion Lerp(Quaternion a, Quaternion b, float t) => a;
        public static Quaternion Inverse(Quaternion q) => identity;
        public static float Angle(Quaternion a, Quaternion b) => 0f;
        public static Vector3 operator *(Quaternion q, Vector3 v) => v;
        public override string ToString() => "(" + x + "," + y + "," + z + "," + w + ")";
    }

    public struct Matrix4x4
    {
        public static Matrix4x4 identity => new Matrix4x4();
        public static Matrix4x4 zero => new Matrix4x4();
        public Vector3 MultiplyPoint(Vector3 p) => p;
        public Vector3 MultiplyVector(Vector3 v) => v;
        public Vector3 MultiplyPoint3x4(Vector3 p) => p;
        public static Matrix4x4 TRS(Vector3 p, Quaternion r, Vector3 s) => new Matrix4x4();
        public static Matrix4x4 Translate(Vector3 v) => new Matrix4x4();
        public static Matrix4x4 Rotate(Quaternion q) => new Matrix4x4();
        public static Matrix4x4 Scale(Vector3 v) => new Matrix4x4();
        public Quaternion rotation => Quaternion.identity;
        public Vector3 lossyScale => Vector3.one;
        public Matrix4x4 inverse => new Matrix4x4();
        public float Get(int r, int c) => 0f;
    }

    public static class Handheld
    {
        public static void Vibrate() { }
        public static bool PlayFullScreenMovie(string p) => false;
        public static bool PlayFullScreenMovie(string p, Color c, FullScreenMovieControlMode m) => false;
        public static bool PlayFullScreenMovie(string p, Color c, FullScreenMovieControlMode m, FullScreenMovieScalingMode s) => false;
        public static void StartActivityIndicator() { }
        public static void StopActivityIndicator() { }
        public static HideFlags hideFlags { get; set; }
    }

    public enum FullScreenMovieControlMode { Full, Minimal, Hidden }
    public enum FullScreenMovieScalingMode { None, Fill, AspectFill, AspectFit }

    public struct Color
    {
        public float r, g, b, a;
        public Color(float r, float g, float b, float a) { this.r = r; this.g = g; this.b = b; this.a = a; }
        public Color(float r, float g, float b) { this.r = r; this.g = g; this.b = b; a = 1f; }
        public static Color red => new Color(1f, 0f, 0f, 1f);
        public static Color green => new Color(0f, 1f, 0f, 1f);
        public static Color blue => new Color(0f, 0f, 1f, 1f);
        public static Color white => new Color(1f, 1f, 1f, 1f);
        public static Color black => new Color(0f, 0f, 0f, 1f);
        public static Color yellow => new Color(1f, 0.92f, 0.016f, 1f);
        public static Color cyan => new Color(0f, 1f, 1f, 1f);
        public static Color magenta => new Color(1f, 0f, 1f, 1f);
        public static Color gray => new Color(0.5f, 0.5f, 0.5f, 1f);
        public static Color grey => new Color(0.5f, 0.5f, 0.5f, 1f);
        public static Color clear => new Color(0f, 0f, 0f, 0f);
        public float grayscale => 0.299f * r + 0.587f * g + 0.114f * b;
        public float maxColorComponent => Mathf.Max(r, g, b);
        public static Color Lerp(Color a, Color b, float t) => new Color(Mathf.Lerp(a.r, b.r, t), Mathf.Lerp(a.g, b.g, t), Mathf.Lerp(a.b, b.b, t), Mathf.Lerp(a.a, b.a, t));
        public static Color operator *(Color a, Color b) => new Color(a.r * b.r, a.g * b.g, a.b * b.b, a.a * b.a);
        public static Color operator *(Color a, float d) => new Color(a.r * d, a.g * d, a.b * d, a.a * d);
        public static Color operator *(float d, Color a) => a * d;
        public static bool operator ==(Color a, Color b) => a.r == b.r && a.g == b.g && a.b == b.b && a.a == b.a;
        public static bool operator !=(Color a, Color b) => !(a == b);
        public override bool Equals(object o) => o is Color c && c == this;
        public override int GetHashCode() => 0;
        public override string ToString() => "RGBA(" + r + "," + g + "," + b + "," + a + ")";
    }

    public struct Color32
    {
        public byte r, g, b, a;
        public Color32(byte r, byte g, byte b, byte a) { this.r = r; this.g = g; this.b = b; this.a = a; }
        public static Color32 Lerp(Color32 a, Color32 b, float t) => a;
        public static implicit operator Color(Color32 c) => new Color(c.r / 255f, c.g / 255f, c.b / 255f, c.a / 255f);
        public static implicit operator Color32(Color c) => new Color32((byte)(c.r * 255), (byte)(c.g * 255), (byte)(c.b * 255), (byte)(c.a * 255));
        public override string ToString() => "(" + r + "," + g + "," + b + "," + a + ")";
    }

    public struct Rect
    {
        public float x, y, width, height;
        public Rect(float x, float y, float w, float h) { this.x = x; this.y = y; width = w; height = h; }
        public Rect(Vector2 p, Vector2 s) { x = p.x; y = p.y; width = s.x; height = s.y; }
        public Vector2 center => new Vector2(x + width * 0.5f, y + height * 0.5f);
        public Vector2 size => new Vector2(width, height);
        public Vector2 position => new Vector2(x, y);
        public Vector2 min => new Vector2(x, y);
        public Vector2 max => new Vector2(x + width, y + height);
        public bool Contains(Vector2 p) => p.x >= x && p.x <= x + width && p.y >= y && p.y <= y + height;
        public bool Overlaps(Rect o) => true;
        public static Rect zero => new Rect(0f, 0f, 0f, 0f);
        public float xMin => x;
        public float xMax => x + width;
        public float yMin => y;
        public float yMax => y + height;
        public static bool operator ==(Rect a, Rect b) => a.x == b.x && a.y == b.y && a.width == b.width && a.height == b.height;
        public static bool operator !=(Rect a, Rect b) => !(a == b);
        public override bool Equals(object o) => o is Rect r && r == this;
        public override int GetHashCode() => 0;
        public override string ToString() => "(" + x + "," + y + "," + width + "," + height + ")";
    }

    public struct Vector4
    {
        public float x, y, z, w;
        public Vector4(float x, float y, float z, float w) { this.x = x; this.y = y; this.z = z; this.w = w; }
        public Vector4(float x, float y, float z) { this.x = x; this.y = y; this.z = z; w = 0f; }
        public Vector4(float x, float y) { this.x = x; this.y = y; z = 0f; w = 0f; }
        public static Vector4 zero => new Vector4(0f, 0f, 0f, 0f);
        public static Vector4 one => new Vector4(1f, 1f, 1f, 1f);
        public float magnitude => (float)Math.Sqrt(x * x + y * y + z * z + w * w);
        public float sqrMagnitude => x * x + y * y + z * z + w * w;
        public Vector4 normalized { get { float m = magnitude; return m > 1e-9f ? new Vector4(x / m, y / m, z / m, w / m) : zero; } }
        public static Vector4 Lerp(Vector4 a, Vector4 b, float t) => new Vector4(Mathf.Lerp(a.x, b.x, t), Mathf.Lerp(a.y, b.y, t), Mathf.Lerp(a.z, b.z, t), Mathf.Lerp(a.w, b.w, t));
        public static float Dot(Vector4 a, Vector4 b) => a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w;
        public static Vector4 operator +(Vector4 a, Vector4 b) => new Vector4(a.x + b.x, a.y + b.y, a.z + b.z, a.w + b.w);
        public static Vector4 operator -(Vector4 a, Vector4 b) => new Vector4(a.x - b.x, a.y - b.y, a.z - b.z, a.w - b.w);
        public static Vector4 operator *(Vector4 a, float d) => new Vector4(a.x * d, a.y * d, a.z * d, a.w * d);
        public static Vector4 operator *(float d, Vector4 a) => new Vector4(a.x * d, a.y * d, a.z * d, a.w * d);
        public static Vector4 operator /(Vector4 a, float d) => new Vector4(a.x / d, a.y / d, a.z / d, a.w / d);
        public static bool operator ==(Vector4 a, Vector4 b) => a.x == b.x && a.y == b.y && a.z == b.z && a.w == b.w;
        public static bool operator !=(Vector4 a, Vector4 b) => !(a == b);
        public static implicit operator Vector2(Vector4 v) => new Vector2(v.x, v.y);
        public static implicit operator Vector3(Vector4 v) => new Vector3(v.x, v.y, v.z);
        public override bool Equals(object o) => o is Vector4 v && v == this;
        public override int GetHashCode() => 0;
        public override string ToString() => "(" + x + "," + y + "," + z + "," + w + ")";
    }

    public struct Bounds
    {
        public Vector3 center; public Vector3 extents;
        public Bounds(Vector3 c, Vector3 s) { center = c; extents = s * 0.5f; }
        public Vector3 size { get => extents * 2f; set => extents = value * 0.5f; }
        public Vector3 min => center - extents;
        public Vector3 max => center + extents;
        public bool Contains(Vector3 p) => true;
        public void Encapsulate(Bounds b) { }
    }

    public static class Time
    {
        public static float time { get; set; }
        public static float timeSinceLevelLoad { get; set; }
        public static float deltaTime { get; set; } = 0.016f;
        public static float fixedDeltaTime { get; set; } = 0.02f;
        public static float unscaledDeltaTime { get; set; } = 0.016f;
        public static float unscaledTime { get; set; }
        public static float smoothDeltaTime { get; set; } = 0.016f;
        public static float timeScale { get; set; } = 1f;
        public static int frameCount { get; set; }
        public static int renderedFrameCount { get; set; }
        public static float realtimeSinceStartup { get; set; }
        public static float captureFramerate { get; set; }
        public static int captureFramerate_ { get; set; }
        public static float maximumDeltaTime { get; set; }
        public static float fixedTime { get; set; }
    }

    public static class Random
    {
        private static readonly System.Random rng = new System.Random();
        public static float value => (float)rng.NextDouble();
        public static float Range(float a, float b) => a + (float)rng.NextDouble() * (b - a);
        public static int Range(int a, int b) => rng.Next(a, b);
        public static Vector2 insideUnitCircle { get { double r = Math.Sqrt(rng.NextDouble()); double t = rng.NextDouble() * Math.PI * 2; return new Vector2((float)(r * Math.Cos(t)), (float)(r * Math.Sin(t))); } }
        public static Vector2 insideUnitSphere => insideUnitCircle;
        public static Vector3 onUnitSphere => new Vector3(value, value, value).normalized;
        public static Quaternion rotation => Quaternion.identity;
        public static Color ColorHSV() => Color.white;
        public static Color ColorHSV(float h, float s, float v) => Color.white;
        public static void InitState(int seed) { }
    }

    public static class Application
    {
        public static int targetFrameRate { get; set; }
        public static bool runInBackground { get; set; }
        public static BackgroundLoadingPriority backgroundLoadingPriority { get; set; }
        public static string persistentDataPath => Path.Combine(Path.GetTempPath(), "blockout_persist");
        public static string dataPath => Path.GetTempPath();
        public static string streamingAssetsPath => Path.GetTempPath();
        public static string temporaryCachePath => Path.GetTempPath();
        public static string version => "0.0.0";
        public static string unityVersion => "6000.2.7f2";
        public static RuntimePlatform platform => RuntimePlatform.WindowsPlayer;
        public static bool isPlaying => true;
        public static bool isBatchMode => false;
        public static bool isEditor => false;
        public static bool isFocused { get; set; } = true;
        public static string productName { get; set; } = "BlockOut";
        public static string companyName { get; set; }
        public static string absoluteURL => "";
        public static NetworkReachability internetReachability => NetworkReachability.ReachableViaLocalAreaNetwork;
        public static SystemLanguage systemLanguage => SystemLanguage.Chinese;
        public static void Quit(int c = 0) { }
        public static void OpenURL(string u) { }
        public static bool CanStreamedLevelBeLoaded(string n) => false;
        public static void LoadLevel(int i) { }
        public static void LoadLevel(string n) { }
        public static StackTraceLogType stackTraceLogType { get; set; }
        public static ThreadPriority backgroundLoadingPriority2 { get; set; }
    }

    public enum BackgroundLoadingPriority { VeryLow = 0, Low = 500, BelowNormal = 1000, Normal = 2000, High = 3000 }
    public enum NetworkReachability { NotReachable, ReachableViaCarrierDataNetwork, ReachableViaLocalAreaNetwork }
    public enum RuntimePlatform { WindowsPlayer, OSXPlayer, LinuxPlayer, Android, IPhonePlayer, WebGLPlayer }
    public enum SystemLanguage { Chinese, English, Japanese }
    public enum StackTraceLogType { None, ScriptOnly, Full }
    public enum ThreadPriority { Low = 0, BelowNormal = 1, Normal = 2, High = 4 }

    public static class Screen
    {
        public static int width { get; set; } = 1080;
        public static int height { get; set; } = 1920;
        public static float dpi { get; set; } = 160f;
        public static ScreenOrientation orientation { get; set; }
        public static bool autorotateToPortrait { get; set; }
        public static bool fullScreen { get; set; } = true;
        public static FullScreenMode fullScreenMode { get; set; } = FullScreenMode.FullScreenWindow;
        public static Resolution currentResolution => new Resolution { width = 1080, height = 1920, refreshRate = 60 };
        public static Resolution[] resolutions => new Resolution[0];
        public static int sleepTimeout { get; set; }
        public static Rect safeArea { get; set; } = new Rect(0f, 0f, 1080f, 1920f);
        public static void SetResolution(int w, int h, bool f) { width = w; height = h; }
        public static void SetResolution(int w, int h, FullScreenMode m) { }
    }

    public static class SleepTimeout
    {
        public const int NeverSleep = -1;
        public const int SystemSetting = -2;
    }

    public enum ScreenOrientation { Unknown, Portrait, PortraitUpsideDown, LandscapeLeft, LandscapeRight, AutoRotation }
    public enum FullScreenMode { ExclusiveFullScreen, FullScreenWindow, MaximizedWindow, Windowed }
    public struct Resolution { public int width; public int height; public int refreshRate; public override string ToString() => width + "x" + height; }

    public class Camera : Behaviour
    {
        public static Camera main => new Camera();
        public static Camera current => new Camera();
        public bool orthographic { get; set; }
        public float orthographicSize { get; set; } = 5f;
        public float fieldOfView { get; set; } = 60f;
        public float nearClipPlane { get; set; } = 0.3f;
        public float farClipPlane { get; set; } = 1000f;
        public Rect rect { get; set; } = new Rect(0, 0, 1, 1);
        public Color backgroundColor { get; set; } = Color.black;
        public int depth { get; set; }
        public float aspect => 1f;
        public int pixelWidth => 1080;
        public int pixelHeight => 1920;
        public int cullingMask { get; set; } = -1;
        public CameraClearFlags clearFlags { get; set; }
        public Vector3 WorldToScreenPoint(Vector3 p) => p;
        public Vector3 WorldToViewportPoint(Vector3 p) => p;
        public Vector3 ScreenToWorldPoint(Vector3 p) => p;
        public Vector3 ScreenToViewportPoint(Vector3 p) => p;
        public Vector3 ViewportToScreenPoint(Vector3 p) => p;
        public Vector3 ViewportToWorldPoint(Vector3 p) => p;
        public Ray ScreenPointToRay(Vector3 p) => new Ray();
        public Ray ViewportPointToRay(Vector3 p) => new Ray();
        public void ResetAspect() { }
        public void ResetProjectionMatrix() { }
    }

    public enum CameraClearFlags { Skybox = 1, SolidColor = 2, Depth = 3, Nothing = 4 }

    public struct Ray
    {
        public Vector3 origin, direction;
        public Ray(Vector3 o, Vector3 d) { origin = o; direction = d; }
        public Vector3 GetPoint(float t) => origin + direction * t;
        public override string ToString() => origin + " -> " + direction;
    }

    public struct RaycastHit { public Vector3 point; public Vector3 normal; public float distance; public Collider collider; public Transform transform; public Rigidbody rigidbody; }
    public struct RaycastHit2D { public Vector2 point; public Vector2 normal; public float distance; public Collider2D collider; public Transform transform; public Rigidbody2D rigidbody; public float fraction; }

    public class Renderer : Component
    {
        public Material material { get; set; }
        public Material sharedMaterial { get; set; }
        public Material[] materials { get; set; } = new Material[0];
        public Material[] sharedMaterials { get; set; } = new Material[0];
        public Bounds bounds { get; set; }
        public bool enabled { get; set; } = true;
        public int sortingLayerID { get; set; }
        public string sortingLayerName { get; set; }
        public int sortingOrder { get; set; }
        public bool isVisible => true;
    }

    public sealed class SpriteRenderer : Renderer
    {
        public Sprite sprite { get; set; }
        public Color color { get; set; } = Color.white;
        public SpriteDrawMode drawMode { get; set; }
        public Vector2 size { get; set; } = Vector2.one;
        public SpriteMaskInteraction maskInteraction { get; set; }
        public SpriteSortPoint sortPoint { get; set; }
        public float adaptiveModeThreshold { get; set; }
    }

    public enum SpriteDrawMode { Simple, Sliced, Tiled }
    public enum SpriteMaskInteraction { None, VisibleInsideMask, VisibleOutsideMask }
    public enum SpriteSortPoint { Center, Pivot }

    public class Material : Object
    {
        public Material(Shader s) { }
        public Material(string s) { }
        public Color color { get; set; } = Color.white;
        public Texture mainTexture { get; set; }
        public Shader shader { get; set; }
        public int renderQueue { get; set; }
        public void SetColor(string p, Color c) { }
        public Color GetColor(string p) => Color.white;
        public void SetColor(int p, Color c) { }
        public Color GetColor(int p) => Color.white;
        public void SetFloat(string p, float v) { }
        public float GetFloat(string p) => 0f;
        public void SetInt(string p, int v) { }
        public int GetInt(string p) => 0;
        public void SetTexture(string p, Texture t) { }
        public Texture GetTexture(string p) => null;
        public bool HasProperty(string p) => false;
        public bool HasProperty(int p) => false;
        public void EnableKeyword(string k) { }
        public void DisableKeyword(string k) { }
        public void SetPass(int p) { }
        public Material Clone() => this;
    }

    public class Shader : Object
    {
        public static Shader Find(string n) => null;
        public string name { get; set; }
        public int propertyCount => 0;
    }

    public class Texture : Object
    {
        public int width { get; protected set; }
        public int height { get; protected set; }
        public FilterMode filterMode { get; set; }
        public TextureWrapMode wrapMode { get; set; }
        public string name { get; set; }
    }

    public enum FilterMode { Point, Bilinear, Trilinear }
    public enum TextureWrapMode { Repeat, Clamp, Mirror, MirrorOnce }

    public sealed class Texture2D : Texture
    {
        public Texture2D(int w, int h) { width = w; height = h; }
        public Texture2D(int w, int h, TextureFormat f, bool linear) { width = w; height = h; format = f; }
        public Texture2D(int w, int h, TextureFormat f, bool linear, bool mipChain) { width = w; height = h; format = f; }
        public TextureFormat format { get; set; }
        public bool alphaIsTransparency { get; set; }
        public bool readable { get; set; }
        public bool mipmapBias { get; set; }
        public bool mipmapCount { get; set; }
        public void SetPixels(Color[] c) { }
        public void SetPixels(Color[] c, int m) { }
        public void SetPixels(int x, int y, int w, int h, Color[] c) { }
        public void SetPixel(int x, int y, Color c) { }
        public Color[] GetPixels() => new Color[0];
        public Color[] GetPixels(int m) => new Color[0];
        public Color[] GetPixels(int x, int y, int w, int h) => new Color[0];
        public Color GetPixel(int x, int y) => Color.white;
        public Color GetPixelBilinear(float u, float v) => Color.white;
        public Color32[] GetPixels32() => new Color32[0];
        public Color32[] GetPixels32(int m) => new Color32[0];
        public bool SetPixels32(Color32[] c) => true;
        public bool SetPixels32(Color32[] c, int m) => true;
        public bool SetPixels32(int x, int y, int w, int h, Color32[] c) => true;
        public void Apply() { }
        public void Apply(bool um) { }
        public bool LoadImage(byte[] d) => true;
        public bool LoadImage(byte[] d, bool mc) => true;
        public byte[] EncodeToPNG() => new byte[0];
        public byte[] EncodeToJPG(int q = 75) => new byte[0];
        public byte[] GetRawTextureData() => new byte[0];
        public void Compress(bool hq) { }
        public void ClearPixels() { }
        public void ReadPixels(Rect r, int x, int y) { }
        public void ReadPixels(Rect r, int x, int y, bool um) { }
        public Vector2Int texelSize => new Vector2Int(width, height);
    }

    public enum TextureFormat { Alpha8, ARGB4444, RGB24, RGBA32, ARGB32, RGB565, R16, DXT1, DXT5, RGBAHalf, RGBAFloat }

    public sealed class Sprite : Object
    {
        public static Sprite Create(Texture2D t, Rect r, Vector2 p) => new Sprite();
        public static Sprite Create(Texture2D t, Rect r, Vector2 p, float ppu) => new Sprite();
        public static Sprite Create(Texture2D t, Rect r, Vector2 p, float ppu, uint ext, SpriteMeshType mt) => new Sprite();
        public static Sprite Create(Texture2D t, Rect r, Vector2 p, float ppu, uint ext, SpriteMeshType mt, Vector4 border) => new Sprite();
        public static Sprite Create(Texture2D t, Rect r, Vector2 p, float ppu, uint ext, SpriteMeshType mt, Vector4 border, bool bm) => new Sprite();
        public Texture2D texture => null;
        public Rect rect { get; set; }
        public Vector2 pivot { get; set; }
        public float pixelsPerUnit { get; set; } = 100f;
        public Vector4 border { get; set; }
        public Bounds bounds { get; set; }
        public bool packed => false;
        public string packingTag { get; set; }
        public Texture2D associatedAlphaSplitTexture => null;
        public Vector2[] vertices => new Vector2[0];
        public ushort[] triangles => new ushort[0];
        public Vector2[] uv => new Vector2[0];
        public override string ToString() => "Sprite";
    }

    public enum SpriteMeshType { FullRect, Tight }

    public class AnimationCurve
    {
        public AnimationCurve() { }
        public AnimationCurve(params Keyframe[] k) { }
        public int length => 0;
        public Keyframe this[int i] => default;
        public Keyframe[] keys { get; set; } = new Keyframe[0];
        public WrapMode postWrapMode { get; set; }
        public WrapMode preWrapMode { get; set; }
        public float Evaluate(float t) => 0f;
        public int AddKey(float t, float v) => 0;
        public int AddKey(Keyframe k) => 0;
        public void RemoveKey(int i) { }
        public void MoveKey(int i, Keyframe k) { }
        public void SmoothTangents(int i, float w) { }
        public static AnimationCurve Linear(float a, float b, float l1, float l2) => new AnimationCurve();
        public static AnimationCurve EaseInOut(float a, float b, float l1, float l2) => new AnimationCurve();
        public static AnimationCurve Constant(float a, float b, float l) => new AnimationCurve();
    }

    public struct Keyframe
    {
        public float time, value, inTangent, outTangent;
        public Keyframe(float t, float v) { time = t; value = v; inTangent = 0f; outTangent = 0f; }
        public Keyframe(float t, float v, float it, float ot) { time = t; value = v; inTangent = it; outTangent = ot; }
        public int tangentMode { get; set; }
    }

    public enum WrapMode { Once, Loop, PingPong, ClampForever, Default }

    public static class Resources
    {
        public static T Load<T>(string p) where T : Object => default;
        public static Object Load(string p) => null;
        public static Object Load(string p, Type t) => null;
        public static T[] LoadAll<T>(string p) where T : Object => new T[0];
        public static Object[] LoadAll(string p) => new Object[0];
        public static ResourceRequest LoadAsync<T>(string p) where T : Object => new ResourceRequest();
        public static ResourceRequest LoadAsync(string p) => new ResourceRequest();
        public static ResourceRequest LoadAsync(string p, Type t) => new ResourceRequest();
        public static T GetBuiltinResource<T>(string p) where T : Object => default;
        public static Object GetBuiltinResource(string p, Type t) => null;
        public static void UnloadAsset(Object a) { }
        public static AsyncOperation UnloadUnusedAssets() => new AsyncOperation();
    }

    public class ResourceRequest { public Object asset; public bool isDone => true; }
    public class AsyncOperation { public bool isDone => true; public float progress => 1f; public int priority { get; set; } }

    public sealed class TextAsset : Object
    {
        public string text { get; set; }
        public byte[] bytes { get; set; } = new byte[0];
    }

    public static class PlayerPrefs
    {
        private static readonly Dictionary<string, string> store = new Dictionary<string, string>();
        public static bool HasKey(string key) => store.ContainsKey(key);
        public static string GetString(string key, string dv = "") => store.TryGetValue(key, out var v) ? v : dv;
        public static string GetString(string key) => store.TryGetValue(key, out var v) ? v : "";
        public static void SetString(string key, string v) { store[key] = v; }
        public static int GetInt(string key, int dv = 0) => int.TryParse(GetString(key), out var v) ? v : dv;
        public static int GetInt(string key) => GetInt(key, 0);
        public static void SetInt(string key, int v) { store[key] = v.ToString(); }
        public static float GetFloat(string key, float dv = 0f) => float.TryParse(GetString(key), out var v) ? v : dv;
        public static float GetFloat(string key) => GetFloat(key, 0f);
        public static void SetFloat(string key, float v) { store[key] = v.ToString(); }
        public static bool GetBool(string key, bool dv = false) => int.TryParse(GetString(key), out var v) ? v != 0 : dv;
        public static void SetBool(string key, bool v) { store[key] = v ? "1" : "0"; }
        public static void DeleteKey(string key) { store.Remove(key); }
        public static void DeleteAll() { store.Clear(); }
        public static void Save() { }
    }

    public static class JsonUtility
    {
        private static readonly JsonSerializerOptions FieldOpts = new JsonSerializerOptions
        {
            IncludeFields = true,
            IgnoreReadOnlyProperties = true,
        };
        public static string ToJson(object obj) => JsonSerializer.Serialize(obj, obj.GetType(), FieldOpts);
        public static string ToJson(object obj, bool p) => ToJson(obj);
        public static T FromJson<T>(string json) => JsonSerializer.Deserialize<T>(json, FieldOpts);
        public static object FromJson(string json, Type t) => JsonSerializer.Deserialize(json, t, FieldOpts);
        // Unity 语义：覆盖到既有实例。用反射逐字段拷贝模拟（桩只求编译与可运行）。
        public static void FromJsonOverwrite(string json, object obj)
        {
            if (obj == null) return;
            var fresh = JsonSerializer.Deserialize(json, obj.GetType(), FieldOpts);
            if (fresh == null) return;
            foreach (var f in obj.GetType().GetFields(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance))
                if (!f.IsLiteral) f.SetValue(obj, f.GetValue(fresh));
        }
    }

    public class AudioListener : Behaviour { public float volume { get; set; } = 1f; public AudioVelocityUpdateMode velocityUpdateMode { get; set; } }
    public enum AudioVelocityUpdateMode { Auto, Fixed, Dynamic }

    public class AudioSource : Behaviour
    {
        public AudioClip clip { get; set; }
        public float volume { get; set; } = 1f;
        public float pitch { get; set; } = 1f;
        public float panStereo { get; set; }
        public bool loop { get; set; }
        public bool mute { get; set; }
        public bool playOnAwake { get; set; } = true;
        public bool isPlaying => false;
        public float time { get; set; }
        public int priority { get; set; } = 128;
        public float spatialBlend { get; set; }
        public AudioRolloffMode rolloffMode { get; set; }
        public float minDistance { get; set; } = 1f;
        public float maxDistance { get; set; } = 500f;
        public void Play() { }
        public void Play(ulong d) { }
        public void PlayDelayed(float d) { }
        public void PlayOneShot(AudioClip c) { }
        public void PlayOneShot(AudioClip c, float v) { }
        public void Stop() { }
        public void Pause() { }
        public void UnPause() { }
    }

    public enum AudioRolloffMode { Logarithmic, Linear, Custom }

    public class AudioClip : Object
    {
        public float length => 0f;
        public int samples => 0;
        public int channels => 1;
        public int frequency => 44100;
        public bool preloadAudioData { get; set; }
        public bool ambisonic { get; set; }
    }

    public static class Input
    {
        public static Vector3 mousePosition { get; set; }
        public static Vector2 mouseScrollDelta { get; set; }
        public static bool anyKey { get; set; }
        public static bool anyKeyDown { get; set; }
        public static bool GetMouseButton(int b) => false;
        public static bool GetMouseButtonDown(int b) => false;
        public static bool GetMouseButtonUp(int b) => false;
        public static bool GetKey(string k) => false;
        public static bool GetKey(KeyCode k) => false;
        public static bool GetKeyDown(KeyCode k) => false;
        public static bool GetKeyUp(KeyCode k) => false;
        public static float GetAxis(string a) => 0f;
        public static float GetAxisRaw(string a) => 0f;
        public static bool GetButton(string b) => false;
        public static bool GetButtonDown(string b) => false;
        public static bool GetButtonUp(string b) => false;
        public static int touchCount => 0;
        public static Touch GetTouch(int i) => default;
        public static Touch[] touches => new Touch[0];
        public static Vector3 acceleration => Vector3.zero;
        public static IMECompositionMode imeCompositionMode { get; set; }
        public static string compositionString => "";
        public static bool touchSupported => false;
        public static bool multiTouchEnabled { get; set; }
        public static bool simulateMouseWithTouches { get; set; }
        public static bool mousePresent => true;
    }

    public enum IMECompositionMode { Auto, On, Off }

    public enum KeyCode
    {
        None = 0, Backspace = 8, Tab = 9, Clear = 12, Return = 13, Pause = 19, Escape = 27, Space = 32,
        Keypad0 = 256, Keypad1, Keypad2, Keypad3, Keypad4, Keypad5, Keypad6, Keypad7, Keypad8, Keypad9,
        A = 97, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z,
        LeftArrow = 276, RightArrow, UpArrow, DownArrow,
        Mouse0 = 323
    }

    public struct Touch
    {
        public int fingerId;
        public Vector2 position;
        public Vector2 rawPosition;
        public Vector2 deltaPosition;
        public float deltaTime;
        public int tapCount;
        public TouchPhase phase;
        public float pressure;
        public float maximumPossiblePressure;
        public float altitudeAngle;
        public float azimuthAngle;
        public float radius;
        public float radiusVariance;
    }

    public enum TouchPhase { Began, Moved, Stationary, Ended, Canceled }

    public struct LayerMask
    {
        public int value;
        public static implicit operator int(LayerMask m) => m.value;
        public static implicit operator LayerMask(int v) => new LayerMask { value = v };
        public static int NameToLayer(string n) => 0;
        public static string LayerToName(int i) => "";
        public static int GetMask(params string[] n) => 0;
    }

    public static class Physics
    {
        public static Vector3 gravity { get; set; } = new Vector3(0f, -9.81f, 0f);
        public static bool Raycast(Ray r) => false;
        public static bool Raycast(Ray r, out RaycastHit h) { h = default; return false; }
        public static bool Raycast(Ray r, out RaycastHit h, float d) { h = default; return false; }
        public static bool Raycast(Ray r, out RaycastHit h, float d, int m) { h = default; return false; }
        public static bool Raycast(Vector3 o, Vector3 dir, out RaycastHit h, float d, int m) { h = default; return false; }
        public static bool Raycast(Vector3 o, Vector3 dir, out RaycastHit h) { h = default; return false; }
        public static bool Raycast(Vector3 o, Vector3 dir, out RaycastHit h, float d) { h = default; return false; }
        public static RaycastHit[] RaycastAll(Ray r, float d, int m) => new RaycastHit[0];
        public static RaycastHit[] RaycastAll(Ray r) => new RaycastHit[0];
        public static bool Linecast(Vector3 a, Vector3 b, out RaycastHit h) { h = default; return false; }
        public static bool SphereCast(Ray r, float rad, out RaycastHit h, float d, int m) { h = default; return false; }
        public static bool BoxCast(Vector3 c, Vector3 hs, Vector3 dir, out RaycastHit h, Quaternion o, float d, int m) { h = default; return false; }
        public static int defaultSolverIterations { get; set; }
    }

    public static class Physics2D
    {
        public static int defaultContactCount { get; set; }
        public static bool queriesHitTriggers { get; set; } = true;
        public static Vector2 gravity { get; set; } = new Vector2(0f, -9.81f);
        public static bool Raycast(Ray r) => false;
        public static bool Raycast(Ray r, float d) => false;
        public static bool Raycast(Ray r, float d, int m) => false;
        public static bool Raycast(Vector2 o, Vector2 d) => false;
        public static bool Raycast(Vector2 o, Vector2 d, float dist) => false;
        public static bool Raycast(Vector2 o, Vector2 d, float dist, int m) => false;
        public static bool Raycast(Vector2 o, Vector2 d, out RaycastHit2D h, float dist, int m) { h = default; return false; }
        public static bool Raycast(Vector2 o, Vector2 d, out RaycastHit2D h) { h = default; return false; }
        public static bool Raycast(Vector2 o, Vector2 d, out RaycastHit2D h, float dist) { h = default; return false; }
        public static RaycastHit2D[] RaycastAll(Vector2 o, Vector2 d, float dist, int m) => new RaycastHit2D[0];
        public static RaycastHit2D[] RaycastAll(Vector2 o, Vector2 d) => new RaycastHit2D[0];
        public static RaycastHit2D[] RaycastAll(Vector2 o, Vector2 d, float dist) => new RaycastHit2D[0];
        public static Collider2D OverlapPoint(Vector2 p, int m) => null;
        public static Collider2D OverlapPoint(Vector2 p) => null;
        public static int GetRayIntersection(Ray r, RaycastHit2D[] h) => 0;
        public static bool BoxCast(Vector2 o, Vector2 s, float a, Vector2 d, float dist, int m) => false;
        public static bool CircleCast(Vector2 o, float r, Vector2 d, float dist, int m) => false;
    }

    public class Collider : Component { public bool enabled { get; set; } = true; public bool isTrigger { get; set; } public Rigidbody attachedRigidbody => null; public Bounds bounds { get; set; } }
    public class Collider2D : Behaviour { public bool isTrigger { get; set; } public Rigidbody2D attachedRigidbody => null; public Bounds bounds { get; set; } }
    public class Rigidbody : Component { public Vector3 velocity { get; set; } public float mass { get; set; } public bool useGravity { get; set; } public bool isKinematic { get; set; } }
    public class Rigidbody2D : Component { public Vector2 velocity { get; set; } public float mass { get; set; } public bool simulated { get; set; } }

    public class ScriptableObject : Object
    {
        public static T CreateInstance<T>() where T : ScriptableObject => (T)Activator.CreateInstance(typeof(T));
        public static ScriptableObject CreateInstance(Type t) => (ScriptableObject)Activator.CreateInstance(t);
        public static void CreateAsset(Object a, string p) { }
    }

    [AttributeUsage(AttributeTargets.Class)]
    public sealed class CreateAssetMenuAttribute : Attribute
    {
        public string menuName;
        public string fileName;
        public int order;
    }

    public struct Pose
    {
        public Vector3 position;
        public Quaternion rotation;
        public Pose(Vector3 p, Quaternion r) { position = p; rotation = r; }
        public static Pose identity => new Pose(Vector3.zero, Quaternion.identity);
    }

    public static class Gizmos
    {
        public static Color color { get; set; }
        public static Matrix4x4 matrix { get; set; }
        public static void DrawLine(Vector3 a, Vector3 b) { }
        public static void DrawWireSphere(Vector3 c, float r) { }
        public static void DrawSphere(Vector3 c, float r) { }
        public static void DrawCube(Vector3 c, Vector3 s) { }
        public static void DrawRay(Ray r) { }
        public static void DrawFrustum(Vector3 c, float fov, float mn, float mx, float a) { }
    }

    public struct Plane
    {
        public Vector3 normal;
        public float distance;
        public Plane(Vector3 n, Vector3 p) { normal = n; distance = -Vector3.Dot(n, p); }
        public bool Raycast(Ray r, out float d) { d = 0f; return false; }
    }

    public class ObjectPool<T> where T : class
    {
        public T Get() => default;
        public void Release(T e) { }
        public int CountAll => 0;
        public int CountActive => 0;
        public int CountInactive => 0;
    }

    public class Mesh : Object
    {
        public Vector3[] vertices { get; set; } = new Vector3[0];
        public Vector2[] uv { get; set; } = new Vector2[0];
        public Vector3[] normals { get; set; } = new Vector3[0];
        public Color32[] colors32 { get; set; } = new Color32[0];
        public int[] triangles { get; set; } = new int[0];
        public int subMeshCount { get; set; }
        public Bounds bounds { get; set; }
        public void Clear() { }
        public void RecalculateBounds() { }
        public void RecalculateNormals() { }
        public void MarkDynamic() { }
        public void UploadMeshData(bool m) { }
    }

    public class Font : Object
    {
        public static Font CreateDynamic(string n) => null;
        public static Font CreateDynamicFontFromOSFont(string n, int s) => null;
        public static Font CreateDynamicFontFromOSFont(string[] n, int s) => null;
        public string[] fontNames { get; set; } = new string[0];
        public int fontSize { get; set; }
        public CharacterInfo[] characterInfo => new CharacterInfo[0];
        public Material material { get; set; }
        public bool dynamic => false;
        public int ascent => 0;
        public int lineHeight => 0;
        public string[] GetOSInstalledFontNames() => new string[0];
        public static string[] GetOSInstalledFontNamesStatic() => new string[0];
        public bool GetCharacterInfo(char c, out CharacterInfo i, int s = 0) { i = default; return false; }
        public void RequestCharactersInTexture(string t, int s = 0) { }
        public bool HasCharacter(char c) => false;
    }

    public struct CharacterInfo
    {
        public int index; public Vector2 uv; public Vector2 vert; public float width; public GlyphMetrics metrics;
        public bool flipped;
        public Vector2 bottomLeft, bottomRight, topRight, topLeft;
        public float advance, bearing, minY, maxY;
    }

    public struct GlyphMetrics { public float width, height, horizontalBearingX, horizontalBearingY, horizontalAdvance; }

    public static class ColorUtility
    {
        public static bool TryParseHtmlString(string html, out Color c)
        {
            c = Color.white;
            if (string.IsNullOrEmpty(html)) return false;
            var s = html.StartsWith("#") ? html.Substring(1) : html;
            if (s.Length == 6 || s.Length == 8)
            {
                try
                {
                    var r = System.Convert.ToInt32(s.Substring(0, 2), 16) / 255f;
                    var g = System.Convert.ToInt32(s.Substring(2, 2), 16) / 255f;
                    var b = System.Convert.ToInt32(s.Substring(4, 2), 16) / 255f;
                    var a = s.Length == 8 ? System.Convert.ToInt32(s.Substring(6, 2), 16) / 255f : 1f;
                    c = new Color(r, g, b, a);
                    return true;
                }
                catch { return false; }
            }
            return false;
        }
    }

    public static class RectTransformUtility
    {
        public static bool ScreenPointToWorldPointInRectangle(RectTransform rect, Vector2 screenPoint, Camera cam, out Vector3 worldPoint) { worldPoint = Vector3.zero; return false; }
        public static bool ScreenPointToLocalPointInRectangle(RectTransform rect, Vector2 screenPoint, Camera cam, out Vector2 localPoint) { localPoint = Vector2.zero; return false; }
        public static bool WorldPointToLocalPointInRectangle(RectTransform rect, Vector3 worldPoint, Camera cam, out Vector2 localPoint) { localPoint = Vector2.zero; return false; }
        public static bool RectangleContainsScreenPoint(RectTransform rect, Vector2 screenPoint, Camera cam) => false;
        public static bool RectangleContainsScreenPoint(RectTransform rect, PointerEventData eventData) => false;
        public static Ray IntersectRaySegments(Ray a, Ray b) => new Ray();
        public static Vector2 TransformPointFromWorldToRelativeSpace(Transform t, Vector3 p) => Vector2.zero;
        public static Vector2 TransformVectorFromWorldToRelativeSpace(Transform t, Vector3 v) => Vector2.zero;
        public static Bounds CalculateRelativeRectTransformBounds(Transform root, RectTransform child) => new Bounds();
        public static Vector2 PixelAdjustPoint(Vector2 point, Transform t, UnityEngine.UI.Canvas c) => point;
        public static Rect PixelAdjustRect(RectTransform rectTransform, UnityEngine.UI.Canvas canvas) => new Rect();
    }

    public static class UnityExtensions
    {
        public static T GetComponentOrAdd<T>(this GameObject g) where T : Component => default;
    }
}

namespace UnityEngine.SceneManagement
{
    public struct Scene
    {
        public string name { get; }
        public string path { get; }
        public int buildIndex { get; }
        public bool isLoaded => true;
        public bool IsValid() => true;
        public GameObject[] GetRootGameObjects() => new GameObject[0];
    }

    public static class SceneManager
    {
        public static Scene GetActiveScene() => default;
        public static void SetActiveScene(Scene s) { }
        public static void LoadScene(int i) { }
        public static void LoadScene(string n) { }
        public static AsyncOperation LoadSceneAsync(string n) => new AsyncOperation();
        public static int sceneCount => 1;
        public static int sceneCountInBuildSettings => 1;
    }
}
