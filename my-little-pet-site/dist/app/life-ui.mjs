import {TRAITS,DECOR,adventure,recordAdventure,claimAdventure,bondLabel,pairKey,placeDecor,putAwayDecor,BASE_LAYOUT} from './life.mjs?v=1.6-free-1';
export function setupLife(api){
 const $=s=>document.querySelector(s);let editing=false,selected='bed',xy=[24,72],preview=true,drag=null;
 const baseSelectors={bed:'.room-bed',roomPlant:'.room-shelf',roomRug:'.rug',foodBowl:'.bowl'};
 const room=$('#pet-room');
 function choose(key){selected=key;xy=[...(api.getState().layout[key]||BASE_LAYOUT[key]||[50,72])];preview=true;render()}
 for(const [key,selector] of Object.entries(baseSelectors))$(selector).dataset.roomItem=key;
 const select=$('#personality-select');select.replaceChildren(...Object.entries(TRAITS).map(([value,t])=>Object.assign(document.createElement('option'),{value,textContent:t.name})));
 const save=()=>{api.persist();api.render()};
 select.onchange=()=>{api.sync();api.getState().trait=select.value;save();api.toast('A little personality, all their own.')};
 $('#quiet-toggle').onclick=()=>{api.sync();const s=api.getState();s.quiet=!s.quiet;save();api.speak(s.quiet?'A quiet little moment. I’ll rest here with you.':'Ready for another little adventure!')};
 $('#pause-toggle').onclick=()=>{api.cancelGames();api.sync();const s=api.getState();s.paused=!s.paused;s.lastAt=Date.now();save();api.toast(s.paused?'Paused. Needs and activities take a break.':'Welcome back. Your little world is awake.')};
 $('#recover-pets').onclick=()=>{api.sync();api.getState().solo=false;api.getState().paused=false;api.resetPosition();save();api.speak('Here we are! Everyone is back in the room.')};
 $('#lost-star').onclick=()=>{api.sync();if(api.getState().paused)return;recordAdventure(api.getState(),'find');save();api.speak('You found my little star! Check Today for our adventure. ✦')};
 $('#claim-adventure').onclick=()=>{api.sync();if(claimAdventure(api.getState())){save();api.toast('+6 coins. A lovely little adventure together.')}};
 $('#decorate-toggle').onclick=()=>{editing=!editing;if(editing)choose(selected);$('#decor-editor').hidden=!editing;render();if(editing)$('#decor-editor').scrollIntoView({behavior:'smooth',block:'nearest'})};
 $('#decor-cancel').onclick=()=>{editing=false;$('#decor-editor').hidden=true;render()};
 for(const axis of ['x','y'])$('#decor-'+axis).oninput=()=>{xy=[$('#decor-x').valueAsNumber,$('#decor-y').valueAsNumber];preview=true;renderDecor()};
 $('#decor-place').onclick=()=>{api.sync();if(placeDecor(api.getState(),selected,xy)){save();api.toast('Placed! You can move owned items for free.')}else api.toast('Save a few more coins. Previewing is always free.')};
 $('#decor-choices').replaceChildren(...Object.entries(DECOR).map(([key,d])=>{const b=document.createElement('button');b.textContent=d.icon+' '+d.name;b.dataset.decor=key;b.onclick=()=>{choose(key)};return b}));
 $('#decor-remove').onclick=()=>{api.sync();if(putAwayDecor(api.getState(),selected)){preview=false;save();api.toast('Put away safely. Select it and Place to bring it back for free.')}};
 room.addEventListener('click',e=>{if(editing){e.preventDefault();e.stopImmediatePropagation()}},true);
 room.addEventListener('pointerdown',e=>{
  if(!editing||e.button!==0)return;
  const item=e.target.closest('[data-room-item]');if(!item)return;
  e.preventDefault();e.stopPropagation();choose(item.dataset.roomItem);
  const r=room.getBoundingClientRect();drag={id:e.pointerId,start:[e.clientX,e.clientY],offset:[(e.clientX-r.left)/r.width*100-xy[0],(e.clientY-r.top)/r.height*100-xy[1]],moved:false};room.setPointerCapture(e.pointerId);
 });
 room.addEventListener('pointermove',e=>{if(!drag||e.pointerId!==drag.id)return;const r=room.getBoundingClientRect();if(Math.hypot(e.clientX-drag.start[0],e.clientY-drag.start[1])>3)drag.moved=true;if(!drag.moved)return;xy=[Math.max(16,Math.min(84,(e.clientX-r.left)/r.width*100-drag.offset[0])),Math.max(22,Math.min(86,(e.clientY-r.top)/r.height*100-drag.offset[1]))];renderDecor();$('#decor-x').value=xy[0];$('#decor-y').value=xy[1]});
 room.addEventListener('pointerup',e=>{if(!drag||e.pointerId!==drag.id)return;const moved=drag.moved;drag=null;room.releasePointerCapture(e.pointerId);if(moved){api.sync();if(placeDecor(api.getState(),selected,xy)){save();api.toast('Position saved.')}}});
 room.addEventListener('pointercancel',()=>{drag=null;choose(selected)});
 function renderDecor(){
  const s=api.getState(),layout={...BASE_LAYOUT,...s.layout};if(editing&&preview)layout[selected]=xy;
  const hidden=key=>(s.hiddenDecor||[]).includes(key)&&!(editing&&preview&&selected===key);
  for(const [key,selector] of Object.entries(baseSelectors)){
   const el=$(selector),pos=layout[key];el.hidden=hidden(key);el.classList.toggle('decor-preview',editing&&preview&&selected===key);
   if(pos){el.style.left=pos[0]+'%';el.style.top=pos[1]+'%';el.style.bottom='auto';el.style.right='auto';el.style.translate='-50% -50%'}else{for(const prop of ['left','top','bottom','right','translate'])el.style[prop]=''}
  }
  const keys=new Set([...s.ownedDecor.filter(k=>!Object.hasOwn(baseSelectors,k)&&(k==='toy'||s.layout[k])),...(editing&&preview&&!Object.hasOwn(baseSelectors,selected)?[selected]:[])]);
  $('#placed-decor').replaceChildren(...[...keys].filter(k=>!hidden(k)).map(key=>{const p=layout[key]||BASE_LAYOUT[key]||[76,76],el=document.createElement('span');el.dataset.roomItem=key;el.className='decor-item decor-'+key+(editing&&preview&&selected===key?' decor-preview':'');if(key==='toy'||['flowers','lamp','books'].includes(key)){const img=document.createElement('img');img.src=`../assets/supplies/${key==='toy'?'toy-'+s.selectedToy:'decor-'+key}.png`;img.alt=key==='toy'?'Selected toy':DECOR[key].name;el.append(img)}else el.textContent=DECOR[key].icon;el.style.left=p[0]+'%';el.style.top=p[1]+'%';return el}));
 }
 function render(){
  const s=api.getState(),a=adventure(s);$('#room-panel').classList.toggle('room-editing',editing);$('#pet-room').classList.toggle('quiet-time',s.quiet);$('#pet-room').classList.toggle('world-paused',s.paused);$('#quiet-toggle').setAttribute('aria-pressed',String(s.quiet));$('#quiet-toggle').textContent=s.quiet?'☾ Quiet time on':'☾ Quiet time';$('#pause-toggle').textContent=s.paused?'Resume':'Pause';
  $('#trait-note').textContent=`${s.pet} · ${TRAITS[s.trait].name} · ${TRAITS[s.trait].detail}${s.paused?' · Paused':''}`;
  select.value=s.trait;$('#personality-detail').textContent=TRAITS[s.trait].detail;
  const people=[s,...s.companions],rows=[];for(let i=0;i<people.length;i++)for(let j=i+1;j<people.length;j++){const points=s.bonds[pairKey(people[i],people[j])]?.points||0,row=document.createElement('div');row.className='friendship-row';row.append(Object.assign(document.createElement('strong'),{textContent:`${people[i].pet} + ${people[j].pet}`}),Object.assign(document.createElement('small'),{textContent:`${bondLabel(points)} · ${points}/100`}),Object.assign(document.createElement('progress'),{value:points,max:100}));rows.push(row)}$('#friendship-list').replaceChildren(...rows);if(!rows.length)$('#friendship-list').textContent='Add a friend to begin a growing friendship.';
  $('#adventure-list').replaceChildren(...[['find','Find the lost star',1],['game','Play Fetch or Hurdles',1],['cuddle','Give little cuddles',3]].map(([k,label,n])=>{const row=document.createElement('p');row.textContent=`${a[k]||0}/${n} · ${label}`;return row}));$('#claim-adventure').disabled=a.claimed||!a.find||!a.game||a.cuddle<3;$('#claim-adventure').textContent=a.claimed?'Today’s adventure collected ✓':'Claim 6 coins';
  const star=$('#lost-star');star.hidden=!!a.find||editing;star.style.left=(18+[...a.date].reduce((n,c)=>n+c.charCodeAt(0),0)%60)+'%';
  document.querySelectorAll('[data-decor]').forEach(b=>{b.setAttribute('aria-pressed',String(b.dataset.decor===selected))});$('#decor-x').value=xy[0];$('#decor-y').value=xy[1];$('#decor-remove').disabled=!s.ownedDecor.includes(selected)||(s.hiddenDecor||[]).includes(selected);const cost=s.ownedDecor.includes(selected)?0:DECOR[selected].price;$('#decor-place').textContent=cost?`Buy & place · ${cost} coins`:'Place for free';renderDecor();
 }
 return {render};
}
