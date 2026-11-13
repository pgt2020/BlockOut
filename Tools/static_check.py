#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BlockOut 静态检查（Tools/static_check.py）

覆盖（不运行 Unity）：
  1. 括号/方括号配平（剥离注释与字符串后）
  2. 裸方法调用必须可解析（本类成员 / 本文件局部 / 工程内方法 / Unity 消息方法 / 已知外部类型）
  3. 私有方法声明未使用
  4. 事件 += / -= 配对
  5. asmdef 引用闭环（引用必须存在；无循环）
  6. 资产 GUID 引用完整性（prefab/unity/asset 中的 guid 必须能在 .meta 中找到）
  7. 目录 manifest（需求 §3 目标目录）
  8. 关键契约抽查（章节图 sprite meta / 启动场景唯一 / 无运行时自动启动 / 旧启动器已删）

历史价值：本检查的"裸调用可解析"一项曾抓到真实编译阻塞
（OnApplicationPause 调用了不存在的 PauseByAppBackground）。

用法：python Tools/static_check.py
"""
import os
import re
import sys
import json
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "Assets", "BlockOut")

KW = {"if", "for", "foreach", "while", "switch", "using", "lock", "catch", "fixed",
      "return", "typeof", "sizeof", "nameof", "new", "base", "this", "value", "await",
      "when", "case", "default", "in", "is", "as", "else", "try", "do", "throw", "yield"}

# Unity 消息方法（由引擎调用，不是未定义符号）
UNITY_MAGIC = {
    "Awake", "Start", "Update", "FixedUpdate", "LateUpdate", "OnEnable", "OnDisable",
    "OnDestroy", "OnApplicationPause", "OnApplicationFocus", "OnApplicationQuit",
    "OnValidate", "Reset", "OnGUI", "OnDrawGizmos", "OnDrawGizmosSelected",
    "OnTriggerEnter", "OnCollisionEnter", "OnAnimatorMove", "OnTransformChildrenChanged",
    "OnTransformParentChanged", "OnBeforeTransformParentChanged", "OnRectTransformDimensionsChange",
    "OnPointerDown", "OnPointerUp", "OnPointerClick", "OnBeginDrag", "OnDrag", "OnEndDrag",
    "OnScroll", "OnMove", "OnSubmit", "OnCancel", "OnSelect", "OnDeselect",
    "OnPreprocessBuild", "OnPostBuild", "callbackOrder",
}
BASE = {"ToString", "GetHashCode", "GetType", "Equals", "ReferenceEquals", "Dispose",
        "Invoke", "ConfigureAwait", "GetAwaiter", "GetValue", "SetValue", "ContainsKey",
        "TryGetValue", "Add", "Remove", "Clear", "CopyTo", "MoveNext", "get_Current",
        "GetComponent", "GetComponentInChildren", "GetComponentInParent", "GetComponents",
        "GetComponentsInChildren", "GetComponentsInParent", "FindObjectOfType",
        "FindObjectsOfType", "Instantiate", "Destroy", "DestroyImmediate", "DontDestroyOnLoad",
        "SetParent", "GetChild", "SetSiblingIndex", "Play", "Stop", "PlayOneShot", "UnPause",
        "ApplyModifiedProperties", "ApplyModifiedPropertiesWithoutUndo", "FindProperty",
        "GetArrayElementAtIndex", "arraySize", "SetChecked", "GetChecked", "Log", "LogWarning",
        "LogError", "Assert", "AreEqual", "AreNotEqual", "IsTrue", "IsFalse", "IsNull",
        "IsNotNull", "Greater", "Less", "Fail", "Ignore", "Pass", "That", "Throws", "DoesNotThrow",
        "Contains", "AreEquivalent", "IsEmpty", "IsNotEmpty", "Yield", "CreateAssetMenu",
        # Unity 特性 / 编辑器 API
        "MenuItem", "Header", "Tooltip", "RequireComponent", "SerializeField", "HideInInspector",
        "Space", "Range", "Multiline", "TextArea", "ContextMenu", "AddComponentMenu",
        "DisallowMultipleComponent", "ExecuteInEditMode", "CreateAssetMenu",
        "BuildFailedException", "StartCoroutine", "StopCoroutine", "StopAllCoroutines",
        "InvokeRepeating", "CancelInvoke", "DebugBreak", "ClearConsole",
        # System / 常用外部类型
        "ArgumentNullException", "ArgumentException", "InvalidOperationException",
        "NotSupportedException", "NotImplementedException", "FormatException",
        "Color32", "Color", "Vector2", "Vector3", "Vector4", "Quaternion", "Rect", "Bounds",
        "Mathf", "Random", "Time", "Input", "Screen", "Application", "SystemInfo",
        "PlayerPrefs", "Resources", "AssetDatabase", "EditorUtility", "PrefabUtility",
        "EditorBuildSettings", "PlayerSettings", "EditorUserBuildSettings", "Selection",
        "Handheld", "SleepTimeout", "CameraClearFlags", "RenderMode", "TextAnchor",
        "InteractionMode", "SerializedObject", "SerializedProperty", "BuildTarget",
        "BuildOptions", "BuildReport", "EditorApplication", "Undo", "GUI", "GUILayout",
        "EditorGUILayout", "GUIStyle", "GUIContent", "Event", "Physics", "Physics2D",
        "LayerMask", "Physics2D", "Cursor", "QualitySettings"}

# 已知外部命名空间（其静态方法/构造不做本地解析要求）
EXTERNAL_NS = {
    "UnityEngine", "UnityEditor", "System", "NUnit.Framework", "UnityEngine.TestTools",
    "UnityEditor.Build", "UnityEditor.Build.Reporting", "System.Globalization",
    "System.Text", "System.Linq", "System.Collections", "System.Collections.Generic",
    "System.IO", "BlockOut",
}

problems = []


def strip(src):
    out = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c == "/" and i + 1 < n and src[i + 1] == "/":
            while i < n and src[i] != "\n":
                i += 1
        elif c == "/" and i + 1 < n and src[i + 1] == "*":
            i += 2
            while i + 1 < n and not (src[i] == "*" and src[i + 1] == "/"):
                i += 1
            i += 2
        elif c == '"':
            i += 1
            while i < n and src[i] != '"':
                if src[i] == "\\":
                    i += 1
                i += 1
            i += 1
        elif c == "'":
            i += 1
            while i < n and src[i] != "'":
                if src[i] == "\\":
                    i += 1
                i += 1
            i += 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


MOD = r"(?:public|private|protected|internal|static|readonly|const|sealed|virtual|override|new|volatile|partial|event|async|extern|unsafe|abstract)"
TYPE = r"[\w<>\[\],\.\?]*"

# 成员声明（修饰符可选：兼容接口成员与本地函数）
DECL_RE = re.compile(
    r"(?:" + MOD + r"(?:[ \t]+" + MOD + r")*[ \t]+)?" + TYPE +
    r"[ \t]+(?P<name>[A-Za-z_]\w*)[ \t]*\((?P<args>(?:[^()]|\([^()]*\))*)\)\s*(?P<tail>\{|=>|;)", re.M)

CALL_RE = re.compile(r"(?<![\w\.])(?P<name>[A-Za-z_]\w*)\s*\(")
GENERIC = r"[\w\.]+(?:\s*<[^<>]*(?:<[^<>]*>[^<>]*)*>)?(?:\s*\[\s*\])?"
PARAM_RE = re.compile(
    r"[(,]\s*(?:(?:ref|out|params|this)\s+)*(?P<type>(?:System\.)?(?:Action|Func)<[^()]*(?:\([^()]*\)[^()]*)*>|" + GENERIC + r")"
    r"\s+(?P<name>[A-Za-z_]\w*)\s*[,)=]")

EV_RE = re.compile(r"([\w\.]+)\.(On[A-Z]\w*)\s*(\+=|-=)")


def collect_symbols(src):
    syms = set()
    for m in DECL_RE.finditer(src):
        syms.add(m.group("name"))
    for m in PARAM_RE.finditer(src):
        syms.add(m.group("name"))
    for kw in ("foreach", "catch", "using"):
        for m in re.finditer(r"\b" + kw + r"\s*\(\s*(?:[^()]*?\s+)?" + r"([A-Za-z_]\w*)\s*(?:\)|in)", src):
            syms.add(m.group(1))
    # 类型名也算可见符号（构造函数 / 静态方法）
    for m in re.finditer(r"\b(?:class|struct|enum|interface|record)\s+([A-Za-z_]\w*)", src):
        syms.add(m.group(1))
    return syms


def check_file(path, project_methods):
    rel = os.path.relpath(path, ROOT)
    raw = open(path, encoding="utf-8").read()
    src = strip(raw)

    for a, b, label in (("{", "}", "brace"), ("(", ")", "paren"), ("[", "]", "bracket")):
        if src.count(a) != src.count(b):
            problems.append("%s: %s 不配平 %d/%d" % (rel, label, src.count(a), src.count(b)))

    syms = collect_symbols(src)
    usings = set(re.findall(r"using\s+([\w\.]+);", src))
    has_external_using = bool(usings & EXTERNAL_NS)

    undefined = {}
    for m in CALL_RE.finditer(src):
        name = m.group("name")
        if name in KW or name in BASE or name in UNITY_MAGIC or name in syms:
            continue
        if name in project_methods:
            continue
        undefined[name] = undefined.get(name, 0) + 1
    for name, cnt in sorted(undefined.items()):
        problems.append("%s: 未定义调用 %s() x%d" % (rel, name, cnt))

    # 私有方法未使用（把方法组订阅也算引用）
    for m in DECL_RE.finditer(src):
        name = m.group("name")
        seg = src[m.start():m.end()]
        if not re.match(r"\s*private\s", seg):
            continue
        if name in UNITY_MAGIC:
            continue
        if m.group("tail") != "{":
            continue
        refs = len(re.findall(r"(?<![\w\.])" + re.escape(name) + r"\b", src))
        if refs <= 1:
            problems.append("%s: 私有方法声明未使用 %s()" % (rel, name))

    # 事件配对
    subs, unsubs = {}, {}
    for m in EV_RE.finditer(src):
        key = (m.group(1), m.group(2))
        table = subs if m.group(3) == "+=" else unsubs
        table[key] = table.get(key, 0) + 1
    for key in sorted(subs):
        a, r = subs[key], unsubs.get(key, 0)
        if a != r and not re.search(r"\.%s\s*\+=\s*[\(:]" % re.escape(key[1]), src):
            problems.append("%s: 事件未配对 %s.%s +=%d -=%d" % (rel, key[0], key[1], a, r))


def check_asmdefs():
    asmdefs = {}
    for p in glob.glob(os.path.join(SRC, "**", "*.asmdef"), recursive=True):
        d = json.load(open(p, encoding="utf-8"))
        asmdefs[d["name"]] = (os.path.relpath(p, ROOT), d.get("references", []))
    names = set(asmdefs)
    for name, (path, refs) in sorted(asmdefs.items()):
        for r in refs:
            if r.startswith("Unity") or r == "nunit.framework.dll":
                continue
            if r not in names:
                problems.append("%s: 引用不存在的程序集 %s" % (path, r))
    graph = {n: [r for r in refs if r in names] for n, (_, refs) in asmdefs.items()}
    for start in graph:
        seen, stack = set(), [start]
        while stack:
            cur = stack.pop()
            for nxt in graph.get(cur, []):
                if nxt == start:
                    problems.append("程序集循环依赖：%s → ... → %s" % (start, cur))
                elif nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
    return asmdefs


def check_asset_guids():
    known = set()
    for f in glob.glob(os.path.join(ROOT, "Assets", "**", "*.meta"), recursive=True) + \
             glob.glob(os.path.join(ROOT, "Packages", "**", "*.meta"), recursive=True):
        m = re.search(r"guid: ([0-9a-f]{32})", open(f, encoding="utf-8", errors="ignore").read())
        if m:
            known.add(m.group(1))
    builtin = {"0000000000000000e000000000000000", "0000000000000000f000000000000000"}
    targets = [os.path.join(SRC, "Scenes", "Launcher.unity")] + \
              glob.glob(os.path.join(SRC, "Resources", "Prefabs", "**", "*.prefab"), recursive=True) + \
              glob.glob(os.path.join(SRC, "Settings", "*.asset"))
    for path in targets:
        if not os.path.exists(path):
            problems.append("缺少资产：" + os.path.relpath(path, ROOT))
            continue
        text = open(path, encoding="utf-8").read()
        for g in set(re.findall(r"guid: ([0-9a-f]{32})", text)):
            if g not in known and g not in builtin:
                problems.append("%s: 引用未知 GUID %s" % (os.path.relpath(path, ROOT), g))


def check_manifest():
    required = [
        "Assets/BlockOut/Runtime/Bootstrap", "Assets/BlockOut/Runtime/Contracts",
        "Assets/BlockOut/Runtime/Core", "Assets/BlockOut/Runtime/Gameplay",
        "Assets/BlockOut/Runtime/UI", "Assets/BlockOut/Runtime/Rendering",
        "Assets/BlockOut/Runtime/Infrastructure/Persistence",
        "Assets/BlockOut/Runtime/Infrastructure/Configuration",
        "Assets/BlockOut/Runtime/Infrastructure/Resources",
        "Assets/BlockOut/Runtime/Infrastructure/Audio",
        "Assets/BlockOut/Runtime/Infrastructure/Analytics",
        "Assets/BlockOut/Runtime/Infrastructure/Ads",
        "Assets/BlockOut/Editor", "Assets/BlockOut/Tests/EditMode", "Assets/BlockOut/Tests/PlayMode",
        "Assets/BlockOut/Scenes", "Assets/BlockOut/Settings",
    ]
    for d in required:
        if not os.path.isdir(os.path.join(ROOT, d)):
            problems.append("目录 manifest 缺失：" + d)


def check_contracts():
    ebs = open(os.path.join(ROOT, "ProjectSettings/EditorBuildSettings.asset"), encoding="utf-8").read()
    if "Launcher.unity" not in ebs:
        problems.append("EditorBuildSettings 未指向 Launcher.unity")
    if ebs.count("- enabled: 1") != 1:
        problems.append("EditorBuildSettings 启用场景数 != 1")
    for p in glob.glob(os.path.join(SRC, "**", "*.cs"), recursive=True):
        if p.endswith("BlockOutProjectChecks.cs"):
            continue   # 检查器自身含匹配字面量，跳过
        if "[RuntimeInitializeOnLoadMethod" in open(p, encoding="utf-8").read():
            problems.append("残留运行时自动启动：%s" % os.path.relpath(p, ROOT))
    for legacy in ("BlockOutBootstrapper.cs", "BlockOutGameBootstrap.cs"):
        if os.path.exists(os.path.join(SRC, "Runtime/Bootstrap", legacy)):
            problems.append("旧启动器未删除：" + legacy)


def main():
    files = sorted(glob.glob(os.path.join(SRC, "**", "*.cs"), recursive=True))
    # 工程内方法名索引（跨文件静态调用放行）
    project_methods = set()
    for f in files:
        src = strip(open(f, encoding="utf-8").read())
        for m in DECL_RE.finditer(src):
            project_methods.add(m.group("name"))
    for f in files:
        check_file(f, project_methods)
    asmdefs = check_asmdefs()
    check_asset_guids()
    check_manifest()
    check_contracts()

    print("检查脚本数：%d" % len(files))
    print("程序集数：%d（%s）" % (len(asmdefs), ", ".join(sorted(asmdefs))))
    if problems:
        print("\n发现 %d 个问题：" % len(problems))
        for p in problems:
            print("  - " + p)
        sys.exit(1)
    print("\n全部静态检查通过。")


if __name__ == "__main__":
    main()
