#!/usr/bin/env python3
"""Create a small offline Hollywood streets/footways vector layer from OSM.
Source: OpenStreetMap contributors, ODbL 1.0. No copyrighted map tiles copied.
"""
import json, urllib.request, urllib.parse, datetime as dt, pathlib, time
# Full core Hollywood Boulevard + Vine corridor including cross streets.
BBOX=(34.091,-118.355,34.110,-118.305)
QUERY="""[out:json][timeout:90];
(
 way["highway"~"^(primary|secondary|tertiary|residential|living_street|pedestrian|footway|path|service|steps|crossing)$"](%s,%s,%s,%s);
);
out geom;""" % BBOX
ENDPOINTS=["https://overpass.kumi.systems/api/interpreter","https://overpass-api.de/api/interpreter","https://overpass.nchc.org.tw/api/interpreter"]
def download():
    last=None
    for endpoint in ENDPOINTS:
        try:
            req=urllib.request.Request(endpoint,data=urllib.parse.urlencode({"data":QUERY}).encode(),headers={"User-Agent":"WalkOfFameExplorer/1.0 (public noncommercial OSM map builder)","Content-Type":"application/x-www-form-urlencoded"},method="POST")
            with urllib.request.urlopen(req,timeout=130) as f:return json.load(f)
        except Exception as e:
            last=e
            print(endpoint, type(e).__name__,e)
    raise RuntimeError("All OSM Overpass endpoints failed: "+str(last))
def main():
    obj=download();features=[];seen=set()
    for way in obj.get("elements",[]):
        if way.get("type")!="way" or way.get("id") in seen:continue
        coords=[[round(pt["lon"],7),round(pt["lat"],7)] for pt in way.get("geometry",[]) if "lon" in pt and "lat" in pt]
        if len(coords)<2:continue
        seen.add(way["id"])
        tags=way.get("tags",{})
        features.append({"type":"Feature","id":"way/"+str(way["id"]),"properties":{k:tags[k] for k in ("highway","name","footway","sidewalk","oneway") if k in tags},"geometry":{"type":"LineString","coordinates":coords}})
    if len(features)<100:raise RuntimeError("Too few street features: "+str(len(features)))
    fc={"type":"FeatureCollection","name":"Hollywood OSM ways – offline vector road network","attribution":"© OpenStreetMap contributors; https://www.openstreetmap.org/copyright","license":"ODbL-1.0","collected_at":dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),"bbox":[BBOX[1],BBOX[0],BBOX[3],BBOX[2]],"features":features}
    path=pathlib.Path("hollywood-roads.geojson")
    path.write_text(json.dumps(fc,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
    print(f"Saved {len(features)} OSM street/footway vectors to {path} ({path.stat().st_size} bytes)")
if __name__=="__main__":main()
