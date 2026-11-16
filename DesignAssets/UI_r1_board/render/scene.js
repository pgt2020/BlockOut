// BlockOut · 对局页代表页渲染（three.js / 正交相机 / 真实光照 + 阴影）
// 坐标：设计尺寸 1080×1920，世界单位 = 设计像素，原点在屏幕中心，+Y 向上。
import * as THREE from './vendor/three.module.js';
import { RoomEnvironment } from './vendor/environments/RoomEnvironment.js';

const W = 1080, H = 1920;
const SS = 2;                       // 超采样
const BOARD_BOX = 840;              // 棋盘可视区上限（正方形）
let CELL = 78;                      // 棋盘格边长（按关卡行列自适应）
const TILT = -12 * Math.PI / 180;    // 棋盘俯仰，用来露出方块的"下唇"厚度

// ---------- 文案（真实关卡数据，不虚构） ----------
const L = {
  levelTitle: '第 15 关',
  levelSub: '第 1 章',
  pause: null,
  hint: '轻点方块 · 沿箭头方向飞出',
  tools: [
    { key: 'bulb',  name: '提示', count: 3 },
    { key: 'hammer', name: '锤子', count: 2 },
    { key: 'bomb',  name: '炸弹', count: 1 },
  ],
};

// ---------- 调色（承接 Docs/DesignSystem.md §1 的角色分工） ----------
const C = {
  bgTop: '#FFFAF2', bgBottom: '#F1DEC2',
  tray: '#FFFCF6', traySide: '#E3CEAD',
  plate: '#EFDCC0',
  ink: '#3B2A24', ink2: '#6E5449',
  card: '#FFFCF5', cardSide: '#EADFCB',
  primary: '#4A2F26',
  go: '#1E8F68',
  bad: '#D93A4E',
  gold: '#E8A20C',
  groove: '#EBD6B8',
  arrow: '#FFFCF4',
};

const P = (px, py) => new THREE.Vector2(px - W / 2, H / 2 - py);   // 屏幕 → 世界

// ---------- 基础几何 ----------
function rrect(w, h, r, cx = 0, cy = 0) {
  const s = new THREE.Shape();
  const x = cx - w / 2, y = cy - h / 2;
  r = Math.min(r, w / 2, h / 2);
  s.moveTo(x + r, y);
  s.lineTo(x + w - r, y); s.quadraticCurveTo(x + w, y, x + w, y + r);
  s.lineTo(x + w, y + h - r); s.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  s.lineTo(x + r, y + h); s.quadraticCurveTo(x, y + h, x, y + h - r);
  s.lineTo(x, y + r); s.quadraticCurveTo(x, y, x + r, y);
  return s;
}

function circle(r, cx = 0, cy = 0) {
  const s = new THREE.Shape();
  s.absarc(cx, cy, r, 0, Math.PI * 2, false);
  return s;
}

function heartShape(s) {
  const k = s / 34;                       // 经典参数心形横向约 32 单位
  const p = new THREE.Shape();
  const N = 96;
  for (let i = 0; i <= N; i++) {
    const t = (i / N) * Math.PI * 2;
    const x = 16 * Math.pow(Math.sin(t), 3);
    const y = 13 * Math.cos(t) - 5 * Math.cos(2 * t) - 2 * Math.cos(3 * t) - Math.cos(4 * t);
    if (i === 0) p.moveTo(x * k, y * k); else p.lineTo(x * k, y * k);
  }
  p.closePath();
  return p;
}

// 朝上的箭头（之后整体旋转到目标方向）
function arrowShape(sz) {
  const sw = sz * 0.145, hw = sz * 0.33, tip = sz * 0.42, base = sz * 0.04, tail = -sz * 0.40;
  const p = new THREE.Shape();
  p.moveTo(0, tip);
  p.lineTo(hw, base);
  p.lineTo(sw, base);
  p.lineTo(sw, tail);
  p.lineTo(-sw, tail);
  p.lineTo(-sw, base);
  p.lineTo(-hw, base);
  p.closePath();
  return p;
}

// 多格足迹 → 圆角外轮廓（沿格线求边界环，向内收 g 留缝，再逐顶点倒圆）
function traceLoop(cells) {
  const key = (x, y) => `${x},${y}`;
  const set = new Set(cells.map(([c, r]) => key(c, r)));
  const has = (c, r) => set.has(key(c, r));
  const edges = [];
  for (const [c, r] of cells) {
    if (!has(c, r - 1)) edges.push([[c, r], [c + 1, r]]);
    if (!has(c + 1, r)) edges.push([[c + 1, r], [c + 1, r + 1]]);
    if (!has(c, r + 1)) edges.push([[c + 1, r + 1], [c, r + 1]]);
    if (!has(c - 1, r)) edges.push([[c, r + 1], [c, r]]);
  }
  const byStart = new Map();
  for (const e of edges) {
    const k = key(e[0][0], e[0][1]);
    if (!byStart.has(k)) byStart.set(k, []);
    byStart.get(k).push(e);
  }
  const used = new Set();
  const loop = [];
  let cur = edges[0][0];
  for (let guard = 0; guard < 400; guard++) {
    const cand = (byStart.get(key(cur[0], cur[1])) || []).filter(e => !used.has(e));
    if (!cand.length) break;
    const e = cand[0];
    used.add(e);
    loop.push(e[0]);
    cur = e[1];
    if (cur[0] === edges[0][0][0] && cur[1] === edges[0][0][1]) break;
  }
  return loop;
}

// 直角多边形的等距内缩：每条边沿内侧法线平移 g，再求相邻交点
function offsetLoop(pts, g) {
  const n = pts.length;
  let area = 0;
  for (let i = 0; i < n; i++) {
    const a = pts[i], b = pts[(i + 1) % n];
    area += a[0] * b[1] - b[0] * a[1];
  }
  const ccw = area > 0;
  const lines = [];
  for (let i = 0; i < n; i++) {
    const a = pts[i], b = pts[(i + 1) % n];
    let dx = b[0] - a[0], dy = b[1] - a[1];
    const L = Math.hypot(dx, dy); dx /= L; dy /= L;
    let nx = -dy, ny = dx;
    if (!ccw) { nx = -nx; ny = -ny; }
    lines.push({ px: a[0] + nx * g, py: a[1] + ny * g, dx, dy });
  }
  const out = [];
  for (let i = 0; i < n; i++) {
    const l1 = lines[(i - 1 + n) % n], l2 = lines[i];
    const det = l1.dx * l2.dy - l1.dy * l2.dx;
    if (Math.abs(det) < 1e-9) { out.push([l2.px, l2.py]); continue; }
    const t = ((l2.px - l1.px) * l2.dy - (l2.py - l1.py) * l2.dx) / det;
    out.push([l1.px + l1.dx * t, l1.py + l1.dy * t]);
  }
  return out;
}

function footprint(cells, cell, rad, gapPx = 0) {
  let loop = traceLoop(cells);
  if (gapPx > 0) loop = offsetLoop(loop, gapPx / cell);
  // 去掉共线点
  const pts = [];
  for (let i = 0; i < loop.length; i++) {
    const a = loop[(i - 1 + loop.length) % loop.length];
    const b = loop[i];
    const c = loop[(i + 1) % loop.length];
    const cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]);
    if (Math.abs(cross) > 1e-6) pts.push(b);
  }
  const shape = new THREE.Shape();
  const n = pts.length;
  for (let i = 0; i < n; i++) {
    const v = pts[i], pv = pts[(i - 1 + n) % n], nv = pts[(i + 1) % n];
    const ax = v[0] - pv[0], ay = v[1] - pv[1];
    const bx = nv[0] - v[0], by = nv[1] - v[1];
    const la = Math.hypot(ax, ay), lb = Math.hypot(bx, by);
    const rr = Math.min(rad / cell, la * 0.5, lb * 0.5);
    const p1 = [(v[0] - ax / la * rr) * cell, -(v[1] - ay / la * rr) * cell];
    const p2 = [(v[0] + bx / lb * rr) * cell, -(v[1] + by / lb * rr) * cell];
    const ctrl = [v[0] * cell, -v[1] * cell];
    if (i === 0) shape.moveTo(p1[0], p1[1]);
    else shape.lineTo(p1[0], p1[1]);
    shape.quadraticCurveTo(ctrl[0], ctrl[1], p2[0], p2[1]);
  }
  shape.closePath();
  return shape;
}

// ---------- 材质 ----------
const M = {};
function paint(hex, rough = 0.66, extra = {}) {
  return new THREE.MeshPhysicalMaterial({
    color: new THREE.Color(hex),
    roughness: rough, metalness: 0,
    clearcoat: 0.12, clearcoatRoughness: 0.72,
    envMapIntensity: 0.5,
    ...extra,
  });
}
function sideMat(hex, rough = 0.78) {
  return new THREE.MeshPhysicalMaterial({
    color: new THREE.Color(hex), roughness: rough, metalness: 0,
    envMapIntensity: 0.35,
  });
}

function slab(shape, depth, faceHex, sideHex, bevel = 5, opts = {}) {
  const g = new THREE.ExtrudeGeometry(shape, {
    depth, bevelEnabled: true,
    bevelThickness: bevel * 0.55, bevelSize: bevel * 0.9,
    bevelSegments: 3, curveSegments: 16,
  });
  const m = new THREE.Mesh(g, [paint(faceHex, opts.rough ?? 0.66), sideMat(sideHex ?? shade(faceHex, -0.1))]);
  m.castShadow = opts.cast !== false;
  m.receiveShadow = true;
  return m;
}

function shade(hex, amt) {
  const c = new THREE.Color(hex);
  const hsl = {}; c.getHSL(hsl);
  c.setHSL(hsl.h, hsl.s, THREE.MathUtils.clamp(hsl.l + amt, 0, 1));
  return '#' + c.getHexString();
}

// ---------- 场景 ----------
const canvas = document.getElementById('c');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(SS);
renderer.setSize(W, H, false);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.NoToneMapping;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const scene = new THREE.Scene();
const camera = new THREE.OrthographicCamera(-W / 2, W / 2, H / 2, -H / 2, -4000, 8000);
camera.position.set(0, 0, 3000);
camera.lookAt(0, 0, 0);

const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

// 光：主光在上偏右，投影落向左下；补光弱，模拟窗口漫射
const key = new THREE.DirectionalLight(0xFFF1D8, 1.5);
key.position.set(330, 880, 700);
key.target.position.set(0, 0, 0);
key.castShadow = true;
key.shadow.mapSize.set(2048, 2048);
const sc = key.shadow.camera;
sc.left = -760; sc.right = 760; sc.top = 1120; sc.bottom = -1120; sc.near = 200; sc.far = 3200;
key.shadow.radius = 5.5;
key.shadow.bias = -0.0009;
scene.add(key, key.target);

const fill = new THREE.DirectionalLight(0xE6EEFF, 0.42);
fill.position.set(-700, 220, 520);
scene.add(fill);

scene.add(new THREE.HemisphereLight(0xFFF8EC, 0xC8AE8E, 0.42));

// ---------- 背景板（渐变 + 极轻纸纹，同时接收阴影） ----------
function backdropTexture() {
  const s = 1024;
  const cv = document.createElement('canvas');
  cv.width = cv.height = s;
  const g = cv.getContext('2d');
  const rg = g.createRadialGradient(s * 0.5, s * 0.34, s * 0.05, s * 0.5, s * 0.45, s * 0.86);
  rg.addColorStop(0, C.bgTop);
  rg.addColorStop(0.62, '#FAEEDC');
  rg.addColorStop(1, C.bgBottom);
  g.fillStyle = rg; g.fillRect(0, 0, s, s);
  // 纸纹颗粒
  const img = g.getImageData(0, 0, s, s);
  for (let i = 0; i < img.data.length; i += 4) {
    const n = (Math.random() - 0.5) * 9;
    img.data[i] += n; img.data[i + 1] += n; img.data[i + 2] += n;
  }
  g.putImageData(img, 0, 0);
  const t = new THREE.CanvasTexture(cv);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
const back = new THREE.Mesh(
  new THREE.PlaneGeometry(W, H),
  new THREE.MeshBasicMaterial({ map: backdropTexture() })
);
back.position.z = -60;
back.receiveShadow = true;
scene.add(back);

// ---------- 棋盘托盘 + 底板 ----------
const TRAY = { x: 38, y: 296, w: 1004, h: 1004 };
const PLATE = 908;

const boardGroup = new THREE.Group();
const trayC = P(TRAY.x + TRAY.w / 2, TRAY.y + TRAY.h / 2);
boardGroup.position.set(trayC.x, trayC.y, 0);
boardGroup.rotation.x = TILT;
scene.add(boardGroup);

const tray = slab(rrect(TRAY.w, TRAY.h, 56), 22, C.tray, C.traySide, 9);
tray.position.z = -28;   // 挤出+倒角后前表面约在 +0.95
boardGroup.add(tray);

function plateTexture(px) {
  const s = px;
  const cv = document.createElement('canvas');
  cv.width = cv.height = s;
  const g = cv.getContext('2d');
  const k = s / 968;
  const r = 44 * k;
  const path = (inset) => {
    const x = inset, y = inset, w = s - inset * 2, h = s - inset * 2, rr = r - inset * 0.5;
    g.beginPath();
    g.moveTo(x + rr, y);
    g.arcTo(x + w, y, x + w, y + h, rr);
    g.arcTo(x + w, y + h, x, y + h, rr);
    g.arcTo(x, y + h, x, y, rr);
    g.arcTo(x, y, x + w, y, rr);
    g.closePath();
  };
  g.clearRect(0, 0, s, s);
  path(0); g.fillStyle = C.plate; g.fill();
  // 内阴影
  g.save();
  path(0); g.clip();
  g.shadowColor = 'rgba(112,78,44,0.46)';
  g.shadowBlur = 30 * k;
  g.lineWidth = 26 * k;
  path(14 * k); g.strokeStyle = 'rgba(120,86,50,0.10)'; g.stroke();
  g.restore();
  // 点阵底纹
  g.save();
  path(0); g.clip();
  const gap = 26 * k, rad = 1.9 * k;
  g.fillStyle = 'rgba(168,132,92,0.26)';
  for (let y = gap; y < s; y += gap) {
    for (let x = gap; x < s; x += gap) {
      g.beginPath(); g.arc(x, y, rad, 0, Math.PI * 2); g.fill();
    }
  }
  g.restore();
  const t = new THREE.CanvasTexture(cv);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  return t;
}

const plateSize = PLATE;
const plate = new THREE.Mesh(
  new THREE.PlaneGeometry(plateSize, plateSize),
  new THREE.MeshStandardMaterial({
    map: plateTexture(1200), roughness: 0.92, metalness: 0,
    transparent: true, envMapIntensity: 0.25,
  })
);
plate.position.z = 2.2;
plate.receiveShadow = true;
boardGroup.add(plate);

// ---------- 方块 ----------
const boardData = await fetch('../data/board.json').then(r => r.json());
CELL = Math.min(BOARD_BOX / boardData.cols, BOARD_BOX / boardData.rows);
const boardW = boardData.cols * CELL;
const boardH = boardData.rows * CELL;
const bx0 = -boardW / 2, by0 = boardH / 2;      // 棋盘左上（本地坐标）

const blockMats = {};
function blockMat(fam) {
  if (!blockMats[fam]) {
    const p = boardData.palette[fam];
    const boost = (c, k) => {
      const h = {}; c.getHSL(h);
      return new THREE.Color().setHSL(h.h, Math.min(1, h.s * k), Math.min(1, h.l * 1.02));
    };
    const face = boost(new THREE.Color(p.top).lerp(new THREE.Color(p.bottom), 0.44), 1.22);
    const side = boost(new THREE.Color(p.bottom).lerp(new THREE.Color(p.top), 0.05), 1.18).multiplyScalar(0.95);
    blockMats[fam] = [
      new THREE.MeshPhysicalMaterial({
        color: face, roughness: 0.58, metalness: 0,
        clearcoat: 0.14, clearcoatRoughness: 0.7, envMapIntensity: 0.45,
      }),
      new THREE.MeshPhysicalMaterial({
        color: side, roughness: 0.74, metalness: 0, envMapIntensity: 0.3,
      }),
    ];
  }
  return blockMats[fam];
}

const DIRS = { up: 0, right: -Math.PI / 2, down: Math.PI, left: Math.PI / 2 };
const DEPTH = 34;
const GAP = CELL * 0.045;

for (const b of boardData.blocks) {
  if (b.skip) continue;
  const shape = footprint(b.cells, CELL, CELL * 0.30, GAP);
  const g = new THREE.ExtrudeGeometry(shape, {
    depth: DEPTH, bevelEnabled: true,
    bevelThickness: 4.5, bevelSize: 3.6, bevelSegments: 3, curveSegments: 16,
  });
  const mesh = new THREE.Mesh(g, blockMat(b.family));
  mesh.position.set(bx0, by0, 3.2);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  boardGroup.add(mesh);

  // 箭头
  const [ac, ar] = b.arrow;
  const as = arrowShape(CELL * 0.60);
  const ag = new THREE.ExtrudeGeometry(as, {
    depth: 5, bevelEnabled: true, bevelThickness: 1.6, bevelSize: 1.4,
    bevelSegments: 2, curveSegments: 12,
  });
  const arrow = new THREE.Mesh(ag, paint(C.arrow, 0.72));
  arrow.position.set(bx0 + (ac + 0.5) * CELL, by0 - (ar + 0.5) * CELL, 3.2 + DEPTH + 1.2);
  arrow.rotation.z = DIRS[b.dir] ?? 0;
  arrow.castShadow = true;
  arrow.receiveShadow = true;
  boardGroup.add(arrow);
}

// ---------- HUD ----------
const hud = new THREE.Group();
scene.add(hud);

// 暂停键
const pauseC = P(96 + 48, 130 + 48);
const pauseBtn = slab(rrect(96, 96, 30), 12, C.card, C.cardSide, 6);
pauseBtn.position.set(pauseC.x, pauseC.y, 0);
hud.add(pauseBtn);
for (const dx of [-13, 13]) {
  const bar = slab(rrect(11, 38, 5), 6, C.ink, shade(C.ink, -0.05), 2.5);
  bar.position.set(pauseC.x + dx, pauseC.y, 12);
  hud.add(bar);
}

// 心
const heartSize = 58;
const heartGap = 14;
for (let i = 0; i < 3; i++) {
  const px = 1020 - (2 - i) * (heartSize + heartGap) - heartSize / 2;
  const w = P(px, 152);
  const hs = slab(heartShape(heartSize), 10, C.bad, shade(C.bad, -0.12), 4);
  hs.position.set(w.x, w.y + 4, 0);
  hs.scale.y = -1;
  hud.add(hs);
}

// 进度条
const PROG = { x1: 60, x2: 842, y: 252, h: 26 };
const progW = PROG.x2 - PROG.x1;
const trough = slab(rrect(progW + 8, PROG.h + 8, (PROG.h + 8) / 2), 6, C.groove, shade(C.groove, -0.1), 3);
const pc = P(PROG.x1 + progW / 2, PROG.y + PROG.h / 2);
trough.position.set(pc.x, pc.y, -2);
hud.add(trough);
const ratio = Math.max(0.06, boardData.cleared / boardData.total);
const fillBar = slab(rrect(progW * ratio, PROG.h, PROG.h / 2), 8, C.go, shade(C.go, -0.1), 3);
fillBar.position.set(pc.x - progW / 2 + progW * ratio / 2, pc.y, 2);
hud.add(fillBar);

// 工具卡
const cards = [];
const cardW = 300, cardH = 286, cardGap = 24;
const cardsTotalW = cardW * 3 + cardGap * 2;
const cardX0 = (W - cardsTotalW) / 2;
const cardY = 1452;
L.tools.forEach((t, i) => {
  const cx = cardX0 + i * (cardW + cardGap) + cardW / 2;
  const cc = P(cx, cardY + cardH / 2);
  const card = slab(rrect(cardW, cardH, 40), 16, C.card, C.cardSide, 8);
  card.position.set(cc.x, cc.y, 0);
  hud.add(card);
  cards.push({ x: cx, y: cardY + cardH / 2 });

  const iconG = new THREE.Group();
  iconG.position.set(cc.x, cc.y + 26, 16);
  hud.add(iconG);
  const s = 1.18;
  if (t.key === 'bulb') {
    const glass = slab(circle(46 * s), 10, '#F7C64B', '#D89B12', 4);
    glass.position.set(0, 18, 0); iconG.add(glass);
    const neck = slab(rrect(40 * s, 22, 7), 8, '#F0B93A', '#D08F0C', 3);
    neck.position.set(0, -30, 0); iconG.add(neck);
    const base = slab(rrect(34 * s, 12, 5), 7, '#B9A48F', '#9C8674', 3);
    base.position.set(0, -48, 0); iconG.add(base);
  } else if (t.key === 'hammer') {
    const handle = slab(rrect(18 * s, 84, 8), 9, '#C08A55', '#9B6A3B', 4);
    handle.position.set(-6, -22, 0); handle.rotation.z = 0.34; iconG.add(handle);
    const head = slab(rrect(78 * s, 40, 12), 14, '#9A8A7C', '#7A6B5F', 5);
    head.position.set(2, 26, 2); head.rotation.z = -0.1; iconG.add(head);
  } else {
    const body = slab(circle(44 * s), 12, '#5A463C', '#3F302A', 5);
    body.position.set(-4, -8, 0); iconG.add(body);
    const cap = slab(rrect(20 * s, 14, 5), 8, '#7C6656', '#5E4B3E', 3);
    cap.position.set(16, 32, 0); cap.rotation.z = 0.35; iconG.add(cap);
    const spark = slab(circle(11 * s, 0, 0), 6, '#F7C64B', '#D89B12', 3);
    spark.position.set(32, 44, 0); iconG.add(spark);
  }
});

// ---------- 文字层（DOM，原生排版，不进烘焙） ----------
const labelsEl = document.getElementById('labels');
function label(text, px, py, size, color, weight, ls = 0, shadow = true, align = 'center') {
  const d = document.createElement('div');
  d.className = 'lb';
  d.textContent = text;
  d.style.left = px + 'px';
  d.style.top = py + 'px';
  d.style.fontSize = size + 'px';
  d.style.fontWeight = weight;
  d.style.color = color;
  d.style.letterSpacing = ls + 'px';
  if (align === 'right') d.style.transform = 'translate(-100%,-50%)';
  if (shadow) d.style.textShadow = '0 2px 0 rgba(255,255,255,.55)';
  labelsEl.appendChild(d);
}

label(L.levelTitle, 540, 152, 54, C.ink, 800, 1.5);
label(L.levelSub, 540, 204, 27, C.ink2, 500, 3, false);
label('剩余 ' + (boardData.blocks.filter(b => !b.skip).length) + ' 块', 1022, 253, 30, C.ink2, 700, 0, false, 'right');
label(L.hint, 540, 1352, 28, C.ink2, 500, 1, false);
L.tools.forEach((t, i) => {
  label(t.count + '', cards[i].x - cardW / 2 + 56, cards[i].y - cardH / 2 + 56, 30, '#FFFFFF', 800, 0, false);
  label(t.name, cards[i].x, cards[i].y + 92, 33, C.ink, 700, 2);
});

// 工具卡角标
L.tools.forEach((t, i) => {
  const bx = cards[i].x - cardW / 2 + 56, by = cards[i].y - cardH / 2 + 56;
  const badge = slab(circle(33), 8, C.primary, shade(C.primary, -0.1), 3);
  const w = P(bx, by);
  badge.position.set(w.x, w.y, 22);
  hud.add(badge);
});

// ---------- 渲染 ----------
renderer.render(scene, camera);
requestAnimationFrame(() => { renderer.render(scene, camera); window.__ready = true; });

// ---- 调试：输出关键元素在屏幕上的包围盒（设计像素） ----
(function dbg() {
  const box = new THREE.Box3();
  const out = {};
  for (const [k, obj] of [['tray', tray], ['plate', plate]]) {
    box.setFromObject(obj);
    out[k] = { y: [Math.round(960 - box.max.y), Math.round(960 - box.min.y)],
               x: [Math.round(540 + box.min.x), Math.round(540 + box.max.x)] };
  }
  const grid = { x: [Math.round(540 + boardGroup.position.x + bx0),
                     Math.round(540 + boardGroup.position.x + bx0 + boardW)],
                 y: [Math.round(960 - (boardGroup.position.y + by0 * Math.cos(TILT))),
                     Math.round(960 - (boardGroup.position.y + (by0 - boardH) * Math.cos(TILT)))] };
  out.grid = grid;
  console.log('DBG ' + JSON.stringify(out));
})();
