export const VERSION=1;
export const PETS={cat:{name:'Kitty',price:0},dog:{name:'Puppy',price:120},bunny:{name:'Bunny',price:150},fox:{name:'Fox',price:200}};
export const STYLES={none:{name:'Natural cuteness',price:0,emoji:''},bow:{name:'Pretty bow',price:35,emoji:'🎀'},flower:{name:'Flower friend',price:35,emoji:'🌸'},crown:{name:'Tiny royalty',price:100,emoji:'👑'}};
export const ROOMS={classic:{name:'Lavender nook',level:1},garden:{name:'Garden room',level:3},starlight:{name:'Starlight room',level:5}};
export const name=(v,fallback)=>typeof v==='string'?v.replace(/[^a-z0-9 -]/gi,'').trim().slice(0,12)||fallback:fallback;
const num=(v,min,max,fallback)=>typeof v==='number'&&Number.isFinite(v)?Math.min(max,Math.max(min,v)):fallback;
export const dayKey=(now=Date.now())=>{const d=new Date(now);return `${d.getFullYear()}-${d.getMonth()+1}-${d.getDate()}`};
export function fresh(owner='Friend',pet='Mochi',now=Date.now()) {return {format:'my-little-pet-mobile',version:VERSION,owner:name(owner,'Friend'),pet:name(pet,'Mochi'),species:'cat',coat:0,accessory:'none',room:'classic',ownedPets:['cat'],ownedStyles:['none'],food:80,happy:85,energy:90,coins:20,level:1,xp:0,lastAt:now,sleeping:false,cooldowns:{},daily:{date:dayKey(now),feed:0,play:0,pet:0,claimed:false},totalCare:0,onboarded:false,sound:false};}
export function normalize(raw,now=Date.now()) {
  if(!raw||typeof raw!=='object'||Array.isArray(raw)||raw.format!=='my-little-pet-mobile'||raw.version!==VERSION)throw new Error('This is not a supported My Little Pet mobile backup.');
  let s=fresh(raw.owner,raw.pet,now);
  for(const k of ['food','happy','energy'])s[k]=num(raw[k],0,100,s[k]);
  s.coins=Math.floor(num(raw.coins,0,1000000,20));s.level=Math.floor(num(raw.level,1,999,1));s.xp=Math.floor(num(raw.xp,0,xpNeeded(s.level)-1,0));
  s.ownedPets=[...new Set(['cat',...(Array.isArray(raw.ownedPets)?raw.ownedPets.filter(p=>Object.hasOwn(PETS,p)):[])])];
  s.ownedStyles=[...new Set(['none',...(Array.isArray(raw.ownedStyles)?raw.ownedStyles.filter(p=>Object.hasOwn(STYLES,p)):[])])];
  s.species=s.ownedPets.includes(raw.species)?raw.species:'cat';s.accessory=s.ownedStyles.includes(raw.accessory)?raw.accessory:'none';s.coat=Math.floor(num(raw.coat,0,2,0));
  s.room=Object.hasOwn(ROOMS,raw.room)&&ROOMS[raw.room].level<=s.level?raw.room:'classic';s.lastAt=num(raw.lastAt,0,now,now);s.sleeping=raw.sleeping===true;s.sound=raw.sound===true;s.onboarded=raw.onboarded===true;s.totalCare=Math.floor(num(raw.totalCare,0,1e9,0));
  for(const k of ['feed','play','pet','game'])s.cooldowns[k]=num(raw.cooldowns?.[k],0,now+60000,0);
  if(raw.daily?.date===dayKey(now))for(const k of ['feed','play','pet'])s.daily[k]=Math.floor(num(raw.daily[k],0,3,0));
  s.daily.claimed=raw.daily?.date===s.daily.date&&raw.daily?.claimed===true;
  return s;
}
export function tick(s,now=Date.now()) {
  const elapsed=Math.max(0,Math.min(43200,(now-s.lastAt)/1000));
  s.food=Math.min(s.food,Math.max(15,s.food-elapsed*.004));s.happy=Math.min(s.happy,Math.max(25,s.happy-elapsed*.002));
  s.energy=s.sleeping?Math.min(100,s.energy+elapsed*.5):Math.min(s.energy,Math.max(20,s.energy-elapsed*.001));
  if(s.energy>=100)s.sleeping=false;s.lastAt=now;
  if(s.daily.date!==dayKey(now))s.daily={date:dayKey(now),feed:0,play:0,pet:0,claimed:false};
  return s;
}
export function xpNeeded(level){return 40+20*(level-1)}
export function reward(s,xp,coins){s.coins+=coins;s.xp+=xp;let levels=0;while(s.xp>=xpNeeded(s.level)&&s.level<999){s.xp-=xpNeeded(s.level);s.level++;s.coins+=20;levels++}return levels}
export function care(s,kind,now=Date.now()) {
  tick(s,now);
  if(kind==='rest'){s.sleeping=!s.sleeping;return {ok:true,message:s.sleeping?'A cozy nap. I’ll be right here.':'Good morning, '+s.owner+'!',pose:s.sleeping?'sleep':'idle'};}
  if(!['feed','play','pet'].includes(kind))return {ok:false,message:'Choose a care action.'};
  if(s.sleeping)return {ok:false,message:'I’m having a little nap. Tap Wake up first.'};
  if((s.cooldowns[kind]||0)>now)return {ok:false,message:`Let’s take a breath. Try again in ${Math.ceil((s.cooldowns[kind]-now)/1000)}s.`};
  if(kind==='feed'&&s.food>=98)return {ok:false,message:'My tummy is full. Thank you, '+s.owner+'!'};
  if(kind==='play'&&s.energy<12)return {ok:false,message:'A little sleepy. Let’s rest first.'};
  const amounts={feed:[5,2],play:[10,5],pet:[3,1]};
  s.cooldowns[kind]=now+(kind==='pet'?10000:15000);s.totalCare++;
  if(kind==='feed'){s.food=Math.min(100,s.food+20);s.happy=Math.min(100,s.happy+4)}
  if(kind==='play'){s.happy=Math.min(100,s.happy+15);s.energy=Math.max(0,s.energy-10)}
  if(kind==='pet')s.happy=Math.min(100,s.happy+7);
  s.daily[kind]=Math.min(3,s.daily[kind]+1);
  const levels=reward(s,...amounts[kind]);
  return {ok:true,pose:kind==='feed'?'eat':'happy',message:levels?`Level ${s.level}! We’re growing together. +20 coins`:{feed:'Yum! You know the way to my heart.',play:'Best. Little. Break. Ever!',pet:'Purr… I’m so glad you’re my person.'}[kind]};
}
export function claimDaily(s,now=Date.now()){tick(s,now);if(s.daily.claimed||s.daily.feed<2||s.daily.play<2||s.daily.pet<2)return false;s.daily.claimed=true;s.coins+=30;return true;}
export function buy(s,kind,key){const catalog=kind==='pet'?PETS:kind==='style'?STYLES:null;if(!catalog||!Object.hasOwn(catalog,key))return false;const owned=kind==='pet'?s.ownedPets:s.ownedStyles;if(!owned.includes(key)){if(s.coins<catalog[key].price)return false;s.coins-=catalog[key].price;owned.push(key)}if(kind==='pet'){s.species=key;s.coat=0}else s.accessory=key;return true;}
export function finishHunt(s,hits,now=Date.now()){if((s.cooldowns.game||0)>now)return false;const count=Math.floor(num(hits,0,12,0));s.cooldowns.game=now+60000;reward(s,count*2,count);s.happy=Math.min(100,s.happy+count);return true;}
