import {startGame,finishGame} from './engine.mjs?v=1.6-free-1';
import {PetPlayRound} from './pet-play.mjs?v=1.6-free-1';
import {createPetPainter} from './room-world.mjs?v=1.6-free-1';
export function setupPetGames(api){
 const $=s=>document.querySelector(s),dialog=$('#petgame-dialog'),stage=$('#petgame-stage');let entry=null,model=null,raf=0,last=0,lastMessage='';
 const native=document.createElement('canvas');native.width=native.height=24;native.className='game-native-pet';native.hidden=true;native.setAttribute('aria-hidden','true');stage.append(native);
 let paint=null;const animation={pose:'idle',age:0};
 createPetPainter().then(renderer=>{paint=renderer}).catch(()=>api.toast('Pet frames could not load. Reopen online to finish updating.'));
 function persistRound(){api.persist();api.render()}
 function stop(){cancelAnimationFrame(raf);raf=0}
 function cancel(){if(!entry)return;const id=entry.id;entry=null;stop();api.sync();if(api.getState().round?.id===id){api.getState().round=null;persistRound()}api.toast('Round ended. No rewards; watch mode is always free.')}
 function frame(t){if(!entry)return;const dt=last?Math.min(.05,(t-last)/1000):0;model.step(dt);last=t;
  const seconds=Math.max(0,Math.ceil((entry.duration-(Date.now()-entry.startAt))/1000));$('#petgame-time').textContent=`${seconds}s · ${entry.watch?'Watching':entry.paid?'Play together':'Free practice'}`;$('#petgame-score').textContent=`${model.score} points`;
  const actor=$('#game-pet');actor.style.left=model.x+'%';actor.style.top=model.y+'%';actor.style.translate=`-50% calc(-100% - ${model.height*65}px)`;
  const pose=entry.kind==='hurdles'?'walk_right':model.phase==='out'?'walk_right':model.phase==='back'?'walk_left':'sit';
  if(animation.pose!==pose){animation.pose=pose;animation.age=0}else animation.age+=dt;
  if(paint?.(animation,native,api.getState())){actor.hidden=true;native.hidden=false;native.style.left=actor.style.left;native.style.top=actor.style.top;native.style.translate=actor.style.translate}
  const ball=$('#game-ball');ball.hidden=entry.kind!=='fetch'||model.phase==='ready';ball.style.left=(model.phase==='back'?model.x:model.target[0])+'%';ball.style.top=(model.phase==='back'?model.y-7:model.target[1])+'%';
  const hurdle=$('#game-hurdle');hurdle.hidden=entry.kind!=='hurdles';hurdle.style.left=model.obstacle+'%';
  if(lastMessage!==model.message){lastMessage=model.message;$('#petgame-help').textContent=model.message}
  if(!seconds){const r=entry;entry=null;stop();api.sync();const result=finishGame(api.getState(),r.id,model.score);persistRound();$('#petgame-help').textContent=result?`${model.score} points. ${r.watch?'Your pet had a lovely play break. No lives or coins used.':result.practice?'Free practice complete.':`+${result.coins} coins · +${result.xp} XP.`}`:'This round changed in another tab. No duplicate rewards.';$('#petgame-done').hidden=false;return}
  raf=requestAnimationFrame(frame);
 }
 function start(kind,watch){api.sync();entry=startGame(api.getState(),kind,Date.now(),watch);if(!entry){api.toast('Wake or resume your pet before playing.');return}model=new PetPlayRound(kind,watch);last=0;lastMessage='';const p=api.getState();$('#game-pet').src=`../assets/pets/${p.species}-${p.coat}-happy.gif`;$('#game-pet').alt=p.pet;$('#petgame-title').textContent=kind==='fetch'?'Fetch relay':'Garden hurdles';$('#petgame-done').hidden=true;$('#game-cheer').textContent=p.solo?'':p.companions.map(f=>f.pet).join(' & ')+(p.companions.length?' are cheering!':'');persistRound();dialog.showModal();stage.focus();raf=requestAnimationFrame(frame)}
 function act(e){if(!entry||entry.watch)return;if(entry.kind==='hurdles')model.leap();else{const r=stage.getBoundingClientRect();model.throw((e.clientX-r.left)/r.width*100,(e.clientY-r.top)/r.height*100)}}
 stage.addEventListener('pointerdown',act);dialog.addEventListener('keydown',e=>{if(e.code==='Space'&&entry&&!entry.watch){e.preventDefault();if(e.repeat)return;if(entry.kind==='hurdles')model.leap();else model.throw(72,65)}});
 document.querySelectorAll('[data-petgame]').forEach(b=>b.onclick=()=>start(b.dataset.petgame,b.dataset.watch==='true'));
 dialog.addEventListener('close',cancel);$('#petgame-done').onclick=()=>dialog.close();$('#petgame-close').onclick=()=>dialog.close();return {cancel:()=>{cancel();dialog.close()}};
}
