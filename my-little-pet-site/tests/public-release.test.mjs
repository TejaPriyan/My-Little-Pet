import assert from 'node:assert/strict';
import {readFile,readdir,stat} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
const root=path.resolve(import.meta.dirname,'../../public-site');
async function walk(dir){const result=[];for(const e of await readdir(dir,{withFileTypes:true})){const f=path.join(dir,e.name);if(e.isDirectory())result.push(...await walk(f));else result.push(f)}return result}
const files=await walk(root),names=files.map(f=>path.relative(root,f).replaceAll('\\','/'));
for(const n of names)assert(!/(^|\/)(?:\.env[^/]*|payment-server|checkout\.mjs|payment-key\.json|entitlement\.mjs|node_modules|private-releases)|\.(?:msix|py|pyw|pem|key)$/.test(n),`Private file: ${n}`);
assert(names.includes('app/app.mjs'));assert(names.includes('app/sw.js'));
const release=JSON.parse(await readFile(path.join(root,'downloads/release.json'),'utf8'));
assert.equal(release.downloads.length,2);
assert.deepEqual(names.filter(n=>n.endsWith('.exe')).sort(),release.downloads.map(d=>'downloads/'+d.file).sort());
for(const d of release.downloads){assert(d.free);const bytes=await readFile(path.join(root,'downloads',d.file));assert.equal(createHash('sha256').update(bytes).digest('hex'),d.sha256);assert(bytes.length>1000000)}
let count=0;
for(const file of files.filter(f=>/\.(html|js|mjs|json|css|txt)$/.test(f))){
 const text=await readFile(file,'utf8');assert(!/checkout\.razorpay|rzp_(?:test|live)_|owner-preview|restore-purchase|coming soon|₹99/i.test(text),`Stale paid flow: ${file}`);
 if(!file.endsWith('.html'))continue;
 const name=path.relative(root,file).replaceAll('\\','/'),ids=[...text.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);assert.equal(ids.length,new Set(ids).size);
 for(const [,value] of text.matchAll(/(?:src|href)="([^"]+)"/g)){
  if(/^(?:https?:|mailto:|data:)/.test(value))continue;
  if(value.startsWith('#')){assert(ids.includes(value.slice(1)));continue}
  const url=new URL(value,`https://test.invalid/${name}`);let target=path.join(root,decodeURIComponent(url.pathname));if(url.pathname.endsWith('/'))target=path.join(target,'index.html');
  assert((await stat(target)).isFile(),`Missing ${value} in ${name}`);if(url.hash)assert((await readFile(target,'utf8')).includes(`id="${url.hash.slice(1)}"`));count++;
 }
}
const home=await readFile(path.join(root,'index.html'),'utf8');assert(home.includes('https://tejapriyan.itch.io/mylittlepet'));assert(home.includes('https://buymeacoffee.com/tejapriyan'));
assert((await readFile(path.join(root,'app/index.html'),'utf8')).includes('https://buymeacoffee.com/tejapriyan'));
console.log(`PASS public release: ${names.length} files, ${count} links, two verified free installers, mobile room and optional support`);
