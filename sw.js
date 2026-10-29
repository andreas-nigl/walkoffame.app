/* Offline app shell + latest verified data file; no third-party map tiles are bulk cached. */
const CACHE="walkoffame-shell-v3",DATA_CACHE="walkoffame-data-v3";
self.addEventListener("install",ev=>{ev.waitUntil(caches.open(CACHE).then(c=>c.addAll(["./","./index.html","./survey.html","./survey.webmanifest","./manifest.webmanifest","./wof-icon.svg"])).then(()=>self.skipWaiting()))});
self.addEventListener("activate",ev=>{ev.waitUntil(Promise.all([caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith("walkoffame-")&&!([CACHE,DATA_CACHE].includes(k))).map(k=>caches.delete(k)))),self.clients.claim()]))});
self.addEventListener("fetch",ev=>{
 const req=ev.request;
 if(req.method!=="GET"||new URL(req.url).origin!==self.location.origin)return;
 const path=new URL(req.url).pathname;
 if(path.endsWith("/stars.json")||path.endsWith("/hollywood-roads.geojson")){
  ev.respondWith(fetch(req).then(async response=>{if(response.ok){const c=await caches.open(DATA_CACHE);await c.put(req,response.clone())}return response}).catch(()=>caches.match(req)));
  return;
 }
 if(req.mode==="navigate"){
  ev.respondWith(fetch(req).then(async response=>{if(response.ok){const c=await caches.open(CACHE);await c.put("./index.html",response.clone())}return response}).catch(async()=>await caches.match("./index.html")||Response.error()));
 }
});
