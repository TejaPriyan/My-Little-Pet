import assert from 'node:assert/strict';
import {fresh,normalize,tick,care,buy,claimDaily,xpNeeded,startGame,finishGame,buySlot,addFriend,selectFriend,selectFood,refillLives,PETS,greetFriend,buyRoom} from '../dist/app/engine.mjs';
const now=new Date(2026,9,15,12).getTime();
let s=fresh('Rose','Mochi',now);s.onboarded=true;
assert.equal(care(s,'feed',now).ok,true);assert.equal(s.food,100);assert.equal(s.coins,20);assert.equal(care(s,'feed',now+10).ok,false);
care(s,'pet',now);const xp=s.xp;care(s,'pet',now+3000);assert.equal(s.xp,xp);assert.equal(s.coins,20,'cuddle spam cannot generate coins or XP');
const cooldownSave=normalize(JSON.parse(JSON.stringify(s)),now+4000);care(cooldownSave,'pet',now+5000);assert.equal(cooldownSave.xp,xp,'cooldown survives reload');
s.food=20;s.happy=20;s.energy=20;care(s,'rest',now);tick(s,now+120000);assert.equal(s.energy,80);tick(s,now+240000);assert.equal(s.energy,100);assert.equal(s.sleeping,false);
s=fresh('Rose','Mochi',now);s.coins=159;assert.equal(buy(s,'pet','dog'),false);s.coins=160;assert.equal(buy(s,'pet','dog'),true);assert.equal(s.coins,0);assert.equal(buy(s,'pet','dog'),true);assert.equal(buy(s,'pet','toString'),false);
s.daily={date:s.daily.date,feed:2,play:2,pet:2,claimed:false};assert.equal(claimDaily(s,now),true);assert.equal(s.coins,12);assert.equal(claimDaily(s,now),false);
s=fresh('Rose','Mochi',now);s.xp=xpNeeded(1)-1;let round=startGame(s,'hunt',now);assert.equal(s.arcade.lives,2);assert.equal(finishGame(s,round.id,32,now+100),null,'early quitting cannot earn');let result=finishGame(s,round.id,32,now+30000);assert.equal(result.coins,8);assert.equal(s.level,2);assert.equal(finishGame(s,round.id,32,now+30000),null,'no double collect');
s.arcade.lives=0;round=startGame(s,'memory',now+31000);const before=s.coins;result=finishGame(s,round.id,80,now+76000);assert.equal(result.practice,true);assert.equal(s.coins,before);
s.arcade.lives=0;s.arcade.refillAt=now;tick(s,now+1800000);assert.equal(s.arcade.lives,1);tick(s,now+3600000);assert.equal(s.arcade.lives,2);
s.coins=20;assert.equal(refillLives(s,now+3600000),true);assert.equal(s.coins,0);assert.equal(s.arcade.lives,3);
s=fresh('Rose','Mochi',now);s.coins=3000;assert.equal(buySlot(s),true);assert.equal(s.slots,2);assert.equal(addFriend(s,'tiger','Tiggy'),false);buy(s,'pet','tiger');s.species='cat';assert.equal(addFriend(s,'tiger','Tiggy'),true);assert.equal(addFriend(s,'cat','Third'),false,'slot limits enforced');s.food=33;s.companions[0].food=66;const wallet=s.coins;assert.equal(selectFriend(s,0),true);assert.equal(s.pet,'Tiggy');assert.equal(s.food,66);assert.equal(s.companions[0].pet,'Mochi');assert.equal(s.companions[0].food,33);assert.equal(s.coins,wallet);
assert.equal(selectFood(s,'fish'),true);s.food=20;care(s,'feed',now);assert.equal(s.food,58);assert.equal(s.pantry.fish,0);s.food=20;care(s,'feed',now+15001);assert.ok(s.food<41,'empty pantry falls back to free basic food');
const restored=normalize(JSON.parse(JSON.stringify(s)),now+20000);assert.equal(restored.pet,'Tiggy');assert.equal(restored.companions[0].pet,'Mochi');assert.equal(restored.slots,2);
const old={...fresh('Old','Friend',now),version:1};delete old.companions;delete old.arcade;delete old.slots;old.coins=987;const migrated=normalize(old,now);assert.equal(migrated.coins,987);assert.equal(migrated.version,3);assert.equal(migrated.slots,1);assert.equal(migrated.arcade.lives,3);
const bad=normalize({...s,owner:[],pet:'<script>',species:'__proto__',ownedPets:['__proto__'],coins:-100,energy:NaN,room:'starlight',companions:[null,{}],slots:99},now);assert.equal(bad.owner,'Friend');assert.equal(bad.species,'cat');assert.equal(bad.coins,0);assert.equal(bad.energy,90);assert.equal(bad.room,'classic');assert.equal(bad.slots,4);assert.throws(()=>normalize({}));assert.throws(()=>normalize({...s,version:999}));
s=fresh('Rose','Mochi',now);s.arcade.earned=39;round=startGame(s,'rhythm',now);assert.equal(finishGame(s,round.id,120,now+30000).coins,1);
assert.equal(Object.keys(PETS).length,7);s.food=1;s.happy=2;tick(s,now+86400000);assert.equal(s.food,1);assert.equal(s.happy,2);
console.log('PASS mobile: migration, household/slots, separate needs, food pantry, persisted reward limits, arcade lives/refills/practice, daily cap, no early/double claims, malformed backups');

s=fresh('Rose','Mochi',now);s.coins=1000;buySlot(s);addFriend(s,'cat','Luna');const names=JSON.stringify([s.pet,...s.companions.map(p=>p.pet)]), count=s.companions.length, savedCoins=s.coins;
for(let i=0;i<30;i++)assert.match(greetFriend(s,0),/Luna: Hi Rose/);
assert.equal(s.companions.length,count);assert.equal(JSON.stringify([s.pet,...s.companions.map(p=>p.pet)]),names);assert.equal(s.coins,savedCoins);assert.equal(s.xp,0);
assert.equal(buyRoom(s,'moon'),true);assert.equal(s.coins,savedCoins-400);assert.equal(buyRoom(s,'moon'),true);assert.equal(s.coins,savedCoins-400);assert.equal(buyRoom(s,'starlight'),false);assert.equal(buyRoom(s,'__proto__'),false);
const roomSave=normalize(JSON.parse(JSON.stringify(s)),now);assert.equal(roomSave.room,'moon');assert.ok(roomSave.ownedRooms.includes('moon'));
s.companions[0].energy=10;tick(s,now+60000);assert.equal(s.companions[0].sleeping,true);assert.ok(s.companions[0].energy>10);
console.log('PASS companion taps never add pets; room bundle purchase/ownership/migration; autonomous friend rest');

for(const kind of ['bugs','drop']){const pet=fresh();const start=Date.now();const entry=startGame(pet,kind,start);assert(entry);assert.equal(normalize(pet,start).round.kind,kind);assert.equal(finishGame(pet,entry.id,40,start+5000),null);const prize=finishGame(pet,entry.id,40,start+30001);assert.equal(prize.coins,8);assert.equal(finishGame(pet,entry.id,40,start+30002),null)}
console.log('PASS Catch the Bug / Treat Drop share the reward cap, persistence and duplicate-claim protection');
