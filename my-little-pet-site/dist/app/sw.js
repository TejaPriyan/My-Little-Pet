const CACHE='my-little-pet-mobile-v1.6-free-1';
const FILES=['./','./index.html','./app.css','./app.mjs','./boot.mjs','./comforts.mjs','./comforts.css','./toy-play.mjs','./landscape.css','./native-room.css','./room-world.css','./room-world.mjs','../assets/pets/clips.json','./engine.mjs','./arcade.mjs','./catch-games.mjs','./life.mjs','./life-ui.mjs','./pet-play.mjs','./pet-games.mjs','./manifest.webmanifest','../assets/icon-192.png','../assets/icon-512.png','../assets/food.png','../assets/plant.png'];
for(let i=0;i<FILES.length;i++)if(/\.(mjs|css)$/.test(FILES[i]))FILES[i]+='?v=1.6-free-1';
for(const species of ['cat','dog','bunny','fox','dino','tiger','parrot'])for(let coat=0;coat<3;coat++){FILES.push(`../assets/pets/${species}-${coat}.png`,`../assets/pets/${species}-${coat}-sheet.png`);for(const pose of ['idle','sleep','eat','happy','dance','wave','walk_left','walk_right'])FILES.push(`../assets/pets/${species}-${coat}-${pose}.gif`)}
for(const food of ['kibble','berries','fish','greens','feast','milk','soup'])FILES.push(`../assets/supplies/food-${food}.png`);
for(const toy of ['ball','yarn','mouse','feather','spring','butterfly'])FILES.push(`../assets/supplies/toy-${toy}.png`);
for(const decor of ['flowers','lamp','books'])FILES.push(`../assets/supplies/decor-${decor}.png`);
for(const room of ['classic','garden','starlight','seaside','cabin','moon'])for(const part of ['background','bed'])FILES.push(`../assets/rooms/${room}-${part}.png`);
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(async cache=>{await cache.addAll(FILES);await self.skipWaiting()})));
self.addEventListener('activate',e=>e.waitUntil((async()=>{for(const key of await caches.keys())if(key.startsWith('my-little-pet-mobile-')&&key!==CACHE)await caches.delete(key);await self.clients.claim();for(const c of await self.clients.matchAll())c.postMessage({type:'OFFLINE_READY'})})()));
self.addEventListener('message',e=>{if(e.data?.type==='CHECK_OFFLINE')e.waitUntil(caches.has(CACHE).then(ready=>{if(ready)e.source?.postMessage({type:'OFFLINE_READY'})}))});
self.addEventListener('fetch',e=>{const url=new URL(e.request.url);if(e.request.method!=='GET'||url.origin!==self.location.origin)return;const root=new URL('./',self.location).pathname;
  if(e.request.mode==='navigate'&&url.pathname.startsWith(root)){e.respondWith(fetch(e.request).catch(()=>caches.match(new URL('./index.html',self.location).href)));return}
  if(FILES.some(file=>new URL(file,self.location).href===url.href))e.respondWith(caches.match(e.request).then(cached=>cached||fetch(e.request)));
});
