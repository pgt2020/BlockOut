# -*- coding: utf-8 -*-
"""
Stage B level port: copy the first 12 real ArtOut chapter-1 levels from the read-only
reference project into BlockOut's Resources, in reference manifest order.

Source of truth (read-only):
  E:/UnityProject/ArrowOutBlockGallery/ArtOutBlockGallery/Assets/Bundles/Main/ArtOutLevels/<id>.bytes   (gzip JSON)
  E:/UnityProject/ArrowOutBlockGallery/ArtOutBlockGallery/Assets/Resources/ArtOut/GameAssets.json       (manifest order)

Target:
  E:/UnityProject/MutiplayGame/BlockOut/Assets/Resources/ArtOut/Levels/<id>.json (+ .meta)

Chapter 1 layout (12 levels, LevelsPerChapter = 12):
  1-2   : existing local tutorial levels (blockout_tutorial_01/02, kept for save compatibility)
  3-12  : reference manifest entries 3..12, ported verbatim (pieces/colors/arrowCell/dataVersion)

Porting rules (documented in Docs/ArtOut玩法对齐实现记录.md):
  - id / pieces / colors / arrowCell / dataVersion / rewardCoins / chapter / levelInChapter: verbatim
  - difficulty: reference stores a NUMBER (1); reference runtime infers the token from the id
    suffix ("_easy") because JsonUtility drops the numeric into the string field. We write the
    resolved token explicitly ("easy") so the result is deterministic and identical.
  - displayName: reference values are internal design-tool artifacts (e.g. "前10关重排候选 1");
    the reference HUD itself shows "Level N", so we write "Level N" to match the shipped UX.
  - pictureId: verbatim (level id); ArtOutPictureConfig.json gains one entry per ported level
    pointing at the locally delivered block/ch01 artwork (same pattern as pic_tutorial_01/02).
"""
import gzip
import json
import os
import random
import sys

REF_ROOT = r"E:/UnityProject/ArrowOutBlockGallery/ArtOutBlockGallery"
REF_MANIFEST = os.path.join(REF_ROOT, "Assets/Resources/ArtOut/GameAssets.json")
REF_LEVELS = os.path.join(REF_ROOT, "Assets/Bundles/Main/ArtOutLevels")

TGT_ROOT = r"E:/UnityProject/MutiplayGame/BlockOut"
TGT_LEVELS = os.path.join(TGT_ROOT, "Assets/Resources/ArtOut/Levels")
TGT_MANIFEST = os.path.join(TGT_ROOT, "Assets/Resources/ArtOut/GameAssets.json")

# Chapter 1 = levels 1..2 local tutorials + reference manifest entries 3..12 (10 levels).
LOCAL_FIRST = ["blockout_tutorial_01", "blockout_tutorial_02"]
REF_TAIL_COUNT = 10

META_TEMPLATE = """fileFormatVersion: 2
guid: {guid}
TextScriptImporter:
  externalObjects: {{}}
  userData:
  assetBundleName:
  assetBundleVariant:
"""


def load_reference_manifest():
    with open(REF_MANIFEST, encoding="utf-8-sig") as f:
        return json.load(f)


def existing_guids():
    guids = set()
    for root, _dirs, files in os.walk(os.path.join(TGT_ROOT, "Assets")):
        for name in files:
            if name.endswith(".meta"):
                try:
                    with open(os.path.join(root, name), encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith("guid:"):
                                guids.add(line.split(":", 1)[1].strip())
                                break
                except OSError:
                    pass
    return guids


def make_guid(rng, taken):
    while True:
        g = "%032x" % rng.getrandbits(128)
        if g not in taken:
            taken.add(g)
            return g


def port_level(level_id, display_name, rng, taken):
    src = os.path.join(REF_LEVELS, level_id + ".bytes")
    with gzip.open(src, "rt", encoding="utf-8") as f:
        data = json.load(f)

    # difficulty: numeric token in reference JSON -> resolved string token ("easy")
    data["difficulty"] = "easy"
    # displayName: reference HUD shows "Level N"; reference displayNames are dev artifacts
    data["displayName"] = display_name

    dst = os.path.join(TGT_LEVELS, level_id + ".json")
    with open(dst, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    meta = os.path.join(dst + ".meta")
    if not os.path.exists(meta):
        with open(meta, "w", encoding="utf-8", newline="\n") as f:
            f.write(META_TEMPLATE.format(guid=make_guid(rng, taken)))
    return data


def main():
    manifest = load_reference_manifest()
    ref_entries = manifest["levels"]
    tail = [e["id"] for e in ref_entries[2:2 + REF_TAIL_COUNT]]
    if len(tail) != REF_TAIL_COUNT:
        print("FATAL: expected %d tail levels, got %d" % (REF_TAIL_COUNT, len(tail)))
        sys.exit(1)

    os.makedirs(TGT_LEVELS, exist_ok=True)
    rng = random.Random(20261020)
    taken = existing_guids()

    summary = []
    for i, level_id in enumerate(tail):
        display = "Level %d" % (len(LOCAL_FIRST) + i + 1)
        data = port_level(level_id, display, rng, taken)
        summary.append((display, level_id, data.get("width"), data.get("height"), len(data.get("pieces", []))))

    for display, level_id, w, h, n in summary:
        print("ported %-10s %-34s %dx%d pieces=%d" % (display, level_id, w, h, n))

    print("OK: %d levels ported" % len(summary))


if __name__ == "__main__":
    main()
