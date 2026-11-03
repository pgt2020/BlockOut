#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BlockOut 工程化重构 · 资产生成器（Tools/gen_blockout_assets.py）

生成内容（真实 Unity 资产文件，非占位）：
  1. Assets/BlockOut/Scenes/Launcher.unity          唯一启动场景
  2. Assets/BlockOut/Resources/Prefabs/**           页面 / AppRoot / 棋盘容器 Prefab
  3. Assets/BlockOut/Settings/*.asset               启动配置与 LevelPlay 广告配置资产

设计约定：
  - 所有 .meta 已预先存在并带固定 GUID；本脚本只写资产本体，不生成/修改 GUID；
  - Prefab 根挂 BlockOutPageView（命名锚点自描述），静态层级 + 动态内容分离：
    页面内容仍由既有工厂填充（需求允许"保留必要的动态棋盘和区域生成"）；
  - 重复执行是幂等的（同样输入 → 同样输出）。

用法：python Tools/gen_blockout_assets.py
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---- GUID（与 .meta 一一对应，改动前先同步 .meta）----
G_LAUNCHER = "f7215426537f40c8baf0d117c3fd344e"      # BlockOutLauncher.cs
G_APPROOT = "8937d44eec4445a882a5b59ed6e519a5"      # BlockOutAppRoot.cs
G_PAGEVIEW = "e7d74714e2044a26bbdbbc2401c2ba01"     # BlockOutPageView (BlockOutUIPrefabRegistry.cs)
G_STARTUP_CFG = "461e749e46ee42fe984a0e955168b8fd"  # BlockOutStartupConfig.cs
G_AD_CFG = "e9cc124e53e841f2bbc96748039f7e1d"       # BlockOutAdConfig.cs

G_PREFAB_APPROOT = "7f4a029d26f643c2898c7d62703effe4"
G_SCENE_LAUNCHER = "a289df1e153c4b67a295ab66a07c2d4e"
G_ASSET_CFG_DEV = "fe09e2c617144e6391e14b5718b1b037"
G_ASSET_CFG_REL = "5b68de31e3974a76a5953fa9abf2fe4f"
G_ASSET_AD_CFG = "e81645cb4428443cbc7f519dfc4e28a6"

# 屏幕枚举值（BlockOutScreenId）
SCREEN = {"Splash": 0, "Loading": 1, "Home": 2, "Board": 5, "Settlement": 7,
          "Collection": 8, "Store": 10, "Settings": 15}

YAML_HEAD = "%YAML 1.1\n%TAG !u! tag:unity3d.com,2011:\n"


def fid(n):
    """稳定 fileID：避免手写重复/冲突。"""
    return 1000000000000000 + n * 1000


# ---------------------------------------------------------------- 基础块

def gameobject(n, name, components, active=1):
    comps = "".join("  - component: {fileID: %d}\n" % c for c in components)
    return ("--- !u!1 &%d\n"
            "GameObject:\n"
            "  m_ObjectHideFlags: 0\n"
            "  m_CorrespondingSourceObject: {fileID: 0}\n"
            "  m_PrefabInstance: {fileID: 0}\n"
            "  m_PrefabAsset: {fileID: 0}\n"
            "  serializedVersion: 6\n"
            "  m_Component:\n"
            "%s"
            "  m_Layer: 5\n"
            "  m_Name: %s\n"
            "  m_TagString: Untagged\n"
            "  m_Icon: {fileID: 0}\n"
            "  m_NavMeshLayer: 0\n"
            "  m_StaticEditorFlags: 0\n"
            "  m_IsActive: %d\n") % (fid(n), comps, name, active)


def transform(n, go, children=(), parent=0, root_order=0,
              amin=(0, 0), amax=(1, 1), pos=(0, 0), size=(0, 0), pivot=(0.5, 0.5)):
    kids = "".join("  - {fileID: %d}\n" % c for c in children)
    if not kids:
        kids = "  []\n"
    return ("--- !u!224 &%d\n"
            "RectTransform:\n"
            "  m_ObjectHideFlags: 0\n"
            "  m_CorrespondingSourceObject: {fileID: 0}\n"
            "  m_PrefabInstance: {fileID: 0}\n"
            "  m_PrefabAsset: {fileID: 0}\n"
            "  m_GameObject: {fileID: %d}\n"
            "  m_LocalRotation: {x: 0, y: 0, z: 0, w: 1}\n"
            "  m_LocalPosition: {x: 0, y: 0, z: 0}\n"
            "  m_LocalScale: {x: 1, y: 1, z: 1}\n"
            "  m_Children:\n"
            "%s"
            "  m_Father: {fileID: %d}\n"
            "  m_RootOrder: %d\n"
            "  m_LocalEulerAnglesHint: {x: 0, y: 0, z: 0}\n"
            "  m_AnchorMin: {x: %s, y: %s}\n"
            "  m_AnchorMax: {x: %s, y: %s}\n"
            "  m_AnchoredPosition: {x: %s, y: %s}\n"
            "  m_SizeDelta: {x: %s, y: %s}\n"
            "  m_Pivot: {x: %s, y: %s}\n") % (
        fid(n), fid(go), kids, parent, root_order,
        amin[0], amin[1], amax[0], amax[1], pos[0], pos[1], size[0], size[1], pivot[0], pivot[1])


def plain_transform(n, go, parent=0, root_order=0):
    return ("--- !u!4 &%d\n"
            "Transform:\n"
            "  m_ObjectHideFlags: 0\n"
            "  m_CorrespondingSourceObject: {fileID: 0}\n"
            "  m_PrefabInstance: {fileID: 0}\n"
            "  m_PrefabAsset: {fileID: 0}\n"
            "  m_GameObject: {fileID: %d}\n"
            "  m_LocalRotation: {x: 0, y: 0, z: 0, w: 1}\n"
            "  m_LocalPosition: {x: 0, y: 0, z: 0}\n"
            "  m_LocalScale: {x: 1, y: 1, z: 1}\n"
            "  m_Children: []\n"
            "  m_Father: {fileID: %d}\n"
            "  m_RootOrder: %d\n"
            "  m_LocalEulerAnglesHint: {x: 0, y: 0, z: 0}\n") % (fid(n), fid(go), parent, root_order)


def mono(n, go, script_guid, fields):
    body = "".join("  %s: %s\n" % kv for kv in fields)
    return ("--- !u!114 &%d\n"
            "MonoBehaviour:\n"
            "  m_ObjectHideFlags: 0\n"
            "  m_CorrespondingSourceObject: {fileID: 0}\n"
            "  m_PrefabInstance: {fileID: 0}\n"
            "  m_PrefabAsset: {fileID: 0}\n"
            "  m_GameObject: {fileID: %d}\n"
            "  m_Enabled: 1\n"
            "  m_EditorHideFlags: 0\n"
            "  m_Script: {fileID: 11500000, guid: %s, type: 3}\n"
            "  m_Name: \n"
            "  m_EditorClassIdentifier: \n"
            "%s") % (fid(n), fid(go), script_guid, body)


def yaml_list(items):
    if not items:
        return "[]"
    return "[" + ", ".join(items) + "]"


# ---------------------------------------------------------------- Prefab 生成

class Node:
    def __init__(self, name, amin=(0, 0), amax=(1, 1), pos=(0, 0), size=(0, 0)):
        self.name = name
        self.amin, self.amax, self.pos, self.size = amin, amax, pos, size
        self.children = []
        self.view = None      # BlockOutPageView 字段（screenId, anchorNames）

    def add(self, name, **kw):
        n = Node(name, **kw)
        self.children.append(n)
        return n


def build_prefab(root_name, screen_id, children_spec, path, extra_root_components=None):
    """children_spec: list of (name, amin, amax, pos, size)"""
    blocks = []
    counter = [0]

    def new_id():
        counter[0] += 1
        return counter[0]

    root = Node(root_name)
    root.view = screen_id
    for spec in children_spec:
        name, amin, amax, pos, size = spec
        root.add(name, amin=amin, amax=amax, pos=pos, size=size)

    # 分配 id：root 先占 1..2（GO + RT）
    go_root, rt_root = 1, 2
    next_id = 3

    def emit(node, parent_rt, order):
        nonlocal next_id
        my_go = next_id; next_id += 1
        my_rt = next_id; next_id += 1
        child_rt_ids = []
        specs = []
        for i, ch in enumerate(node.children):
            c_go = next_id; next_id += 1
            c_rt = next_id; next_id += 1
            child_rt_ids.append(c_rt)
            specs.append((ch, c_go, c_rt))
        comps = [my_rt]
        my_view_id = None
        if node.view is not None:
            my_view_id = next_id; next_id += 1
            comps.append(my_view_id)
        if extra_root_components and node is root:
            for _ in extra_root_components:
                comps.append(next_id); next_id += 1

        blocks.append(gameobject(my_go, node.name, comps))
        blocks.append(transform(my_rt, my_go, children=child_rt_ids, parent=parent_rt,
                                root_order=order, amin=node.amin, amax=node.amax,
                                pos=node.pos, size=node.size))
        if node.view is not None:
            anchors = yaml_list(['"%s"' % c.name for c in node.children])
            blocks.append(mono(my_view_id, my_go, G_PAGEVIEW,
                               [("screenId", str(node.view)), ("anchorNames", anchors)]))
        for i, (ch, c_go, c_rt) in enumerate(specs):
            emit_into(ch, c_go, c_rt, my_rt, i)
        return my_rt

    def emit_into(node, go_id, rt_id, parent_rt, order):
        blocks.append(gameobject(go_id, node.name, [rt_id]))
        blocks.append(transform(rt_id, go_id, children=(), parent=parent_rt,
                                root_order=order, amin=node.amin, amax=node.amax,
                                pos=node.pos, size=node.size))

    root_rt = emit(root, 0, 0)
    text = YAML_HEAD + "".join(blocks)
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(text)
    return full


# ---------------------------------------------------------------- 具体资产

def gen_prefabs():
    made = []

    # AppRoot：唯一应用根，持服务注册表 + 生命周期
    blocks = [YAML_HEAD]
    blocks.append(gameobject(1, "BlockOutAppRoot", [2, 3]))
    blocks.append(plain_transform(2, 1))
    blocks.append(mono(3, 1, G_APPROOT, []))
    p = os.path.join(ROOT, "Assets/BlockOut/Resources/Prefabs/App/BlockOutAppRoot.prefab")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write("".join(blocks))
    made.append(p)

    STRETCH = ((0, 0), (1, 1), (0, 0), (0, 0))
    TOPBAR = ((0, 1), (1, 1), (0, -48), (0, 96))
    BODY = ((0, 0), (1, 1), (0, 96), (0, -96))
    BOTTOM = ((0, 0), (1, 0), (0, 60), (0, 120))
    FULLSCREEN = ((0, 0), (1, 1), (0, 0), (0, 0))

    made.append(build_prefab(
        "BlockOutLoadingPage", SCREEN["Loading"],
        [("BG",) + STRETCH, ("Center",) + ((0, 0.5), (1, 0.5), (0, 0), (0, 200))],
        "Assets/BlockOut/Resources/Prefabs/UI/BlockOutLoadingPage.prefab"))

    made.append(build_prefab(
        "BlockOutHomePage", SCREEN["Home"],
        [("TopBar",) + TOPBAR, ("Content",) + BODY, ("Deco",) + STRETCH],
        "Assets/BlockOut/Resources/Prefabs/UI/BlockOutHomePage.prefab"))

    # 游戏 HUD：BoardArea 是棋盘挂点（AppBuilder 按名字查找）
    made.append(build_prefab(
        "BlockOutGameHud", SCREEN["Board"],
        [("TopHUD",) + TOPBAR, ("BoardArea",) + ((0, 0), (1, 1), (0, 130), (0, -130)),
         ("Toolbar",) + BOTTOM],
        "Assets/BlockOut/Resources/Prefabs/UI/BlockOutGameHud.prefab"))

    made.append(build_prefab(
        "BlockOutCollectionPage", SCREEN["Collection"],
        [("TopBar",) + TOPBAR, ("Body",) + BODY, ("BigImageLayer",) + FULLSCREEN],
        "Assets/BlockOut/Resources/Prefabs/UI/BlockOutCollectionPage.prefab"))

    made.append(build_prefab(
        "BlockOutStorePage", SCREEN["Store"],
        [("TopBar",) + TOPBAR, ("Body",) + BODY],
        "Assets/BlockOut/Resources/Prefabs/UI/BlockOutStorePage.prefab"))

    # 以下三个为"层"资产：已交付但尚未接入正常路径（UIManager 仍代码构建这些层）
    made.append(build_prefab(
        "BlockOutSettlementPage", SCREEN["Settlement"],
        [("Dim",) + STRETCH, ("SafeRoot",) + STRETCH, ("Card",) + STRETCH],
        "Assets/BlockOut/Resources/Prefabs/UI/BlockOutSettlementPage.prefab"))

    made.append(build_prefab(
        "BlockOutPopupLayer", SCREEN["Board"],
        [("PauseLayer",) + STRETCH, ("FailLayer",) + STRETCH, ("ConfirmLayer",) + STRETCH],
        "Assets/BlockOut/Resources/Prefabs/UI/BlockOutPopupLayer.prefab"))

    made.append(build_prefab(
        "BlockOutSettingsPage", SCREEN["Settings"],
        [("Dim",) + STRETCH, ("SafeRoot",) + STRETCH, ("Card",) + STRETCH],
        "Assets/BlockOut/Resources/Prefabs/UI/BlockOutSettingsPage.prefab"))

    made.append(build_prefab(
        "BlockOutBoardRoot", SCREEN["Board"],
        [("Cells",) + STRETCH],
        "Assets/BlockOut/Resources/Prefabs/Board/BlockOutBoardRoot.prefab"))

    return made


# ---------------------------------------------------------------- 配置资产

def scriptable_object(script_guid, fields):
    body = "".join("  %s: %s\n" % kv for kv in fields)
    return (YAML_HEAD +
            "--- !u!114 &11400000\n"
            "MonoBehaviour:\n"
            "  m_ObjectHideFlags: 0\n"
            "  m_CorrespondingSourceObject: {fileID: 0}\n"
            "  m_PrefabInstance: {fileID: 0}\n"
            "  m_PrefabAsset: {fileID: 0}\n"
            "  m_GameObject: {fileID: 0}\n"
            "  m_Enabled: 1\n"
            "  m_EditorHideFlags: 0\n"
            "  m_Script: {fileID: 11500000, guid: " + script_guid + ", type: 3}\n"
            "  m_Name: \n"
            "  m_EditorClassIdentifier: \n"
            + body)


def gen_settings():
    made = []

    # 开发档：允许替身服务、开日志、不开广告
    made.append(_write(
        "Assets/BlockOut/Settings/BlockOutStartupConfig_Development.asset",
        scriptable_object(G_STARTUP_CFG, [
            ("environment", "1"),          # Development
            ("targetFrameRate", "60"),
            ("runInBackground", "0"),
            ("forceInvariantCulture", "1"),
            ("verboseLog", "1"),
            ("startupStepTimeoutSeconds", "10"),
            ("deferredPreload", "1"),
            ("preloadChapterArt", "1"),
            ("preloadAudio", "1"),
            ("allowFakeServices", "1"),
            ("adsEnabled", "0"),
            ("showStartupSplash", "1"),
            ("splashMinSeconds", "0.6"),
        ])))

    # 发布档：禁替身、禁详细日志、广告开关由 AdConfig 决定
    made.append(_write(
        "Assets/BlockOut/Settings/BlockOutStartupConfig_Release.asset",
        scriptable_object(G_STARTUP_CFG, [
            ("environment", "2"),          # Release
            ("targetFrameRate", "60"),
            ("runInBackground", "0"),
            ("forceInvariantCulture", "1"),
            ("verboseLog", "0"),
            ("startupStepTimeoutSeconds", "15"),
            ("deferredPreload", "1"),
            ("preloadChapterArt", "1"),
            ("preloadAudio", "1"),
            ("allowFakeServices", "0"),
            ("adsEnabled", "1"),
            ("showStartupSplash", "1"),
            ("splashMinSeconds", "0.8"),
        ])))

    # LevelPlay 配置：**故意留空**——不编造凭据、不复制参考工程凭据
    made.append(_write(
        "Assets/BlockOut/Settings/BlockOutAdConfig.asset",
        scriptable_object(G_AD_CFG, [
            ("levelPlayAppKey", '""'),
            ("rewardedPlacementId", '""'),
            ("levelPlayTestMode", "0"),
            ("adsEnabled", "0"),
            ("sdkImported", "0"),
        ])))
    return made


def _write(rel, text):
    p = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    return p


# ---------------------------------------------------------------- Launcher 场景

SETTINGS_BLOCKS = """--- !u!29 &1
OcclusionCullingSettings:
  m_ObjectHideFlags: 0
  serializedVersion: 2
  m_OcclusionBakeSettings:
    smallestOccluder: 5
    smallestHole: 0.25
    backfaceThreshold: 100
  m_SceneGUID: 00000000000000000000000000000000
  m_OcclusionCullingData: {fileID: 0}
--- !u!104 &2
RenderSettings:
  m_ObjectHideFlags: 0
  serializedVersion: 10
  m_Fog: 0
  m_FogColor: {r: 0.5, g: 0.5, b: 0.5, a: 1}
  m_FogMode: 3
  m_FogDensity: 0.01
  m_LinearFogStart: 0
  m_LinearFogEnd: 300
  m_AmbientSkyColor: {r: 0.212, g: 0.227, b: 0.259, a: 1}
  m_AmbientEquatorColor: {r: 0.114, g: 0.125, b: 0.133, a: 1}
  m_AmbientGroundColor: {r: 0.047, g: 0.043, b: 0.035, a: 1}
  m_AmbientIntensity: 1
  m_AmbientMode: 3
  m_SubtractiveShadowColor: {r: 0.42, g: 0.478, b: 0.627, a: 1}
  m_SkyboxMaterial: {fileID: 0}
  m_HaloStrength: 0.5
  m_FlareStrength: 1
  m_FlareFadeSpeed: 1
  m_HaloTexture: {fileID: 0}
  m_SpotCookie: {fileID: 10001, guid: 0000000000000000e000000000000000, type: 0}
  m_DefaultReflectionMode: 0
  m_DefaultReflectionResolution: 128
  m_ReflectionBounces: 1
  m_ReflectionIntensity: 1
  m_CustomReflection: {fileID: 0}
  m_Sun: {fileID: 0}
  m_UseRadianceAmbientProbe: 0
--- !u!157 &3
LightmapSettings:
  m_ObjectHideFlags: 0
  serializedVersion: 13
  m_BakeOnSceneLoad: 0
  m_GISettings:
    serializedVersion: 2
    m_BounceScale: 1
    m_IndirectOutputScale: 1
    m_AlbedoBoost: 1
    m_EnvironmentLightingMode: 0
    m_EnableBakedLightmaps: 0
    m_EnableRealtimeLightmaps: 0
  m_LightmapEditorSettings:
    serializedVersion: 12
    m_Resolution: 2
    m_BakeResolution: 40
    m_AtlasSize: 1024
    m_AO: 0
    m_AOMaxDistance: 0.25
    m_CompAOExponent: 1
    m_CompAOExponentDirect: 0
    m_ExtractAO: 0
    m_LightmapsBakeMode: 1
    m_TextureCompression: 1
    m_ReflectionCompression: 2
    m_MixedBakeMode: 2
    m_BakeBackend: 1
    m_PVRSampling: 1
    m_PVRDirectSampleCount: 32
    m_PVRSampleCount: 512
    m_PVRBounces: 2
    m_PVREnvironmentSampleCountMultiplier: 1
    m_PVREnvironmentReferencePointCount: 2048
    m_PVRFilteringMode: 1
    m_PVRDenoiserTypeDirect: 1
    m_PVRDenoiserTypeIndirect: 1
    m_PVRDenoiserTypeAO: 1
    m_PVRFilterType: 0
    m_PVREnvironmentMIS: 1
    m_PVRCulling: 1
    m_PVRFilteringGaussRadius: 1
    m_PVRFilteringAtrousPositionSigma: 1
    m_ExportTrainingData: 0
    m_TrainingDataDestination: TrainingData
    m_LightProbeSampleCountMultiplier: 4
  m_LightingDataAsset: {fileID: 0}
  m_LightingSettings: {fileID: 0}
--- !u!196 &4
NavMeshSettings:
  serializedVersion: 2
  m_ObjectHideFlags: 0
  m_BuildSettings:
    serializedVersion: 3
    agentTypeID: 0
    agentRadius: 0.5
    agentHeight: 2
    agentSlope: 45
    agentClimb: 0.4
    ledgeDropHeight: 0
    maxJumpAcrossDistance: 0
    minRegionArea: 2
    manualCellSize: 0
    cellSize: 0.16666667
    manualTileSize: 0
    tileSize: 256
    buildHeightMesh: 0
    maxJobWorkers: 2
    preserveTilesOutsideBounds: 0
    debug:
      m_Flags: 0
  m_NavMeshData: {fileID: 0}
"""


def gen_launcher_scene():
    go = ("--- !u!1 &1000000000000000\n"
          "GameObject:\n"
          "  m_ObjectHideFlags: 0\n"
          "  m_CorrespondingSourceObject: {fileID: 0}\n"
          "  m_PrefabInstance: {fileID: 0}\n"
          "  m_PrefabAsset: {fileID: 0}\n"
          "  serializedVersion: 6\n"
          "  m_Component:\n"
          "  - component: {fileID: 4000000000000000}\n"
          "  - component: {fileID: 1140000000000000}\n"
          "  m_Layer: 0\n"
          "  m_Name: BlockOut_Launcher\n"
          "  m_TagString: Untagged\n"
          "  m_Icon: {fileID: 0}\n"
          "  m_NavMeshLayer: 0\n"
          "  m_StaticEditorFlags: 0\n"
          "  m_IsActive: 1\n")
    tr = ("--- !u!4 &4000000000000000\n"
          "Transform:\n"
          "  m_ObjectHideFlags: 0\n"
          "  m_CorrespondingSourceObject: {fileID: 0}\n"
          "  m_PrefabInstance: {fileID: 0}\n"
          "  m_PrefabAsset: {fileID: 0}\n"
          "  m_GameObject: {fileID: 1000000000000000}\n"
          "  m_LocalRotation: {x: 0, y: 0, z: 0, w: 1}\n"
          "  m_LocalPosition: {x: 0, y: 0, z: 0}\n"
          "  m_LocalScale: {x: 1, y: 1, z: 1}\n"
          "  m_Children: []\n"
          "  m_Father: {fileID: 0}\n"
          "  m_RootOrder: 0\n"
          "  m_LocalEulerAnglesHint: {x: 0, y: 0, z: 0}\n")
    mb = ("--- !u!114 &1140000000000000\n"
          "MonoBehaviour:\n"
          "  m_ObjectHideFlags: 0\n"
          "  m_CorrespondingSourceObject: {fileID: 0}\n"
          "  m_PrefabInstance: {fileID: 0}\n"
          "  m_PrefabAsset: {fileID: 0}\n"
          "  m_GameObject: {fileID: 1000000000000000}\n"
          "  m_Enabled: 1\n"
          "  m_EditorHideFlags: 0\n"
          "  m_Script: {fileID: 11500000, guid: %s, type: 3}\n"
          "  m_Name: \n"
          "  m_EditorClassIdentifier: \n"
          "  startupConfig: {fileID: 11400000, guid: %s, type: 2}\n"
          "  adConfig: {fileID: 11400000, guid: %s, type: 2}\n"
          "  appRootPrefab: {fileID: 1000000000000000, guid: %s, type: 3}\n"
          "  showSplash: 1\n") % (G_LAUNCHER, G_ASSET_CFG_DEV, G_ASSET_AD_CFG, G_PREFAB_APPROOT)
    roots = ("--- !u!1660057539 &9223372036854775807\n"
             "SceneRoots:\n"
             "  m_ObjectHideFlags: 0\n"
             "  m_Roots:\n"
             "  - {fileID: 1000000000000000}\n")
    text = YAML_HEAD + SETTINGS_BLOCKS + go + tr + mb + roots
    return _write("Assets/BlockOut/Scenes/Launcher.unity", text)


def main():
    made = []
    made += gen_prefabs()
    made += gen_settings()
    made.append(gen_launcher_scene())
    print("生成 %d 个资产：" % len(made))
    for m in made:
        print("  " + os.path.relpath(m, ROOT))


if __name__ == "__main__":
    main()
