"""
PyMsi Game - 内置游戏模板库 (30+ 游戏)
========================================
用法:
    import PyMsi as PM
    PM.game.Grap("Snake")    # 启动贪吃蛇
    PM.game.list()            # 列出所有游戏

两行代码，即开即玩！
"""

import os
import sys
import tempfile
import webbrowser
import subprocess
from pathlib import Path

# ═══════════════════════════════════════════════════════════════
# 游戏模板 (全部是自包含的 HTML+JS+CSS)
# ═══════════════════════════════════════════════════════════════

_GAMES = {}

# ─── 1. 贪吃蛇 Snake ───────────────────────────────────────
_GAMES["Snake"] = r'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>贪吃蛇 Snake</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{background:#1a1a2e;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Arial;overflow:hidden;flex-direction:column}
canvas{border:2px solid #e94560;background:#16213e;border-radius:4px}
.info{color:#eee;margin-bottom:10px;font-size:20px;display:flex;gap:40px}
.info span{color:#e94560;font-weight:bold}
.msg{color:#0f3460;margin-top:10px;font-size:14px}</style></head><body>
<div class="info">得分: <span id="s">0</span> 最高: <span id="h">0</span></div>
<canvas id="c"></canvas>
<div class="msg">方向键移动 | 空格暂停 | R 重新开始</div>
<script>
const c=document.getElementById('c'),ctx=c.getContext('2d'),gs=20,TW=20,TH=20;
c.width=TW*gs;c.height=TH*gs;
let snake=[{x:10,y:10}],dir={x:1,y:0},food={},score=0,high=0,paused=0,gameOver=0,speed=100;
function placeFood(){do{food={x:Math.floor(Math.random()*TW),y:Math.floor(Math.random()*TH)}}while(snake.some(s=>s.x===food.x&&s.y===food.y))}
placeFood();
function draw(){ctx.fillStyle='#16213e';ctx.fillRect(0,0,c.width,c.height);
snake.forEach((s,i)=>{ctx.fillStyle=i===0?'#e94560':'#0f3460';ctx.fillRect(s.x*gs,s.y*gs,gs-2,gs-2)});
ctx.fillStyle='#f5c518';ctx.fillRect(food.x*gs,food.y*gs,gs-2,gs-2);
if(gameOver){ctx.fillStyle='rgba(0,0,0,0.7)';ctx.fillRect(0,0,c.width,c.height);
ctx.fillStyle='#fff';ctx.font='30px Arial';ctx.textAlign='center';ctx.fillText('游戏结束',c.width/2,c.height/2);ctx.font='16px Arial';ctx.fillText('按 R 重新开始',c.width/2,c.height/2+30)}}
function step(){if(paused||gameOver)return;const head={x:snake[0].x+dir.x,y:snake[0].y+dir.y};
if(head.x<0||head.x>=TW||head.y<0||head.y>=TH||snake.some(s=>s.x===head.x&&s.y===head.y)){gameOver=1;if(score>high){high=score;document.getElementById('h').textContent=high};return}
snake.unshift(head);if(head.x===food.x&&head.y===food.y){score+=10;document.getElementById('s').textContent=score;placeFood()}else{snake.pop()}}
setInterval(()=>{step();draw()},speed);
document.addEventListener('keydown',e=>{switch(e.key){case'ArrowUp':if(dir.y===0){dir={x:0,y:-1}}break;case'ArrowDown':if(dir.y===0){dir={x:0,y:1}}break;case'ArrowLeft':if(dir.x===0){dir={x:-1,y:0}}break;case'ArrowRight':if(dir.x===0){dir={x:1,y:0}}break;case' ':e.preventDefault();paused=!paused;break;case'r':case'R':snake=[{x:10,y:10}];dir={x:1,y:0};score=0;gameOver=0;paused=0;document.getElementById('s').textContent='0';placeFood();break}});
</script></body></html>'''

# ─── 2. 俄罗斯方块 Tetris ─────────────────────────────────
_GAMES["Tetris"] = r'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>俄罗斯方块 Tetris</title>
<style>*{margin:0;padding:0}body{background:#0a0a0a;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Arial;flex-direction:column}
canvas{border:2px solid #555;background:#111}
.info{color:#fff;margin-bottom:10px;font-size:18px;display:flex;gap:30px}
.info span{color:#0ff}</style></head><body>
<div class="info">得分: <span id="s">0</span> 行数: <span id="l">0</span> 等级: <span id="lv">1</span></div>
<canvas id="c"></canvas><div style="color:#555;margin-top:8px;font-size:12px">方向键移动 | 上键旋转 | 空格硬降 | P暂停</div>
<script>
const c=document.getElementById('c'),ctx=c.getContext('2d'),COLS=10,ROWS=20,BS=30;
c.width=COLS*BS;c.height=ROWS*BS;
const SHAPES=[[[1,1,1,1]],[[1,1],[1,1]],[[0,1,0],[1,1,1]],[[1,0,0],[1,1,1]],[[0,0,1],[1,1,1]],[[0,1,1],[1,1,0]],[[1,1,0],[0,1,1]]];
const COLORS=['#0ff','#ff0','#a0f','#0f0','#f00','#f80','#08f'];
let board=Array(ROWS).fill().map(()=>Array(COLS).fill(0)),piece,px,py,score=0,lines=0,level=1,paused=0,gameOver=0;
function spawn(){const idx=Math.floor(Math.random()*SHAPES.length);piece=SHAPES[idx];px=Math.floor((COLS-piece[0].length)/2);py=0;
if(!valid(px,py)){gameOver=1}}
function valid(x,y){for(let r=0;r<piece.length;r++)for(let c=0;c<piece[r].length;c++)if(piece[r][c]&&(x+c<0||x+c>=COLS||y+r>=ROWS||(y+r>=0&&board[y+r][x+c])))return 0;return 1}
function lock(){for(let r=0;r<piece.length;r++)for(let c=0;c<piece[r].length;c++)if(piece[r][c])board[py+r][px+c]=COLORS.indexOf(COLORS[SHAPES.indexOf(piece)])+1;
let cleared=0;for(let r=ROWS-1;r>=0;r--){if(board[r].every(v=>v)){board.splice(r,1);board.unshift(Array(COLS).fill(0));cleared++;r++}}
if(cleared){score+=[0,100,300,500,800][cleared]*level;lines+=cleared;level=Math.floor(lines/10)+1
document.getElementById('s').textContent=score;document.getElementById('l').textContent=lines;document.getElementById('lv').textContent=level}
spawn()}
function rotate(){const n=piece[0].map((_,i)=>piece.map(r=>r[i]).reverse());const old=piece;piece=n;if(!valid(px,py))piece=old}
function drop(){if(valid(px,py+1)){py++}else{lock()}}
function hardDrop(){while(valid(px,py+1))py++;lock()}
function draw(){ctx.fillStyle='#111';ctx.fillRect(0,0,c.width,c.height);
for(let r=0;r<ROWS;r++)for(let c2=0;c2<COLS;c2++){if(board[r][c2]){ctx.fillStyle=COLORS[board[r][c2]-1];ctx.fillRect(c2*BS,r*BS,BS-1,BS-1)}}
if(!gameOver)for(let r=0;r<piece.length;r++)for(let c2=0;c2<piece[r].length;c2++){if(piece[r][c2]){ctx.fillStyle=COLORS[SHAPES.indexOf(piece)];ctx.fillRect((px+c2)*BS,(py+r)*BS,BS-1,BS-1)}}
if(gameOver){ctx.fillStyle='rgba(0,0,0,0.7)';ctx.fillRect(0,0,c.width,c.height);ctx.fillStyle='#fff';ctx.font='28px Arial';ctx.textAlign='center';ctx.fillText('游戏结束',c.width/2,c.height/2);ctx.font='14px Arial';ctx.fillText('按 R 重新开始',c.width/2,c.height/2+30)}}
spawn();let dropInterval=800;let lastDrop=Date.now();
function loop(){const now=Date.now();if(!paused&&!gameOver&&now-lastDrop>dropInterval){drop();lastDrop=now;dropInterval=Math.max(100,800-level*50)}
draw();requestAnimationFrame(loop)}
document.addEventListener('keydown',e=>{if(gameOver&&e.key==='r'){board=Array(ROWS).fill().map(()=>Array(COLS).fill(0));score=0;lines=0;level=1;dropInterval=800;gameOver=0;document.getElementById('s').textContent='0';document.getElementById('l').textContent='0';document.getElementById('lv').textContent='1';spawn();return}
if(gameOver)return;switch(e.key){case'ArrowLeft':if(valid(px-1,py))px--;break;case'ArrowRight':if(valid(px+1,py))px++;break;case'ArrowDown':drop();break;case'ArrowUp':rotate();break;case' ':e.preventDefault();hardDrop();break;case'p':case'P':paused=!paused;break}});
loop();
</script></body></html>'''

# ─── 3. 扫雷 Minesweeper ──────────────────────────────────
_GAMES["Minesweeper"] = r'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>扫雷 Minesweeper</title>
<style>*{margin:0;padding:0}body{background:#1a1a2e;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Arial;flex-direction:column}
#board{display:grid;grid-template-columns:repeat(9,40px);gap:1px;background:#333;padding:2px;border-radius:4px}
.cell{width:40px;height:40px;background:#4a4a6a;display:flex;justify-content:center;align-items:center;font-weight:bold;font-size:16px;cursor:pointer;border-radius:3px;user-select:none}
.cell.revealed{background:#2a2a4a}.cell.mine{background:#e94560}
.info{color:#eee;margin-bottom:10px;font-size:18px;display:flex;gap:20px}
.info span{color:#e94560}button{background:#e94560;color:#fff;border:none;padding:8px 20px;border-radius:4px;cursor:pointer;margin-top:10px}</style></head><body>
<div class="info">💣 剩余: <span id="m">10</span> 🏆 最佳: <span id="b">-</span></div>
<div id="board"></div><button onclick="init()">🔄 新游戏</button>
<script>
const R=9,C=9,M=10;let board,mines,revealed,flagged,gameOver,best=null;
function init(){board=Array(R).fill().map(()=>Array(C).fill(0));revealed=Array(R).fill().map(()=>Array(C).fill(0));flagged=Array(R).fill().map(()=>Array(C).fill(0));gameOver=0;
mines=new Set();while(mines.size<M){const r=Math.floor(Math.random()*R),c=Math.floor(Math.random()*C);mines.add(r*C+c);board[r][c]=-1}
for(let r=0;r<R;r++)for(let c=0;c<C;c++){if(board[r][c]===-1)continue;let cnt=0;for(let dr=-1;dr<=1;dr++)for(let dc=-1;dc<=1;dc++){const nr=r+dr,nc=c+dc;if(nr>=0&&nr<R&&nc>=0&&nc<C&&board[nr][nc]===-1)cnt++}board[r][c]=cnt}
document.getElementById('m').textContent=M;render()}
function render(){const b=document.getElementById('board');b.innerHTML='';
for(let r=0;r<R;r++)for(let c=0;c<C;c++){const cell=document.createElement('div');cell.className='cell';cell.dataset.r=r;cell.dataset.c=c;
if(revealed[r][c]){cell.classList.add('revealed');if(board[r][c]===-1){cell.classList.add('mine');cell.textContent='💣'}else if(board[r][c]>0){cell.textContent=board[r][c];const colors=['','#0ff','#0f0','#f00','#08f','#800','#0f8','#000','#888'];cell.style.color=colors[board[r][c]]}}
else if(flagged[r][c]){cell.textContent='🚩'}
cell.addEventListener('click',e=>click(r,c));cell.addEventListener('contextmenu',e=>{e.preventDefault();flag(r,c)});b.appendChild(cell)}}
function click(r,c){if(gameOver||revealed[r][c]||flagged[r][c])return;
if(board[r][c]===-1){revealed[r][c]=1;gameOver=1;for(const m of mines){const mr=m/C|0,mc=m%C;revealed[mr][mc]=1}render();alert('💥 踩雷了！');return}
reveal(r,c);if(checkWin()){gameOver=1;const t=revealed.flat().filter(v=>v).length;if(!best||t<best){best=t;document.getElementById('b').textContent=best}render();setTimeout(()=>alert('🎉 你赢了！'),100)}render()}
function reveal(r,c){if(r<0||r>=R||c<0||c>=C||revealed[r][c]||flagged[r][c])return;revealed[r][c]=1;
if(board[r][c]===0){for(let dr=-1;dr<=1;dr++)for(let dc=-1;dc<=1;dc++)reveal(r+dr,c+dc)}}
function flag(r,c){if(gameOver||revealed[r][c])return;flagged[r][c]=!flagged[r][c];const cnt=flagged.flat().filter(v=>v).length;document.getElementById('m').textContent=M-cnt;render()}
function checkWin(){for(let r=0;r<R;r++)for(let c=0;c<C;c++)if(board[r][c]!==-1&&!revealed[r][c])return 0;return 1}
init();
</script></body></html>'''

# ─── 4. 2048 ──────────────────────────────────────────────
_GAMES["2048"] = r'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>2048</title>
<style>*{margin:0;padding:0}body{background:#faf8ef;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Arial;flex-direction:column}
h1{color:#776e65;font-size:48px;margin-bottom:10px}
.info{display:flex;gap:20px;margin-bottom:10px}
.score-box{background:#bbada0;color:#fff;padding:5px 15px;border-radius:4px;font-size:14px;text-align:center}
.score-box span{display:block;font-size:22px;font-weight:bold}
#board{display:grid;grid-template-columns:repeat(4,100px);gap:10px;background:#bbada0;padding:10px;border-radius:6px}
.tile{width:100px;height:100px;background:#cdc1b4;display:flex;justify-content:center;align-items:center;font-size:36px;font-weight:bold;border-radius:4px;color:#776e65;transition:all 0.1s}
button{background:#8f7a66;color:#fff;border:none;padding:10px 20px;border-radius:4px;font-size:16px;cursor:pointer;margin-top:10px}</style></head><body>
<h1>2048</h1><div class="info"><div class="score-box">得分<span id="s">0</span></div><div class="score-box">最高<span id="h">0</span></div></div>
<div id="board"></div><button onclick="init()">🔄 新游戏</button><div style="color:#aaa;margin-top:8px;font-size:12px">方向键移动</div>
<script>
let grid,score=0,high=0;
function init(){grid=Array(4).fill().map(()=>Array(4).fill(0));score=0;document.getElementById('s').textContent='0';spawn();spawn();render()}
function spawn(){const empty=[];for(let r=0;r<4;r++)for(let c=0;c<4;c++)if(!grid[r][c])empty.push({r,c});if(empty.length){const{ r,c }=empty[Math.floor(Math.random()*empty.length)];grid[r][c]=Math.random()<0.9?2:4}}
function render(){const b=document.getElementById('board');b.innerHTML='';const colors={0:'#cdc1b4',2:'#eee4da',4:'#ede0c8',8:'#f2b179',16:'#f59563',32:'#f67c5f',64:'#f65e3b',128:'#edcf72',256:'#edcc61',512:'#edc850',1024:'#edc53f',2048:'#edc22e',4096:'#3c3a32'};
for(let r=0;r<4;r++)for(let c=0;c<4;c++){const t=document.createElement('div');t.className='tile';const v=grid[r][c];t.textContent=v||'';t.style.background=colors[v]||'#3c3a32';if(v>=8)t.style.color='#fff';if(v>2048)t.style.fontSize='28px';b.appendChild(t)}}
function move(dir){let moved=0;const old=grid.map(r=>[...r]);
if(dir==='left'||dir==='right'){for(let r=0;r<4;r++){let row=grid[r].filter(v=>v);if(dir==='right')row.reverse();for(let i=0;i<row.length-1;i++){if(row[i]&&row[i]===row[i+1]){row[i]*=2;score+=row[i];row[i+1]=0}}row=row.filter(v=>v);while(row.length<4)dir==='left'?row.push(0):row.unshift(0);if(dir==='right')row.reverse();grid[r]=row}}
else{for(let c=0;c<4;c++){let col=[grid[0][c],grid[1][c],grid[2][c],grid[3][c]].filter(v=>v);if(dir==='down')col.reverse();for(let i=0;i<col.length-1;i++){if(col[i]&&col[i]===col[i+1]){col[i]*=2;score+=col[i];col[i+1]=0}}col=col.filter(v=>v);while(col.length<4)dir==='up'?col.push(0):col.unshift(0);if(dir==='down')col.reverse();for(let r=0;r<4;r++)grid[r][c]=col[r]}}
for(let r=0;r<4;r++)for(let c=0;c<4;c++)if(grid[r][c]!==old[r][c])moved=1;
if(moved){spawn();document.getElementById('s').textContent=score;if(score>high){high=score;document.getElementById('h').textContent=high}render();if(isGameOver()){setTimeout(()=>alert('游戏结束！'),200)}}}
function isGameOver(){for(let r=0;r<4;r++)for(let c=0;c<4;c++){if(!grid[r][c])return 0;if(c<3&&grid[r][c]===grid[r][c+1])return 0;if(r<3&&grid[r][c]===grid[r+1][c])return 0}return 1}
document.addEventListener('keydown',e=>{switch(e.key){case'ArrowUp':move('up');break;case'ArrowDown':move('down');break;case'ArrowLeft':move('left');break;case'ArrowRight':move('right');break}});
init();
</script></body></html>'''

# ─── 5. 打砖块 Breakout ──────────────────────────────────
_GAMES["Breakout"] = r'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>打砖块 Breakout</title>
<style>*{margin:0;padding:0}body{background:#0a0a0a;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Arial;flex-direction:column}
canvas{border:1px solid #333;background:#111}
.info{color:#fff;margin-bottom:8px;font-size:18px;display:flex;gap:30px}
.info span{color:#0ff}</style></head><body>
<div class="info">得分: <span id="s">0</span> 生命: <span id="l">3</span> 关卡: <span id="lv">1</span></div>
<canvas id="c"></canvas><div style="color:#555;margin-top:6px;font-size:12px">鼠标/方向键移动 | 空格开始</div>
<script>
const c=document.getElementById('c'),ctx=c.getContext('2d');
let W=480,H=500,paddle={w:80,h:12,x:200,y:470},ball={r:6,x:240,y:450,vx:3,vy:-3},bricks=[],score=0,lives=3,level=1,running=0;
function initBricks(){bricks=[];const rows=4+level,cols=8,bw=(W-20)/cols,bh=20;for(let r=0;r<rows;r++)for(let c2=0;c2<cols;c2++)bricks.push({x:10+c2*bw,y:40+r*bh,w:bw-2,h:bh-2,alive:1,color:`hsl(${r*40+c2*10},70%,${50+r*5}%)`})}
function draw(){ctx.fillStyle='#111';ctx.fillRect(0,0,W,H);ctx.fillStyle='#0ff';ctx.fillRect(paddle.x,paddle.y,paddle.w,paddle.h);
ctx.beginPath();ctx.arc(ball.x,ball.y,ball.r,0,Math.PI*2);ctx.fillStyle='#fff';ctx.fill();
bricks.forEach(b=>{if(b.alive){ctx.fillStyle=b.color;ctx.fillRect(b.x,b.y,b.w,b.h)}});
if(!running){ctx.fillStyle='#fff';ctx.font='18px Arial';ctx.textAlign='center';ctx.fillText('按空格键开始',W/2,H/2)}}
function update(){if(!running)return;ball.x+=ball.vx;ball.y+=ball.vy;
if(ball.x-ball.r<0||ball.x+ball.r>W)ball.vx*=-1;if(ball.y-ball.r<0)ball.vy*=-1;
if(ball.y+ball.r>H){lives--;document.getElementById('l').textContent=lives;if(lives<=0){alert('游戏结束！得分: '+score);initGame()}else{resetBall()}}
if(ball.y+ball.r>paddle.y&&ball.y-ball.r<paddle.y+paddle.h&&ball.x>paddle.x&&ball.x<paddle.x+paddle.w){ball.vy=-Math.abs(ball.vy);ball.vx+=(ball.x-(paddle.x+paddle.w/2))*0.15}
bricks.forEach(b=>{if(b.alive&&ball.x+ball.r>b.x&&ball.x-ball.r<b.x+b.w&&ball.y+ball.r>b.y&&ball.y-ball.r<b.y+b.h){b.alive=0;ball.vy*=-1;score+=10;document.getElementById('s').textContent=score;
if(bricks.every(b2=>!b2.alive)){level++;document.getElementById('lv').textContent=level;initBricks();resetBall()}}})}
function resetBall(){ball.x=paddle.x+paddle.w/2;ball.y=paddle.y-20;ball.vx=3+level;ball.vy=-(3+level);running=0}
function initGame(){score=0;lives=3;level=1;document.getElementById('s').textContent='0';document.getElementById('l').textContent='3';document.getElementById('lv').textContent='1';initBricks();resetBall()}
function loop(){update();draw();requestAnimationFrame(loop)}
c.addEventListener('mousemove',e=>{const rect=c.getBoundingClientRect();paddle.x=e.clientX-rect.left-paddle.w/2;paddle.x=Math.max(0,Math.min(W-paddle.w,paddle.x))});
document.addEventListener('keydown',e=>{if(e.key===' '){e.preventDefault();if(!running)running=1}
if(e.key==='ArrowLeft')paddle.x=Math.max(0,paddle.x-20);if(e.key==='ArrowRight')paddle.x=Math.min(W-paddle.w,paddle.x+20)});
initGame();loop();
</script></body></html>'''

# ─── 6. 弹球 Pong ─────────────────────────────────────────
_GAMES["Pong"] = r'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>弹球 Pong</title>
<style>*{margin:0;padding:0}body{background:#000;display:flex;justify-content:center;align-items:center;height:100vh;font-family:monospace;flex-direction:column}
canvas{border:1px solid #333}
.info{color:#fff;margin-bottom:8px;font-size:18px;display:flex;gap:40px}
.info span{color:#0f0}</style></head><body>
<div class="info">玩家: <span id="p1">0</span> 电脑: <span id="p2">0</span></div>
<canvas id="c"></canvas><div style="color:#555;margin-top:6px;font-size:12px">W/S 移动 | 空格开始</div>
<script>
const c=document.getElementById('c'),ctx=c.getContext('2d'),W=600,H=400;
let p1={x:20,y:160,w:10,h:80},p2={x:570,y:160,w:10,h:80},ball={x:300,y:200,r:6,vx:4,vy:2},s1=0,s2=0,running=0;
function draw(){ctx.fillStyle='#000';ctx.fillRect(0,0,W,H);for(let i=0;i<H;i+=20){ctx.fillStyle='#333';ctx.fillRect(W/2-1,i,2,10)}
ctx.fillStyle='#fff';ctx.fillRect(p1.x,p1.y,p1.w,p1.h);ctx.fillRect(p2.x,p2.y,p2.w,p2.h);ctx.beginPath();ctx.arc(ball.x,ball.y,ball.r,0,Math.PI*2);ctx.fill();
if(!running){ctx.fillStyle='#fff';ctx.font='16px monospace';ctx.textAlign='center';ctx.fillText('按空格键开始',W/2,H/2+40)}}
function update(){if(!running)return;ball.x+=ball.vx;ball.y+=ball.vy;
if(ball.y-ball.r<0||ball.y+ball.r>H)ball.vy*=-1;
if(ball.x-ball.r<p1.x+p1.w&&ball.y>p1.y&&ball.y<p1.y+p1.h){ball.vx=Math.abs(ball.vx);ball.vx+=0.2;ball.vy+=(ball.y-(p1.y+p1.h/2))*0.1}
if(ball.x+ball.r>p2.x&&ball.y>p2.y&&ball.y<p2.y+p2.h){ball.vx=-Math.abs(ball.vx);ball.vx-=0.2;ball.vy+=(ball.y-(p2.y+p2.h/2))*0.1}
if(ball.x<0){s2++;document.getElementById('p2').textContent=s2;reset()}if(ball.x>W){s1++;document.getElementById('p1').textContent=s1;reset()}
p2.y+=(ball.y-(p2.y+p2.h/2))*0.08}
function reset(){ball.x=W/2;ball.y=H/2;ball.vx=(Math.random()>0.5?1:-1)*4;ball.vy=(Math.random()-0.5)*6;running=0}
function loop(){update();draw();requestAnimationFrame(loop)}
document.addEventListener('keydown',e=>{if(e.key===' '){e.preventDefault();running=1}
if(e.key==='w'||e.key==='W')p1.y=Math.max(0,p1.y-15);if(e.key==='s'||e.key==='S')p1.y=Math.min(H-p1.h,p1.y+15)});
loop();
</script></body></html>'''

# ─── 7. 太空射击 Space Invaders ───────────────────────────
_GAMES["SpaceInvaders"] = r'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>太空射击 Space Invaders</title>
<style>*{margin:0;padding:0}body{background:#000;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Arial;flex-direction:column}
canvas{border:1px solid #333}
.info{color:#fff;margin-bottom:8px;font-size:18px;display:flex;gap:30px}
.info span{color:#f0f}</style></head><body>
<div class="info">得分: <span id="s">0</span> 生命: <span id="l">3</span> 波次: <span id="w">1</span></div>
<canvas id="c"></canvas><div style="color:#555;margin-top:6px;font-size:12px">方向键移动 | 空格射击 | P暂停</div>
<script>
const c=document.getElementById('c'),ctx=c.getContext('2d'),W=500,H=600;
let player={x:225,y:540,w:50,h:20},bullets=[],enemies=[],eBullets=[],score=0,lives=3,wave=1,paused=0,gameOver=0,dir=1,lastShot=0;
function spawnEnemies(){enemies=[];for(let r=0;r<4;r++)for(let c2=0;c2<8;c2++)enemies.push({x:60+c2*50,y:50+r*40,w:36,h:28,alive:1});dir=1}
function draw(){ctx.fillStyle='#000';ctx.fillRect(0,0,W,H);ctx.fillStyle='#0f0';ctx.fillRect(player.x,player.y,player.w,player.h);
bullets.forEach(b=>{ctx.fillStyle='#ff0';ctx.fillRect(b.x,b.y,3,10)});
eBullets.forEach(b=>{ctx.fillStyle='#f44';ctx.fillRect(b.x,b.y,3,10)});
enemies.forEach(e=>{if(e.alive){ctx.fillStyle='#f0f';ctx.fillRect(e.x,e.y,e.w,e.h)}});
if(gameOver){ctx.fillStyle='rgba(0,0,0,0.7)';ctx.fillRect(0,0,W,H);ctx.fillStyle='#fff';ctx.font='24px Arial';ctx.textAlign='center';ctx.fillText('游戏结束',W/2,H/2);ctx.font='14px Arial';ctx.fillText('按 R 重新开始',W/2,H/2+30)}}
function update(){if(paused||gameOver)return;
bullets.forEach(b=>b.y-=6);bullets=bullets.filter(b=>b.y>-10);
eBullets.forEach(b=>b.y+=3);eBullets=eBullets.filter(b=>b.y<H+10);
let edge=0;enemies.forEach(e=>{if(e.alive&&(e.x+e.w>=W-10||e.x<=10))edge=1});
if(edge){dir*=-1;enemies.forEach(e=>e.y+=15)}
enemies.forEach(e=>{if(e.alive){e.x+=dir*1.5;
if(Math.random()<0.003)eBullets.push({x:e.x+e.w/2,y:e.y+e.h})}});
bullets.forEach((b,bi)=>{enemies.forEach((e,ei)=>{if(e.alive&&b.x>e.x&&b.x<e.x+e.w&&b.y>e.y&&b.y<e.y+e.h){e.alive=0;bullets.splice(bi,1);score+=10*wave;document.getElementById('s').textContent=score}})});
eBullets.forEach((b,bi)=>{if(b.x>player.x&&b.x<player.x+player.w&&b.y+10>player.y&&b.y<player.y+player.h){eBullets.splice(bi,1);lives--;document.getElementById('l').textContent=lives;if(lives<=0)gameOver=1}});
if(enemies.every(e=>!e.alive)){wave++;document.getElementById('w').textContent=wave;spawnEnemies()}}
document.addEventListener('keydown',e=>{if(gameOver&&e.key==='r'){score=0;lives=3;wave=1;gameOver=0;document.getElementById('s').textContent='0';document.getElementById('l').textContent='3';document.getElementById('w').textContent='1';spawnEnemies();return}
if(e.key==='p'||e.key==='P')paused=!paused;if(e.key===' '){e.preventDefault();const now=Date.now();if(now-lastShot>200){bullets.push({x:player.x+player.w/2-1,y:player.y});lastShot=now}}});
let keys={};document.addEventListener('keydown',e=>keys[e.key]=1);document.addEventListener('keyup',e=>keys[e.key]=0);
function loop(){if(keys['ArrowLeft'])player.x=Math.max(0,player.x-4);if(keys['ArrowRight'])player.x=Math.min(W-player.w,player.x+4);update();draw();requestAnimationFrame(loop)}
spawnEnemies();loop();
</script></body></html>'''

# ─── 8. 五子棋 Gomoku ─────────────────────────────────────
_GAMES["Gomoku"] = r'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>五子棋 Gomoku</title>
<style>*{margin:0;padding:0}body{background:#deb887;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Arial;flex-direction:column}
canvas{cursor:pointer;border:2px solid #8b4513}
.info{color:#5c3317;margin-bottom:8px;font-size:20px;font-weight:bold}
.info span{color:#c00}button{background:#8b4513;color:#fff;border:none;padding:8px 20px;border-radius:4px;cursor:pointer;margin-top:8px}</style></head><body>
<div class="info">当前: <span id="t">⚫ 黑棋</span></div>
<canvas id="c"></canvas><button onclick="reset()">🔄 新游戏</button>
<script>
const c=document.getElementById('c'),ctx=c.getContext('2d'),S=15,CS=36,PAD=10;
c.width=S*CS+PAD*2;c.height=S*CS+PAD*2;
let board=Array(S).fill().map(()=>Array(S).fill(0)),turn=1,gameOver=0;
function draw(){ctx.fillStyle='#deb887';ctx.fillRect(0,0,c.width,c.height);
for(let i=0;i<S;i++){ctx.strokeStyle='#8b4513';ctx.beginPath();ctx.moveTo(PAD+CS/2,PAD+i*CS+CS/2);ctx.lineTo(PAD+(S-1)*CS+CS/2,PAD+i*CS+CS/2);ctx.stroke();ctx.beginPath();ctx.moveTo(PAD+i*CS+CS/2,PAD+CS/2);ctx.lineTo(PAD+i*CS+CS/2,PAD+(S-1)*CS+CS/2);ctx.stroke()}
for(let r=0;r<S;r++)for(let c2=0;c2<S;c2++){if(board[r][c2]){ctx.beginPath();ctx.arc(PAD+c2*CS+CS/2,PAD+r*CS+CS/2,CS/2-2,0,Math.PI*2);ctx.fillStyle=board[r][c2]===1?'#000':'#fff';ctx.fill();ctx.strokeStyle='#333';ctx.stroke()}}}
function check(r,c2){const dirs=[[0,1],[1,0],[1,1],[1,-1]];for(const[dr,dc]of dirs){let cnt=1;for(let i=1;i<5;i++){const nr=r+dr*i,nc=c2+dc*i;if(nr>=0&&nr<S&&nc>=0&&nc<S&&board[nr][nc]===board[r][c2])cnt++;else break}
for(let i=1;i<5;i++){const nr=r-dr*i,nc=c2-dc*i;if(nr>=0&&nr<S&&nc>=0&&nc<S&&board[nr][nc]===board[r][c2])cnt++;else break}if(cnt>=5)return 1}return 0}
c.addEventListener('click',e=>{if(gameOver)return;const rect=c.getBoundingClientRect();const x=e.clientX-rect.left-PAD,y=e.clientY-rect.top-PAD;const c2=Math.round(x/CS),r=Math.round(y/CS);
if(r<0||r>=S||c2<0||c2>=S||board[r][c2])return;board[r][c2]=turn;
if(check(r,c2)){gameOver=1;document.getElementById('t').textContent=(turn===1?'⚫ 黑棋':'⚪ 白棋')+' 获胜！';setTimeout(()=>alert('🎉 '+(turn===1?'黑棋':'白棋')+'获胜！'),100)}else{turn=turn===1?2:1;document.getElementById('t').textContent=turn===1?'⚫ 黑棋':'⚪ 白棋'}draw()});
function reset(){board=Array(S).fill().map(()=>Array(S).fill(0));turn=1;gameOver=0;document.getElementById('t').textContent='⚫ 黑棋';draw()}
draw();
</script></body></html>'''

# ─── 9. 井字棋 TicTacToe ──────────────────────────────────
_GAMES["TicTacToe"] = r'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>井字棋 Tic Tac Toe</title>
<style>*{margin:0;padding:0}body{background:#1a1a2e;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Arial;flex-direction:column}
h1{color:#e94560;margin-bottom:15px}
#board{display:grid;grid-template-columns:repeat(3,100px);gap:4px;background:#e94560;padding:4px;border-radius:8px}
.cell{width:100px;height:100px;background:#16213e;display:flex;justify-content:center;align-items:center;font-size:48px;font-weight:bold;cursor:pointer;color:#fff;border-radius:4px;transition:background 0.2s}
.cell:hover{background:#1a1a4e}
.info{color:#eee;margin-top:15px;font-size:18px}
button{background:#e94560;color:#fff;border:none;padding:8px 20px;border-radius:4px;cursor:pointer;margin-top:10px;font-size:14px}</style></head><body>
<h1>井字棋</h1><div id="board"></div><div class="info" id="msg">轮到: ❌</div><button onclick="reset()">🔄 新游戏</button>
<script>
let board,player,gameOver;
function reset(){board=Array(9).fill(0);player=1;gameOver=0;document.getElementById('msg').textContent='轮到: ❌';render()}
function render(){const b=document.getElementById('board');b.innerHTML='';board.forEach((v,i)=>{const c=document.createElement('div');c.className='cell';c.textContent=v===1?'❌':v===2?'⭕':'';c.addEventListener('click',()=>move(i));b.appendChild(c)})}
function move(i){if(gameOver||board[i])return;board[i]=player;
if(checkWin()){gameOver=1;document.getElementById('msg').textContent=(player===1?'❌':'⭕')+' 获胜！'}else if(board.every(v=>v)){gameOver=1;document.getElementById('msg').textContent='平局！'}else{player=player===1?2:1;document.getElementById('msg').textContent='轮到: '+(player===1?'❌':'⭕')}render()}
function checkWin(){const wins=[[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]];return wins.some(w=>board[w[0]]&&board[w[0]]===board[w[1]]&&board[w[1]]===board[w[2]])}
reset();
</script></body></html>'''

# ─── 10. 记忆翻牌 Memory ─────────────────────────────────
_GAMES["Memory"] = r'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>记忆翻牌 Memory</title>
<style>*{margin:0;padding:0}body{background:#1a1a2e;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Arial;flex-direction:column}
#board{display:grid;grid-template-columns:repeat(4,80px);gap:6px}
.card{width:80px;height:80px;background:#e94560;display:flex;justify-content:center;align-items:center;font-size:36px;cursor:pointer;border-radius:8px;transition:all 0.3s;user-select:none}
.card.flipped{background:#0f3460;transform:rotateY(180deg)}
.card.matched{background:#0f0;pointer-events:none}
.info{color:#eee;margin-bottom:10px;font-size:18px;display:flex;gap:30px}
.info span{color:#e94560}button{background:#e94560;color:#fff;border:none;padding:8px 20px;border-radius:4px;cursor:pointer;margin-top:10px}</style></head><body>
<div class="info">步数: <span id="m">0</span> 配对: <span id="p">0</span>/8</div>
<div id="board"></div><button onclick="init()">🔄 新游戏</button>
<script>
const emojis=['🐶','🐱','🐼','🐨','🦊','🐸','🐵','🦁'];let cards,flipped,matched,moves,locked;
function init(){cards=[...emojis,...emojis].sort(()=>Math.random()-0.5);flipped=[];matched=[];moves=0;locked=0;document.getElementById('m').textContent='0';document.getElementById('p').textContent='0';render()}
function render(){const b=document.getElementById('board');b.innerHTML='';cards.forEach((v,i)=>{const c=document.createElement('div');c.className='card';if(flipped.includes(i)||matched.includes(i)){c.classList.add('flipped');c.textContent=v}if(matched.includes(i))c.classList.add('matched');c.addEventListener('click',()=>flip(i));b.appendChild(c)})}
function flip(i){if(locked||flipped.includes(i)||matched.includes(i))return;flipped.push(i);moves++;document.getElementById('m').textContent=moves;
if(flipped.length===2){locked=1;if(cards[flipped[0]]===cards[flipped[1]]){matched.push(...flipped);flipped=[];locked=0;document.getElementById('p').textContent=matched.length/2;if(matched.length===cards.length)setTimeout(()=>alert('🎉 完成！用了 '+moves+' 步'),300)}else{setTimeout(()=>{flipped=[];locked=0;render()},600)}}render()}
init();
</script></body></html>'''

# ─── 11. 飞扬的小鸟 Flappy Bird ───────────────────────────
_GAMES["FlappyBird"] = r'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>飞扬的小鸟 Flappy Bird</title>
<style>*{margin:0;padding:0}body{background:#70c5ce;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Arial;flex-direction:column}
canvas{border:2px solid #000}
.info{color:#fff;margin-bottom:8px;font-size:20px;text-shadow:1px 1px 2px #000}
.info span{color:#ff0}</style></head><body>
<div class="info">得分: <span id="s">0</span></div>
<canvas id="c"></canvas><div style="color:#fff;margin-top:6px;font-size:14px;text-shadow:1px 1px 2px #000">空格/点击 跳跃</div>
<script>
const c=document.getElementById('c'),ctx=c.getContext('2d'),W=400,H=500;
let bird={x:80,y:250,r:15,vy:0},pipes=[],score=0,gameOver=0,started=0,frame=0;
function draw(){ctx.fillStyle='#70c5ce';ctx.fillRect(0,0,W,H);
ctx.fillStyle='#8B4513';ctx.fillRect(0,H-40,W,40);ctx.fillStyle='#2E8B57';ctx.fillRect(0,H-50,W,10);
ctx.fillStyle='#FFD700';ctx.beginPath();ctx.arc(bird.x,bird.y,bird.r,0,Math.PI*2);ctx.fill();ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(bird.x+5,bird.y-3,4,0,Math.PI*2);ctx.fill();ctx.fillStyle='#000';ctx.beginPath();ctx.arc(bird.x+7,bird.y-3,2,0,Math.PI*2);ctx.fill();
ctx.fillStyle='#FF6347';ctx.beginPath();ctx.moveTo(bird.x+12,bird.y);ctx.lineTo(bird.x+22,bird.y+2);ctx.lineTo(bird.x+12,bird.y+5);ctx.fill();
pipes.forEach(p=>{ctx.fillStyle='#228B22';ctx.fillRect(p.x,0,p.w,p.top);ctx.fillRect(p.x,p.top+p.gap,p.w,H-p.top-p.gap);ctx.fillStyle='#006400';ctx.fillRect(p.x-3,p.top-20,p.w+6,20);ctx.fillRect(p.x-3,p.top+p.gap,p.w+6,20)});
if(gameOver){ctx.fillStyle='rgba(0,0,0,0.5)';ctx.fillRect(0,0,W,H);ctx.fillStyle='#fff';ctx.font='30px Arial';ctx.textAlign='center';ctx.fillText('游戏结束',W/2,H/2);ctx.font='16px Arial';ctx.fillText('点击重新开始',W/2,H/2+30)}}
function update(){if(!started||gameOver)return;frame++;bird.vy+=0.4;bird.y+=bird.vy;
if(frame%90===0){const top=Math.random()*(H-200)+40;pipes.push({x:W,top:top,gap:140,w:50})}
pipes.forEach(p=>p.x-=2);pipes=pipes.filter(p=>p.x>-60);
if(bird.y+bird.r>H-40||bird.y-bird.r<0)endGame();
pipes.forEach(p=>{if(bird.x+bird.r>p.x&&bird.x-bird.r<p.x+p.w){if(bird.y-bird.r<p.top||bird.y+bird.r>p.top+p.gap)endGame()}
if(p.x+p.w<bird.x&&!p.passed){p.passed=1;score++;document.getElementById('s').textContent=score}})}
function endGame(){gameOver=1;started=0}
function jump(){bird.vy=-7;if(!started&&!gameOver){started=1;bird.y=250;bird.vy=0;pipes=[];score=0;document.getElementById('s').textContent='0'}}
document.addEventListener('keydown',e=>{if(e.key===' '){e.preventDefault();if(gameOver){gameOver=0;bird.y=250;bird.vy=0;pipes=[];score=0;document.getElementById('s').textContent='0'}jump()}});
c.addEventListener('click',()=>{if(gameOver){gameOver=0;bird.y=250;bird.vy=0;pipes=[];score=0;document.getElementById('s').textContent='0'}jump()});
function loop(){update();draw();requestAnimationFrame(loop)}
loop();
</script></body></html>'''

# ─── 12. 吃豆人 PacMan ────────────────────────────────────
_GAMES["PacMan"] = r'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>吃豆人 Pac-Man</title>
<style>*{margin:0;padding:0}body{background:#000;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Arial;flex-direction:column}
canvas{border:1px solid #2121de}
.info{color:#ff0;margin-bottom:8px;font-size:18px;display:flex;gap:30px}
.info span{color:#fff}</style></head><body>
<div class="info">得分: <span id="s">0</span> 生命: <span id="l">3</span></div>
<canvas id="c"></canvas><div style="color:#555;margin-top:6px;font-size:12px">方向键移动</div>
<script>
const c=document.getElementById('c'),ctx=c.getContext('2d'),GS=20,COLS=21,ROWS=21;
c.width=COLS*GS;c.height=ROWS*GS;
const MAP=[
[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],[1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1],[1,2,1,1,1,2,1,1,1,1,1,1,1,2,1,1,1,2,1,2,1],[1,2,1,2,2,2,1,2,2,2,2,2,1,2,2,2,1,2,1,2,1],[1,2,1,2,2,2,2,2,2,2,2,2,2,2,2,1,2,2,1,2,1],[1,2,2,2,2,1,2,2,2,2,2,2,2,2,1,2,2,2,2,2,1],[1,2,1,2,2,2,2,2,1,2,2,1,2,2,2,2,2,1,2,2,1],[1,2,2,2,1,2,2,2,1,2,2,1,2,2,2,1,2,2,2,2,1],[1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1],[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]];
let pac={x:10,y:8,dir:0,nextDir:0},dots=[],ghosts=[{x:9,y:8,dx:0,dy:-1,color:'#ffb8ff'},{x:10,y:8,dx:1,dy:0,color:'#00b8ff'}],score=0,lives=3,gameOver=0;
function initDots(){dots=[];for(let r=0;r<ROWS;r++)for(let c2=0;c2<COLS;c2++)if(MAP[r][c2]===2)dots.push({x:c2,y:r})}
function draw(){ctx.fillStyle='#000';ctx.fillRect(0,0,c.width,c.height);
for(let r=0;r<ROWS;r++)for(let c2=0;c2<COLS;c2++){if(MAP[r][c2]===1){ctx.fillStyle='#2121de';ctx.fillRect(c2*GS,r*GS,GS,GS)}}
dots.forEach(d=>{ctx.fillStyle='#ffb8ae';ctx.beginPath();ctx.arc(d.x*GS+GS/2,d.y*GS+GS/2,3,0,Math.PI*2);ctx.fill()});
ctx.fillStyle='#ff0';ctx.beginPath();ctx.arc(pac.x*GS+GS/2,pac.y*GS+GS/2,GS/2-1,pac.dir*0.2,(pac.dir+1)*0.2||Math.PI*2);ctx.lineTo(pac.x*GS+GS/2,pac.y*GS+GS/2);ctx.fill();
ghosts.forEach(g=>{ctx.fillStyle=g.color;ctx.beginPath();ctx.arc(g.x*GS+GS/2,g.y*GS+GS/2,GS/2-1,0,Math.PI*2);ctx.fill()});
if(gameOver){ctx.fillStyle='rgba(0,0,0,0.7)';ctx.fillRect(0,0,c.width,c.height);ctx.fillStyle='#ff0';ctx.font='24px Arial';ctx.textAlign='center';ctx.fillText('游戏结束',c.width/2,c.height/2);ctx.font='14px Arial';ctx.fillText('按 R 重新开始',c.width/2,c.height/2+30)}}
function canMove(x,y){return MAP[y][x]!==1}
function update(){if(gameOver)return;
if(pac.nextDir&&canMove(pac.x+(pac.nextDir===1?1:pac.nextDir===3?-1:0),pac.y+(pac.nextDir===2?1:pac.nextDir===0?-1:0))){pac.dir=pac.nextDir;pac.nextDir=0}
let nx=pac.x,ny=pac.y;switch(pac.dir){case 1:nx++;break;case 3:nx--;break;case 2:ny++;break;case 0:ny--;break}
if(canMove(nx,ny)){pac.x=nx;pac.y=ny}
const di=dots.findIndex(d=>d.x===pac.x&&d.y===pac.y);if(di>=0){dots.splice(di,1);score+=10;document.getElementById('s').textContent=score}
ghosts.forEach(g=>{const dirs=[[0,-1],[1,0],[0,1],[-1,0]];const valid=dirs.filter(d=>canMove(g.x+d[0],g.y+d[1]));if(valid.length){const d=valid[Math.floor(Math.random()*valid.length)];g.x+=d[0];g.y+=d[1];g.dx=d[0];g.dy=d[1]}});
ghosts.forEach(g=>{if(g.x===pac.x&&g.y===pac.y){lives--;document.getElementById('l').textContent=lives;if(lives<=0){gameOver=1}else{pac.x=10;pac.y=8;pac.dir=0;pac.nextDir=0}}});
if(dots.length===0){setTimeout(()=>alert('🎉 你赢了！'),200);gameOver=1}}
document.addEventListener('keydown',e=>{switch(e.key){case'ArrowUp':pac.nextDir=0;break;case'ArrowRight':pac.nextDir=1;break;case'ArrowDown':pac.nextDir=2;break;case'ArrowLeft':pac.nextDir=3;break;case'r':case'R':pac={x:10,y:8,dir:0,nextDir:0};ghosts=[{x:9,y:8,dx:0,dy:-1,color:'#ffb8ff'},{x:10,y:8,dx:1,dy:0,color:'#00b8ff'}];score=0;lives=3;gameOver=0;document.getElementById('s').textContent='0';document.getElementById('l').textContent='3';initDots();break}});
initDots();setInterval(update,150);setInterval(draw,50);
</script></body></html>'''

# ─── 13. 数独 Sudoku ──────────────────────────────────────
_GAMES["Sudoku"] = r'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>数独 Sudoku</title>
<style>*{margin:0;padding:0}body{background:#1a1a2e;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Arial;flex-direction:column}
h1{color:#e94560;margin-bottom:10px}
#board{display:grid;grid-template-columns:repeat(9,44px);gap:1px;background:#333;padding:2px;border-radius:4px}
.cell{width:44px;height:44px;background:#16213e;display:flex;justify-content:center;align-items:center;font-size:18px;font-weight:bold;color:#fff;cursor:pointer;border:none;text-align:center;outline:none}
.cell.given{color:#e94560}.cell:nth-child(3n){margin-right:2px}.cell:nth-child(9n+1){margin-left:2px}
.cell:nth-child(n+19):nth-child(-n+27){margin-bottom:2px}.cell:nth-child(n+46):nth-child(-n+54){margin-bottom:2px}
.info{color:#eee;margin-top:10px;font-size:14px}button{background:#e94560;color:#fff;border:none;padding:8px 20px;border-radius:4px;cursor:pointer;margin:4px;font-size:14px}</style></head><body>
<h1>数独</h1><div id="board"></div><div class="info" id="msg"></div><div><button onclick="newGame('easy')">简单</button><button onclick="newGame('medium')">中等</button><button onclick="newGame('hard')">困难</button></div>
<script>
const puzzles={easy:'530070000600195000098000060800060003400803001700020006060000280000419005000080079',medium:'000260701680070090190004500820100040004602900050003028009300074040050036703018000',hard:'800000000003600000070090200050007000000045700000100030001000068008500010090000400'};
let board,solution,given;
function newGame(lvl){const s=puzzles[lvl];board=s.split('').map(v=>parseInt(v)||0);given=board.map(v=>v!==0);solution=JSON.parse(JSON.stringify(board));solve(solution);render()}
function solve(grid){for(let r=0;r<9;r++)for(let c=0;c<9;c++){if(!grid[r][c]){for(let n=1;n<=9;n++){if(isValid(grid,r,c,n)){grid[r][c]=n;if(solve(grid))return 1;grid[r][c]=0}}return 0}}return 1}
function isValid(grid,r,c,n){for(let i=0;i<9;i++)if(grid[r][i]===n||grid[i][c]===n)return 0;const br=Math.floor(r/3)*3,bc=Math.floor(c/3)*3;for(let i=br;i<br+3;i++)for(let j=bc;j<bc+3;j++)if(grid[i][j]===n)return 0;return 1}
function render(){const b=document.getElementById('board');b.innerHTML='';board.forEach((v,i)=>{const inp=document.createElement('input');inp.className='cell';inp.maxLength=1;inp.value=v||'';if(given[i]){inp.classList.add('given');inp.readOnly=1}
inp.dataset.idx=i;inp.addEventListener('input',e=>{const val=parseInt(e.target.value)||0;if(val>=1&&val<=9){board[i]=val;if(checkComplete()){document.getElementById('msg').textContent='🎉 恭喜完成！'}}else{board[i]=0;e.target.value=''}e.target.value=board[i]||''});b.appendChild(inp)})}
function checkComplete(){for(let i=0;i<81;i++)if(!board[i])return 0;for(let r=0;r<9;r++){const row=[];for(let c=0;c<9;c++)row.push(board[r*9+c]);if(new Set(row).size!==9)return 0}
for(let c=0;c<9;c++){const col=[];for(let r=0;r<9;r++)col.push(board[r*9+c]);if(new Set(col).size!==9)return 0}
for(let br=0;br<3;br++)for(let bc=0;bc<3;bc++){const box=[];for(let r=br*3;r<br*3+3;r++)for(let c=bc*3;c<bc*3+3;c++)box.push(board[r*9+c]);if(new Set(box).size!==9)return 0}return 1}
newGame('easy');
</script></body></html>'''

# ─── 14. 颜色记忆 Simon Says ──────────────────────────────
_GAMES["SimonSays"] = r'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>颜色记忆 Simon Says</title>
<style>*{margin:0;padding:0}body{background:#1a1a2e;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Arial;flex-direction:column}
h1{color:#fff;margin-bottom:15px}
#board{display:grid;grid-template-columns:repeat(2,120px);gap:8px}
.btn{width:120px;height:120px;border-radius:12px;cursor:pointer;opacity:0.6;transition:all 0.15s}
.btn.active{opacity:1;transform:scale(1.05)}
.btn:nth-child(1){background:#f44}.btn:nth-child(2){background:#4f4}.btn:nth-child(3){background:#44f}.btn:nth-child(4){background:#ff4}
.info{color:#fff;margin-top:15px;font-size:20px}
.info span{color:#e94560}button{background:#e94560;color:#fff;border:none;padding:10px 24px;border-radius:4px;cursor:pointer;margin-top:10px;font-size:16px}</style></head><body>
<h1>🔴 Simon Says</h1><div id="board"><div class="btn" data-id="0"></div><div class="btn" data-id="1"></div><div class="btn" data-id="2"></div><div class="btn" data-id="3"></div></div>
<div class="info">得分: <span id="s">0</span> 最高: <span id="h">0</span></div><div class="info" id="msg" style="font-size:14px">观察颜色顺序...</div><button onclick="newGame()">🔄 新游戏</button>
<script>
let sequence=[],playerIdx=0,score=0,high=0,showing=0;
const btns=document.querySelectorAll('.btn');
function newGame(){sequence=[];playerIdx=0;score=0;showing=0;document.getElementById('s').textContent='0';addToSequence()}
function addToSequence(){sequence.push(Math.floor(Math.random()*4));playerIdx=0;showSequence()}
function showSequence(){showing=1;let i=0;document.getElementById('msg').textContent='观察颜色顺序...';const interval=setInterval(()=>{if(i>0)btns[sequence[i-1]].classList.remove('active');if(i>=sequence.length){clearInterval(interval);showing=0;document.getElementById('msg').textContent='轮到你了！';return}btns[sequence[i]].classList.add('active');i++},500)}
btns.forEach(b=>{b.addEventListener('click',()=>{if(showing)return;const id=parseInt(b.dataset.id);b.classList.add('active');setTimeout(()=>b.classList.remove('active'),200);
if(id===sequence[playerIdx]){playerIdx++;if(playerIdx>=sequence.length){score++;document.getElementById('s').textContent=score;if(score>high){high=score;document.getElementById('h').textContent=high}document.getElementById('msg').textContent='正确！下一个...';setTimeout(addToSequence,800)}}else{document.getElementById('msg').textContent='错误！游戏结束';if(score>high){high=score;document.getElementById('h').textContent=high}setTimeout(newGame,1500)}})});
newGame();
</script></body></html>'''

# ─── 15. 消消乐 Match3 ────────────────────────────────────
_GAMES["Match3"] = r'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>消消乐 Match 3</title>
<style>*{margin:0;padding:0}body{background:#1a1a2e;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Arial;flex-direction:column}
canvas{cursor:pointer;border-radius:8px}
.info{color:#fff;margin-bottom:8px;font-size:18px;display:flex;gap:30px}
.info span{color:#e94560}</style></head><body>
<div class="info">得分: <span id="s">0</span> 连击: <span id="c">0</span></div>
<canvas id="c"></canvas>
<script>
const c=document.getElementById('c'),ctx=c.getContext('2d'),R=8,C=8,CS=60;
c.width=C*CS;c.height=R*CS;
const COLORS=['#f44','#4f4','#44f','#ff4','#f4f','#4ff'];let grid,score=0,combo=0,sel=null;
function init(){grid=Array(R).fill().map(()=>Array(C).fill().map(()=>Math.floor(Math.random()*COLORS.length)));score=0;combo=0;document.getElementById('s').textContent='0';document.getElementById('c').textContent='0'}
function draw(){ctx.fillStyle='#1a1a2e';ctx.fillRect(0,0,c.width,c.height);
for(let r=0;r<R;r++)for(let c2=0;c2<C;c2++){ctx.fillStyle=COLORS[grid[r][c2]];ctx.beginPath();ctx.roundRect(c2*CS+3,r*CS+3,CS-6,CS-6,8);ctx.fill()}
if(sel){ctx.strokeStyle='#fff';ctx.lineWidth=3;ctx.beginPath();ctx.roundRect(sel.c*CS+2,sel.r*CS+2,CS-4,CS-4,8);ctx.stroke()}}
function findMatches(){const matches=[];for(let r=0;r<R;r++){let start=0;for(let c2=1;c2<=C;c2++){if(c2<C&&grid[r][c2]===grid[r][start])continue;if(c2-start>=3)for(let i=start;i<c2;i++)matches.push({r,c:i});start=c2}}
for(let c2=0;c2<C;c2++){let start=0;for(let r=1;r<=R;r++){if(r<R&&grid[r][c2]===grid[start][c2])continue;if(r-start>=3)for(let i=start;i<r;i++)matches.push({r:i,c:c2});start=r}}
return matches}
function removeMatches(){let matches=findMatches();let removed=0;while(matches.length>0){removed+=matches.length;const unique=new Set(matches.map(m=>m.r*C+m.c));unique.forEach(idx=>{grid[idx/C|0][idx%C]=-1});
for(let c2=0;c2<C;c2++){let wr=R-1;for(let r=R-1;r>=0;r--){if(grid[r][c2]!==-1){grid[wr][c2]=grid[r][c2];wr--}}for(let r=wr;r>=0;r--)grid[r][c2]=Math.floor(Math.random()*COLORS.length)}
matches=findMatches()}
if(removed>0){score+=removed*10;combo++;document.getElementById('s').textContent=score;document.getElementById('c').textContent=combo}return removed>0}
function swap(r1,c1,r2,c2){const t=grid[r1][c1];grid[r1][c1]=grid[r2][c2];grid[r2][c2]=t}
c.addEventListener('click',e=>{const rect=c.getBoundingClientRect();const c2=Math.floor((e.clientX-rect.left)/CS),r=Math.floor((e.clientY-rect.top)/CS);
if(!sel){sel={r,c2}}else{const dr=Math.abs(r-sel.r),dc=Math.abs(c2-sel.c);if((dr===1&&dc===0)||(dr===0&&dc===1)){swap(sel.r,sel.c,r,c2);if(!removeMatches()){swap(sel.r,sel.c,r,c2)}else{combo=0;document.getElementById('c').textContent='0'}}sel=null}draw()});
init();draw();
</script></body></html>'''

# ─── 16. 跳一跳 Doodle Jump ───────────────────────────────
_GAMES["DoodleJump"] = r'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>跳一跳 Doodle Jump</title>
<style>*{margin:0;padding:0}body{background:#f0f0f0;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Arial;flex-direction:column}
canvas{border:2px solid #ccc;background:#fff}
.info{color:#333;margin-bottom:8px;font-size:18px}
.info span{color:#e94560}</style></head><body>
<div class="info">得分: <span id="s">0</span> 最高: <span id="h">0</span></div>
<canvas id="c"></canvas><div style="color:#999;margin-top:6px;font-size:12px">方向键移动</div>
<script>
const c=document.getElementById('c'),ctx=c.getContext('2d'),W=400,H=600;
let player={x:180,y:300,w:40,h:40,vy:0},platforms=[],score=0,high=0,gameOver=0,camY=0,jumpCount=0;
function init(){platforms=[{x:160,y:550,w:80,h:12}];for(let i=0;i<8;i++)platforms.push({x:Math.random()*(W-80),y:400-i*70,w:80,h:12});player={x:180,y:300,w:40,h:40,vy:0};score=0;gameOver=0;camY=0;jumpCount=0;document.getElementById('s').textContent='0'}
function draw(){ctx.fillStyle='#fff';ctx.fillRect(0,0,W,H);
platforms.forEach(p=>{const y=p.y-camY;if(y>-20&&y<H+20){ctx.fillStyle='#4a4';ctx.fillRect(p.x,y,p.w,p.h)}});
ctx.fillStyle='#e94560';ctx.fillRect(player.x,player.y-camY,player.w,player.h);
ctx.fillStyle='#fff';ctx.fillRect(player.x+10,player.y-camY+8,6,6);ctx.fillRect(player.x+24,player.y-camY+8,6,6);
ctx.fillStyle='#000';ctx.fillRect(player.x+12,player.y-camY+10,3,3);ctx.fillRect(player.x+26,player.y-camY+10,3,3);
if(gameOver){ctx.fillStyle='rgba(0,0,0,0.5)';ctx.fillRect(0,0,W,H);ctx.fillStyle='#fff';ctx.font='24px Arial';ctx.textAlign='center';ctx.fillText('游戏结束',W/2,H/2);ctx.font='14px Arial';ctx.fillText('点击重新开始',W/2,H/2+30)}}
function update(){if(gameOver)return;player.vy+=0.5;player.y+=player.vy;
platforms.forEach(p=>{if(player.vy>0&&player.y+player.h>p.y&&player.y+player.h<p.y+p.h+10&&player.y<p.y+p.h&&player.x+player.w>p.x&&player.x<p.x+p.w){player.vy=-10;jumpCount++;score+=10;document.getElementById('s').textContent=score;if(score>high){high=score;document.getElementById('h').textContent=high}}});
if(player.y-camY<H/3)camY=player.y-H/3;
while(platforms[platforms.length-1].y-camY>-50){platforms.push({x:Math.random()*(W-80),y:platforms[platforms.length-1].y-70,w:80,h:12})}
platforms=platforms.filter(p=>p.y-camY<H+50);
if(player.y-camY>H){gameOver=1;if(score>high){high=score;document.getElementById('h').textContent=high}}}
document.addEventListener('keydown',e=>{if(e.key==='ArrowLeft')player.x-=8;if(e.key==='ArrowRight')player.x+=8;player.x=Math.max(0,Math.min(W-player.w,player.x))});
c.addEventListener('click',()=>{if(gameOver)init()});
function loop(){update();draw();requestAnimationFrame(loop)}
init();loop();
</script></body></html>'''

# ─── 17. 乒乓球 Ping Pong ─────────────────────────────────
_GAMES["PingPong"] = r'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>乒乓球 Ping Pong</title>
<style>*{margin:0;padding:0}body{background:#0a4a0a;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Arial;flex-direction:column}
canvas{background:#0a2a0a;border:2px solid #fff}
.info{color:#fff;margin-bottom:8px;font-size:18px;display:flex;gap:40px}
.info span{color:#0f0}</style></head><body>
<div class="info">玩家1: <span id="p1">0</span> 玩家2: <span id="p2">0</span></div>
<canvas id="c"></canvas><div style="color:#fff;margin-top:6px;font-size:12px">玩家1: W/S | 玩家2: 方向键上下</div>
<script>
const c=document.getElementById('c'),ctx=c.getContext('2d'),W=600,H=400;
let p1={x:20,y:160,w:10,h:80},p2={x:570,y:160,w:10,h:80},ball={x:300,y:200,r:6,vx:4,vy:3},s1=0,s2=0,running=0;
function draw(){ctx.fillStyle='#0a2a0a';ctx.fillRect(0,0,W,H);for(let i=0;i<H;i+=20){ctx.fillStyle='#fff';ctx.fillRect(W/2-1,i,2,10)}
ctx.fillStyle='#fff';ctx.fillRect(p1.x,p1.y,p1.w,p1.h);ctx.fillRect(p2.x,p2.y,p2.w,p2.h);ctx.beginPath();ctx.arc(ball.x,ball.y,ball.r,0,Math.PI*2);ctx.fill();
if(!running){ctx.fillStyle='#fff';ctx.font='16px Arial';ctx.textAlign='center';ctx.fillText('按空格键开始',W/2,H/2+40)}}
function update(){if(!running)return;ball.x+=ball.vx;ball.y+=ball.vy;
if(ball.y-ball.r<0||ball.y+ball.r>H){ball.vy*=-1;ball.y=Math.max(ball.r,Math.min(H-ball.r,ball.y))}
if(ball.x-ball.r<p1.x+p1.w&&ball.y>p1.y&&ball.y<p1.y+p1.h){ball.vx=Math.abs(ball.vx);ball.vx+=0.3;ball.vy+=(ball.y-(p1.y+p1.h/2))*0.15}
if(ball.x+ball.r>p2.x&&ball.y>p2.y&&ball.y<p2.y+p2.h){ball.vx=-Math.abs(ball.vx);ball.vx-=0.3;ball.vy+=(ball.y-(p2.y+p2.h/2))*0.15}
if(ball.x<0){s2++;document.getElementById('p2').textContent=s2;reset()}if(ball.x>W){s1++;document.getElementById('p1').textContent=s1;reset()}}
function reset(){ball.x=W/2;ball.y=H/2;ball.vx=(Math.random()>0.5?1:-1)*4;ball.vy=(Math.random()-0.5)*6;running=0}
let keys={};document.addEventListener('keydown',e=>{keys[e.key]=1;if(e.key===' '){e.preventDefault();running=1}});document.addEventListener('keyup',e=>keys[e.key]=0);
function loop(){if(keys['w']||keys['W'])p1.y=Math.max(0,p1.y-6);if(keys['s']||keys['S'])p1.y=Math.min(H-p1.h,p1.y+6);if(keys['ArrowUp'])p2.y=Math.max(0,p2.y-6);if(keys['ArrowDown'])p2.y=Math.min(H-p2.h,p2.y+6);update();draw();requestAnimationFrame(loop)}
loop();
</script></body></html>'''

# ─── 18. 打地鼠 Whack a Mole ──────────────────────────────
_GAMES["WhackMole"] = r'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>打地鼠 Whack-a-Mole</title>
<style>*{margin:0;padding:0}body{background:#8B4513;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Arial;flex-direction:column}
h1{color:#FFD700;margin-bottom:10px;text-shadow:2px 2px 4px #000}
#board{display:grid;grid-template-columns:repeat(3,100px);gap:8px}
.hole{width:100px;height:100px;background:#5C3317;border-radius:50%;display:flex;justify-content:center;align-items:center;cursor:pointer;overflow:hidden;position:relative}
.mole{width:70px;height:70px;background:#8B6914;border-radius:50%;position:absolute;bottom:-70px;transition:bottom 0.1s;font-size:36px;display:flex;justify-content:center;align-items:center}
.mole.up{bottom:10px}
.info{color:#fff;margin-top:10px;font-size:20px;display:flex;gap:30px;text-shadow:1px 1px 2px #000}
.info span{color:#FFD700}button{background:#FFD700;color:#5C3317;border:none;padding:10px 24px;border-radius:4px;cursor:pointer;margin-top:10px;font-size:16px;font-weight:bold}</style></head><body>
<h1>🔨 打地鼠</h1><div id="board"></div>
<div class="info">得分: <span id="s">0</span> 时间: <span id="t">30</span>s</div><button onclick="startGame()">开始游戏</button>
<script>
let score=0,time=30,active=null,gameRunning=0,timer;
const holes=document.querySelectorAll('.hole');
function startGame(){score=0;time=30;gameRunning=1;document.getElementById('s').textContent='0';document.getElementById('t').textContent=time;holes.forEach(h=>{h.innerHTML='<div class="mole">🐹</div>'});timer=setInterval(()=>{time--;document.getElementById('t').textContent=time;if(time<=0)endGame()},1000);spawnMole()}
function endGame(){gameRunning=0;clearInterval(timer);holes.forEach(h=>{const m=h.querySelector('.mole');if(m)m.classList.remove('up')});setTimeout(()=>alert('游戏结束！得分: '+score),200)}
function spawnMole(){if(!gameRunning)return;holes.forEach(h=>{const m=h.querySelector('.mole');m.classList.remove('up')});const idx=Math.floor(Math.random()*9);const m=holes[idx].querySelector('.mole');m.classList.add('up');setTimeout(spawnMole,500+Math.random()*800)}
holes.forEach(h=>{h.addEventListener('click',()=>{if(!gameRunning)return;const m=h.querySelector('.mole');if(m.classList.contains('up')){m.classList.remove('up');score++;document.getElementById('s').textContent=score}})});
</script></body></html>'''

# ─── 19. 滑块拼图 Sliding Puzzle ─────────────────────────
_GAMES["SlidingPuzzle"] = r'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>滑块拼图 Sliding Puzzle</title>
<style>*{margin:0;padding:0}body{background:#1a1a2e;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Arial;flex-direction:column}
#board{display:grid;grid-template-columns:repeat(4,80px);gap:3px;background:#333;padding:3px;border-radius:8px}
.tile{width:80px;height:80px;background:#e94560;display:flex;justify-content:center;align-items:center;font-size:28px;font-weight:bold;color:#fff;cursor:pointer;border-radius:6px;transition:all 0.15s;user-select:none}
.tile.empty{background:transparent;pointer-events:none}
.info{color:#eee;margin-bottom:10px;font-size:18px}
.info span{color:#e94560}button{background:#e94560;color:#fff;border:none;padding:8px 20px;border-radius:4px;cursor:pointer;margin-top:10px}</style></head><body>
<div class="info">步数: <span id="m">0</span></div><div id="board"></div><button onclick="init()">🔄 新游戏</button>
<script>
let board,moves;
function init(){board=Array.from({length:15},(_,i)=>i+1);board.push(0);for(let i=board.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[board[i],board[j]]=[board[j],board[i]]}moves=0;document.getElementById('m').textContent='0';render()}
function render(){const b=document.getElementById('board');b.innerHTML='';board.forEach((v,i)=>{const t=document.createElement('div');t.className='tile'+(v===0?' empty':'');t.textContent=v||'';t.addEventListener('click',()=>move(i));b.appendChild(t)})}
function move(i){if(board[i]===0)return;const empty=board.indexOf(0);const er=empty/4|0,ec=empty%4,tr=i/4|0,tc=i%4;if(Math.abs(er-tr)+Math.abs(ec-tc)===1){[board[i],board[empty]]=[board[empty],board[i]];moves++;document.getElementById('m').textContent=moves;render();if(isSolved())setTimeout(()=>alert('🎉 完成！用了 '+moves+' 步'),200)}}
function isSolved(){for(let i=0;i<15;i++)if(board[i]!==i+1)return 0;return board[15]===0}
init();
</script></body></html>'''

# ─── 20. 迷宫 Maze ─────────────────────────────────────────
_GAMES["Maze"] = r'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>迷宫 Maze</title>
<style>*{margin:0;padding:0}body{background:#1a1a2e;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Arial;flex-direction:column}
canvas{border:2px solid #e94560}
.info{color:#fff;margin-bottom:8px;font-size:18px;display:flex;gap:30px}
.info span{color:#e94560}button{background:#e94560;color:#fff;border:none;padding:8px 20px;border-radius:4px;cursor:pointer;margin-top:8px}</style></head><body>
<div class="info">步数: <span id="s">0</span> 时间: <span id="t">0</span>s</div>
<canvas id="c"></canvas><button onclick="gen()">🔄 新迷宫</button><div style="color:#555;margin-top:6px;font-size:12px">方向键移动</div>
<script>
const c=document.getElementById('c'),ctx=c.getContext('2d'),S=21,CS=20;
c.width=S*CS;c.height=S*CS;
let maze,player={x:1,y:1},steps=0,sec=0,started=0,timer;
function gen(){maze=Array(S).fill().map(()=>Array(S).fill(1));const stack=[],visited=new Set();player.x=1;player.y=1;maze[1][1]=0;visited.add('1,1');stack.push({x:1,y:1});
while(stack.length){const cur=stack[stack.length-1];const dirs=[[0,-2],[2,0],[0,2],[-2,0]].sort(()=>Math.random()-0.5);let moved=0;
for(const[dx,dy]of dirs){const nx=cur.x+dx,ny=cur.y+dy;if(nx>0&&nx<S-1&&ny>0&&ny<S-1&&!visited.has(nx+','+ny)){maze[ny][nx]=0;maze[cur.y+dy/2][cur.x+dx/2]=0;visited.add(nx+','+ny);stack.push({x:nx,y:ny});moved=1;break}}
if(!moved)stack.pop()}
maze[S-2][S-2]=0;steps=0;sec=0;started=0;document.getElementById('s').textContent='0';document.getElementById('t').textContent='0';if(timer)clearInterval(timer);draw()}
function draw(){ctx.fillStyle='#16213e';ctx.fillRect(0,0,c.width,c.height);
for(let r=0;r<S;r++)for(let c2=0;c2<S;c2++){if(maze[r][c2]){ctx.fillStyle='#333';ctx.fillRect(c2*CS,r*CS,CS,CS)}}
ctx.fillStyle='#0f0';ctx.fillRect((S-2)*CS+2,(S-2)*CS+2,CS-4,CS-4);ctx.fillStyle='#e94560';ctx.fillRect(player.x*CS+4,player.y*CS+4,CS-8,CS-8)}
function move(dx,dy){if(!started){started=1;timer=setInterval(()=>{sec++;document.getElementById('t').textContent=sec},1000)}
const nx=player.x+dx,ny=player.y+dy;if(nx>=0&&nx<S&&ny>=0&&ny<S&&!maze[ny][nx]){player.x=nx;player.y=ny;steps++;document.getElementById('s').textContent=steps;if(player.x===S-2&&player.y===S-2){clearInterval(timer);setTimeout(()=>alert('🎉 完成！'+steps+'步 '+sec+'秒'),200)}}draw()}
document.addEventListener('keydown',e=>{switch(e.key){case'ArrowUp':move(0,-1);break;case'ArrowDown':move(0,1);break;case'ArrowLeft':move(-1,0);break;case'ArrowRight':move(1,0);break}});
gen();
</script></body></html>'''

# ─── 21. 四子棋 Connect Four ──────────────────────────────
_GAMES["ConnectFour"] = r'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>四子棋 Connect Four</title>
<style>*{margin:0;padding:0}body{background:#1a1a2e;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Arial;flex-direction:column}
h1{color:#fff;margin-bottom:10px}
#board{display:grid;grid-template-columns:repeat(7,60px);gap:4px;background:#224;padding:6px;border-radius:8px}
.cell{width:60px;height:60px;background:#16213e;border-radius:50%;cursor:pointer;transition:background 0.2s}
.cell.p1{background:#e94560}.cell.p2{background:#ffd700}
.info{color:#fff;margin-top:10px;font-size:18px}button{background:#e94560;color:#fff;border:none;padding:8px 20px;border-radius:4px;cursor:pointer;margin-top:8px}</style></head><body>
<h1>四子棋</h1><div id="board"></div><div class="info" id="msg">轮到: 🔴 红色</div><button onclick="reset()">🔄 新游戏</button>
<script>
let grid,player,gameOver;
function reset(){grid=Array(6).fill().map(()=>Array(7).fill(0));player=1;gameOver=0;document.getElementById('msg').textContent='轮到: 🔴 红色';render()}
function render(){const b=document.getElementById('board');b.innerHTML='';for(let r=0;r<6;r++)for(let c=0;c<7;c++){const cell=document.createElement('div');cell.className='cell';if(grid[r][c]===1)cell.classList.add('p1');if(grid[r][c]===2)cell.classList.add('p2');cell.addEventListener('click',()=>drop(c));b.appendChild(cell)}}
function drop(c){if(gameOver)return;for(let r=5;r>=0;r--){if(!grid[r][c]){grid[r][c]=player;if(checkWin(r,c)){gameOver=1;document.getElementById('msg').textContent='🎉 '+(player===1?'🔴 红色':'🟡 黄色')+'获胜！'}else if(grid[0].every(v=>v)){gameOver=1;document.getElementById('msg').textContent='平局！'}else{player=player===1?2:1;document.getElementById('msg').textContent='轮到: '+(player===1?'🔴 红色':'🟡 黄色')}render();return}}}
function checkWin(r,c){const dirs=[[0,1],[1,0],[1,1],[1,-1]];for(const[dr,dc]of dirs){let cnt=1;for(let i=1;i<4;i++){const nr=r+dr*i,nc=c+dc*i;if(nr>=0&&nr<6&&nc>=0&&nc<7&&grid[nr][nc]===player)cnt++;else break}for(let i=1;i<4;i++){const nr=r-dr*i,nc=c-dc*i;if(nr>=0&&nr<6&&nc>=0&&nc<7&&grid[nr][nc]===player)cnt++;else break}if(cnt>=4)return 1}return 0}
reset();
</script></body></html>'''

# ─── 22. 弹球打砖 Brick Breaker ───────────────────────────
_GAMES["BrickBreaker"] = r'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>弹球打砖 Brick Breaker</title>
<style>*{margin:0;padding:0}body{background:#0a0a0a;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Arial;flex-direction:column}
canvas{border:1px solid #333;background:#111}
.info{color:#fff;margin-bottom:8px;font-size:18px;display:flex;gap:30px}
.info span{color:#0ff}</style></head><body>
<div class="info">得分: <span id="s">0</span> 生命: <span id="l">3</span></div>
<canvas id="c"></canvas><div style="color:#555;margin-top:6px;font-size:12px">鼠标移动 | 点击开始</div>
<script>
const c=document.getElementById('c'),ctx=c.getContext('2d'),W=480,H=550;
let paddle={w:90,h:12,x:195,y:500},ball={x:240,y:480,r:6,vx:3,vy:-3},bricks=[],score=0,lives=3,running=0;
function initBricks(){bricks=[];const colors=['#e94560','#ff6b6b','#ffd93d','#6bcb77','#4d96ff'];for(let r=0;r<5;r++)for(let c2=0;c2<8;c2++)bricks.push({x:10+c2*58,y:50+r*25,w:54,h:21,alive:1,color:colors[r]})}
function draw(){ctx.fillStyle='#111';ctx.fillRect(0,0,W,H);ctx.fillStyle='#fff';ctx.fillRect(paddle.x,paddle.y,paddle.w,paddle.h);
ctx.beginPath();ctx.arc(ball.x,ball.y,ball.r,0,Math.PI*2);ctx.fillStyle='#0ff';ctx.fill();
bricks.forEach(b=>{if(b.alive){ctx.fillStyle=b.color;ctx.fillRect(b.x,b.y,b.w,b.h);ctx.strokeStyle='#222';ctx.strokeRect(b.x,b.y,b.w,b.h)}});
if(!running){ctx.fillStyle='#fff';ctx.font='16px Arial';ctx.textAlign='center';ctx.fillText('点击开始',W/2,H/2)}}
function update(){if(!running)return;ball.x+=ball.vx;ball.y+=ball.vy;
if(ball.x-ball.r<0||ball.x+ball.r>W)ball.vx*=-1;if(ball.y-ball.r<0)ball.vy*=-1;
if(ball.y+ball.r>H){lives--;document.getElementById('l').textContent=lives;if(lives<=0){alert('游戏结束！得分: '+score);init()}else{ball.x=240;ball.y=480;ball.vx=3;ball.vy=-3;running=0}}
if(ball.y+ball.r>paddle.y&&ball.y-ball.r<paddle.y+paddle.h&&ball.x>paddle.x&&ball.x<paddle.x+paddle.w){ball.vy=-4;ball.vx+=(ball.x-(paddle.x+paddle.w/2))*0.15}
bricks.forEach(b=>{if(b.alive&&ball.x+ball.r>b.x&&ball.x-ball.r<b.x+b.w&&ball.y+ball.r>b.y&&ball.y-ball.r<b.y+b.h){b.alive=0;ball.vy*=-1;score+=10;document.getElementById('s').textContent=score;if(bricks.every(b2=>!b2.alive)){setTimeout(()=>{score+=50;initBricks();ball.vy=-4;ball.vx=3;running=0;document.getElementById('s').textContent=score},500)}}})}
function init(){score=0;lives=3;ball={x:240,y:480,r:6,vx:3,vy:-3};paddle.x=195;running=0;document.getElementById('s').textContent='0';document.getElementById('l').textContent='3';initBricks()}
c.addEventListener('mousemove',e=>{const rect=c.getBoundingClientRect();paddle.x=e.clientX-rect.left-paddle.w/2;paddle.x=Math.max(0,Math.min(W-paddle.w,paddle.x))});
c.addEventListener('click',()=>{running=1});
function loop(){update();draw();requestAnimationFrame(loop)}
init();loop();
</script></body></html>'''

# ─── 23. 双人贪吃蛇 Snake 2P ──────────────────────────────
_GAMES["Snake2P"] = r'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>双人贪吃蛇 Snake 2P</title>
<style>*{margin:0;padding:0}body{background:#1a1a2e;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Arial;flex-direction:column}
canvas{border:2px solid #e94560;background:#16213e}
.info{color:#eee;margin-bottom:8px;font-size:18px;display:flex;gap:40px}
.info span{color:#e94560}.info .p2{color:#0ff}</style></head><body>
<div class="info">P1: <span id="p1">0</span> P2: <span class="p2" id="p2">0</span></div>
<canvas id="c"></canvas><div style="color:#555;margin-top:6px;font-size:12px">P1: WASD | P2: 方向键 | 空格暂停</div>
<script>
const c=document.getElementById('c'),ctx=c.getContext('2d'),gs=20,TW=25,TH=25;
c.width=TW*gs;c.height=TH*gs;
let s1=[{x:5,y:12}],d1={x:1,y:0},s2=[{x:19,y:12}],d2={x:-1,y:0},food={},s1s=0,s2s=0,paused=0,g1=0,g2=0;
function placeFood(){do{food={x:Math.floor(Math.random()*TW),y:Math.floor(Math.random()*TH)}}while(s1.some(s=>s.x===food.x&&s.y===food.y)||s2.some(s=>s.x===food.x&&s.y===food.y))}
placeFood();
function draw(){ctx.fillStyle='#16213e';ctx.fillRect(0,0,c.width,c.height);
s1.forEach((s,i)=>{ctx.fillStyle=i===0?'#e94560':'#a02040';ctx.fillRect(s.x*gs,s.y*gs,gs-2,gs-2)});
s2.forEach((s,i)=>{ctx.fillStyle=i===0?'#0ff':'#006080';ctx.fillRect(s.x*gs,s.y*gs,gs-2,gs-2)});
ctx.fillStyle='#f5c518';ctx.fillRect(food.x*gs,food.y*gs,gs-2,gs-2);
if(g1||g2){ctx.fillStyle='rgba(0,0,0,0.7)';ctx.fillRect(0,0,c.width,c.height);ctx.fillStyle='#fff';ctx.font='24px Arial';ctx.textAlign='center';ctx.fillText(g1?'P2 获胜！':g2?'P1 获胜！':'',c.width/2,c.height/2);ctx.font='14px Arial';ctx.fillText('按 R 重新开始',c.width/2,c.height/2+30)}}
function step(){if(paused||g1||g2)return;const h1={x:s1[0].x+d1.x,y:s1[0].y+d1.y},h2={x:s2[0].x+d2.x,y:s2[0].y+d2.y};
if(h1.x<0||h1.x>=TW||h1.y<0||h1.y>=TH||s1.some(s=>s.x===h1.x&&s.y===h1.y)||s2.some(s=>s.x===h1.x&&s.y===h1.y))g1=1;
if(h2.x<0||h2.x>=TW||h2.y<0||h2.y>=TH||s2.some(s=>s.x===h2.x&&s.y===h2.y)||s1.some(s=>s.x===h2.x&&s.y===h2.y))g2=1;
if(g1&&g2){g1=0;g2=0;draw();return}if(g1||g2)return;
s1.unshift(h1);s2.unshift(h2);if(h1.x===food.x&&h1.y===food.y){s1s++;document.getElementById('p1').textContent=s1s;placeFood()}else{s1.pop()}if(h2.x===food.x&&h2.y===food.y){s2s++;document.getElementById('p2').textContent=s2s;placeFood()}else{s2.pop()}}
setInterval(()=>{step();draw()},100);
document.addEventListener('keydown',e=>{if(e.key==='r'||e.key==='R'){s1=[{x:5,y:12}];d1={x:1,y:0};s2=[{x:19,y:12}];d2={x:-1,y:0};s1s=0;s2s=0;g1=0;g2=0;document.getElementById('p1').textContent='0';document.getElementById('p2').textContent='0';placeFood();return}
switch(e.key){case'w':case'W':if(d1.y===0)d1={x:0,y:-1};break;case's':case'S':if(d1.y===0)d1={x:0,y:1};break;case'a':case'A':if(d1.x===0)d1={x:-1,y:0};break;case'd':case'D':if(d1.x===0)d1={x:1,y:0};break;case'ArrowUp':if(d2.y===0)d2={x:0,y:-1};break;case'ArrowDown':if(d2.y===0)d2={x:0,y:1};break;case'ArrowLeft':if(d2.x===0)d2={x:-1,y:0};break;case'ArrowRight':if(d2.x===0)d2={x:1,y:0};break;case' ':e.preventDefault();paused=!paused;break}});
</script></body></html>'''

# ─── 24. 反应测试 Reaction Test ───────────────────────────
_GAMES["ReactionTest"] = r'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>反应测试 Reaction Test</title>
<style>*{margin:0;padding:0}body{background:#1a1a2e;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Arial;flex-direction:column}
#area{width:300px;height:300px;background:#e94560;display:flex;justify-content:center;align-items:center;font-size:24px;color:#fff;cursor:pointer;border-radius:16px;transition:background 0.1s;user-select:none}
#area.waiting{background:#0f0}#area.tooSoon{background:#f00}
.info{color:#fff;margin-top:15px;font-size:20px}
.info span{color:#e94560}button{background:#e94560;color:#fff;border:none;padding:10px 24px;border-radius:4px;cursor:pointer;margin-top:10px;font-size:16px}</style></head><body>
<div id="area">点击开始</div><div class="info">反应时间: <span id="t">--</span> ms</div>
<div class="info">最佳: <span id="b">--</span> ms | 平均: <span id="a">--</span> ms</div><button onclick="reset()">🔄 重置</button>
<script>
let state='idle',startTime,times=[],best=null;
const area=document.getElementById('area');
function reset(){times=[];best=null;state='idle';area.textContent='点击开始';area.className='';document.getElementById('t').textContent='--';document.getElementById('b').textContent='--';document.getElementById('a').textContent='--'}
area.addEventListener('click',()=>{if(state==='idle'){state='waiting';area.textContent='等待...';area.className='waiting';const delay=1000+Math.random()*3000;setTimeout(()=>{if(state==='waiting'){state='ready';area.textContent='现在点击！';area.className='';startTime=Date.now()}},delay)}
else if(state==='ready'){const rt=Date.now()-startTime;times.push(rt);const avg=Math.round(times.reduce((a,b)=>a+b,0)/times.length);if(!best||rt<best)best=rt;document.getElementById('t').textContent=rt;document.getElementById('b').textContent=best;document.getElementById('a').textContent=avg;state='idle';area.textContent='点击开始';area.className=''}
else if(state==='waiting'){state='tooSoon';area.textContent='太早了！';area.className='tooSoon';setTimeout(()=>{state='idle';area.textContent='点击开始';area.className=''},1000)}});
</script></body></html>'''

# ─── 25. 打字速度 Typing Test ─────────────────────────────
_GAMES["TypingTest"] = r'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>打字速度 Typing Test</title>
<style>*{margin:0;padding:0}body{background:#1a1a2e;display:flex;justify-content:center;align-items:center;height:100vh;font-family:monospace;flex-direction:column}
#text{color:#ccc;font-size:18px;max-width:600px;line-height:2;margin-bottom:15px;text-align:center}
#text .correct{color:#0f0}#text .incorrect{color:#f00}#text .current{background:#e94560;color:#fff;padding:2px 4px;border-radius:2px}
#input{background:#16213e;border:2px solid #e94560;color:#fff;padding:10px 15px;font-size:18px;font-family:monospace;width:400px;border-radius:6px;outline:none;text-align:center}
.info{color:#fff;margin-top:15px;font-size:18px;display:flex;gap:30px}
.info span{color:#e94560}button{background:#e94560;color:#fff;border:none;padding:10px 24px;border-radius:4px;cursor:pointer;margin-top:10px;font-size:16px}</style></head><body>
<div id="text"></div><input id="input" placeholder="在这里输入..." autocomplete="off"><div class="info">速度: <span id="w">0</span> WPM | 准确率: <span id="a">100</span>%</div><button onclick="newGame()">🔄 新文本</button>
<script>
const texts=["The quick brown fox jumps over the lazy dog","To be or not to be that is the question","All that glitters is not gold","A journey of a thousand miles begins with a single step","Practice makes perfect"];
let target,pos,correct,started,startTime;
const input=document.getElementById('input'),textDiv=document.getElementById('text');
function newGame(){target=texts[Math.floor(Math.random()*texts.length)].split('');pos=0;correct=0;started=0;input.value='';input.focus();render()}
function render(){textDiv.innerHTML='';target.forEach((ch,i)=>{const span=document.createElement('span');if(i<pos)span.className=correct?'correct':'incorrect';if(i===pos)span.className='current';span.textContent=ch;textDiv.appendChild(span)})}
input.addEventListener('input',()=>{if(!started){started=1;startTime=Date.now()}
const val=input.value;pos=val.length;correct=0;for(let i=0;i<pos;i++){if(val[i]===target[i])correct++}
const elapsed=(Date.now()-startTime)/60000;const wpm=elapsed>0?Math.round(correct/(5*elapsed)):0;const acc=pos>0?Math.round(correct/pos*100):100;document.getElementById('w').textContent=wpm;document.getElementById('a').textContent=acc;
if(pos>=target.length){const elapsed2=(Date.now()-startTime)/60000;const finalWpm=elapsed2>0?Math.round(correct/(5*elapsed2)):0;setTimeout(()=>alert('🎉 完成！速度: '+finalWpm+' WPM'),200)}render()});
newGame();
</script></body></html>'''

# ─── 26. 点击器 Clicker ───────────────────────────────────
_GAMES["Clicker"] = r'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>点击器 Clicker Game</title>
<style>*{margin:0;padding:0}body{background:#1a1a2e;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Arial;flex-direction:column}
#clicker{width:150px;height:150px;background:linear-gradient(135deg,#e94560,#ff6b6b);border-radius:50%;cursor:pointer;display:flex;justify-content:center;align-items:center;font-size:48px;user-select:none;transition:transform 0.1s;box-shadow:0 8px 25px rgba(233,69,96,0.4)}
#clicker:active{transform:scale(0.9)}
.info{color:#fff;margin-top:15px;font-size:20px;display:flex;gap:30px}
.info span{color:#e94560}#shop{display:flex;gap:10px;margin-top:15px}
.shop-item{background:#16213e;color:#fff;padding:8px 16px;border-radius:6px;cursor:pointer;font-size:14px;border:1px solid #333;transition:all 0.2s}
.shop-item:hover{background:#e94560;border-color:#e94560}</style></head><body>
<div id="clicker">🪙</div><div class="info">金币: <span id="c">0</span> | 每秒: <span id="r">0</span></div>
<div id="shop"><div class="shop-item" onclick="buy('click')">+1/点击 (10💰)</div><div class="shop-item" onclick="buy('auto')">+1/秒 (50💰)</div><div class="shop-item" onclick="buy('crit')">暴击 x2 (100💰)</div></div>
<script>
let coins=0,clickPow=1,autoRate=0,critChance=0;
const clicker=document.getElementById('clicker');
function update(){document.getElementById('c').textContent=coins;document.getElementById('r').textContent=autoRate}
clicker.addEventListener('click',()=>{let gain=clickPow;if(Math.random()<critChance)gain*=2;coins+=gain;update()});
function buy(type){if(type==='click'&&coins>=10){coins-=10;clickPow+=1}else if(type==='auto'&&coins>=50){coins-=50;autoRate+=1}else if(type==='crit'&&coins>=100){coins-=100;critChance+=0.1}update()}
setInterval(()=>{coins+=autoRate;update()},1000);
</script></body></html>'''

# ─── 27. 大炮射击 Cannon ──────────────────────────────────
_GAMES["Cannon"] = r'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>大炮射击 Cannon</title>
<style>*{margin:0;padding:0}body{background:#0a0a2e;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Arial;flex-direction:column}
canvas{border:1px solid #333;background:linear-gradient(#1a1a4e,#0a0a2e);cursor:crosshair}
.info{color:#fff;margin-bottom:8px;font-size:18px;display:flex;gap:30px}
.info span{color:#e94560}</style></head><body>
<div class="info">得分: <span id="s">0</span> 弹药: <span id="a">10</span></div>
<canvas id="c"></canvas><div style="color:#555;margin-top:6px;font-size:12px">点击发射 | 调整角度</div>
<script>
const c=document.getElementById('c'),ctx=c.getContext('2d'),W=600,H=450;
let cannon={x:50,y:H-50,angle:-Math.PI/4},targets=[],bullets=[],score=0,ammo=10,gameOver=0;
function spawnTarget(){targets.push({x:300+Math.random()*250,y:30+Math.random()*200,r:15+Math.random()*15,vy:0.5+Math.random()*1.5,dir:Math.random()>0.5?1:-1})}
for(let i=0;i<5;i++)spawnTarget();
function draw(){ctx.clearRect(0,0,W,H);
ctx.fillStyle='#228B22';ctx.fillRect(0,H-30,W,30);ctx.fillStyle='#555';ctx.fillRect(cannon.x-15,cannon.y-10,30,20);ctx.fillStyle='#888';ctx.save();ctx.translate(cannon.x,cannon.y);ctx.rotate(cannon.angle);ctx.fillRect(0,-4,40,8);ctx.restore();
targets.forEach(t=>{ctx.fillStyle='#f44';ctx.beginPath();ctx.arc(t.x,t.y,t.r,0,Math.PI*2);ctx.fill();ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(t.x-3,t.y-3,3,0,Math.PI*2);ctx.fill()});
bullets.forEach(b=>{ctx.fillStyle='#ff0';ctx.beginPath();ctx.arc(b.x,b.y,4,0,Math.PI*2);ctx.fill()});
if(gameOver){ctx.fillStyle='rgba(0,0,0,0.7)';ctx.fillRect(0,0,W,H);ctx.fillStyle='#fff';ctx.font='24px Arial';ctx.textAlign='center';ctx.fillText('游戏结束！得分: '+score,W/2,H/2)}}
function update(){if(gameOver)return;targets.forEach(t=>{t.y+=t.vy;t.x+=t.dir*2;if(t.y>H-30-t.r){t.vy*=-1;t.y=H-30-t.r}if(t.x+t.r>W||t.x-t.r<0)t.dir*=-1;t.x=Math.max(t.r,Math.min(W-t.r,t.x))});
bullets.forEach(b=>{b.x+=b.vx;b.y+=b.vy;b.vy+=0.2});
bullets=bullets.filter(b=>{for(let i=targets.length-1;i>=0;i--){const t=targets[i];const dx=b.x-t.x,dy=b.y-t.y;if(Math.sqrt(dx*dx+dy*dy)<t.r+4){targets.splice(i,1);score+=10;document.getElementById('s').textContent=score;spawnTarget();return 0}}return b.x>0&&b.x<W&&b.y>0&&b.y<H});
if(ammo<=0&&bullets.length===0){gameOver=1}}
c.addEventListener('mousemove',e=>{const rect=c.getBoundingClientRect();const dx=e.clientX-rect.left-cannon.x,dy=e.clientY-rect.top-cannon.y;cannon.angle=Math.atan2(dy,dx)});
c.addEventListener('click',e=>{if(gameOver||ammo<=0)return;const rect=c.getBoundingClientRect();const dx=e.clientX-rect.left-cannon.x,dy=e.clientY-rect.top-cannon.y;const power=8;bullets.push({x:cannon.x+Math.cos(cannon.angle)*40,y:cannon.y+Math.sin(cannon.angle)*40,vx:Math.cos(cannon.angle)*power,vy:Math.sin(cannon.angle)*power});ammo--;document.getElementById('a').textContent=ammo});
setInterval(update,30);setInterval(draw,30);
</script></body></html>'''

# ─── 28. 15拼图 Fifteen Puzzle ────────────────────────────
_GAMES["Fifteen"] = r'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>15拼图 Fifteen</title>
<style>*{margin:0;padding:0}body{background:#1a1a2e;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Arial;flex-direction:column}
h1{color:#fff;margin-bottom:10px;font-size:24px}
#board{display:grid;grid-template-columns:repeat(4,80px);gap:3px;background:#333;padding:3px;border-radius:8px}
.tile{width:80px;height:80px;background:linear-gradient(135deg,#e94560,#c0392b);display:flex;justify-content:center;align-items:center;font-size:28px;font-weight:bold;color:#fff;cursor:pointer;border-radius:6px;transition:all 0.15s;text-shadow:1px 1px 2px rgba(0,0,0,0.5);user-select:none}
.tile:hover{transform:scale(0.95)}.tile.empty{background:transparent;pointer-events:none}
.info{color:#fff;margin-top:10px;font-size:18px;display:flex;gap:30px}
.info span{color:#e94560}button{background:#e94560;color:#fff;border:none;padding:8px 20px;border-radius:4px;cursor:pointer;margin-top:8px;font-size:14px}</style></head><body>
<h1>15 拼图</h1><div id="board"></div><div class="info">步数: <span id="m">0</span> 时间: <span id="t">0</span>s</div><button onclick="init()">🔄 新游戏</button>
<script>
let board,moves,started,startTime,timer;
function init(){board=Array.from({length:15},(_,i)=>i+1);board.push(0);for(let i=board.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[board[i],board[j]]=[board[j],board[i]]}moves=0;started=0;if(timer)clearInterval(timer);document.getElementById('m').textContent='0';document.getElementById('t').textContent='0';render()}
function render(){const b=document.getElementById('board');b.innerHTML='';board.forEach((v,i)=>{const t=document.createElement('div');t.className='tile'+(v===0?' empty':'');t.textContent=v||'';t.addEventListener('click',()=>move(i));b.appendChild(t)})}
function move(i){if(board[i]===0)return;if(!started){started=1;startTime=Date.now();timer=setInterval(()=>{document.getElementById('t').textContent=Math.floor((Date.now()-startTime)/1000)},1000)}
const empty=board.indexOf(0);const er=empty/4|0,ec=empty%4,tr=i/4|0,tc=i%4;if(Math.abs(er-tr)+Math.abs(ec-tc)===1){[board[i],board[empty]]=[board[empty],board[i]];moves++;document.getElementById('m').textContent=moves;render();if(isSolved()){clearInterval(timer);const t2=Math.floor((Date.now()-startTime)/1000);setTimeout(()=>alert('🎉 完成！'+moves+'步 '+t2+'秒'),200)}}}
function isSolved(){for(let i=0;i<15;i++)if(board[i]!==i+1)return 0;return board[15]===0}
init();
</script></body></html>'''

# ─── 29. 算术挑战 Math Quiz ───────────────────────────────
_GAMES["MathQuiz"] = r'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>算术挑战 Math Quiz</title>
<style>*{margin:0;padding:0}body{background:#1a1a2e;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Arial;flex-direction:column}
#question{color:#fff;font-size:48px;margin-bottom:20px}
#answer{background:#16213e;border:2px solid #e94560;color:#fff;padding:10px 20px;font-size:28px;width:150px;border-radius:8px;outline:none;text-align:center;font-family:monospace}
.info{color:#fff;margin-top:15px;font-size:20px;display:flex;gap:30px}
.info span{color:#e94560}.timer{color:#0f0;font-size:24px;margin-bottom:10px}
button{background:#e94560;color:#fff;border:none;padding:10px 24px;border-radius:4px;cursor:pointer;margin-top:10px;font-size:16px}</style></head><body>
<div class="timer" id="timer">⏱ 60</div><div id="question">3 + 5 = ?</div><input id="answer" placeholder="?" autocomplete="off" autofocus>
<div class="info">得分: <span id="s">0</span> 正确: <span id="c">0</span> 错误: <span id="w">0</span></div><button onclick="newGame()">🔄 新游戏</button>
<script>
let score=0,correct=0,wrong=0,timeLeft=60,a,b,op,answerVal,timer;
function newGame(){score=0;correct=0;wrong=0;timeLeft=60;if(timer)clearInterval(timer);document.getElementById('s').textContent='0';document.getElementById('c').textContent='0';document.getElementById('w').textContent='0';document.getElementById('timer').textContent='⏱ 60';document.getElementById('answer').value='';document.getElementById('answer').focus();genQuestion();timer=setInterval(()=>{timeLeft--;document.getElementById('timer').textContent='⏱ '+timeLeft;if(timeLeft<=0){clearInterval(timer);document.getElementById('question').textContent='时间到！';setTimeout(()=>alert('得分: '+score+' 正确: '+correct),300)}},1000)}
function genQuestion(){const ops=['+','-','×','÷'];op=ops[Math.floor(Math.random()*4)];a=Math.floor(Math.random()*50)+1;b=Math.floor(Math.random()*50)+1;switch(op){case'+':answerVal=a+b;break;case'-':answerVal=a-b;break;case'×':answerVal=a*b;break;case'÷':a=a*b;answerVal=b;break}document.getElementById('question').textContent=a+' '+op+' '+b+' = ?'}
document.getElementById('answer').addEventListener('keydown',e=>{if(e.key==='Enter'){const val=parseInt(document.getElementById('answer').value);if(val===answerVal){correct++;score+=10;document.getElementById('c').textContent=correct}else{wrong++;document.getElementById('w').textContent=wrong}document.getElementById('s').textContent=score;document.getElementById('answer').value='';genQuestion()}});
newGame();
</script></body></html>'''

# ─── 30. 翻牌配对 Card Match ──────────────────────────────
_GAMES["CardMatch"] = r'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>翻牌配对 Card Match</title>
<style>*{margin:0;padding:0}body{background:#1a1a2e;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Arial;flex-direction:column}
#board{display:grid;grid-template-columns:repeat(4,100px);gap:8px}
.card{width:100px;height:100px;background:linear-gradient(135deg,#e94560,#ff6b6b);display:flex;justify-content:center;align-items:center;font-size:40px;cursor:pointer;border-radius:10px;transition:all 0.3s;user-select:none;box-shadow:0 4px 10px rgba(0,0,0,0.3)}
.card.flipped{background:linear-gradient(135deg,#0f3460,#1a1a4e);transform:rotateY(180deg)}
.card.matched{background:linear-gradient(135deg,#0a0,#0f0);pointer-events:none}
.info{color:#fff;margin-top:10px;font-size:18px;display:flex;gap:30px}
.info span{color:#e94560}button{background:#e94560;color:#fff;border:none;padding:10px 24px;border-radius:4px;cursor:pointer;margin-top:10px;font-size:16px}</style></head><body>
<div id="board"></div><div class="info">步数: <span id="m">0</span> 配对: <span id="p">0</span>/8</div><button onclick="init()">🔄 新游戏</button>
<script>
const pairs=['🐶','🐱','🐼','🐨','🦊','🐸','🐵','🦁'];let cards,flipped,matched,moves,locked;
function init(){cards=[...pairs,...pairs].sort(()=>Math.random()-0.5);flipped=[];matched=[];moves=0;locked=0;document.getElementById('m').textContent='0';document.getElementById('p').textContent='0';render()}
function render(){const b=document.getElementById('board');b.innerHTML='';cards.forEach((v,i)=>{const c=document.createElement('div');c.className='card';if(flipped.includes(i)||matched.includes(i)){c.classList.add('flipped');c.textContent=v}if(matched.includes(i))c.classList.add('matched');c.addEventListener('click',()=>flip(i));b.appendChild(c)})}
function flip(i){if(locked||flipped.includes(i)||matched.includes(i))return;flipped.push(i);moves++;document.getElementById('m').textContent=moves;
if(flipped.length===2){locked=1;if(cards[flipped[0]]===cards[flipped[1]]){matched.push(...flipped);flipped=[];locked=0;document.getElementById('p').textContent=matched.length/2;if(matched.length===cards.length)setTimeout(()=>alert('🎉 完成！用了 '+moves+' 步'),300)}else{setTimeout(()=>{flipped=[];locked=0;render()},600)}}render()}
init();
</script></body></html>'''


# ═══════════════════════════════════════════════════════════════
# 游戏模块 API
# ═══════════════════════════════════════════════════════════════

_GAME_NAMES = {
    "Snake":        "贪吃蛇",
    "Tetris":       "俄罗斯方块",
    "Minesweeper":  "扫雷",
    "2048":         "2048",
    "Breakout":     "打砖块",
    "Pong":         "弹球",
    "SpaceInvaders":"太空射击",
    "Gomoku":       "五子棋",
    "TicTacToe":    "井字棋",
    "Memory":       "记忆翻牌",
    "FlappyBird":   "飞扬的小鸟",
    "PacMan":       "吃豆人",
    "Sudoku":       "数独",
    "SimonSays":    "颜色记忆",
    "Match3":       "消消乐",
    "DoodleJump":   "跳一跳",
    "PingPong":     "乒乓球",
    "WhackMole":    "打地鼠",
    "SlidingPuzzle":"滑块拼图",
    "Maze":         "迷宫",
    "ConnectFour":  "四子棋",
    "BrickBreaker": "弹球打砖",
    "Snake2P":      "双人贪吃蛇",
    "ReactionTest": "反应测试",
    "TypingTest":   "打字速度",
    "Clicker":      "点击器",
    "Cannon":       "大炮射击",
    "Fifteen":      "15拼图",
    "MathQuiz":     "算术挑战",
    "CardMatch":    "翻牌配对",
}


class _GameModule:
    """
    PyMsi 游戏库 — 30+ 内置游戏模板

    用法:
        import PyMsi as PM
        PM.game.Grap("Snake")    # 启动贪吃蛇
        PM.game.Grap("Tetris")   # 俄罗斯方块
        PM.game.list()            # 列出所有游戏
    """

    def __init__(self):
        pass

    def __repr__(self):
        return "<PyMsi.game> 30+ 内置游戏 | game.list() 查看列表 | game.Grap('名称') 启动游戏"

    def __call__(self, name):
        """快捷调用: PM.game('Snake')"""
        return self.Grap(name)

    def list(self):
        """列出所有可用的游戏"""
        print("=" * 60)
        print("  PyMsi Game — 内置游戏模板库 (30 款)")
        print("=" * 60)
        for i, (key, name) in enumerate(_GAME_NAMES.items(), 1):
            print(f"  {i:2d}. {key:16s} → {name}")
        print("=" * 60)
        print("  用法: PM.game.Grap(\"游戏名称\")")
        print("  例如: PM.game.Grap(\"Snake\")")
        print("=" * 60)

    def ls(self):
        """短别名: PM.game.ls() = PM.game.list()"""
        return self.list()

    def all(self):
        """别名: PM.game.all() = PM.game.list()"""
        return self.list()

    def start(self, name):
        """别名: PM.game.start("Snake") = PM.game.Grap("Snake")"""
        return self.Grap(name)

    def run(self, name):
        """别名: PM.game.run("Snake") = PM.game.Grap("Snake")"""
        return self.Grap(name)

    def open(self, name):
        """别名: PM.game.open("Snake") = PM.game.Grap("Snake")"""
        return self.Grap(name)

    def play(self, name):
        """别名: PM.game.play("Snake") = PM.game.Grap("Snake")"""
        return self.Grap(name)

    def Grap(self, name):
        """
        启动指定游戏

        Args:
            name: 游戏名称 (英文名或中文名，不区分大小写)

        示例:
            PM.game.Grap("Snake")       # 贪吃蛇
            PM.game.Grap("Tetris")      # 俄罗斯方块
            PM.game.Grap("2048")        # 2048
        """
        # 先尝试精确匹配英文名
        key = None
        name_lower = name.lower()

        # 精确匹配英文名
        for k in _GAME_NAMES:
            if k.lower() == name_lower:
                key = k
                break

        # 模糊匹配英文名
        if key is None:
            for k in _GAME_NAMES:
                if name_lower in k.lower():
                    key = k
                    break

        # 匹配中文名
        if key is None:
            for k, cn in _GAME_NAMES.items():
                if name in cn:
                    key = k
                    break

        if key is None:
            print(f"[PyMsi.game] 未找到游戏: {name}")
            print("可用游戏列表:")
            self.list()
            return

        html = _GAMES.get(key)
        if not html:
            print(f"[PyMsi.game] 游戏 '{key}' 模板缺失")
            return

        print(f"[PyMsi.game] 启动: {key} ({_GAME_NAMES[key]})")
        self._launch(key, html)

    def _launch(self, name, html):
        """将 HTML 写入临时文件并在浏览器中打开"""
        try:
            # 写入临时文件
            tmp_dir = tempfile.mkdtemp(prefix="pymsi_game_")
            tmp_file = os.path.join(tmp_dir, f"{name}.html")

            with open(tmp_file, "w", encoding="utf-8") as f:
                f.write(html)

            print(f"[PyMsi.game] 文件: {tmp_file}")

            # 尝试多种方式打开浏览器
            opened = False

            # 方式1: 用 webbrowser 模块
            try:
                webbrowser.open(f"file://{tmp_file}", new=2)
                opened = True
            except Exception:
                pass

            # 方式2: 用系统命令
            if not opened:
                try:
                    if sys.platform == "win32":
                        os.startfile(tmp_file)
                        opened = True
                    elif sys.platform == "darwin":
                        subprocess.Popen(["open", tmp_file])
                        opened = True
                    else:
                        subprocess.Popen(["xdg-open", tmp_file])
                        opened = True
                except Exception:
                    pass

            if opened:
                print(f"[PyMsi.game] 浏览器已打开! 享受 {_GAME_NAMES[name]} 吧!")
                print(f"[PyMsi.game] 提示: 关闭此页面后，临时文件将被系统自动清理")
            else:
                print(f"[PyMsi.game] 无法自动打开浏览器，请手动打开:")
                print(f"           file://{tmp_file}")

        except Exception as e:
            print(f"[PyMsi.game] 启动失败: {e}")

    # ─── 快捷属性 (PM.game.Snake 直接启动) ───
    @property
    def Snake(self):
        return self.Grap("Snake")

    @property
    def Tetris(self):
        return self.Grap("Tetris")

    @property
    def minesweeper(self):
        return self.Grap("Minesweeper")

    @property
    def p2048(self):
        return self.Grap("2048")

    @property
    def Breakout(self):
        return self.Grap("Breakout")

    @property
    def Pong(self):
        return self.Grap("Pong")

    @property
    def SpaceInvaders(self):
        return self.Grap("SpaceInvaders")

    @property
    def Gomoku(self):
        return self.Grap("Gomoku")

    @property
    def TicTacToe(self):
        return self.Grap("TicTacToe")

    @property
    def Memory(self):
        return self.Grap("Memory")

    @property
    def FlappyBird(self):
        return self.Grap("FlappyBird")

    @property
    def PacMan(self):
        return self.Grap("PacMan")

    @property
    def Sudoku(self):
        return self.Grap("Sudoku")

    @property
    def SimonSays(self):
        return self.Grap("SimonSays")

    @property
    def Match3(self):
        return self.Grap("Match3")

    @property
    def DoodleJump(self):
        return self.Grap("DoodleJump")

    @property
    def PingPong(self):
        return self.Grap("PingPong")

    @property
    def WhackMole(self):
        return self.Grap("WhackMole")

    @property
    def SlidingPuzzle(self):
        return self.Grap("SlidingPuzzle")

    @property
    def Maze(self):
        return self.Grap("Maze")

    @property
    def ConnectFour(self):
        return self.Grap("ConnectFour")

    @property
    def BrickBreaker(self):
        return self.Grap("BrickBreaker")

    @property
    def Snake2P(self):
        return self.Grap("Snake2P")

    @property
    def ReactionTest(self):
        return self.Grap("ReactionTest")

    @property
    def TypingTest(self):
        return self.Grap("TypingTest")

    @property
    def Clicker(self):
        return self.Grap("Clicker")

    @property
    def Cannon(self):
        return self.Grap("Cannon")

    @property
    def Fifteen(self):
        return self.Grap("Fifteen")

    @property
    def MathQuiz(self):
        return self.Grap("MathQuiz")

    @property
    def CardMatch(self):
        return self.Grap("CardMatch")