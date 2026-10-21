#!/usr/bin/env python3
"""Conservative Wikipedia data refresh for the Walk of Fame Explorer."""
import datetime as dt
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import unicodedata
from collections import Counter
from pathlib import Path
from bs4 import BeautifulSoup

PATH = Path("stars.json")
PAGE = "List_of_stars_on_the_Hollywood_Walk_of_Fame"
SOURCE = "https://en.wikipedia.org/wiki/" + PAGE
API = "https://en.wikipedia.org/w/api.php?"
CATS = {"motion pictures":"film","film":"film","television":"tv","tv":"tv","recording":"music","music":"music","radio":"radio","live performance":"theatre","live theatre":"theatre","live theater":"theatre","theatre":"theatre","sports entertainment":"sport","sports":"sport"}
def norm(s):
    return " ".join(re.sub(r"\\[[^\\]]*\\]","",str(s or "")).split())
def key(e):
    return tuple(norm(e.get(k)).casefold() for k in ("name","category","address"))
def nc(e):
    return norm(e["name"]).casefold(), e["category"]
def get(params):
    url = API + urllib.parse.urlencode({"format":"json","origin":"*","action":"parse","page":PAGE,**params})
    req=urllib.request.Request(url,headers={"User-Agent":"WalkOfFameExplorer/1.0 (public GitHub Pages project; Wikimedia import)"})
    with urllib.request.urlopen(req,timeout=45) as r:
        return json.load(r)
def rows_from_html(html):
    soup=BeautifulSoup(html,"html.parser")
    result=[]; seen=set()
    for table in soup.select("table.wikitable"):
        trs=table.find_all("tr")
        if not trs: continue
        headings=[norm(x.get_text(" ",strip=True)).lower() for x in trs[0].find_all("th",recursive=False)]
        if not all(x in headings for x in ("name","category","address")): continue
        ni,ci,ai=(headings.index(v) for v in ("name","category","address"))
        carry={}; previous=""
        for tr in trs[1:]:
            cells=tr.find_all(["td","th"],recursive=False); expanded=[]; col=0
            for cell in cells:
                while col in carry:
                    value,remaining=carry[col];expanded.append(value)
                    if remaining<=1: del carry[col]
                    else:carry[col]=(value,remaining-1)
                    col+=1
                value=norm(cell.get_text(" ",strip=True))
                span=int(cell.get("colspan",1)); rs=int(cell.get("rowspan",1))
                for _ in range(span):
                    expanded.append(value)
                    if rs>1:carry[col]=(value,rs-1)
                    col+=1
            while col in carry:
                value,remaining=carry[col];expanded.append(value)
                if remaining<=1:del carry[col]
                else:carry[col]=(value,remaining-1)
                col+=1
            if len(expanded)<=max(ni,ci,ai):continue
            name=expanded[ni] or previous
            if name:previous=name
            category=CATS.get(expanded[ci].lower().strip())
            address=expanded[ai]
            if not name or not category or not address:continue
            row={"name":name,"category":category,"address":address}
            k=key(row)
            if k in seen:continue
            seen.add(k);result.append(row)
    return result
def main():
    old=json.loads(PATH.read_text(encoding="utf-8"))
    if old.get("schema")!="walkoffame-stars-v1":raise ValueError("Unsupported schema")
    parsed=get({"prop":"text|revid","disabletoc":"1"}).get("parse",{})
    revision=parsed.get("revid")
    fetched=rows_from_html(parsed.get("text",{}).get("*",""))
    if len(fetched)<2700:
        raise ValueError(f"Unsafe partial import: only {len(fetched)} rows")
    original=old["entries"]
    existing_keys={key(e):e for e in original}
    by_namecat={}
    for e in original:by_namecat.setdefault(nc(e),[]).append(e)
    added=[];changed=[];preserved=[];seen=set(existing_keys)
    for row in fetched:
        k=key(row)
        if k in seen:continue
        group=by_namecat.get(nc(row),[])
        # Address changes are flagged for manual review; never alter established location data.
        if group:
            changed.append({"name":row["name"],"category":row["category"],"wikipedia_address":row["address"],"current_addresses":[e["address"] for e in group]})
            continue
        base=re.sub(r"[^a-z0-9]","",unicodedata.normalize("NFKD",row["name"]).encode("ascii","ignore").decode().lower())[:24] or "star"
        candidate="wikipedia-auto-"+base+"-"+row["category"]
        used={e["id"] for e in original}
        identifier=candidate;index=2
        while identifier in used:
            identifier=candidate+"-"+str(index);index+=1
        entry={"id":identifier,**row,"source":SOURCE,"precision":"Adresse aus Wikipedia; Kartenposition nur geschätzt","coordinate_source":None,"coordinate_method":"address_estimate","coordinate_accuracy":"Hausnummern-Interpolation, nicht sternpräzise","coordinate_verified":False}
        original.append(entry);existing_keys[k]=entry;by_namecat.setdefault(nc(entry),[]).append(entry);seen.add(k);added.append(row)
    now=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    metadata=old.setdefault("update_info",{})
    metadata.update({"source_revision_id":revision,"last_checked_at":now,"last_successful_import_at":now,"last_added_count":len(added),"last_address_change_candidates":len(changed),"last_wikipedia_rows":len(fetched),"update_method":"github-actions-wikipedia-review-safe"})
    old["count"]=len(original)
    report={"last_checked_at":now,"source_revision_id":revision,"wikipedia_rows":len(fetched),"app_entries":len(original),"added":added,"address_change_candidates":changed,"not_automatically_removed":"Any missing entries are retained; review before deletion."}
    Path("update-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    PATH.write_text(json.dumps(old,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
    print(f"Wikipedia revision {revision}; {len(fetched)} rows, {len(added)} added; {len(changed)} address changes queued for review.")
if __name__=="__main__":
    main()
