#!/usr/bin/env python3
"""Append confirmed honoree names from the Chamber directory when absent.
No coordinates or categories are guessed.
"""
import datetime as dt
import json
import re
import unicodedata
import urllib.request
import urllib.parse
from pathlib import Path
from bs4 import BeautifulSoup

DATA=Path("stars.json")
URL="https://walkoffame.com/browse-stars/"

def normalize(s):
    s=unicodedata.normalize("NFKD",str(s)).encode("ascii","ignore").decode().casefold()
    return re.sub(r"[^a-z0-9]","",s)

def fetch_names():
    req=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0 (compatible; WalkOfFameExplorer/1.0; public directory name verification)"})
    with urllib.request.urlopen(req,timeout=45) as response:
        soup=BeautifulSoup(response.read(),"html.parser")
    names={}
    for heading in soup.find_all(["h2","h3"]):
        heading_name=heading.get_text(" ",strip=True)
        if not re.fullmatch(r"[A-Z#]",heading_name):continue
        for el in heading.next_elements:
            if getattr(el,"name",None) in ("h2","h3"):break
            if getattr(el,"name",None)!="a":continue
            href=el.get("href","")
            name=el.get_text(" ",strip=True)
            target=urllib.parse.urljoin(URL,href)
            parsed=urllib.parse.urlparse(target)
            path=parsed.path.strip("/")
            if parsed.hostname!="walkoffame.com" or not path or "/" in path:continue
            if len(name)<2 or len(name)>120 or path in {"browse-stars","star-map","press","about","history","licensing","gallery"}:continue
            names.setdefault(name,target)
    if len(names)<1800:raise ValueError(f"Official directory extraction too small: {len(names)}")
    return names

def main():
    data=json.loads(DATA.read_text(encoding="utf-8"))
    if data.get("schema")!="walkoffame-stars-v1":raise ValueError("Unexpected stars.json schema")
    names=fetch_names()
    existing={normalize(e.get("name","")) for e in data["entries"]}
    ids={e.get("id") for e in data["entries"]}
    new=[]
    for name,url in names.items():
        key=normalize(name)
        if not key or key in existing:continue
        identifier="chamber-unlocated-"+key[:65]
        if identifier in ids:continue
        e={"id":identifier,"name":name,"category":"unknown","address":"Standort noch unbekannt","source":url,"precision":"Name im offiziellen Verzeichnis; Kategorie und Adresse noch ungeprüft","coordinate_source":None,"coordinate_method":"unlocated","coordinate_accuracy":"Keine Koordinaten verfügbar","coordinate_verified":False,"review_status":"official_name_unlocated"}
        new.append(e);existing.add(key);ids.add(identifier)
    # Never remove existing entries or change their addresses/positions.
    data["entries"].extend(new)
    data["count"]=len(data["entries"])
    now=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    meta=data.setdefault("update_info",{})
    meta.update({"official_directory_checked_at":now,"official_directory_distinct_names":len(names),"official_unlocated_added":len(new),"official_source":URL})
    DATA.write_text(json.dumps(data,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
    print("Official unique names:",len(names),"new missing names:",len(new),"total:",data["count"])
if __name__=="__main__":
    main()
