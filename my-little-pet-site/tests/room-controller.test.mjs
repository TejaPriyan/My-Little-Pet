// Run the actual room controller with a small DOM/animation clock adapter.
// These are interaction checks, without a browser or a player's saved profile.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {setupRoom} from '../dist/app/room-world.mjs';
import {ToyMotion} from '../dist/app/toy-play.mjs';

class Element {
  style={};dataset={};children=[];hidden=false;listeners={};classList={contains:()=>false};
  addEventListener(name,fn){this.listeners[name]=fn}
  setAttribute(name,value){this[name]=value}
  prepend(node){this.children.unshift(node)}
  append(node){this.children.push(node)}
  getContext(){return {clearRect(){},drawImage(){}}}
}
const nodes=new Map();
for(const id of ['#pet-room','#pet-touch','#room-panel','#room-friends','#toy-adventure','#follow-toggle','#recover-pets'])nodes.set(id,new Element());
const clips=JSON.parse(readFileSync(new URL('../dist/assets/pets/clips.json',import.meta.url)));
globalThis.document={
  hidden:false,
  querySelector:s=>nodes.get(s)||null,
  querySelectorAll:()=>[],
  createElement:()=>new Element()
};
globalThis.fetch=async()=>({ok:true,json:async()=>clips});
globalThis.matchMedia=()=>({matches:false});
globalThis.Image=class{complete=true;naturalWidth=24};
let nextFrame,time=performance.now();
globalThis.requestAnimationFrame=fn=>{nextFrame=fn};
function advance(seconds){for(let i=0;i<Math.ceil(seconds*60);i++){time+=1000/60;nextFrame(time)}}
const state={id:'main',species:'cat',coat:0,selectedToy:'ball',companions:[],layout:{foodBowl:[76,86],bed:[24,72],toy:[52,76]},quiet:true,paused:false,sleeping:false};
const calls=[];
const controller=await setupRoom({getState:()=>state,speak:()=>{},ToyMotion,care:kind=>{
  calls.push(kind);
  if(state.paused)return {ok:false};
  if(kind==='rest')state.sleeping=!state.sleeping;
  return {ok:true};
}});
controller.command('feed');
assert.equal(calls.length,0,'food is consumed at the bowl, not on clicking Feed');
advance(4);
assert.deepEqual(calls,['feed'],'manual feeding works during Quiet Time');
assert(Math.abs(parseFloat(nodes.get('#pet-touch').style.left)-76)<.5);
controller.command('rest');
advance(1);
state.paused=true;
const frozen=nodes.get('#pet-touch').style.left;
advance(3);
assert.equal(nodes.get('#pet-touch').style.left,frozen,'pause freezes an approach');
assert.equal(state.sleeping,false,'pause does not finish pending care');
state.paused=false;
advance(6);
assert.equal(state.sleeping,true,'pet naps only after reaching the bed');
assert.equal(nodes.get('#pet-touch').style.left,'24%');
controller.command('rest');
assert.equal(state.sleeping,false,'Rest wakes a sleeping pet');
state.quiet=false;
nodes.get('#recover-pets').listeners.click();
const before=calls.length;
controller.start();
advance(.1);
const toy=nodes.get('#pet-room').children.at(-1);
const caught=toy.style.left;
advance(1.2);
assert.notEqual(toy.style.left,caught,'toy can leave the pet during the catch cooldown');
assert.equal(calls.length,before,'automatic toy play never grants care rewards');
state.paused=true;
const pausedToy=toy.style.left;
advance(2);
assert.equal(toy.style.left,pausedToy,'pause freezes toy motion too');
console.log('PASS room controller: walk-to-feed, quiet care, paused approach, bed sleep/wake, catch release, no autoplay rewards');
