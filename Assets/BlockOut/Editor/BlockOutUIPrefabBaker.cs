using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using BlockOut.UI;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

namespace BlockOut.Editor
{
    /// <summary>Explicit editor command: generate assets in a preview scene, validate, save, and clean up.</summary>
    public static class BlockOutUIPrefabBaker
    {
        private const string Root="Assets/BlockOut/Resources/Prefabs/UI";
        private static readonly Dictionary<string,Sprite> sprites=new Dictionary<string,Sprite>();
        [MenuItem("BlockOut/Prefab/烘焙完整页面与弹窗")]
        public static void BakeAll()
        {
            if(EditorApplication.isPlayingOrWillChangePlaymode)
            { Debug.LogError("[BlockOut] 请退出 Play Mode 后生成资源。"); return; }
            if(File.Exists(Root+"/BlockOutGameHud.prefab"))
            { Debug.LogError("[BlockOut] 已存在按 ArtOut 调整的页面资源。旧烘焙器不能覆盖这些资源；请直接编辑 Prefab，或使用 Tools/UIAuthoring/generate_prefabs.py（包含布局对齐步骤）。"); return; }
            var scene=EditorSceneManager.NewPreviewScene();
            int saved=0;
            try
            {
                sprites.Clear();
                var host=new GameObject("__BlockOutUIAuthoring__");
                SceneManager.MoveGameObjectToScene(host,scene);
                var ui=host.AddComponent<BlockOutUIManager>();
                ui.BuildAuthoring();
                ui.BoardArea=ui.ScreenRoot(BlockOutScreenId.Board).transform.Find("BoardArea") as RectTransform;
                PrepareLists(ui);
                PersistSprites(host);
                string[] layers={"PauseLayer","FailLayer","ConfirmLayer","SettlementLayer","SettingsLayer","AboutLayer","GuideLayer"};
                // Detach first so popups are not duplicated in Board prefabs.
                foreach(var layer in layers) ui.LayerRoot(layer).transform.SetParent(null,false);
                foreach(var id in new[]{BlockOutScreenId.Loading,BlockOutScreenId.Home,BlockOutScreenId.Board,BlockOutScreenId.Collection,BlockOutScreenId.Store})
                {
                    SavePage(ui,ui.ScreenRoot(id),BlockOutUIPrefabRegistry.ResourceName(id),
                        BlockOutUIPrefabRegistry.ViewTypeForScreen(id),false); saved++;
                }
                foreach(var layer in layers)
                {
                    SavePage(ui,ui.LayerRoot(layer),BlockOutUIPrefabRegistry.LayerResourceName(layer),
                        BlockOutUIPrefabRegistry.ViewTypeForLayer(layer),true); saved++;
                }
                AssetDatabase.SaveAssets();
                BlockOutUIPrefabRegistry.ClearCache();
                Debug.Log("[BlockOut] 已保存 "+saved+" 个完整页面/弹窗及 5 个列表条目模板。尚需重载资源、编译和运行验收。");
            }
            catch(Exception e)
            {
                Debug.LogError("[BlockOut] UI 生成失败；仅 "+saved+" 个页面已保存，不能视为完整交付。"+e);
            }
            finally
            {
                sprites.Clear();
                EditorSceneManager.ClosePreviewScene(scene);
            }
        }

        private static void SavePage(BlockOutUIManager ui,GameObject surface,string resource,Type type,bool popup)
        {
            if(surface==null) throw new InvalidOperationException("缺少根节点: "+resource);
            var wrapper=new GameObject(type.Name,typeof(RectTransform));
            SceneManager.MoveGameObjectToScene(wrapper,surface.scene);
            surface.transform.SetParent(wrapper.transform,false);
            surface.SetActive(true);
            var rt=(RectTransform)wrapper.transform;
            rt.anchorMin=Vector2.zero; rt.anchorMax=Vector2.one; rt.sizeDelta=Vector2.zero;
            if(popup)
            {
                // Full-canvas hit surface blocks input outside the fitted content as well.
                var hit=wrapper.AddComponent<Image>(); hit.color=Color.clear; hit.raycastTarget=true;
            }
            var layout=wrapper.AddComponent<BlockOutPageLayout>();
            layout.Surface=(RectTransform)surface.transform;
            layout.DesignSize=new Vector2(390,844);
            layout.Surface.anchorMin=layout.Surface.anchorMax=new Vector2(.5f,.5f);
            layout.Surface.pivot=new Vector2(.5f,.5f);
            layout.Surface.sizeDelta=layout.DesignSize;
            layout.Surface.anchoredPosition=Vector2.zero;
            layout.Surface.localScale=Vector3.one;
            var old=surface.GetComponent<BlockOutPageView>();
            if(old!=null) UnityEngine.Object.DestroyImmediate(old);
            if(type==typeof(BlockOutGuideView)) ui.GuideLayer=wrapper;
            var view=(BlockOutUIViewBase)wrapper.AddComponent(type);
            view.AbsorbFrom(ui);
            Validate(view,resource);
            Save(wrapper,"Assets/BlockOut/Resources/"+resource+".prefab");
        }

        private static void Validate(BlockOutUIViewBase view,string label)
        {
            if(view==null) throw new InvalidOperationException(label+": View 缺失");
            string error;
            if(!view.ValidateReferences(out error)) throw new InvalidOperationException(label+": "+error);
            foreach(var image in view.GetComponentsInChildren<Image>(true))
                if(image.sprite!=null && !AssetDatabase.Contains(image.sprite))
                    throw new InvalidOperationException(label+": 非持久图片 "+image.name);
        }

        private static GameObject Save(GameObject root,string path)
        {
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            bool popup=root.name.Contains("Popup") || root.name.Contains("Settings") || root.name.Contains("Settlement");
            foreach(var rect in root.GetComponentsInChildren<RectTransform>(true))
            {
                bool card=popup && rect.name=="Card";
                if(!card && rect.GetComponent<Button>()==null)continue;
                var feedback=rect.GetComponent<BlockOutUIFeedback>() ?? rect.gameObject.AddComponent<BlockOutUIFeedback>();
                feedback.Popup=card;
                if(rect.GetComponent<BlockOut.Gameplay.BlockOutAnimationPlayer>()==null)rect.gameObject.AddComponent<BlockOut.Gameplay.BlockOutAnimationPlayer>();
                var animator=rect.GetComponent<Animator>() ?? rect.gameObject.AddComponent<Animator>();
                animator.runtimeAnimatorController=Resources.Load<RuntimeAnimatorController>("ArtOutPresentation/Animations/Feedback");
                animator.enabled=false;
            }
            var result=PrefabUtility.SaveAsPrefabAsset(root,path);
            if(result==null) throw new IOException("保存 Prefab 失败: "+path);
            return result;
        }

        private static T SaveItem<T>(T view,string name) where T:BlockOutUIViewBase
        {
            PersistSprites(view.gameObject);
            Validate(view,name);
            var item=Save(view.gameObject,Root+"/Items/"+name+".prefab").GetComponent<T>();
            if(item==null) throw new InvalidOperationException(name+": 保存后 View 丢失");
            return item;
        }

        private static RectTransform Container(Transform parent,string name)
        {
            var go=new GameObject(name,typeof(RectTransform));
            go.transform.SetParent(parent,false);
            var rt=(RectTransform)go.transform;
            rt.anchorMin=new Vector2(0,1); rt.anchorMax=new Vector2(1,1); rt.pivot=new Vector2(.5f,1);
            rt.sizeDelta=new Vector2(0,0);
            return rt;
        }
        private static void Vertical(RectTransform root,float spacing)
        {
            var layout=root.gameObject.AddComponent<VerticalLayoutGroup>();
            layout.spacing=spacing; layout.childControlWidth=true; layout.childControlHeight=true;
            layout.childForceExpandHeight=false; layout.childForceExpandWidth=true;
            var fit=root.gameObject.AddComponent<ContentSizeFitter>(); fit.verticalFit=ContentSizeFitter.FitMode.PreferredSize;
        }
        private static void Height(Transform t,float height)
        {
            var layout=t.GetComponent<LayoutElement>() ?? t.gameObject.AddComponent<LayoutElement>();
            layout.preferredHeight=height; layout.minHeight=height; layout.flexibleHeight=0;
        }

        private static void PrepareLists(BlockOutUIManager ui)
        {
            // Store templates preserve each tool's icon; all share one view/behavior.
            var store=ui.ScreenRoot(BlockOutScreenId.Store).transform;
            ui.StoreItemPrefabs=new BlockOutStoreItemView[ui.StoreProducts.Length];
            for(int i=0;i<ui.StoreProducts.Length;i++)
            {
                var product=ui.StoreProducts[i];
                Height(product.CardRoot.transform,112);
                var item=product.CardRoot.AddComponent<BlockOutStoreItemView>(); item.Product=product;
                ui.StoreItemPrefabs[i]=SaveItem(item,"Store"+product.Tool);
                UnityEngine.Object.DestroyImmediate(product.CardRoot);
            }
            var viewport=Container(store,"StoreViewport");
            viewport.anchorMin=new Vector2(0,0); viewport.anchorMax=new Vector2(1,1);
            viewport.offsetMin=new Vector2(24,112); viewport.offsetMax=new Vector2(-24,-84);
            var bg=viewport.gameObject.AddComponent<Image>(); bg.color=Color.clear;
            viewport.gameObject.AddComponent<RectMask2D>();
            var scroll=viewport.gameObject.AddComponent<ScrollRect>(); scroll.horizontal=false;
            scroll.movementType=ScrollRect.MovementType.Clamped; scroll.viewport=viewport;
            ui.StoreListRoot=Container(viewport,"Products"); Vertical(ui.StoreListRoot,12);
            scroll.content=ui.StoreListRoot;
            // Explanation is outside the product list so rebuilding the list never removes it.
            var note=store.Find("CoinNote"); if(note!=null) UnityEngine.Object.DestroyImmediate(note.gameObject);
            ui.StoreEmptyText=BlockOutWidgets.Label(viewport,"Empty","暂无商品",14,400,
                BlockOutDesignTokens.TextCocoa,TextAnchor.MiddleCenter);
            ui.StoreEmptyText.raycastTarget=false; ui.StoreEmptyText.gameObject.SetActive(false);

            // Collection chapter row template with every state available in the prefab.
            var content=ui.CollectionContent;
            var first=content.Find("ChapterRow_0");
            if(first==null) throw new InvalidOperationException("缺少章节样板");
            var chapter=first.gameObject.AddComponent<BlockOutChapterItemView>();
            chapter.Button=first.GetComponent<Button>() ?? first.gameObject.AddComponent<Button>();
            chapter.Button.targetGraphic=first.GetComponent<Image>();
            chapter.Title=first.Find("Title").GetComponent<Text>();
            chapter.Subtitle=first.Find("Sub").GetComponent<Text>();
            chapter.Thumbnail=first.Find("Thumb").GetComponent<Image>();
            var lockImage=BlockOutWidgets.SpriteImage(chapter.Thumbnail.transform,"Locked",BlockOutIconFactory.LockIcon(),UIAnchorPreset.MiddleCenter,0,0,22,22);
            lockImage.raycastTarget=false; chapter.Locked=lockImage.gameObject;
            Height(first,72);
            ui.ChapterItemPrefab=SaveItem(chapter,"ChapterItem");
            var oldRows=new List<GameObject>();
            foreach(Transform child in content) if(child.name.StartsWith("ChapterRow_")) oldRows.Add(child.gameObject);
            foreach(var child in oldRows) UnityEngine.Object.DestroyImmediate(child);
            ui.CollectionChapterList=Container(content,"ChapterList"); Vertical(ui.CollectionChapterList,8);
            ui.CollectionChapterList.SetSiblingIndex(content.Find("ChapterLabel").GetSiblingIndex()+1);

            // Repeat challenge cells are reusable and no longer depend on child names at runtime.
            var cell=ui.CollectionRepeatGrid.Find("RepeatCell_0");
            var repeat=cell.gameObject.AddComponent<BlockOutRepeatItemView>();
            repeat.Button=cell.GetComponent<Button>(); repeat.Background=cell.Find("Bg").GetComponent<Image>();
            repeat.Number=cell.Find("Num").GetComponent<Text>();
            repeat.Mark=cell.Find("Mark").gameObject; repeat.Locked=cell.Find("Lock").gameObject;
            ui.RepeatItemPrefab=SaveItem(repeat,"RepeatItem");
            var oldCells=new List<GameObject>();
            foreach(Transform child in ui.CollectionRepeatGrid) if(child.name.StartsWith("RepeatCell_")) oldCells.Add(child.gameObject);
            foreach(var child in oldCells) UnityEngine.Object.DestroyImmediate(child);
            ui.RepeatListRoot=Container(ui.CollectionRepeatGrid,"Cells");
            ui.RepeatListRoot.anchoredPosition=new Vector2(0,-36);
            ui.RepeatListRoot.sizeDelta=new Vector2(-24,96);
            var grid=ui.RepeatListRoot.gameObject.AddComponent<GridLayoutGroup>();
            grid.cellSize=new Vector2(44,44); grid.spacing=new Vector2(8,4);
            grid.constraint=GridLayoutGroup.Constraint.FixedColumnCount; grid.constraintCount=6;
            grid.childAlignment=TextAnchor.UpperCenter;
            Vertical(content,12);
            foreach(Transform child in content)
            {
                if(child==ui.CollectionChapterList) continue;
                var rect=(RectTransform)child;
                Height(child,child==ui.CollectionRepeatGrid ? 160 : Mathf.Max(24,rect.rect.height));
            }
            // Collection has one scroll content containing summary, rows and the repeat grid.
            ui.collectionScroll.content=content;
        }

        private static void PersistSprites(GameObject root)
        {
            foreach(var image in root.GetComponentsInChildren<Image>(true))
            {
                var sprite=image.sprite;
                if(sprite==null || AssetDatabase.Contains(sprite)) continue;
                var source=sprite.texture;
                var rect=sprite.rect;
                Texture2D crop=null;
                try
                {
                    if(source==null || !source.isReadable || sprite.packed)
                        throw new InvalidOperationException("不支持的临时 Sprite: "+image.name);
                    int x=Mathf.RoundToInt(rect.x), y=Mathf.RoundToInt(rect.y);
                    int width=Mathf.RoundToInt(rect.width), height=Mathf.RoundToInt(rect.height);
                    if(width<=0 || height<=0) throw new InvalidOperationException("空 Sprite: "+image.name);
                    crop=new Texture2D(width,height,TextureFormat.RGBA32,false);
                    crop.SetPixels(source.GetPixels(x,y,width,height)); crop.Apply();
                    var bytes=crop.EncodeToPNG();
                    if(bytes==null || bytes.Length==0) throw new IOException("PNG 编码失败: "+image.name);
                    var pivot=new Vector2(sprite.pivot.x/width,sprite.pivot.y/height);
                    string settings=string.Join("|",new[]{
                        sprite.border.x.ToString("R",CultureInfo.InvariantCulture),sprite.border.y.ToString("R",CultureInfo.InvariantCulture),
                        sprite.border.z.ToString("R",CultureInfo.InvariantCulture),sprite.border.w.ToString("R",CultureInfo.InvariantCulture),
                        pivot.x.ToString("R",CultureInfo.InvariantCulture),pivot.y.ToString("R",CultureInfo.InvariantCulture),
                        sprite.pixelsPerUnit.ToString("R",CultureInfo.InvariantCulture),source.filterMode.ToString(),source.wrapMode.ToString()});
                    byte[] extra=Encoding.UTF8.GetBytes(settings);
                    byte[] key=new byte[bytes.Length+extra.Length];
                    Buffer.BlockCopy(bytes,0,key,0,bytes.Length); Buffer.BlockCopy(extra,0,key,bytes.Length,extra.Length);
                    string hash;
                    using(var sha=SHA256.Create()) hash=BitConverter.ToString(sha.ComputeHash(key)).Replace("-","").ToLowerInvariant();
                    Sprite persisted;
                    if(!sprites.TryGetValue(hash,out persisted))
                    {
                        string path=Root+"/GeneratedSprites/ui_"+hash+".png";
                        Directory.CreateDirectory(Path.GetDirectoryName(path));
                        if(!File.Exists(path)) File.WriteAllBytes(path,bytes);
                        AssetDatabase.ImportAsset(path,ImportAssetOptions.ForceSynchronousImport);
                        var importer=AssetImporter.GetAtPath(path) as TextureImporter;
                        if(importer==null) throw new IOException("图片导入器缺失: "+path);
                        importer.textureType=TextureImporterType.Sprite; importer.spriteImportMode=SpriteImportMode.Single;
                        importer.spriteBorder=sprite.border; importer.spritePixelsPerUnit=sprite.pixelsPerUnit;
                        var settingsData=new TextureImporterSettings(); importer.ReadTextureSettings(settingsData);
                        settingsData.spriteAlignment=9; settingsData.spritePivot=pivot; importer.SetTextureSettings(settingsData);
                        importer.npotScale=TextureImporterNPOTScale.None; importer.textureCompression=TextureImporterCompression.Uncompressed;
                        importer.maxTextureSize=8192; importer.mipmapEnabled=false; importer.alphaIsTransparency=true;
                        importer.filterMode=source.filterMode; importer.wrapMode=source.wrapMode;
                        importer.SaveAndReimport();
                        persisted=AssetDatabase.LoadAssetAtPath<Sprite>(path);
                        if(persisted==null) throw new IOException("图片重载失败: "+path);
                        sprites[hash]=persisted;
                    }
                    image.sprite=persisted;
                }
                finally { if(crop!=null) UnityEngine.Object.DestroyImmediate(crop); }
            }
        }
    }
}
