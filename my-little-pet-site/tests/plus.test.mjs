import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {ToyMotion} from '../dist/app/toy-play.mjs';
import {TOYS} from '../dist/app/life.mjs';
const patterns=[];for(const kind of Object.keys(TOYS)){const toy=new ToyMotion(kind,()=>.25);for(let i=0;i<2000;i++){toy.update(.02);assert.ok(toy.x>=12&&toy.x<=88&&toy.y>=58&&toy.y<=88)}patterns.push([toy.x,toy.y,toy.z].map(n=>Math.round(n)).join(','));}
assert.equal(new Set(patterns).size,6);
const app=readFileSync(new URL('../dist/app/app.mjs',import.meta.url),'utf8');assert.equal((app.match(/lifeUI=setupLife\(/g)||[]).length,1);
const manifest=JSON.parse(readFileSync(new URL('../dist/app/manifest.webmanifest',import.meta.url)));assert.equal(manifest.orientation,'landscape');
const index=readFileSync(new URL('../dist/index.html',import.meta.url),'utf8');
assert.ok(index.includes('Also free'));assert.ok(index.includes('https://buymeacoffee.com/tejapriyan'));
const boot=readFileSync(new URL('../dist/app/boot.mjs',import.meta.url),'utf8');assert.ok(boot.includes("await import('./app.mjs"));assert.ok(!/entitlement|license|fetch/.test(boot));
console.log('PASS toy bounds, distinct patterns, single onboarding, landscape installation and free access');

assert.equal((app.match(/setupComforts\(\{getState/g)||[]).length,1);assert.equal((app.match(/const catchGames=/g)||[]).length,1);
