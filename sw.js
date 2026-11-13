/* PWA offline shell. Data from OSM stays local; no third-party map tile prefetch. */
const CACHE="walkoffame-shell-v4-261113-icons",DATA_CACHE="walkoffame-data-v4";
const SHELL=["./","./index.html","./survey.html","./survey.webmanifest","./manifest.webmanifest","./wof-icon.svg","./gehweg/icon.svg","./walkoffame/icon.svg"];
self.addEventListener("install",event=>{
 event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(SHELL)).then(()=>self.skipWaiting()));
});
self.addEventListener("activate",event=>{
 event.waitUntil(Promise.all([
  caches.keys().then(keys=>Promise.all(keys.filter(key=>key.startsWith("walkoffame-")&&![CACHE,DATA_CACHE].includes(key)).map(key=>caches.delete(key)))),
  self.clients.claim()
 ]));
});
self.addEventListener("fetch",event=>{
 const request=event.request;
 if(request.method!=="GET"||new URL(request.url).origin!==self.location.origin)return;
 const path=new URL(request.url).pathname;
 if(path.endsWith("/stars.json")||path.endsWith("/hollywood-roads.geojson")){
  event.respondWith(fetch(request).then(async response=>{
    if(response.ok){try{const cache=await caches.open(DATA_CACHE);await cache.put(request,response.clone())}catch(err){console.warn("Datencache nicht verfügbar",err)}}
    return response;
  }).catch(async()=>await caches.match(request)||Response.error()));
  return;
 }
 if(request.mode==="navigate"){
  const target=path.endsWith("/survey.html")?"./survey.html":"./index.html";
  event.respondWith(fetch(request).then(async response=>{
    if(response.ok){try{const cache=await caches.open(CACHE);await cache.put(target,response.clone())}catch(err){console.warn("Seiten-Cache nicht verfügbar",err)}}
    return response;
  }).catch(async()=>await caches.match(target)||Response.error()));
 }
});

