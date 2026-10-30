import {readFile,stat} from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve(import.meta.dirname,'../dist');
let checks=0;
for(const page of ['index.html','privacy.html','guide.html','terms.html','about.html','pricing.html','installation.html','contact.html','refunds.html','delivery.html','app/index.html']){
  const html=await readFile(path.join(root,page),'utf8');
  const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);
  assert.equal(ids.length,new Set(ids).size,`${page}: duplicate IDs`);
  for(const match of html.matchAll(/\bpattern="([^"]+)"/g)){
    const pattern=new RegExp(`^(?:${match[1]})$`,'v');
    assert(pattern.test('Rose-Marie'),`${page}: hyphens must work`);
    assert(!pattern.test('<script>'),`${page}: invalid name characters`);
  }
  for(const match of html.matchAll(/(?:src|href)="([^"]+)"/g)){
    const url=match[1];if(/^(https?:|mailto:|data:)/.test(url))continue;
    if(url.startsWith('#')){assert(ids.includes(url.slice(1)),`${page}: missing anchor ${url}`);continue}
    const target=new URL(url,`https://site.test/${page}`);
    let file=path.join(root,decodeURIComponent(target.pathname).replace(/^\//,''));
    if(target.pathname.endsWith('/'))file=path.join(file,'index.html');
    assert((await stat(file)).isFile(),`Missing file ${file}`);checks++;
    if(target.hash){const targetHtml=await readFile(file,'utf8');assert(targetHtml.includes(`id="${decodeURIComponent(target.hash.slice(1))}"`),`${page}: missing cross-page anchor ${url}`)}
  }
}
for(const species of ['cat','dog','bunny','fox','dino','tiger','parrot'])for(let coat=0;coat<3;coat++)for(const pose of ['idle','sleep','eat','happy','dance','wave']){assert((await stat(path.join(root,`assets/pets/${species}-${coat}-${pose}.gif`))).size>0);checks++}
const manifest=JSON.parse(await readFile(path.join(root,'app/manifest.webmanifest'),'utf8'));assert.equal(manifest.display,'standalone');assert.equal(manifest.scope,'./');
const release=JSON.parse(await readFile(path.join(root,'downloads/release.json'),'utf8'));assert(release.sizeMB<25);
console.log(`PASS static website: ${checks} file references, anchors, unique IDs, pet animations, install manifest and download metadata`);
