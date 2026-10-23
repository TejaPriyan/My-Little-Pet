import {readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
import path from 'node:path';
const root=path.resolve(import.meta.dirname,'../dist');
const base='https://littlepet.in';
const read=file=>readFile(path.join(root,file),'utf8');
for(const file of ['index.html','guide.html','privacy.html','terms.html','about.html','pricing.html','installation.html','coming-soon.html','contact.html','refunds.html','delivery.html']){
  const html=await read(file);
  assert.match(html,/<meta name="description" content="[^"]+"/);
  assert(html.includes(`rel="canonical" href="${base}/${file==='index.html'?'':file}"`));
  assert.equal((html.match(/<h1\b/g)||[]).length,1,`${file}: one main heading`);
  for(const match of html.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)){
    const data=JSON.parse(match[1]);assert.equal(data['@context'],'https://schema.org');
    for(const entry of data['@graph'])if(entry['@type']==='FAQPage')for(const question of entry.mainEntity){
      assert(html.includes(question.name));assert(html.includes(question.acceptedAnswer.text));
    }
  }
}
assert.equal((await read('google2af4e1ed3191321d.html')).trim(),'google-site-verification: google2af4e1ed3191321d.html');
assert((await read('robots.txt')).includes(`Sitemap: ${base}/sitemap.xml`));
const sitemap=await read('sitemap.xml');
assert(!sitemap.includes('/app/'));
for(const [,url] of sitemap.matchAll(/<loc>([^<]+)<\/loc>/g))assert.equal(new URL(url).search,'');
assert((await read('app/index.html')).includes('content="noindex,follow"'));
assert((await read('llms.txt')).includes('not an indexing guarantee'));
console.log('PASS SEO: canonical URLs, descriptions, headings, valid and visible JSON-LD, sitemap, verification, app exclusion');
