import {startGame,finishGame} from './engine.mjs?v=1.6-free-1';

// The same short arcade breaks as Windows, with touch and keyboard controls.
export function setupCatchGames(api){
 const dialog=document.createElement('dialog');dialog.id='catch-dialog';
 dialog.innerHTML='<button class="close-dialog" aria-label="End arcade game">×</button><h2></h2><p class="catch-status" role="status"></p><canvas width="480" height="240" tabindex="0" aria-label="Arcade field. Tap bugs to catch them. For Treat Drop, drag the basket or use left and right arrows."></canvas><p class="catch-help"></p><button class="primary catch-done" hidden>Back to my little friend</button>';
 document.body.append(dialog);
 const field=dialog.querySelector('canvas'),ctx=field.getContext('2d'),status=dialog.querySelector('.catch-status'),done=dialog.querySelector('.catch-done');
 let game=null,frame=0,last=0,basket=240,held=0;
 const treat=new Image();treat.src='../assets/supplies/food-berries.png';
 function spawn(){return {x:25+Math.random()*430,y:game.kind==='bugs'?25+Math.random()*150:-16,vx:(Math.random()-.5)*90,vy:game.kind==='bugs'?(Math.random()-.5)*75:65+Math.random()*50,gold:Math.random()<.2}}
 function draw(){
  ctx.clearRect(0,0,480,240);ctx.fillStyle='#f0eadb';ctx.fillRect(0,0,480,240);ctx.fillStyle='#bed5a0';ctx.fillRect(0,198,480,42);
  for(const p of game.items){if(game.kind==='drop'){if(treat.complete&&treat.naturalWidth)ctx.drawImage(treat,p.x-12,p.y-12,24,24);else{ctx.fillStyle='#bd4b70';ctx.fillRect(p.x-8,p.y-8,16,16)}}else{ctx.fillStyle=p.gold?'#be8620':'#665582';ctx.fillRect(p.x-6,p.y-7,12,14);ctx.fillStyle=p.gold?'#f5cb59':'#c6a8dc';ctx.fillRect(p.x-13,p.y-5,7,10);ctx.fillRect(p.x+6,p.y-5,7,10);ctx.fillStyle='#362746';ctx.fillRect(p.x-4,p.y-3,2,2);ctx.fillRect(p.x+2,p.y-3,2,2)}}
  if(game.kind==='drop'){ctx.fillStyle='#a76e49';ctx.fillRect(basket-27,211,54,20);ctx.fillStyle='#e8bf82';ctx.fillRect(basket-31,207,62,6)}
 }
 function finish(){const completed=game;game=null;cancelAnimationFrame(frame);api.sync();const result=finishGame(api.getState(),completed.id,completed.score);api.persist();api.render();status.textContent=`${completed.score} points · ${result?(result.practice?'Free practice':`+${result.coins} coins · +${result.xp} XP`):'Round replaced in another tab; no duplicate reward.'}`;done.hidden=false;api.speak('What a lovely little game!')}
 function step(t){if(!game)return;const dt=Math.min(.05,(t-last)/1000||0);last=t;if(Date.now()-game.startAt>=game.duration){finish();return}
  basket=Math.max(31,Math.min(449,basket+held*220*dt));
  if(game.kind==='drop'&&t-game.spawned>650){game.items.push(spawn());game.spawned=t}
  for(const p of game.items){p.x+=p.vx*dt;p.y+=p.vy*dt;if(p.x<16||p.x>464){p.vx=-p.vx;p.x=Math.max(16,Math.min(464,p.x))}if(game.kind==='bugs'&&(p.y<16||p.y>188)){p.vy=-p.vy;p.y=Math.max(16,Math.min(188,p.y))}if(game.kind==='drop'&&p.y>=201&&p.y<=229&&Math.abs(p.x-basket)<34){game.score++;p.y=260;api.sound()}}
  game.items=game.items.filter(p=>p.y<250);draw();status.textContent=`${Math.ceil((game.duration-(Date.now()-game.startAt))/1000)}s · ${game.score} points${game.paid?'':' · Free practice'}`;frame=requestAnimationFrame(step);
 }
 function start(kind){api.sync();const entry=startGame(api.getState(),kind);if(!entry){api.toast('Wake your pet and resume the room before playing.');return}game={...entry,score:0,items:[],spawned:0};basket=240;held=0;last=0;if(kind==='bugs')game.items=Array.from({length:5},spawn);api.persist();api.render();dialog.querySelector('h2').textContent=kind==='bugs'?'Catch the Bug':'Treat Drop';dialog.querySelector('.catch-help').textContent=kind==='bugs'?'Tap the fluttering bugs. Golden bugs are worth three points.':'Drag the basket to catch falling treats. You can also use the arrow keys.';done.hidden=true;dialog.showModal();field.focus();frame=requestAnimationFrame(step)}
 function point(e){const r=field.getBoundingClientRect();return {x:(e.clientX-r.left)*480/r.width,y:(e.clientY-r.top)*240/r.height}}
 field.onpointerdown=e=>{if(!game)return;const p=point(e);if(game.kind==='drop'){basket=Math.max(31,Math.min(449,p.x));field.setPointerCapture(e.pointerId)}else{const i=game.items.findIndex(b=>Math.hypot(p.x-b.x,p.y-b.y)<25);if(i>=0){game.score+=game.items[i].gold?3:1;game.items[i]=spawn();api.sound()}}};
 field.onpointermove=e=>{if(game?.kind==='drop'&&field.hasPointerCapture(e.pointerId))basket=Math.max(31,Math.min(449,point(e).x))};
 field.onpointerup=e=>{if(field.hasPointerCapture(e.pointerId))field.releasePointerCapture(e.pointerId)};
 field.onkeydown=e=>{if(game?.kind==='drop'&&['ArrowLeft','ArrowRight'].includes(e.key)){e.preventDefault();held=e.key==='ArrowLeft'?-1:1}};
 field.onkeyup=()=>held=0;field.onblur=()=>held=0;
 function cancel(){if(game){const id=game.id;game=null;cancelAnimationFrame(frame);api.sync();if(api.getState().round?.id===id){api.getState().round=null;api.persist()}api.toast('Round ended early. No reward claimed.')}if(dialog.open)dialog.close()}
 dialog.querySelector('.close-dialog').onclick=cancel;done.onclick=cancel;dialog.addEventListener('close',cancel);
 document.querySelector('#start-bugs').onclick=()=>start('bugs');document.querySelector('#start-drop').onclick=()=>start('drop');
 return {cancel};
}
