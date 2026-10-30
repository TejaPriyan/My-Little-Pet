// One owner for room movement, poses and toy interactions. No autoplay rewards.
export function moveTowards(actor, target, dt, speed=12){
 const dx=target.x-actor.x,dy=(target.y-actor.y)*.4375,d=Math.hypot(dx,dy);
 if(d>.2&&dt>0){const step=Math.min(d,speed*Math.max(0,Math.min(.05,dt)));actor.x+=dx/d*step;actor.y+=dy/d*step/.4375;actor.pose=Math.abs(dx)>Math.abs(dy)?(dx<0?'walk_left':'walk_right'):(dy<0?'walk_up':'walk_down');}
 return d;
}
// Share the original frames between the room and pet-led games.
export async function createPetPainter(){
 const clips=await fetch('../assets/pets/clips.json').then(r=>{if(!r.ok)throw Error('Room frames unavailable');return r.json()});
 const images=new Map();
 return (actor,canvas,pet)=>{
  const key=`${pet.species}-${pet.coat}`;
  if(!images.has(key)){const im=new Image();im.src=`../assets/pets/${key}-sheet.png`;images.set(key,im)}
  const im=images.get(key),clip=clips[key]?.[actor.pose]||clips[key]?.idle;
  if(!clip||!im.complete||!im.naturalWidth)return false;
  const ctx=canvas.getContext('2d');ctx.imageSmoothingEnabled=false;ctx.clearRect(0,0,24,24);
  ctx.drawImage(im,(Math.floor(actor.age*clip.fps)%clip.count)*24,clip.row*24,24,24,0,0,24,24);
  return true;
 };
}
export async function setupRoom({getState,speak,care,ToyMotion}){
 const $=s=>document.querySelector(s),room=$('#pet-room'),pet=$('#pet-touch');
 const paint=await createPetPainter();
 const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
 const actors=new Map();let last=performance.now(),motion=null,catchHold=0,catchCooldown=0,toyTime=0,following=false,pending=null;
 const main={x:52,y:76,pose:'idle',age:0,wait:3,target:null};
 let social=null,lastPet=getState().id;
 const canvas=document.createElement('canvas');canvas.width=canvas.height=24;canvas.className='native-pet';canvas.setAttribute('aria-hidden','true');pet.prepend(canvas);
 const toy=document.createElement('img');toy.className='room-floor-toy';toy.hidden=true;toy.alt='Moving toy';room.append(toy);
 function point(key,fallback){const pos=getState().layout?.[key];return pos?{x:pos[0],y:Math.max(48,pos[1])}:{...fallback}}
 function pose(a,next){if(a.pose!==next){a.pose=next;a.age=0}}
 function draw(a,el,c,p){
  paint({...a,age:reduced?0:a.age},c,p);
  el.style.left=a.x+'%';el.style.top=a.y+'%';el.style.zIndex=String(20+Math.round(a.y));
 }
 function stopToy(){motion=null;toy.hidden=true;room.dataset.playing='false';catchHold=0}
 function stopFollowing(){following=false;$('#follow-toggle').setAttribute('aria-pressed','false')}
 function go(key,kind){stopToy();following=false;const s=getState();if(s.paused)return;
  if(s.sleeping&&kind!=='rest'){speak('Wake me with Rest first.');return}
  if((s.hiddenDecor||[]).includes(key)){speak('Place the '+(key==='bed'?'bed':'bowl')+' in Decorate first.');return}
  if(kind==='rest'&&s.sleeping){care('rest');return}
  stopFollowing();social=null;pending=kind;main.target=point(key,kind==='feed'?{x:76,y:86}:{x:24,y:72});main.wait=0;
 }
 function startToy(){main.wait=6;const s=getState();if(s.paused||s.sleeping||s.quiet||reduced)return;
  if((s.hiddenDecor||[]).includes('toy')){speak('Bring the toy back in Decorate first.');return}
  stopFollowing();social=null;pending=null;main.target=null;motion=new ToyMotion(s.selectedToy);const p=point('toy',{x:76,y:76});motion.x=p.x;motion.y=p.y;motion.engaged=false;toyTime=0;catchHold=0;catchCooldown=0;toy.src=`../assets/supplies/toy-${s.selectedToy}.png`;toy.hidden=false;room.dataset.playing='true';
 }
 function command(kind){if(kind==='feed')go('foodBowl','feed');else if(kind==='rest')go('bed','rest');else if(kind==='play'){if(care('play')?.ok)startToy()}else{const result=care(kind);if(!result?.ok)return;stopToy();stopFollowing();social=null;pending=null;main.target=null;pose(main,kind==='dance'?'dance':'wave');main.wait=2.5}}
 // Capture before the legacy buttons so a meal occurs after reaching its bowl.
 for(const b of document.querySelectorAll('[data-care]'))b.addEventListener('click',e=>{e.stopImmediatePropagation();command(b.dataset.care)},true);
 pet.addEventListener('click',e=>{e.stopImmediatePropagation();command('pet')},true);
 $('#toy-adventure').onclick=()=>command('play');
 $('#follow-toggle').onclick=()=>{following=!following;stopToy();pending=null;$('#follow-toggle').setAttribute('aria-pressed',String(following));speak(following?'Show me where to go!':'I’ll explore my room.');};
 room.addEventListener('pet-social',e=>{if(getState().paused||getState().sleeping)return;stopToy();stopFollowing();pending=null;main.target=null;social={kind:e.detail.kind,left:4.5};});
 room.addEventListener('friend-greet',e=>{const a=actors.get(e.detail.id);if(a){a.target=null;a.greeting=3;a.wait=4}});
 function floorPoint(e){const r=room.getBoundingClientRect();return {x:Math.max(8,Math.min(92,(e.clientX-r.left)/r.width*100)),y:Math.max(48,Math.min(90,(e.clientY-r.top)/r.height*100))}}
 room.addEventListener('pointermove',e=>{if(following)main.target=floorPoint(e)});
 room.addEventListener('click',e=>{if($('#room-panel').classList.contains('room-editing')||e.target.closest('button'))return;
  const item=e.target.closest('[data-room-item]')?.dataset.roomItem;
  if(item==='foodBowl')command('feed');else if(item==='bed')command('rest');else if(item==='toy')command('play');
  else if(!item){stopToy();pending=null;main.target=floorPoint(e);main.wait=0}
 });
 $('#recover-pets').addEventListener('click',()=>{stopToy();pending=null;stopFollowing();social=null;main.x=52;main.y=76;main.target=null;main.wait=3;actors.clear()});
 function step(now){const dt=Math.min(.05,Math.max(0,(now-last)/1000));last=now;const s=getState();
  const blocked=document.hidden||$('#room-panel').hidden||document.querySelector('dialog[open]')||$('#room-panel').classList.contains('room-editing');
  room.dataset.native='true';
  if(s.id!==lastPet){lastPet=s.id;stopToy();pending=null;social=null;main.target=null;pose(main,'idle');main.wait=3}
  if(!blocked&&!s.paused){main.age+=dt;
   if(s.sleeping){stopToy();main.target=null;Object.assign(main,point('bed',{x:24,y:72}));pose(main,'sleep')}
   else if(social&&!s.quiet&&!reduced){social.left-=dt;pose(main,social.kind==='dance'?'dance':social.kind==='wrestle'?'play':'wave');main.wait=3;if(social.left<=0){social=null;pose(main,'sit')}}
   else if(motion&&!s.quiet&&!reduced){toyTime+=dt;catchCooldown-=dt;
    if(catchHold>0){catchHold-=dt;pose(main,'play')}
    else {if(motion.engaged)motion.update(dt);const previous=main.pose,d=moveTowards(main,motion,dt,16);if(previous!==main.pose)main.age=0;
     if(d<3&&catchCooldown<=0){catchCooldown=1.8;motion.engaged=true;motion.bat();catchHold=.8;pose(main,'play');speak('Caught it! ♡')}
    }
    toy.style.left=motion.x+'%';toy.style.top=(motion.y-motion.z)+'%';
    if(toyTime>18){stopToy();pose(main,'sit');main.wait=4}
   }else if(main.target){const previous=main.pose;if(moveTowards(main,main.target,dt)<.5){main.target=null;pose(main,'sit');main.wait=3;
      if(pending){const kind=pending;pending=null;const result=care(kind);if(result?.ok)pose(main,kind==='feed'?'eat':'sleep');main.wait=3}}
     if(previous!==main.pose)main.age=0;
   }else {if(s.quiet||reduced){stopToy();social=null}main.wait-=dt;if(main.wait<=0){if(s.quiet||reduced||following){pose(main,'sit')}else if(Math.random()<.25){startToy()}else if(Math.random()<.4){pose(main,'sit');main.wait=5+Math.random()*5}else{main.target={x:12+Math.random()*76,y:55+Math.random()*33};main.wait=2}}}
  }
  draw(main,pet,canvas,s);
  for(const [i,el] of [...$('#room-friends').children].entries()){
   const friend=s.companions[i];if(!friend)continue;let a=actors.get(friend.id||friend.pet);if(!a){a={x:25+i*20,y:70+i*5,pose:'idle',age:0,wait:3+i,target:null};actors.set(friend.id||friend.pet,a)}
   let c=el.querySelector('canvas');if(!c){c=document.createElement('canvas');c.width=c.height=24;c.className='native-pet';el.prepend(c)}
   if(!blocked&&!s.paused){a.age+=dt;if(friend.sleeping)pose(a,'sleep');else if(s.quiet||reduced){a.target=null;pose(a,'sit')}else if(social){a.target=null;pose(a,social.kind==='dance'?'dance':social.kind==='wrestle'?'play':'wave');a.wait=3}else if(a.greeting>0){a.greeting-=dt;pose(a,'wave')}else if(a.target){const old=a.pose;if(moveTowards(a,a.target,dt,8)<.5){a.target=null;pose(a,'sit');a.wait=4+Math.random()*6}if(old!==a.pose)a.age=0}else if((a.wait-=dt)<=0)a.target={x:12+Math.random()*76,y:54+Math.random()*34}; pose(a,'sit')}
   draw(a,el,c,friend);
  }
  requestAnimationFrame(step);
 }
 requestAnimationFrame(step);
 return {command,start:startToy,stop:stopToy};
}
