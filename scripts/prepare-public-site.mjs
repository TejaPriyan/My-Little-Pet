// Package only the public showcase. Never publish dist/app or owner/payment files.
import {mkdir,readFile,writeFile,copyFile,readdir,lstat} from 'node:fs/promises';
import path from 'node:path';
const root=path.resolve(import.meta.dirname,'..'),src=path.join(root,'my-little-pet-site/dist');
const out=path.join(root,'public-site');
const siteUrl=(process.env.PUBLIC_SITE_URL||'https://littlepet.in').replace(/\/$/,'');
const siteBase=new URL(siteUrl+'/');
if(siteBase.protocol!=='https:')throw new Error('PUBLIC_SITE_URL must use HTTPS');
const pages=['index.html','about.html','pricing.html','installation.html','coming-soon.html','contact.html','privacy.html','terms.html','refunds.html','delivery.html','guide.html'];
// Refuse a dirty output directory rather than accidentally carrying old private files into a release.
try {await mkdir(out);} catch(error) {
  if(error.code!=='EEXIST')throw error;
  const existing=await readdir(out);
  if(existing.length)throw new Error('public-site already contains files. Archive it before rebuilding.');
}
async function copy(file){const from=path.join(src,file);if(!(await lstat(from)).isFile())throw new Error('Expected regular file: '+file);const dest=path.join(out,file);await mkdir(path.dirname(dest),{recursive:true});await copyFile(from,dest);}
for(const file of [...pages,'style.css','plus.css','site.js','plus-checkout.js','robots.txt','sitemap.xml','llms.txt','google2af4e1ed3191321d.html','downloads/release.json','downloads/SHA256SUMS.txt','downloads/THIRD-PARTY-NOTICES.txt'])await copy(file);
// Assets explicitly referenced by public pages, plus the interactive pet greeting variants.
const assets=new Set();
for(const file of [...pages,'style.css','plus.css','site.js','plus-checkout.js']){
  const text=await readFile(path.join(src,file),'utf8');
  for(const match of text.matchAll(/(?:["'(]|https:\/\/littlepet\.in\/)(assets\/[\w./-]+\.(?:png|gif|svg|ico|woff2?|ttf))/g))assets.add(match[1]);
}
for(const species of ['cat','dog','bunny','fox','dino','tiger','parrot']){assets.add(`assets/pets/${species}-0.png`);assets.add(`assets/pets/${species}-0-idle.gif`);}
for(const asset of assets)await copy(asset);
await copy('payment-success.html');
await mkdir(path.join(out,'app'));
const notice=await readFile(path.join(out,'coming-soon.html'),'utf8');
await writeFile(path.join(out,'app/index.html'),notice.replace('<head>','<head><base href="../">').replace('content="index,follow"','content="noindex,follow"'));
await writeFile(path.join(out,'404.html'),notice.replace('<head>',`<head><base href="${siteUrl}/">`).replace('<title>Plus is coming soon','<title>Page not found').replace('<h1>Plus is coming soon</h1>','<h1>Page not found</h1>').replace('content="index,follow"','content="noindex,follow"'));
// Keep canonical URLs, social images and the sitemap on the actual deployed host.
for(const file of [...pages,'app/index.html','404.html','robots.txt','sitemap.xml','llms.txt']){
  const dest=path.join(out,file);
  await writeFile(dest,(await readFile(dest,'utf8')).replaceAll('https://littlepet.in',siteUrl));
}
await writeFile(path.join(out,'.nojekyll'),'');
await writeFile(path.join(out,'_headers'),'/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  X-Frame-Options: DENY\n');
console.log(`Public showcase prepared at ${out} (${pages.length} pages, ${assets.size} artwork files). No Plus game, API, keys, saves or installers included.`);
