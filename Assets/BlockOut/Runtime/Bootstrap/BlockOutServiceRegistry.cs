using System;
using System.Collections.Generic;

namespace BlockOut.Bootstrap
{
    /// <summary>
    /// 轻量服务注册表（R03/R09）。不引入大型 DI 框架：
    /// Bootstrap 组装期 Register，业务期 Resolve；支持显式释放（IDisposable）。
    /// </summary>
    public sealed class BlockOutServiceRegistry
    {
        private readonly Dictionary<Type, object> services = new Dictionary<Type, object>();

        public void Register<T>(T instance) where T : class
        {
            if (instance == null) throw new ArgumentNullException(nameof(instance));
            services[typeof(T)] = instance;
        }

        public T Resolve<T>() where T : class
        {
            return TryResolve<T>(out var svc) ? svc : null;
        }

        public bool TryResolve<T>(out T service) where T : class
        {
            if (services.TryGetValue(typeof(T), out var raw) && raw is T typed)
            {
                service = typed;
                return true;
            }
            service = null;
            return false;
        }

        public bool IsRegistered<T>() where T : class
        {
            return services.ContainsKey(typeof(T));
        }

        /// <summary>释放全部已注册服务（AppRoot 显式销毁时调用）。</summary>
        public void DisposeAll()
        {
            foreach (var kv in services)
            {
                if (kv.Value is IDisposable d)
                {
                    try { d.Dispose(); }
                    catch (Exception e) { UnityEngine.Debug.LogWarning("[BlockOut] dispose " + kv.Key.Name + " failed: " + e.Message); }
                }
            }
            services.Clear();
        }

        public IEnumerable<string> Describe()
        {
            foreach (var kv in services) yield return kv.Key.Name;
        }
    }
}
