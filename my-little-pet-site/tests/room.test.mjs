import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import vm from 'node:vm';
import {moveTowards} from '../dist/app/room-world.mjs';
import {ToyMotion} from '../dist/app/toy-play.mjs';
let a={x:12,y:55,pose:'idle'};const target={x:88,y:88};
for(let i=0;i<1200;i++){moveTowards(a,target,1/60);assert(a.x<=88&&a.y<=88)}
assert(Math.abs(a.x-target.x)<.3&&Math.abs(a.y-target.y)<.3);
const frozen={...a};moveTowards(a,{x:0,y:0},0);assert.deepEqual(a,frozen);
const ball=new ToyMotion('ball');for(let i=0;i<400;i++)ball.update(.02);assert.equal(ball.z,0);assert.equal(ball.vx,0);ball.bat();ball.update(.02);assert(ball.z>0);
const clips=JSON.parse(readFileSync(new URL('../dist/assets/pets/clips.json',import.meta.url)));
assert.equal(Object.keys(clips).length,21);for(const [key,poses] of Object.entries(clips)){assert(existsSync(new URL(`../dist/assets/pets/${key}-sheet.png`,import.meta.url)));for(const pose of ['idle','sit','play','eat','sleep','walk_left','walk_right','walk_up','walk_down'])assert(poses[pose].count>0&&poses[pose].fps>0)}
const worker={self:{addEventListener(){}}};
vm.runInNewContext(readFileSync(new URL('../dist/app/sw.js',import.meta.url),'utf8')+';this.files=FILES;',worker);
for(const file of worker.files)assert(existsSync(new URL('../dist/app/'+file.split('?')[0],import.meta.url)),`Offline cache file missing: ${file}`);
for(const module of ['room-world.mjs','toy-play.mjs','pet-games.mjs'])assert(worker.files.some(file=>file.startsWith('./'+module+'?')),'Offline room module missing: '+module);
console.log(`PASS room arrival without overshoot, frozen movement, ball settling/restart, 21 complete native animation sheets and ${worker.files.length} offline files`);
