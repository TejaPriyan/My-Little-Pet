import assert from 'node:assert/strict';
import {readFile,readdir,stat} from 'node:fs/promises';
import path from 'node:path';
const root=path.resolve(import.meta.dirname,'../../public-site');
async function walk(dir){const result=[];for(const entry of await readdir(dir,{withFileTypes:true})){const name=path.join(dir,entry.name);if(entry.isDirectory())result.push(...await walk(name));else result.push(name)}return result;}
const files=await walk(root),names=files.map(f=>path.relative(root,f).replaceAll('\\','/'));
for(const name of names)assert(!/(^|\/)(?:\.env[^/]*|payment-server|checkout\.mjs|payment-key\.json|node_modules|private-releases)|\.(?:exe|msix|py|pyw|pem|key)$/.test(name),`Private/runtime file in public bundle: ${name}`);
assert.deepEqual(names.filter(n=>n.startsWith('app/')),['app/index.html']);
let count=0;
for(const file of files.filter(f=>f.endsWith('.html'))){
  const html=await readFile(file,'utf8'),name=path.relative(root,file).replaceAll('\\','/');
  assert(!/checkout\.razorpay|rzp_test_|owner-preview|restore-purchase|checkout\.mjs/.test(html));
  const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);assert.equal(ids.length,new Set(ids).size);
  const base=name.startsWith('app/')||name==='404.html'?'https://littlepet.in/':`https://littlepet.in/${name}`;
  for(const [,value] of html.matchAll(/(?:src|href)="([^"]+)"/g)){
    if(/^(?:https?:|mailto:|data:)/.test(value))continue;
    if(value.startsWith('#')){assert(ids.includes(value.slice(1)));continue;}
    const url=new URL(value,base);let target=path.join(root,url.pathname);
    if(url.pathname.endsWith('/'))target=path.join(target,'index.html');
    assert((await stat(target)).isFile(),`Missing ${value} in ${name}`);
    if(url.hash)assert((await readFile(target,'utf8')).includes(`id="${url.hash.slice(1)}"`));count++;
  }
}
const home=await readFile(path.join(root,'index.html'),'utf8');
const buttons=[...home.matchAll(/<a[^>]*data-buy-plus[^>]*>/g)];assert.equal(buttons.length,2);
for(const [markup] of buttons)assert(markup.includes('href="coming-soon.html"'));
assert(home.includes('https://tejapriyan.itch.io/mylittlepet'));
assert((await readFile(path.join(root,'contact.html'),'utf8')).includes('mailto:teja1616150@gmail.com'));
const js=await readFile(path.join(root,'site.js'),'utf8');assert(!js.includes('URLSearchParams'));assert(!js.includes('/api/'));
console.log(`PASS public release: ${names.length} allowed files, ${count} links, Free download, Coming soon, contact, no checkout or private game`);
