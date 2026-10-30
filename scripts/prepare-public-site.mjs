// Build the free website, mobile room and approved Windows downloads.
import {mkdir,readFile,writeFile,copyFile,readdir,lstat} from 'node:fs/promises';
import path from 'node:path';
const root=path.resolve(import.meta.dirname,'..'),src=path.join(root,'my-little-pet-site/dist'),out=path.join(root,'public-site');
const base=(process.env.PUBLIC_SITE_URL||'https://littlepet.in').replace(/\/$/,'');
if(!/^https:\/\/[\w.-]+(?:\/[\w.-]+)*$/.test(base))throw new Error('Expected a public HTTPS site URL');
try{await mkdir(out)}catch(e){if(e.code!=='EEXIST')throw e;if((await readdir(out)).length)throw new Error('Archive the existing public-site folder before rebuilding.')}
const pages=['index.html','about.html','pricing.html','installation.html','contact.html','privacy.html','terms.html','refunds.html','delivery.html','guide.html'];
const downloads=['MyLittlePet-1.1.0-Windows-Setup.exe','MyLittlePet-Plus-1.6.0-Windows-Setup.exe','release.json','SHA256SUMS.txt','THIRD-PARTY-NOTICES.txt'];
let copied=0;
async function copy(file){
 const from=path.join(src,file),to=path.join(out,file),s=await lstat(from);
 if(!s.isFile())throw new Error('Not a regular file: '+file);
 await mkdir(path.dirname(to),{recursive:true});
 if(/\.(html|xml|txt)$/.test(file))await writeFile(to,(await readFile(from,'utf8')).replaceAll('https://littlepet.in',base));else await copyFile(from,to);copied++;
}
async function tree(folder){for(const entry of await readdir(path.join(src,folder),{withFileTypes:true})){const file=folder+'/'+entry.name;if(entry.isSymbolicLink())throw new Error('Symlinks cannot be published');if(entry.isDirectory())await tree(file);else if(/\.(?:html|mjs|js|css|webmanifest|json|png|gif|svg|ico|woff2?|ttf)$/.test(file)&&!/(?:entitlement|payment|checkout|secret|\.env)/i.test(file))await copy(file);else throw new Error('Unexpected public asset: '+file)}}
for(const file of [...pages,'style.css','plus.css','site.js','robots.txt','sitemap.xml','llms.txt','google2af4e1ed3191321d.html',...downloads.map(n=>'downloads/'+n)])await copy(file);
await tree('assets');await tree('app');
await writeFile(path.join(out,'404.html'),`<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,follow"><title>Page not found — My Little Pet</title></head><body><h1>This little path ends here.</h1><p><a href="${base}/">Return to My Little Pet</a> or <a href="${base}/app/">open your free pet room</a>.</p></body></html>`);
await writeFile(path.join(out,'.nojekyll'),'');
await writeFile(path.join(out,'_headers'),'/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  X-Frame-Options: DENY\n');
console.log(`Prepared ${copied} public files, including the free mobile room and both Windows installers.`);
