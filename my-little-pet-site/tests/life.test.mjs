import assert from 'node:assert/strict';
import {fresh,normalize,addFriend,selectFriend,startGame,finishGame,tick,selectFood,FOODS,care} from '../dist/app/engine.mjs';
import {befriend,pairKey,recordAdventure,claimAdventure,placeDecor,putAwayDecor,TOYS,selectToy} from '../dist/app/life.mjs';
import {PetPlayRound} from '../dist/app/pet-play.mjs';
const now=Date.now();let s=fresh('Rose','Mochi',now);s.slots=4;s.coins=1000;s.trait='shy';addFriend(s,'cat','Pip');s.companions[0].trait='sleepy';
const first=s.id,second=s.companions[0].id,key=pairKey(s,s.companions[0]);
assert.notEqual(first,second);assert.equal(befriend(s,s,s.companions[0],now),2);assert.equal(befriend(s,s,s.companions[0],now+1),2);
selectFriend(s,0);assert.equal(s.id,second);assert.equal(s.trait,'sleepy');assert.equal(s.companions[0].id,first);assert.equal(pairKey(s,s.companions[0]),key);
s=normalize(JSON.parse(JSON.stringify(s)),now);assert.equal(s.bonds[key].points,2);assert.equal(s.companions[0].trait,'shy');
const migrated=normalize({...fresh(),version:1,id:null,companions:undefined},now);assert(migrated.id);assert.equal(migrated.coins,20);
assert.equal(placeDecor(s,'plant',[50,70]),true);assert.equal(s.coins,945);assert.equal(placeDecor(s,'plant',[70,75]),true);assert.equal(s.coins,945);assert.equal(placeDecor(s,'plant',[NaN,70]),false);assert.equal(placeDecor(s,'__proto__',[50,70]),false);
for(const kind of ['find','game','cuddle','cuddle','cuddle'])recordAdventure(s,kind,now);assert(claimAdventure(s,now));assert(!claimAdventure(s,now));assert.equal(s.coins,951);
for(const kind of ['fetch','hurdles']){
 const model=new PetPlayRound(kind,true);for(let i=0;i<900;i++)model.step(.05);assert(model.score>0,`${kind} pet should score while watching`);
 const coins=s.coins,lives=s.arcade.lives,round=startGame(s,kind,now,true);assert.equal(s.arcade.lives,lives);assert(!finishGame(s,round.id,model.score,now+44999));const result=finishGame(s,round.id,model.score,now+45000);assert.equal(result.coins,0);assert.equal(result.xp,0);assert.equal(s.coins,coins);assert(!finishGame(s,round.id,model.score,now+46000));
}
const live=new PetPlayRound('fetch');assert(!live.throw(10,70));assert(live.throw(75,70));assert(!live.throw(60,70));for(let i=0;i<200;i++)live.step(.05);assert.equal(live.score,4);assert.equal(live.phase,'ready');
s.paused=true;s.lastAt=now;const values=[s.food,s.happy,s.energy];tick(s,now+60000);assert.deepEqual([s.food,s.happy,s.energy],values);assert.equal(startGame(s,'fetch',now+60000),null);
console.log('PASS personalities, stable friendships, save migration, decor ownership, daily caps, pet-led games, watch rewards, pause');
const supplies=fresh('Teja','Mochi',now);supplies.coins=10000;supplies.slots=2;supplies.solo=true;
assert(addFriend(supplies,'cat','Pip'));assert.equal(supplies.solo,false);assert(!addFriend(supplies,'cat','Extra'));
for(const [key,food] of Object.entries(FOODS)){
 supplies.pantry[key]=0;supplies.food=10;supplies.sleeping=false;supplies.cooldowns={};
 const before=supplies.coins;assert(selectFood(supplies,key));assert.equal(supplies.coins,before-food.price);
 assert(selectFood(supplies,key));assert.equal(supplies.coins,before-food.price);
 assert(care(supplies,'feed',now).ok);assert(supplies.food>10);assert.equal(supplies.selectedFood,'kibble');
}
for(const [key,toy] of Object.entries(TOYS)){
 const before=supplies.coins;assert(selectToy(supplies,key));assert.equal(supplies.coins,before-toy.price);
 assert(selectToy(supplies,key));assert.equal(supplies.coins,before-toy.price);
}
assert.equal(normalize(supplies,now).selectedToy,'butterfly');assert.equal(selectToy(supplies,'__proto__'),false);
for(const key of ['flowers','lamp','books'])assert(placeDecor(supplies,key,[50,72]));
console.log('PASS adoption unhides family; milk/soup portions, toy ownership, decor and save round trips');
const layoutPet=fresh('Rose','Mochi',now), wallet=layoutPet.coins;
for(const key of ['roomPlant','roomRug','foodBowl','bed','toy']){
 assert(placeDecor(layoutPet,key,[32,72]));assert(putAwayDecor(layoutPet,key));
 const loaded=normalize(layoutPet,now);assert(loaded.hiddenDecor.includes(key));
 assert.deepEqual(loaded.layout[key],[32,72]);assert(placeDecor(layoutPet,key,[60,68]));
 assert(!layoutPet.hiddenDecor.includes(key));assert.equal(layoutPet.coins,wallet);
}
assert(!putAwayDecor(layoutPet,'books'));assert(!placeDecor(layoutPet,'plant',[50,72]));
assert(!placeDecor(layoutPet,'bed',[NaN,72]));
assert.deepEqual(normalize({...layoutPet,hiddenDecor:['bed',{},'__proto__']},now).hiddenDecor,['bed']);
console.log('PASS existing furniture moves, put away/restore is free, reload preserves layout and malformed data is ignored');

const comfort=normalize({...fresh(),petSize:'large',roomTime:'night',weather:'snow'});assert.equal(comfort.petSize,'large');assert.equal(comfort.roomTime,'night');assert.equal(comfort.weather,'snow');const invalid=normalize({...comfort,petSize:'giant',weather:'storm',roomTime:'oops'});assert.equal(invalid.petSize,'medium');assert.equal(invalid.weather,'clear');assert.equal(invalid.roomTime,'real');
