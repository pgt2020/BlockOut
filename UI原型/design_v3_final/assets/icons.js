// BlockOut C方案 · 手写 SVG 图标库（替代 emoji，保证精致统一）
(function() {
  const S = (inner, vb) => `<svg viewBox="${vb||'0 0 24 24'}" xmlns="http://www.w3.org/2000/svg" fill="none">${inner}</svg>`;

  const PATHS = {
    // 红心
    heart: (c) => S(`<path d="M12 20.5s-7.8-4.9-9.7-9.3C.7 7.6 2.8 4 6.4 4c2 0 3.7 1 5.6 3.1C13.9 5 15.6 4 17.6 4c3.6 0 5.7 3.6 4.1 7.2-1.9 4.4-9.7 9.3-9.7 9.3z" fill="${c}"/>`),
    // 金币
    coin: (c) => S(`<circle cx="12" cy="12" r="9" fill="${c}"/><circle cx="12" cy="12" r="6.2" fill="none" stroke="rgba(255,255,255,.55)" stroke-width="1.4"/><text x="12" y="16.2" text-anchor="middle" font-size="10" font-weight="900" fill="rgba(255,255,255,.9)" font-family="Arial">$</text>`),
    // 星星
    star: (c) => S(`<path d="M12 2.2l2.9 6.2 6.8.8-5 4.6 1.3 6.7L12 17.2 6 20.5l1.3-6.7-5-4.6 6.8-.8z" fill="${c}"/>`),
    // 暂停
    pause: (c) => S(`<rect x="6.5" y="4" width="4.2" height="16" rx="2" fill="${c}"/><rect x="13.3" y="4" width="4.2" height="16" rx="2" fill="${c}"/>`),
    // 设置（滑块风格，可爱风更合适）
    settings: (c) => S(`<g stroke="${c}" stroke-width="2.2" stroke-linecap="round"><path d="M3.5 7h17M3.5 12h17M3.5 17h17"/></g><circle cx="9" cy="7" r="2.6" fill="#fff" stroke="${c}" stroke-width="2.2"/><circle cx="15.5" cy="12" r="2.6" fill="#fff" stroke="${c}" stroke-width="2.2"/><circle cx="7.5" cy="17" r="2.6" fill="#fff" stroke="${c}" stroke-width="2.2"/>`),
    // 奖杯
    trophy: (c) => S(`<path d="M7 4h10v4a5 5 0 0 1-10 0z" fill="${c}"/><path d="M7 5H4.5v1.5A3.5 3.5 0 0 0 8 9.8M17 5h2.5v1.5A3.5 3.5 0 0 1 16 9.8" stroke="${c}" stroke-width="1.8" fill="none" stroke-linecap="round"/><path d="M11 13h2v3h3v2H8v-2h3z" fill="${c}"/><rect x="8" y="18" width="8" height="2.4" rx="1.2" fill="${c}"/>`),
    // 图集/相册
    album: (c) => S(`<rect x="3" y="4.5" width="18" height="15" rx="3" fill="${c}"/><circle cx="8.6" cy="9.6" r="1.7" fill="rgba(255,255,255,.9)"/><path d="M4.5 17.5l4.2-4.2 3 3 3.6-3.6 4.2 4.2" stroke="rgba(255,255,255,.9)" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`),
    // 商店/购物车
    shop: (c) => S(`<path d="M3.5 5h2.2l2.3 10.5h9.6l2-7.5H7" stroke="${c}" stroke-width="2.1" fill="none" stroke-linecap="round" stroke-linejoin="round"/><circle cx="10" cy="19" r="1.7" fill="${c}"/><circle cx="16.5" cy="19" r="1.7" fill="${c}"/>`),
    // 皇冠
    crown: (c) => S(`<path d="M3 8.5l3.5 3L12 4.5l5.5 7 3.5-3-1.8 10H4.8z" fill="${c}"/><circle cx="12" cy="4" r="1.6" fill="${c}"/>`),
    // 日历
    calendar: (c) => S(`<rect x="3.5" y="5" width="17" height="15" rx="3" fill="${c}"/><path d="M3.5 9.5h17" stroke="rgba(255,255,255,.85)" stroke-width="1.8"/><path d="M8 3v4M16 3v4" stroke="${c}" stroke-width="2.2" stroke-linecap="round"/>`),
    // 奖牌
    medal: (c) => S(`<circle cx="12" cy="14.5" r="5.5" fill="${c}"/><path d="M8.5 3l2.2 4.2-2 .8-2.5-4.2zM15.5 3l-2.2 4.2 2 .8 2.5-4.2z" fill="${c}"/><path d="M12 8.5l1 2.2 2.3.2-1.7 1.6.5 2.3-2.1-1.2-2.1 1.2.5-2.3-1.7-1.6 2.3-.2z" fill="rgba(255,255,255,.95)"/>`),
    // 账号
    account: (c) => S(`<circle cx="12" cy="8.5" r="4" fill="${c}"/><path d="M4.5 20.5c0-3.6 3.4-5.5 7.5-5.5s7.5 1.9 7.5 5.5" fill="${c}"/>`),
    // 客服耳机
    headset: (c) => S(`<path d="M4.5 14v-2a7.5 7.5 0 0 1 15 0v2" stroke="${c}" stroke-width="2.2" fill="none" stroke-linecap="round"/><rect x="3" y="13" width="4" height="6.5" rx="2" fill="${c}"/><rect x="17" y="13" width="4" height="6.5" rx="2" fill="${c}"/><path d="M19 19.5v.5a2.5 2.5 0 0 1-2.5 2.5H13" stroke="${c}" stroke-width="2" fill="none" stroke-linecap="round"/>`),
    // 锁
    lock: (c) => S(`<rect x="5" y="10.5" width="14" height="9.5" rx="2.8" fill="${c}"/><path d="M8 10.5V8a4 4 0 0 1 8 0v2.5" stroke="${c}" stroke-width="2.2" fill="none" stroke-linecap="round"/><circle cx="12" cy="15.2" r="1.6" fill="rgba(255,255,255,.9)"/>`),
    // 关闭
    close: (c) => S(`<path d="M6 6l12 12M18 6L6 18" stroke="${c}" stroke-width="2.6" stroke-linecap="round"/>`),
    // 返回
    back: (c) => S(`<path d="M15 4.5L7.5 12l7.5 7.5" stroke="${c}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>`),
    // 播放
    play: (c) => S(`<path d="M8 5.5l11 6.5-11 6.5z" fill="${c}"/>`),
    // 分享
    share: (c) => S(`<circle cx="6" cy="12" r="2.6" fill="${c}"/><circle cx="17.5" cy="6" r="2.6" fill="${c}"/><circle cx="17.5" cy="18" r="2.6" fill="${c}"/><path d="M8.4 10.8l6.8-3.6M8.4 13.2l6.8 3.6" stroke="${c}" stroke-width="1.9" stroke-linecap="round"/>`),
    // 灯泡
    bulb: (c) => S(`<path d="M12 3a6 6 0 0 1 3.4 10.9c-.7.5-1 1.2-1 2.1h-4.8c0-.9-.3-1.6-1-2.1A6 6 0 0 1 12 3z" fill="${c}"/><path d="M9.8 18.5h4.4M10.5 21h3" stroke="${c}" stroke-width="2" stroke-linecap="round"/>`),
    // 锤子
    hammer: (c) => S(`<path d="M14.5 3.5l6 6-2.5 2.5-6-6z" fill="${c}"/><path d="M13 7l-8.5 8.5c-1 1-1 2.6 0 3.5s2.6 1 3.5 0L16.5 11" stroke="${c}" stroke-width="2.2" fill="none" stroke-linecap="round"/>`),
    // 魔法棒
    wand: (c) => S(`<path d="M5 19L15.5 8.5" stroke="${c}" stroke-width="2.4" stroke-linecap="round"/><path d="M16.5 3.5l1.2 2.8 2.8 1.2-2.8 1.2-1.2 2.8-1.2-2.8-2.8-1.2 2.8-1.2z" fill="${c}"/><path d="M19.5 14l.8 1.7 1.7.8-1.7.8-.8 1.7-.8-1.7-1.7-.8 1.7-.8z" fill="${c}"/>`),
    // 云
    cloud: (c) => S(`<path d="M7 18.5a4.5 4.5 0 0 1-.4-9A6 6 0 0 1 18.3 10a4 4 0 0 1-.8 8z" fill="${c}"/>`),
    // 铃铛
    bell: (c) => S(`<path d="M12 3.5a5.5 5.5 0 0 1 5.5 5.5c0 4 1.5 5.5 1.5 5.5H5s1.5-1.5 1.5-5.5A5.5 5.5 0 0 1 12 3.5z" fill="${c}"/><path d="M10 17.5a2.2 2.2 0 0 0 4 0" stroke="${c}" stroke-width="2" fill="none" stroke-linecap="round"/>`),
    // 语言
    globe: (c) => S(`<circle cx="12" cy="12" r="8.5" stroke="${c}" stroke-width="2.1" fill="none"/><path d="M3.5 12h17M12 3.5c2.6 2.4 2.6 14.6 0 17-2.6-2.4-2.6-14.6 0-17z" stroke="${c}" stroke-width="1.8" fill="none"/>`),
    // 刷新
    refresh: (c) => S(`<path d="M20 12a8 8 0 1 1-2.4-5.7" stroke="${c}" stroke-width="2.2" fill="none" stroke-linecap="round"/><path d="M20 3.5v4h-4" stroke="${c}" stroke-width="2.2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`),
    // 垃圾桶
    trash: (c) => S(`<path d="M5 7h14l-1.2 13a2 2 0 0 1-2 1.8H8.2a2 2 0 0 1-2-1.8z" fill="${c}"/><path d="M3.5 7h17M9.5 7V4.5h5V7" stroke="${c}" stroke-width="2" fill="none" stroke-linecap="round"/>`),
    // 文档
    doc: (c) => S(`<path d="M6 3.5h8l4 4v13H6z" fill="${c}"/><path d="M14 3.5v4h4" stroke="rgba(255,255,255,.7)" stroke-width="1.6" fill="none"/>`),
    // 信息
    info: (c) => S(`<circle cx="12" cy="12" r="8.5" fill="${c}"/><path d="M12 10.5v6" stroke="rgba(255,255,255,.95)" stroke-width="2.4" stroke-linecap="round"/><circle cx="12" cy="7.6" r="1.4" fill="rgba(255,255,255,.95)"/>`),
    // 箭头（方块内）：up/down/left/right
    arrow_up: (c) => S(`<path d="M12 3.5l8.5 11h-5.5v6h-6v-6H3.5z" fill="${c}"/>`),
    arrow_down: (c) => S(`<path d="M12 20.5L3.5 9.5h5.5v-6h6v6h5.5z" fill="${c}"/>`),
    arrow_left: (c) => S(`<path d="M3.5 12L14.5 3.5v5.5h6v6h-6v5.5z" fill="${c}"/>`),
    arrow_right: (c) => S(`<path d="M20.5 12L9.5 20.5v-5.5h-6v-6h6V3.5z" fill="${c}"/>`),
    // 复活（心+箭头）
    revive: (c1, c2) => S(`<path d="M12 20.5s-7.8-4.9-9.7-9.3C.7 7.6 2.8 4 6.4 4c2 0 3.7 1 5.6 3.1C13.9 5 15.6 4 17.6 4c3.6 0 5.7 3.6 4.1 7.2-1.9 4.4-9.7 9.3-9.7 9.3z" fill="${c1||'#FF6B6B'}"/>`),
    // 盾牌（VIP）
    shield: (c) => S(`<path d="M12 3l7.5 3v6c0 4.5-3.2 7.6-7.5 9-4.3-1.4-7.5-4.5-7.5-9V6z" fill="${c}"/><path d="M8.8 12l2.3 2.3 4.2-4.5" stroke="rgba(255,255,255,.95)" stroke-width="2.1" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`),
    // 礼物
    gift: (c) => S(`<rect x="3.5" y="8.5" width="17" height="4" rx="1.5" fill="${c}"/><rect x="5" y="12.5" width="14" height="8" rx="1.8" fill="${c}"/><path d="M12 8.5v12" stroke="rgba(255,255,255,.75)" stroke-width="1.8"/><path d="M12 8.5C10 8.5 7.5 8 7.5 5.8 7.5 4.3 8.7 3.5 9.8 3.5c1.8 0 2.2 2.5 2.2 5zM12 8.5c2 0 4.5-.5 4.5-2.7 0-1.5-1.2-2.3-2.3-2.3-1.8 0-2.2 2.5-2.2 5z" fill="${c}"/>`),
    // 火箭/双倍
    rocket: (c) => S(`<path d="M12 2.5c3.5 2.2 5.5 6 5.5 10l-2.5 3h-6L6.5 12.5c0-4 2-7.8 5.5-10z" fill="${c}"/><circle cx="12" cy="10" r="2.2" fill="rgba(255,255,255,.9)"/><path d="M9 15.5l-2 4 3-1.2M15 15.5l2 4-3-1.2" stroke="${c}" stroke-width="2" fill="none" stroke-linecap="round"/>`),
    // 勾
    check: (c) => S(`<path d="M4.5 12.5l5 5 10-11" stroke="${c}" stroke-width="2.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`),
    // 警告
    warn: (c) => S(`<path d="M12 3.5L22 20.5H2z" fill="${c}"/><path d="M12 9.5v5" stroke="rgba(255,255,255,.95)" stroke-width="2.4" stroke-linecap="round"/><circle cx="12" cy="17.3" r="1.4" fill="rgba(255,255,255,.95)"/>`),
    // 小爪印
    paw: (c) => S(`<ellipse cx="12" cy="15.5" rx="4.6" ry="3.8" fill="${c}"/><circle cx="5.5" cy="10.5" r="2.1" fill="${c}"/><circle cx="18.5" cy="10.5" r="2.1" fill="${c}"/><circle cx="9" cy="6.5" r="2.1" fill="${c}"/><circle cx="15" cy="6.5" r="2.1" fill="${c}"/>`),
    // 棒棒糖
    candy: (c) => S(`<circle cx="12" cy="9.5" r="6" fill="${c}"/><path d="M12 3.5a6 6 0 0 1 0 12A6 6 0 0 1 12 3.5z" fill="none"/><path d="M6.5 9.5a5.5 5.5 0 0 1 11 0" stroke="rgba(255,255,255,.75)" stroke-width="1.8" fill="none"/><path d="M12 15.5v5.5" stroke="#E6C7B6" stroke-width="2" stroke-linecap="round"/>`),
    // 纸杯蛋糕
    cupcake: (c) => S(`<path d="M6 11h12l-1.5 8.5a2 2 0 0 1-2 1.7h-5a2 2 0 0 1-2-1.7z" fill="${c}"/><path d="M7.5 11a4.5 4.5 0 0 1 9 0z" fill="${c}"/><circle cx="12" cy="4.8" r="1.8" fill="${c}"/>`)
  };

  window.ICON = function(name, size, color, extra) {
    const fn = PATHS[name];
    if(!fn) return '';
    const svg = fn(color || '#5C3A2A', extra || '#FF7A6B');
    return `<span class="icn" style="display:inline-flex;width:${size||20}px;height:${size||20}px">${svg}</span>`;
  };
  window.ICON_RAW = function(name, color, extra) {
    const fn = PATHS[name];
    if(!fn) return '';
    return fn(color || '#5C3A2A', extra || '#FF7A6B');
  };
  window.ICON_NAMES = Object.keys(PATHS);
})();
