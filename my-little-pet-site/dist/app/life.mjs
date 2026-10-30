export const TRAITS={playful:{name:'Playful',detail:'Balls, zoomies and tiny dances'},shy:{name:'Shy',detail:'Gentle steps and quiet hellos'},sleepy:{name:'Sleepy',detail:'Slow mornings and cozy naps'},curious:{name:'Curious',detail:'Always ready for a little adventure'}};
export const BASE_LAYOUT={bed:[24,72],toy:[76,76],roomPlant:[82,34],roomRug:[50,78],foodBowl:[76,86]};
export const DECOR={roomPlant:{name:'Room plant',price:0,icon:'🌿'},roomRug:{name:'Room rug',price:0,icon:'▱'},foodBowl:{name:'Food bowl',price:0,icon:'◡'},bed:{name:'Cozy bed',price:0,icon:'🛏'},toy:{name:'Play ball',price:0,icon:'⚽'},rug:{name:'Picnic rug',price:45,icon:'▱'},plant:{name:'Leafy friend',price:55,icon:'🌿'},cushion:{name:'Soft pillow',price:70,icon:'☁'},flowers:{name:'Flower vase',price:60,icon:'💐'},lamp:{name:'Honey lamp',price:85,icon:'💡'},books:{name:'Story shelf',price:120,icon:'📚'}};
export const TOYS={ball:{name:'Striped ball',price:0},yarn:{name:'Yarn ball',price:45},mouse:{name:'Felt mouse',price:65},feather:{name:'Feather rattle',price:80},spring:{name:'Rainbow spring',price:100},butterfly:{name:'Flutter bug',price:125}};
const num=(v,min,max,f=0)=>typeof v==='number'&&Number.isFinite(v)?Math.max(min,Math.min(max,v)):f;
const day=now=>{const d=new Date(now);return `${d.getFullYear()}-${d.getMonth()+1}-${d.getDate()}`};
export const uid=()=>globalThis.crypto?.randomUUID?.()||`${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
export const validId=v=>typeof v==='string'&&/^[a-z0-9-]{8,60}$/i.test(v);
export function lifeMember(raw){return {id:validId(raw.id)?raw.id:uid(),trait:Object.hasOwn(TRAITS,raw.trait)?raw.trait:'playful'}}
export function normalizeLife(raw,s,now=Date.now()){
 const seen=new Set([s.id]);for(const p of s.companions){if(seen.has(p.id))p.id=uid();seen.add(p.id)}
 s.bonds={};if(raw.bonds&&typeof raw.bonds==='object')for(const [key,v] of Object.entries(raw.bonds)){const ids=key.split(':');if(ids.length===2&&ids[0]!==ids[1]&&ids.every(id=>seen.has(id))&&v&&typeof v==='object')s.bonds[key]={points:Math.floor(num(v.points,0,100)),next:num(v.next,0,now+60000)}}
 const a=raw.adventure;s.adventure=a?.date===day(now)?{date:day(now),find:Math.floor(num(a.find,0,1)),game:Math.floor(num(a.game,0,1)),cuddle:Math.floor(num(a.cuddle,0,3)),claimed:a.claimed===true}:{date:day(now),find:0,game:0,cuddle:0,claimed:false};
 s.ownedDecor=[...new Set([...Object.keys(BASE_LAYOUT),...(Array.isArray(raw.ownedDecor)?raw.ownedDecor.filter(k=>typeof k==='string'&&Object.hasOwn(DECOR,k)):[])])];
 s.hiddenDecor=Array.isArray(raw.hiddenDecor)?[...new Set(raw.hiddenDecor.filter(k=>typeof k==='string'&&Object.hasOwn(DECOR,k)))]:[];
 s.layout={};if(raw.layout&&typeof raw.layout==='object')for(const [k,v] of Object.entries(raw.layout)){if(s.ownedDecor.includes(k)&&Array.isArray(v)&&v.length===2)s.layout[k]=[num(v[0],16,84,50),num(v[1],22,86,72)]}
 s.ownedToys=[...new Set(['ball',...(Array.isArray(raw.ownedToys)?raw.ownedToys.filter(k=>typeof k==='string'&&Object.hasOwn(TOYS,k)):[])])];s.selectedToy=s.ownedToys.includes(raw.selectedToy)?raw.selectedToy:'ball';
 s.petSize=['small','medium','large'].includes(raw.petSize)?raw.petSize:'medium';s.roomTime=['real','day','night'].includes(raw.roomTime)?raw.roomTime:'real';s.weather=['clear','rain','snow'].includes(raw.weather)?raw.weather:'clear';
 s.quiet=raw.quiet===true;s.paused=raw.paused===true;
}
export function adventure(s,now=Date.now()){if(s.adventure?.date!==day(now))s.adventure={date:day(now),find:0,game:0,cuddle:0,claimed:false};return s.adventure}
export function recordAdventure(s,kind,now=Date.now()){const a=adventure(s,now),n={find:1,game:1,cuddle:3}[kind];if(n)a[kind]=Math.min(n,(a[kind]||0)+1)}
export function claimAdventure(s,now=Date.now()){const a=adventure(s,now);if(a.claimed||a.find<1||a.game<1||a.cuddle<3)return false;a.claimed=true;s.coins+=6;return true}
export const pairKey=(a,b)=>[a.id,b.id].sort().join(':');
export const bondLabel=points=>points>=60?'Best friends':points>=25?'Buddies':'Getting to know you';
export function befriend(s,a,b,now=Date.now()){if(!a||!b||a.id===b.id)return 0;const key=pairKey(a,b),v=s.bonds[key]??={points:0,next:0};if(now>=v.next){v.points=Math.min(100,v.points+2);v.next=now+60000}return v.points}
export function placeDecor(s,key,xy){if(!Object.hasOwn(DECOR,key)||!Array.isArray(xy)||xy.length!==2||xy.some(v=>!Number.isFinite(v)))return false;const price=s.ownedDecor.includes(key)?0:DECOR[key].price;if(s.coins<price)return false;s.coins-=price;if(!s.ownedDecor.includes(key))s.ownedDecor.push(key);s.layout[key]=[num(xy[0],16,84,50),num(xy[1],22,86,72)];s.hiddenDecor=(s.hiddenDecor||[]).filter(k=>k!==key);return true}

export function selectToy(s,key){if(!Object.hasOwn(TOYS,key))return false;const cost=s.ownedToys.includes(key)?0:TOYS[key].price;if(s.coins<cost)return false;s.coins-=cost;if(!s.ownedToys.includes(key))s.ownedToys.push(key);s.selectedToy=key;return true}

export function putAwayDecor(s,key){if(!s.ownedDecor.includes(key))return false;s.hiddenDecor??=[];if(!s.hiddenDecor.includes(key))s.hiddenDecor.push(key);return true}
