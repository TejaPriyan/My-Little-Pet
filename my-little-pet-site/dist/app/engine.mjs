import {lifeMember,normalizeLife,recordAdventure,adventure} from './life.mjs?v=1.6-free-1';
export const VERSION=3;
export const PETS={cat:{name:'Kitty',price:0},dog:{name:'Puppy',price:160},bunny:{name:'Bunny',price:200},fox:{name:'Fox',price:260},dino:{name:'Dino',price:450},tiger:{name:'Tiger',price:650},parrot:{name:'Parrot',price:800}};
export const SLOT_PRICES=[250,600,1000];
export const FOODS={kibble:{name:'Everyday bowl',price:0,food:20,happy:3,energy:0,icon:'◒'},berries:{name:'Berry bowl',price:8,food:28,happy:10,energy:0,icon:'🫐'},fish:{name:'Fish bites',price:12,food:38,happy:8,energy:3,icon:'🐟'},greens:{name:'Garden greens',price:10,food:32,happy:6,energy:8,icon:'🥬'},milk:{name:'Creamy pet milk',price:8,food:18,happy:9,energy:6,icon:'🥛'},soup:{name:'Pumpkin soup',price:14,food:35,happy:8,energy:10,icon:'🥣'},feast:{name:'Party platter',price:24,food:55,happy:20,energy:12,icon:'🍱'}};
export const STYLES={none:{name:'Natural cuteness',price:0,emoji:''},bow:{name:'Pretty bow',price:35,emoji:'🎀'},flower:{name:'Flower friend',price:35,emoji:'🌸'},crown:{name:'Tiny royalty',price:100,emoji:'👑'}};
export const ROOMS={classic:{name:'Lavender nook',level:1},garden:{name:'Garden room',level:3},starlight:{name:'Starlight room',level:5},seaside:{name:'Seaside cottage',level:1,price:180},cabin:{name:'Woodland cabin',level:1,price:260},moon:{name:'Moon suite',level:1,price:400}};
export const name=(v,fallback)=>typeof v==='string'?v.replace(/[^a-z0-9 -]/gi,'').trim().slice(0,12)||fallback:fallback;
const num=(v,min,max,fallback)=>typeof v==='number'&&Number.isFinite(v)?Math.min(max,Math.max(min,v)):fallback;
export const dayKey=(now=Date.now())=>{const d=new Date(now);return `${d.getFullYear()}-${d.getMonth()+1}-${d.getDate()}`};
export function fresh(owner='Friend',pet='Mochi',now=Date.now()){return {format:'my-little-pet-mobile',version:VERSION,owner:name(owner,'Friend'),pet:name(pet,'Mochi'),species:'cat',coat:0,accessory:'none',room:'classic',ownedPets:['cat'],ownedRooms:['classic'],ownedStyles:['none'],food:80,happy:85,energy:90,coins:20,level:1,xp:0,lastAt:now,sleeping:false,cooldowns:{},rewardTimes:{},daily:{date:dayKey(now),feed:0,play:0,pet:0,claimed:false},totalCare:0,onboarded:false,sound:false,companions:[],slots:1,solo:false,pantry:{},selectedFood:'kibble',arcade:{lives:3,refillAt:now,date:dayKey(now),earned:0},round:null,...lifeMember({}),bonds:{},adventure:{},ownedDecor:['bed','toy','roomPlant','roomRug','foodBowl'],hiddenDecor:[],ownedToys:['ball'],selectedToy:'ball',layout:{},quiet:false,paused:false};}
function member(raw,s){return {...lifeMember(raw),pet:name(raw.pet,'Little friend'),species:s.ownedPets.includes(raw.species)?raw.species:'cat',coat:Math.floor(num(raw.coat,0,2,0)),accessory:s.ownedStyles.includes(raw.accessory)?raw.accessory:'none',food:num(raw.food,0,100,80),happy:num(raw.happy,0,100,85),energy:num(raw.energy,0,100,90),sleeping:raw.sleeping===true};}
export function normalize(raw,now=Date.now()){
 if(!raw||typeof raw!=='object'||Array.isArray(raw)||raw.format!=='my-little-pet-mobile'||![1,2,3].includes(raw.version))throw new Error('This is not a supported My Little Pet mobile backup.');
 const s=fresh(raw.owner,raw.pet,now);
 s.coins=Math.floor(num(raw.coins,0,1000000,20));s.level=Math.floor(num(raw.level,1,999,1));s.xp=Math.floor(num(raw.xp,0,xpNeeded(s.level)-1,0));
 s.ownedPets=[...new Set(['cat',...(Array.isArray(raw.ownedPets)?raw.ownedPets.filter(p=>typeof p==='string'&&Object.hasOwn(PETS,p)):[])])];
 s.ownedStyles=[...new Set(['none',...(Array.isArray(raw.ownedStyles)?raw.ownedStyles.filter(p=>typeof p==='string'&&Object.hasOwn(STYLES,p)):[])])];
 Object.assign(s,member(raw,s));s.ownedRooms=[...new Set(['classic',...Object.keys(ROOMS).filter(k=>!ROOMS[k].price&&ROOMS[k].level<=s.level),...(Array.isArray(raw.ownedRooms)?raw.ownedRooms.filter(k=>typeof k==='string'&&Object.hasOwn(ROOMS,k)):[])])];s.room=s.ownedRooms.includes(raw.room)?raw.room:'classic';
 s.lastAt=num(raw.lastAt,0,now,now);s.sound=raw.sound===true;s.onboarded=raw.onboarded===true;s.totalCare=Math.floor(num(raw.totalCare,0,1e9,0));
 for(const k of ['feed','play','pet','game','friend'])s.cooldowns[k]=num(raw.cooldowns?.[k],0,now+60000,0);
 for(const k of ['feed','play','pet'])s.rewardTimes[k]=num(raw.rewardTimes?.[k],0,now+180000,0);
 if(raw.daily?.date===dayKey(now))for(const k of ['feed','play','pet'])s.daily[k]=Math.floor(num(raw.daily[k],0,3,0));
 s.daily.claimed=raw.daily?.date===s.daily.date&&raw.daily?.claimed===true;
 s.slots=Math.floor(num(raw.slots,1,4,1));s.solo=raw.solo===true;
 if(Array.isArray(raw.companions))s.companions=raw.companions.filter(p=>p&&typeof p==='object'&&!Array.isArray(p)).slice(0,s.slots-1).map(p=>member(p,s));
 for(const k of Object.keys(FOODS))s.pantry[k]=Math.floor(num(raw.pantry?.[k],0,999,0));
 s.selectedFood=typeof raw.selectedFood==='string'&&Object.hasOwn(FOODS,raw.selectedFood)?raw.selectedFood:'kibble';
 s.arcade={lives:Math.floor(num(raw.arcade?.lives,0,3,3)),refillAt:num(raw.arcade?.refillAt,0,now,now),date:raw.arcade?.date===dayKey(now)?dayKey(now):'',earned:Math.floor(num(raw.arcade?.earned,0,40,0))};
 if(raw.round&&['hunt','memory','rhythm','fetch','hurdles','bugs','drop'].includes(raw.round.kind)&&typeof raw.round.id==='string')s.round={id:raw.round.id.slice(0,80),kind:raw.round.kind,paid:raw.round.paid===true,startAt:num(raw.round.startAt,0,now,now),duration:['memory','fetch','hurdles'].includes(raw.round.kind)?45000:30000,watch:raw.round.watch===true};
 normalizeLife(raw,s,now);
 return s;
}
function age(p,elapsed){p.food=Math.min(p.food,Math.max(15,p.food-elapsed*.004));p.happy=Math.min(p.happy,Math.max(25,p.happy-elapsed*.002));p.energy=p.sleeping?Math.min(100,p.energy+elapsed*.5):Math.min(p.energy,Math.max(20,p.energy-elapsed*.001));if(p.energy>=100)p.sleeping=false;}
export function tick(s,now=Date.now()){
 const elapsed=s.paused?0:Math.max(0,Math.min(43200,(now-s.lastAt)/1000));adventure(s,now);const sleeping=s.sleeping;if(s.quiet)s.sleeping=true;age(s,elapsed);if(s.quiet)s.sleeping=sleeping;for(const p of s.companions){if(p.energy<(p.trait==='sleepy'?55:35))p.sleeping=true;age(p,elapsed);if(!p.sleeping&&p.food<35)p.food=Math.min(35,p.food+elapsed*.04)}s.lastAt=now;
 if(s.daily.date!==dayKey(now))s.daily={date:dayKey(now),feed:0,play:0,pet:0,claimed:false};
 const a=s.arcade;a.refillAt=Math.min(now,a.refillAt);if(a.lives>=3)a.refillAt=now;else{const n=Math.floor(Math.max(0,now-a.refillAt)/1800000);a.lives=Math.min(3,a.lives+n);a.refillAt+=n*1800000;}
 if(a.date!==dayKey(now)){a.date=dayKey(now);a.earned=0}return s;
}
export function xpNeeded(level){return 40+20*(level-1)}
export function reward(s,xp,coins){s.coins+=coins;s.xp+=xp;let levels=0;while(s.xp>=xpNeeded(s.level)&&s.level<999){s.xp-=xpNeeded(s.level);s.level++;s.coins+=8;levels++}return levels}
export function reaction(s){const personal={shy:`A little hello, ${s.owner}. I feel safe here.`,sleepy:'Five more minutes? I was dreaming of snacks.',curious:`What’s over there, ${s.owner}? Let’s explore!`};if(personal[s.trait])return personal[s.trait];const lines=[`Hi ${s.owner}! You’re my person.`,`Tiny paws. Big love!`,`One more cuddle?`,`You make my tail wiggle!`,`Best friend alert!`,`I saved a little smile for you.`];return lines[Math.floor(Math.random()*lines.length)]}
export function care(s,kind,now=Date.now()){
 tick(s,now);
 if(s.paused)return {ok:false,message:'Your little world is paused. Tap Resume first.'};
 if(kind==='rest'){s.sleeping=!s.sleeping;return {ok:true,message:s.sleeping?'A cozy nap. I’ll be right here.':'Good morning, '+s.owner+'!',pose:s.sleeping?'sleep':'idle'}}
 if(kind==='dance'||kind==='wave'){if(s.sleeping)return {ok:false,message:'Wake me for our little dance.'};return {ok:true,message:kind==='dance'?'One, two, tiny wiggle!':reaction(s),pose:kind}}
 if(!['feed','play','pet'].includes(kind))return {ok:false,message:'Choose a care action.'};
 if(s.sleeping)return {ok:false,message:'I’m having a little nap. Tap Wake up first.'};
 if((s.cooldowns[kind]||0)>now)return {ok:false,message:kind==='pet'?reaction(s):`A little pause. Try again in ${Math.ceil((s.cooldowns[kind]-now)/1000)}s.`};
 if(kind==='feed'&&s.food>=98)return {ok:false,message:'My tummy is full. Thank you, '+s.owner+'!'};
 if(kind==='play'&&s.energy<12)return {ok:false,message:'A little sleepy. Let’s rest first.'};
 s.cooldowns[kind]=now+(kind==='pet'?2500:15000);s.totalCare++;
 if(kind==='feed'){let key=s.selectedFood;if(key!=='kibble'&&!s.pantry[key])key='kibble';if(key!=='kibble')s.pantry[key]--;const f=FOODS[key];s.food=Math.min(100,s.food+f.food);s.happy=Math.min(100,s.happy+f.happy);s.energy=Math.min(100,s.energy+f.energy);if(key!=='kibble'&&!s.pantry[key])s.selectedFood='kibble'}
 if(kind==='play'){s.happy=Math.min(100,s.happy+15);s.energy=Math.max(0,s.energy-10)}
 if(kind==='pet'){s.happy=Math.min(100,s.happy+4);recordAdventure(s,'cuddle',now)}
 s.daily[kind]=Math.min(3,s.daily[kind]+1);
 let levels=0;if((s.rewardTimes[kind]||0)<=now){s.rewardTimes[kind]=now+(kind==='play'?180000:120000);levels=reward(s,{feed:5,play:10,pet:3}[kind],kind==='play'?1:0)}
 return {ok:true,pose:kind==='feed'?'eat':kind==='pet'?'wave':'happy',message:levels?`Level ${s.level}! +8 coins. We’re growing together.`:kind==='pet'?reaction(s):kind==='feed'?'Yum! A little bowl of happiness.':'Best. Little. Break. Ever!'};
}
export function claimDaily(s,now=Date.now()){tick(s,now);if(s.daily.claimed||s.daily.feed<2||s.daily.play<2||s.daily.pet<2)return false;s.daily.claimed=true;s.coins+=12;return true}
export function buy(s,kind,key){const catalog=kind==='pet'?PETS:kind==='style'?STYLES:null;if(!catalog||!Object.hasOwn(catalog,key))return false;const owned=kind==='pet'?s.ownedPets:s.ownedStyles;if(!owned.includes(key)){if(s.coins<catalog[key].price)return false;s.coins-=catalog[key].price;owned.push(key)}if(kind==='pet'){s.species=key;s.coat=0}else s.accessory=key;return true}
export function buySlot(s){if(s.slots>=4||s.coins<SLOT_PRICES[s.slots-1])return false;s.coins-=SLOT_PRICES[s.slots-1];s.slots++;return true}
export function addFriend(s,species,pet){if(s.companions.length+1>=s.slots||!s.ownedPets.includes(species))return false;s.companions.push(member({pet:name(pet,PETS[species].name),species,coat:0},s));s.solo=false;return true}
export function selectFriend(s,index){if(!Number.isInteger(index)||index<0||index>=s.companions.length)return false;const old=member(s,s);Object.assign(s,s.companions[index]);s.companions[index]=old;return true}
export function selectFood(s,key){if(!Object.hasOwn(FOODS,key))return false;const f=FOODS[key];if(key!=='kibble'&&!(s.pantry[key]>0)){if(s.coins<f.price)return false;s.coins-=f.price;s.pantry[key]=1}s.selectedFood=key;return true}
export function refillLives(s,now=Date.now()){tick(s,now);if(s.arcade.lives>=3||s.coins<20)return false;s.coins-=20;s.arcade.lives=3;s.arcade.refillAt=now;return true}
export function startGame(s,kind,now=Date.now(),watch=false){tick(s,now);if(!['hunt','memory','rhythm','fetch','hurdles','bugs','drop'].includes(kind)||s.sleeping||s.paused)return null;watch=watch===true;const paid=!watch&&s.arcade.lives>0;if(paid)s.arcade.lives--;s.round={id:`${now}-${Math.random().toString(36).slice(2)}`,kind,paid,startAt:now,duration:['memory','fetch','hurdles'].includes(kind)?45000:30000,watch};return {...s.round}}
export function finishGame(s,id,score,now=Date.now()){tick(s,now);const r=s.round;if(!r||r.id!==id||now-r.startAt<r.duration)return null;s.round=null;const points=Math.floor(num(score,0,120,0));const coins=r.paid?Math.min(8,Math.floor(points/4),40-s.arcade.earned):0;const xp=r.paid?Math.min(18,points):0;if(!r.watch&&['fetch','hurdles'].includes(r.kind)&&points>0)recordAdventure(s,'game',now);s.arcade.earned+=coins;reward(s,xp,coins);if(!r.watch)s.happy=Math.min(100,s.happy+15);return {coins,xp,practice:!r.paid}}
export function finishHunt(s,hits,now=Date.now()){return s.round?.kind==='hunt'?finishGame(s,s.round.id,hits,now):null}

export function greetFriend(s,index){if(!Number.isInteger(index)||index<0||index>=s.companions.length)return null;const p=s.companions[index];if(s.paused)return 'Your little world is paused.';if((s.cooldowns.friend||0)>Date.now())return `${p.pet}: Hi ${s.owner}! One more little smile.`;s.cooldowns.friend=Date.now()+2500;recordAdventure(s,'cuddle');p.happy=Math.min(100,p.happy+3);return `${p.pet}: Hi ${s.owner}! Tiny paws, big love. ♡`;}
export function buyRoom(s,key){if(!Object.hasOwn(ROOMS,key))return false;const r=ROOMS[key];if(!s.ownedRooms.includes(key)){if(r.price){if(s.coins<r.price)return false;s.coins-=r.price}else if(s.level<r.level)return false;s.ownedRooms.push(key)}s.room=key;return true;}
