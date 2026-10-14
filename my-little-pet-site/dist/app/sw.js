const CACHE='my-little-pet-mobile-v1.1.0-3';
const FILES=['./','./index.html','./app.css','./app.mjs','./engine.mjs','./manifest.webmanifest','../assets/icon-192.png','../assets/icon-512.png','../assets/food.png','../assets/plant.png'];
for(const species of ['cat','dog','bunny','fox'])for(let coat=0;coat<3;coat++){FILES.push(`../assets/pets/${species}-${coat}.png`);for(const pose of ['idle','sleep','eat','happy'])FILES.push(`../assets/pets/${species}-${coat}-${pose}.gif`)}
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(FILES))));
self.addEventListener('activate',e=>e.waitUntil((async()=>{for(const key of await caches.keys())if(key.startsWith('my-little-pet-mobile-')&&key!==CACHE)await caches.delete(key);await self.clients.claim();for(const c of await self.clients.matchAll())c.postMessage({type:'OFFLINE_READY'})})()));
self.addEventListener('message',e=>{if(e.data?.type==='CHECK_OFFLINE')e.waitUntil(caches.has(CACHE).then(ready=>{if(ready)e.source?.postMessage({type:'OFFLINE_READY'})}))});
self.addEventListener('fetch',e=>{const url=new URL(e.request.url);if(e.request.method!=='GET'||url.origin!==self.location.origin)return;const root=new URL('./',self.location).pathname;
  if(e.request.mode==='navigate'&&url.pathname.startsWith(root)){e.respondWith(fetch(e.request).catch(()=>caches.match(new URL('./index.html',self.location).href)));return}
  if(FILES.some(file=>new URL(file,self.location).href===url.href))e.respondWith(caches.match(e.request).then(cached=>cached||fetch(e.request)));
});
