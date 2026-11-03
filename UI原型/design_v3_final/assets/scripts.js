// BlockOut C方案 · 星形糖果可爱风 · 通用脚本
(function() {
  const TILE_COLORS = ['strawberry','orange','lemon','mint','grape','blueberry'];
  const ARROWS = { up:'↑', down:'↓', left:'←', right:'→' };

  // 星形 footprint：9列 x 11行，1=存在，0=空洞。轮廓带凹角，更像五角星。
  const DEFAULT_STAR = [
    [0,0,0,1,1,1,0,0,0],
    [0,0,1,1,1,1,1,0,0],
    [0,1,1,1,1,1,1,1,0],
    [1,1,1,0,1,0,1,1,1],
    [1,1,0,0,1,0,0,1,1],
    [1,1,1,1,1,1,1,1,1],
    [0,1,1,0,1,0,1,1,0],
    [0,0,1,1,1,1,1,0,0],
    [0,1,1,1,1,1,1,1,0],
    [1,1,1,0,1,0,1,1,1],
    [0,0,0,1,1,1,0,0,0]
  ];

  function rand(min, max){ return Math.random()*(max-min)+min; }
  function randInt(min, max){ return Math.floor(rand(min,max)); }
  function pick(arr){ return arr[Math.floor(Math.random()*arr.length)]; }

  window.BO = {
    DEFAULT_STAR: DEFAULT_STAR,

    renderBokeh: function(container, count=8){
      for(let i=0;i<count;i++){
        const el = document.createElement('div');
        el.className = 'bokeh';
        const size = randInt(40, 140);
        el.style.width = size+'px';
        el.style.height = size+'px';
        el.style.left = randInt(-20, 360)+'px';
        el.style.top = randInt(-20, 820)+'px';
        el.style.opacity = rand(0.12, 0.35);
        container.appendChild(el);
      }
    },

    renderDeco: function(container, types=['cupcake','blueberry','star','paw','candy'], count=5){
      for(let i=0;i<count;i++){
        const el = document.createElement('div');
        const type = pick(types);
        el.className = 'deco deco-'+type;
        el.style.left = randInt(10, 330)+'px';
        el.style.top = randInt(60, 740)+'px';
        el.style.opacity = rand(0.35, 0.65);
        el.style.transform = 'rotate('+randInt(-20,20)+'deg)';
        container.appendChild(el);
      }
    },

    renderHUD: function(container, opts={}){
      const hearts = opts.hearts!==undefined ? opts.hearts : 5;
      const coins = opts.coins || '3,000';
      const progress = opts.progress || 3;
      const pauseIcon = opts.pauseIcon || '<span style="font-weight:900; font-size:14px; color:var(--ink-primary)">II</span>';
      const html = `
        <div class="hud">
          <div class="hud-pill">
            <div class="btn-icon small" style="margin:-2px 0">${pauseIcon}</div>
            <div class="hud-icon">❤️</div>
            <span class="hud-text num">${hearts}</span>
            <div class="star-bar">
              ${[0,1,2,3,4].map(i=>`<div class="star-segment ${i<progress?'filled':''}"></div>`).join('')}
            </div>
          </div>
          <div class="hud-pill">
            <div class="hud-icon">🪙</div>
            <span class="hud-text num">${coins}</span>
          </div>
        </div>
      `;
      container.insertAdjacentHTML('beforeend', html);
    },

    renderStarBoard: function(container, opts={}){
      const tileSize = opts.tileSize || 30;
      const grid = opts.grid || DEFAULT_STAR;
      const colors = opts.colors || TILE_COLORS;
      const board = document.createElement('div');
      board.className = 'board';
      const rows = grid.length;
      const cols = grid[0].length;
      const boardW = cols * tileSize;
      const boardH = rows * tileSize;
      board.style.width = boardW+'px';
      board.style.height = boardH+'px';
      board.style.left = '50%';
      board.style.top = '50%';
      board.style.transform = 'translate(-50%, -50%)';

      grid.forEach((row, r)=>{
        row.forEach((cell, c)=>{
          if(!cell) return;
          const tile = document.createElement('div');
          const color = pick(colors);
          const dir = pick(Object.keys(ARROWS));
          tile.className = 'tile '+color;
          tile.style.width = tileSize+'px';
          tile.style.height = tileSize+'px';
          tile.style.left = (c*tileSize)+'px';
          tile.style.top = (r*tileSize)+'px';
          tile.style.fontSize = (tileSize*0.55)+'px';
          tile.textContent = ARROWS[dir];
          if(Math.random() < 0.18) tile.classList.add('fly');
          board.appendChild(tile);
        });
      });

      const base = document.createElement('div');
      base.className = 'board-base';
      base.style.width = (boardW*0.92)+'px';
      base.style.height = (boardH*0.92)+'px';
      container.insertBefore(base, container.firstChild);
      container.appendChild(board);
    },

    renderBanner: function(container, hidden=false){
      const el = document.createElement('div');
      el.className = 'banner-ad'+(hidden?' hidden':'');
      el.innerHTML = '<span>Banner Ad Placeholder · LevelPlay</span>';
      container.appendChild(el);
    },

    renderHint: function(container, text, withClose=true){
      const el = document.createElement('div');
      el.className = 'flex col center';
      el.style.cssText = 'position:absolute; bottom:76px; left:0; right:0;';
      el.innerHTML = `
        <div class="body" style="color:var(--ink-secondary); margin-bottom:8px;">${text}</div>
        ${withClose?'<div class="btn-close">✕</div>':''}
      `;
      container.appendChild(el);
    },

    initBackground: function(screenEl, opts={}){
      const bg = document.createElement('div');
      bg.className = 'bg';
      screenEl.appendChild(bg);
      const dots = document.createElement('div');
      dots.className = 'dots';
      screenEl.appendChild(dots);
      this.renderBokeh(screenEl, opts.bokeh||8);
      if(opts.deco!==false) this.renderDeco(screenEl, opts.decoTypes, opts.decoCount||5);
    }
  };
})();
