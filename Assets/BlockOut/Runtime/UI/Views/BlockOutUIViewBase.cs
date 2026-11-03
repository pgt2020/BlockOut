using System;
using System.Reflection;
using UnityEngine;

namespace BlockOut.UI
{
    /// <summary>
    /// UI View 基类（UI-03）：固定控件经序列化字段在 Prefab 中绑定；
    /// 运行时/烘焙时与 BlockOutUIManager 的公开字段按“同名同型”互传，
    /// 使控制器仍经 UI.XXX 读控件、而控件来源从“代码构建”切换为“Prefab 绑定”。
    /// 不做任何业务，只承载引用与传输。
    /// </summary>
    public abstract class BlockOutUIViewBase : MonoBehaviour
    {
        /// <summary>把来源对象的同名公开字段拷入本 View（烘焙：UIManager → View）。</summary>
        public void AbsorbFrom(object source) { CopyFields(source, this, "AbsorbFrom"); }

        /// <summary>把本 View 的同名公开字段拷入目标（运行：View → UIManager）。</summary>
        public void ApplyTo(object target) { CopyFields(this, target, "ApplyTo"); }

        // 仅拷贝“目标拥有、且与来源同名同型”的公开实例字段；缺失/类型不符记日志（便于定位）。
        private static void CopyFields(object from, object to, string tag)
        {
            if (from == null || to == null) return;
            var toType = to.GetType();
            var fromType = from.GetType();
            const BindingFlags flags = BindingFlags.Public | BindingFlags.Instance;
            foreach (var tf in toType.GetFields(flags))
            {
                if (tf.IsLiteral || tf.IsNotSerialized) continue;
                var sf = fromType.GetField(tf.Name, flags);
                if (sf == null) continue;
                if (sf.FieldType != tf.FieldType) continue;
                try { tf.SetValue(to, sf.GetValue(from)); }
                catch (Exception e) { Debug.LogWarning("[BlockOut][" + tag + "] 字段传输失败 " + tf.Name + ": " + e.Message); }
            }
        }

        /// <summary>U01：校验序列化引用完整性；缺失按“页面(View 类型)+字段名”明确报错（含数组成员）。</summary>
        public bool ValidateReferences(out string error)
        {
            var missing=new System.Collections.Generic.List<string>();
            ValidateFields(this,GetType().Name,missing);
            error=string.Join("; ",missing);
            return missing.Count==0;
        }
        public void ReportMissingRefs()
        {
            string error;
            if(!ValidateReferences(out error)) Debug.LogError("[BlockOut][UI] "+error);
        }
        private static void ValidateFields(object value,string path,System.Collections.Generic.List<string> missing)
        {
            foreach(var f in value.GetType().GetFields(BindingFlags.Public|BindingFlags.Instance))
            {
                if(f.IsLiteral || f.IsNotSerialized) continue;
                object child=f.GetValue(value);
                ValidateValue(child,f.FieldType,path+"."+f.Name,missing);
            }
        }
        private static void ValidateValue(object value,Type type,string path,System.Collections.Generic.List<string> missing)
        {
            if(typeof(UnityEngine.Object).IsAssignableFrom(type))
            {
                if((UnityEngine.Object)value==null) missing.Add(path);
            }
            else if(type.IsArray)
            {
                var array=value as Array;
                if(array==null) { missing.Add(path); return; }
                for(int i=0;i<array.Length;i++) ValidateValue(array.GetValue(i),type.GetElementType(),path+"["+i+"]",missing);
            }
            else if(type==typeof(ToolSlotRefs) || type==typeof(StoreProductRefs))
            {
                if(value==null) missing.Add(path); else ValidateFields(value,path,missing);
            }
        }
    }
}
