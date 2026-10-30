import {setupCatchGames} from './catch-games.mjs?v=1.6-free-1';
import {setupToyPlay} from './toy-play.mjs?v=1.6-free-1';
import {fresh,normalize,tick,care,name,buy,claimDaily,xpNeeded,PETS,STYLES,ROOMS,FOODS,SLOT_PRICES,buySlot,addFriend,selectFriend,selectFood,refillLives,greetFriend,buyRoom} from './engine.mjs?v=1.6-free-1';
import {setupArcade} from './arcade.mjs?v=1.6-free-1';
import {setupPetGames} from './pet-games.mjs?v=1.6-free-1';
import {setupLife} from './life-ui.mjs?v=1.6-free-1';
import {befriend,bondLabel,pairKey,TOYS,selectToy} from './life.mjs?v=1.6-free-1';
import {setupComforts} from './comforts.mjs?v=1.6-free-1';
let lifeUI=null;
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)], KEY='my-little-pet-plus-mobile-v1';
let storageOK=true, state, currentTab='room', poseTimer, toastTimer, promptEvent, audioContext, confirmAction, socialUntil=0, socialKind="";
const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
function warnStorage(){storageOK=false;$('#storage-warning').hidden=false;$('#storage-warning').textContent='This browser could not save your pet. Keep this page open and use Settings → Export backup before leaving.';}
function read(){try{const value=localStorage.getItem(KEY)||localStorage.getItem('my-little-pet-mobile-v1');return value?normalize(JSON.parse(value)):null}catch(e){warnStorage();return null}}
const initialSave=read();state=initialSave||fresh();tick(state);
function persist(){try{localStorage.setItem(KEY,JSON.stringify(state));storageOK=true;$('#storage-warning').hidden=true}catch(e){warnStorage()}}
function sync(){const saved=read();if(saved)state=tick(saved);else tick(state);}
function toast(message){$('#toast').textContent=message;$('#toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').hidden=true,3800)}
function speak(message){$('#speech').textContent=message}
function sound(){if(!state.sound||state.quiet||state.paused)return;try{audioContext??=new (window.AudioContext||window.webkitAudioContext)();audioContext.resume();const o=audioContext.createOscillator(),g=audioContext.createGain();const voices={cat:[560,790,'sine'],dog:[180,90,'triangle'],bunny:[900,1200,'sine'],fox:[420,850,'triangle'],dino:[220,350,'triangle'],tiger:[130,65,'triangle'],parrot:[1200,700,'sine']};const [a,b,w]=voices[state.species];o.type=w;o.frequency.setValueAtTime(a,audioContext.currentTime);o.frequency.exponentialRampToValueAtTime(b,audioContext.currentTime+.13);g.gain.setValueAtTime(.035,audioContext.currentTime);g.gain.exponentialRampToValueAtTime(.001,audioContext.currentTime+.22);o.connect(g);g.connect(audioContext.destination);o.start();o.stop(audioContext.currentTime+.23)}catch{}}
function petImage(pose){$('#pet-image').style.transform=reduced||state.quiet||state.paused?'none':pose==='eat'?'translateY(3px) scale(.98)':pose==='happy'||pose==='dance'?'translateY(-3px) scale(1.02)':'none';const next=`../assets/pets/${state.species}-${state.coat}${reduced||state.quiet||state.paused?'.png':`-${pose}.gif`}`;if($('#pet-image').getAttribute('src')!==next)$('#pet-image').src=next;$('#pet-image').alt=`${state.pet}, your little ${PETS[state.species].name.toLowerCase()}`;}
function render(){
  const bowl=document.querySelector('.bowl');bowl.src=`../assets/supplies/food-${state.selectedFood}.png`;bowl.alt=FOODS[state.selectedFood].name;
  $('#greeting').replaceChildren(document.createTextNode(`Hi, ${state.owner} `),Object.assign(document.createElement('span'),{textContent:'♡'}));
  $('#subtitle').textContent=state.sleeping?`${state.pet} is dreaming of little adventures.`:`${state.pet} is happy you’re here.`;
  $('#coins').textContent=state.coins;$('#pet-level').textContent=`${state.pet} · Level ${state.level}`;$('#xp-label').textContent=`${state.xp} / ${xpNeeded(state.level)} XP`;$('#xp').max=xpNeeded(state.level);$('#xp').value=state.xp;
  for(const [id,key] of [['food','food'],['happy','happy'],['energy','energy']]){$(`#${id}-meter`).value=state[key];$(`#${id}-value`).textContent=`${Math.round(state[key])}%`}
  $('#pet-room').className=`pet-room ${state.room}${!state.solo&&state.companions.length?' has-family':''}${Date.now()<socialUntil?' social-'+socialKind:''}`;$('#room-label').textContent=ROOMS[state.room].name.toUpperCase();$('#accessory').textContent=STYLES[state.accessory].emoji;$('#accessory').hidden=state.sleeping;$('#sleep-label').hidden=!state.sleeping;
  $('#rest-button b').textContent=state.sleeping?'Wake up':'Rest';$('#rest-button small').textContent=state.sleeping?'hello again':'restore energy';
  if(!poseTimer||state.quiet||state.paused)petImage(state.sleeping?'sleep':'idle');
  $('#save-note').textContent=storageOK?'Saved on this device. A little world of your own.':'Save unavailable. Export a backup in Settings.';
  if(currentTab==='wardrobe')renderShop();if(currentTab==='goals')renderGoals();if(currentTab==='family')renderFamily();renderFriends();const next=Math.max(1,Math.ceil((1800000-(Date.now()-state.arcade.refillAt))/60000));$('#arcade-note').textContent=`${state.arcade.lives}/3 arcade lives · ${state.arcade.earned}/40 game coins today. ${state.arcade.lives<3?'Next life in '+next+' min. ':''}No lives? Play free practice.`;$('#refill-lives').disabled=state.arcade.lives===3||state.coins<20;lifeUI?.render();
}
function tab(key){currentTab=key;$$('.tab-panel').forEach(el=>el.hidden=el.id!==`${key}-panel`);$$('[data-tab]').forEach(b=>{if(b.dataset.tab===key)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current')});sync();render();if(key==='settings'){$('#profile-owner').value=state.owner;$('#profile-pet').value=state.pet;$('#sound-toggle').checked=state.sound}window.scrollTo({top:0,behavior:'instant'})}
$$('[data-tab]').forEach(b=>b.addEventListener('click',()=>tab(b.dataset.tab)));
function doCare(kind){sync();const result=care(state,kind);persist();render();speak(result.message);if(result.ok){if(kind==='play'){socialKind='play';socialUntil=Date.now()+2300;$('#pet-room').classList.add('social-play')}sound();clearTimeout(poseTimer);poseTimer=null;petImage(result.pose);if(!state.sleeping)poseTimer=setTimeout(()=>{poseTimer=null;petImage('idle')},2300)}else toast(result.message);return result;}
$$('[data-care]').forEach(b=>b.addEventListener('click',()=>doCare(b.dataset.care)));$('#pet-touch').addEventListener('click',()=>doCare('pet'));
function card(text,detail,image,selected,handler,emoji){const b=document.createElement('button');b.className='shop-item'+(selected?' selected':'');b.setAttribute('aria-pressed',String(selected));if(image){const img=document.createElement('img');img.src=image;img.alt=text;img.width=100;img.height=100;b.append(img)}else{const e=document.createElement('span');e.className='style-emoji'+(emoji?'':' empty');e.textContent=emoji||'✧';b.append(e)}b.append(Object.assign(document.createElement('strong'),{textContent:text}),Object.assign(document.createElement('small'),{textContent:detail}));b.addEventListener('click',handler);return b}
function renderShop(){
  $('.shop-coins').textContent=`◉ ${state.coins} coins`;
  $('#pet-shop').replaceChildren(...Object.entries(PETS).map(([key,p])=>card(p.name,state.species===key?'Your little friend ✓':state.ownedPets.includes(key)?'Choose this pet':`${p.price} coins`,`../assets/pets/${key}-0.png`,state.species===key,()=>purchase('pet',key))));
  $('#food-shop').replaceChildren(...Object.entries(FOODS).map(([key,f])=>card(f.name,`${key==='kibble'?'Free':`${state.pantry[key]||0} left · ${f.price} coins`} · +${f.food} food`,`../assets/supplies/food-${key}.png`,state.selectedFood===key,()=>{sync();if(!selectFood(state,key)){toast('More coins needed. The everyday bowl is free.');return}persist();render();toast('Next meal: '+f.name)},f.icon)));
  $('#toy-shop').replaceChildren(...Object.entries(TOYS).map(([key,t])=>card(t.name,state.selectedToy===key?'Selected ✓':state.ownedToys.includes(key)?'Choose this toy':`${t.price} coins`,`../assets/supplies/toy-${key}.png`,state.selectedToy===key,()=>{sync();if(!selectToy(state,key)){toast('Save a few more coins for this toy.');return}persist();render();toast(t.name+' is ready for play!')})));
  $('#style-shop').replaceChildren(...Object.entries(STYLES).map(([key,s])=>card(s.name,state.accessory===key?'Wearing ✓':state.ownedStyles.includes(key)?'Put it on':`${s.price} coins`,null,state.accessory===key,()=>purchase('style',key),s.emoji)));
  $('#coat-shop').replaceChildren(...[0,1,2].map(coat=>{const b=document.createElement('button');b.className=coat===state.coat?'selected':'';b.setAttribute('aria-pressed',String(coat===state.coat));const img=document.createElement('img');img.src=`../assets/pets/${state.species}-${coat}.png`;img.alt=`Coat ${coat+1}`;b.append(img,document.createTextNode(['Original','Warm & cozy','Moonlight'][coat]));b.onclick=()=>{sync();state.coat=coat;persist();poseTimer&&clearTimeout(poseTimer);poseTimer=null;render();sound()};return b}));
  $('#room-shop').replaceChildren(...Object.entries(ROOMS).map(([key,r])=>{const b=document.createElement('button');b.className='room-option '+key+(key===state.room?' selected':'');b.setAttribute('aria-pressed',String(key===state.room));b.append(Object.assign(document.createElement('span'),{className:'room-swatch',textContent:'⌂'}),Object.assign(document.createElement('strong'),{textContent:r.name}),Object.assign(document.createElement('small'),{textContent:key===state.room?'Your cozy home ✓':state.ownedRooms.includes(key)?'Move in →':r.price?`${r.price} coins · walls, floor & bed`:`Unlock at level ${r.level}`}));b.onclick=()=>{sync();if(!buyRoom(state,key)){toast(r.price?'Save a few more coins for this home.':`Grow to level ${r.level} to unlock this room.`);return}persist();render();sound();toast(r.name+' is ready. Make yourself at home!')};return b}));
}
function purchase(kind,key){sync();if(!buy(state,kind,key)){toast('A few more coins! Earn them with care and the treat hunt.');return}persist();clearTimeout(poseTimer);poseTimer=null;render();sound();toast(kind==='pet'?'A new look, the same little friendship.':'Looking lovely!');}
function renderGoals(){const done=state.daily;$('#daily-list').replaceChildren(...[['feed','Feed your pet twice'],['play','Play together twice'],['pet','Give two little cuddles']].map(([key,label])=>{const row=document.createElement('div');row.append(document.createTextNode(label),Object.assign(document.createElement('b'),{textContent:`${Math.min(2,done[key])} / 2 ${done[key]>=2?'✓':''}`}));return row}));const ready=done.feed>=2&&done.play>=2&&done.pet>=2;$('#claim-daily').disabled=!ready||done.claimed;$('#claim-daily').textContent=done.claimed?'Today’s coins collected ✓':'Claim 12 coins';$('#daily-status').textContent=done.claimed?'Come back tomorrow for another little day together.':ready?'You made their day. Your reward is ready.':'A few small acts of care. You’ve got this.';$('#milestone-copy').textContent=`${state.totalCare} moments of care. Level ${state.level}. One very loved ${PETS[state.species].name.toLowerCase()}.`;}
$('#claim-daily').onclick=()=>{sync();if(claimDaily(state)){persist();render();sound();toast('+12 coins. What a lovely little day!')}};
$('#profile-form').onsubmit=e=>{e.preventDefault();sync();state.owner=name($('#profile-owner').value,state.owner);state.pet=name($('#profile-pet').value,state.pet);persist();
render();speak(`Hi ${state.owner}! I’m ${state.pet}. ♡`);toast('Names saved. Same little friendship.')};
$('#sound-toggle').onchange=e=>{sync();state.sound=e.target.checked;persist();sound()};
$('#export').onclick=()=>{sync();const blob=new Blob([JSON.stringify(state,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`my-little-pet-${state.pet.toLowerCase().replace(/ /g,'-')}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);toast('Backup created. Keep it somewhere safe.')};
function confirm(title,message,action){confirmAction=action;$('#confirm-title').textContent=title;$('#confirm-message').textContent=message;$('#confirm-dialog').showModal()}
$('#confirm-cancel').onclick=()=>{$('#confirm-dialog').close();confirmAction=null};$('#confirm-yes').onclick=()=>{$('#confirm-dialog').close();const action=confirmAction;confirmAction=null;action?.()};
$('#import').onclick=()=>$('#import-file').click();$('#import-file').onchange=async e=>{const file=e.target.files[0];e.target.value='';if(!file)return;try{if(file.size>100000)throw new Error('This file is too large to be a pet backup.');const imported=normalize(JSON.parse(await file.text()));confirm('Bring back this friend?',`Restore ${imported.pet} for ${imported.owner}? This replaces your current mobile pet. Export your current pet first if you want to keep both.`,()=>{state=tick(imported);state.onboarded=true;persist();tab('room');speak(`Hi ${state.owner}! It’s good to be home. ♡`);toast('Your little friend is back.')})}catch(error){toast(error instanceof SyntaxError?'That file is not valid JSON. Choose a mobile pet backup.':error.message)}};
$('#reset').onclick=()=>confirm('A new little beginning?',`This replaces ${state.pet} and their progress. Export a backup first if you want to keep this friendship.`,()=>{state=fresh();persist();tab('room');$('#welcome-owner').value='';$('#welcome-pet').value='Mochi';$('#welcome-dialog').showModal()});
$('#welcome-form').onsubmit=e=>{e.preventDefault();state.owner=name($('#welcome-owner').value,'Friend');state.pet=name($('#welcome-pet').value,'Mochi');state.onboarded=true;persist();$('#welcome-dialog').close();
render();speak(`Hi ${state.owner}! I’m ${state.pet}. ♡`);};
$('#welcome-dialog').addEventListener('cancel',e=>e.preventDefault());
if(!state.onboarded){const params=new URLSearchParams(location.search);$('#welcome-owner').value=name(params.get('owner'),'');$('#welcome-pet').value=name(params.get('pet'),'Mochi');$('#welcome-dialog').showModal()}
if(location.search)history.replaceState(null,'',location.pathname);
window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();promptEvent=e});
async function install(){if(matchMedia('(display-mode: standalone)').matches||navigator.standalone){toast('Your pet already has a home on this device.');return}if(promptEvent){const event=promptEvent;promptEvent=null;await event.prompt();await event.userChoice}else $('#install-dialog').showModal()}
$$('.install-trigger').forEach(b=>b.onclick=install);window.addEventListener('appinstalled',()=>{promptEvent=null;toast('A new home for your little friend!')});
$$('.close-dialog').forEach(b=>b.onclick=()=>b.closest('dialog').close());
const catchGames=setupCatchGames({getState:()=>state,sync,persist,render,sound,speak,toast});
const arcade=setupArcade({getState:()=>state,sync,persist,render,sound,speak,toast});
const petGames=setupPetGames({getState:()=>state,sync,persist,render,sound,speak,toast});
$('#refill-lives').onclick=()=>{sync();if(refillLives(state)){persist();render();toast('Three lives ready. Have fun!')}};
const friendPoses=new Map();
function renderFriends(){
 const panel=$('#room-friends');if(state.solo){panel.replaceChildren();return}
 while(panel.children.length>state.companions.length)panel.lastElementChild.remove();
 state.companions.forEach((p,i)=>{
  let b=panel.children[i];if(!b){b=document.createElement('button');b.append(document.createElement('img'),document.createElement('small'));b.onclick=()=>{sync();const message=greetFriend(state,i);if(!message)return;persist();friendPoses.set(i,Date.now()+3000);speak(message);renderFriends();$('#pet-room').dispatchEvent(new CustomEvent('friend-greet',{detail:{id:state.companions[i].id}}));sound()};panel.append(b)}
  const phase=(Math.floor(Date.now()/8000)+i*2)%9;
  const pose=state.quiet||state.paused?'idle':p.sleeping?'sleep':Date.now()<(friendPoses.get(i)||0)?'wave':Date.now()<socialUntil&&socialKind==='dance'?'dance':p.food<35?'eat':p.trait==='sleepy'?'sleep':p.trait==='shy'?(phase===6?'wave':'idle'):phase===0?'dance':phase===3?'happy':phase===6?'wave':'idle';
  b.setAttribute('aria-label',`Say hello to ${p.pet}`);const img=b.querySelector('img'),src=`../assets/pets/${p.species}-${p.coat}${reduced||state.quiet||state.paused?'.png':'-'+pose+'.gif'}`;if(img.getAttribute('src')!==src)img.src=src;img.alt=p.pet;b.querySelector('small').textContent=p.pet;
 });
}
function switchFriend(i){friendPoses.clear();sync();if(selectFriend(state,i)){persist();clearTimeout(poseTimer);poseTimer=null;tab('room');speak(`Hi ${state.owner}! It’s ${state.pet}’s turn. ♡`)}}
function renderFamily(){
 $('#family-list').replaceChildren(...[state,...state.companions].map((p,i)=>card(p.pet,`${PETS[p.species].name} · Food ${Math.round(p.food)}% · Joy ${Math.round(p.happy)}%`,`../assets/pets/${p.species}-${p.coat}.png`,i===0,()=>i===0?tab('settings'):switchFriend(i-1))));
 $('#slots-note').textContent=`${state.companions.length+1} pets / ${state.slots} slots. ${state.slots-state.companions.length-1} empty. ${state.coins} coins.`;
 $('#buy-slot').textContent=state.slots===4?'All four slots unlocked':`Unlock slot ${state.slots+1} · ${SLOT_PRICES[state.slots-1]} coins`;$('#buy-slot').disabled=state.slots===4||state.coins<SLOT_PRICES[state.slots-1];
 const select=$('#friend-species'),previous=select.value;select.replaceChildren(...state.ownedPets.map(key=>Object.assign(document.createElement('option'),{value:key,textContent:PETS[key].name})));if(state.ownedPets.includes(previous))select.value=previous;
 $('#add-friend-form button').disabled=state.companions.length+1>=state.slots;
 $('#solo-toggle').textContent=state.solo?'Show my whole family':'Show only my selected pet';$('#solo-toggle').setAttribute('aria-pressed',String(state.solo));
}
$('#buy-slot').onclick=()=>{sync();if(buySlot(state)){persist();render();sound();toast('Slot unlocked! Choose a species and name below to add your pet.');$('#friend-name').focus()}};
$('#add-friend-form').onsubmit=e=>{e.preventDefault();sync();if(addFriend(state,$('#friend-species').value,$('#friend-name').value)){persist();render();sound();tab('room');toast('Welcome home! Both pets are now visible.')}else toast('Unlock a free slot first.')};
$('#solo-toggle').onclick=()=>{sync();state.solo=!state.solo;persist();render()};
let socialTimer;function socialize(kind){sync();if(state.quiet||state.paused)return;if(state.solo||!state.companions.length){toast('Add a friend and show your family first.');return}tab('room');const other=state.companions[Math.floor(Date.now()/30000)%state.companions.length];const points=befriend(state,state,other);persist();if(kind==='chat'&&points>=25)kind='snuggle';const lines={snuggle:[`${state.pet}: Save me a cozy spot?`,`${other.pet}: Always room for you. ${bondLabel(points)}! ♡`],chat:[`${state.pet}: Snack buddies?`,`${other.pet}: Always, bestie! ♡`],dance:[`${state.pet}: One, two, wiggle!`,`${other.pet}: Our little duet! ♫`],wrestle:[`${state.pet}: Pillow duel!`,`${other.pet}: You win! Still best friends. Big hug! ♡`]};speak(lines[kind][0]);clearTimeout(socialTimer);socialTimer=setTimeout(()=>speak(lines[kind][1]),2000);clearTimeout(poseTimer);poseTimer=null;petImage(kind==='dance'?'dance':'happy');socialKind=kind;socialUntil=Date.now()+4500;$('#pet-room').classList.add('social-'+kind);$('#pet-room').dispatchEvent(new CustomEvent('pet-social',{detail:{kind}}));renderFriends();poseTimer=setTimeout(()=>{poseTimer=null;socialUntil=0;render()},4500);sound()}
$$('[data-social]').forEach(b=>b.onclick=()=>socialize(b.dataset.social));
let follow=false;
window.addEventListener('storage',e=>{if(e.key===KEY){sync();clearTimeout(poseTimer);poseTimer=null;render()}});
document.addEventListener('visibilitychange',()=>{if(document.hidden){arcade.cancel();petGames.cancel();catchGames.cancel()}if(!document.hidden){sync();render()}});
setInterval(()=>{if(!document.hidden){sync();render()}},5000);
if('serviceWorker' in navigator){navigator.serviceWorker.register('./sw.js').then(async reg=>{await navigator.serviceWorker.ready;const target=reg.active||reg.waiting||reg.installing;target?.postMessage({type:'CHECK_OFFLINE'})}).catch(()=>{$('#offline-status').textContent='Offline setup is unavailable here. Keep an internet connection for now.'});navigator.serviceWorker.addEventListener('message',e=>{if(e.data?.type==='OFFLINE_READY')$('#offline-status').textContent='Ready for offline visits. Your little room is cached.'})}else $('#offline-status').textContent='This browser does not support offline installation. You can still play online.';
lifeUI=setupLife({getState:()=>state,sync,persist,render,speak,toast,cancelGames:()=>{arcade.cancel();petGames.cancel();catchGames.cancel()},resetPosition:()=>{follow=false;$('#pet-touch').style.translate='0 0';$('#follow-toggle').setAttribute('aria-pressed','false');$('#follow-toggle').textContent='↗ Follow my touch'}});
setInterval(()=>{if(!document.hidden&&currentTab==='room'&&!state.quiet&&!state.paused&&!state.solo&&state.companions.length&&!document.querySelector('dialog[open]'))socialize(['chat','dance','wrestle'][Math.floor(Date.now()/30000)%3])},30000);
setupComforts({getState:()=>state,sync,persist});
render();speak(`Hi ${state.owner}! I’m ${state.pet}. ♡`);

setupToyPlay({getState:()=>state,speak,care:doCare}).catch(()=>toast('Room animations could not load. Reopen the app online to finish updating.'));
