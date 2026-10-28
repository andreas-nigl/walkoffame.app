#!/usr/bin/env python3
"""Conservative catalog QA report: physical identities, categories and candidates.
Never changes public star catalog. Output is a GitHub Actions artifact.
"""
import collections
import datetime as dt
import json
import re
import unicodedata
from pathlib import Path

SOURCE=Path("stars.json")
DEST=Path("catalog-quality-report.json")
def norm(s):
    s=unicodedata.normalize("NFKD",str(s or "")).encode("ascii","ignore").decode().casefold()
    return re.sub(r"[^a-z0-9]+","",s)
def main():
    j=json.loads(SOURCE.read_text(encoding="utf-8"))
    rows=j["entries"]
    idgroups=collections.defaultdict(list)
    physical=collections.defaultdict(list)
    identities=collections.defaultdict(list)
    names=collections.defaultdict(list)
    for e in rows:
        eid=e.get("id")
        idgroups[eid].append(e)
        k=(norm(e.get("name")),norm(e.get("category")),norm(e.get("address")))
        physical[k].append(e)
        identities[(norm(e.get("name")),norm(e.get("category")))].append(e)
        names[norm(e.get("name"))].append(e)
    exact=[{"ids":[e.get("id") for e in group],"name":group[0].get("name"),"category":group[0].get("category"),"address":group[0].get("address")} for group in physical.values() if len(group)>1]
    same_category_different_locations=[{"name":group[0].get("name"),"category":group[0].get("category"),"addresses":[e.get("address") for e in group],"ids":[e.get("id") for e in group]} for group in identities.values() if len({norm(e.get("address")) for e in group})>1]
    multi_category=[{"name":group[0].get("name"),"categories":sorted({e.get("category","") for e in group})} for group in names.values() if len({e.get("category") for e in group})>1]
    missing_loc=[{"name":e.get("name"),"category":e.get("category"),"id":e.get("id")} for e in rows if not re.search(r"\b\d{4}\b",str(e.get("address",""))) and e.get("coordinate_method") not in ("osm_artwork_node","intersection_reference")]
    unknown_category=[{"id":e.get("id"),"name":e.get("name")} for e in rows if e.get("category") in ("unknown",None,"")]
    report={
        "created_at":dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "reference_official_ordinal_latest":2860,
        "reference_disclaimer":"Official 2860th ordinal is not a full export; it cannot prove full coverage of unique physical stars.",
        "total_catalog_rows":len(rows),
        "unique_name_count":len(names),
        "unique_identity_name_category_count":len(identities),
        "unique_name_category_address_count":len(physical),
        "exact_identity_duplicate_count":len(exact),
        "duplicate_ids":[{"id":k,"count":len(v)} for k,v in idgroups.items() if len(v)>1],
        "exact_identity_duplicates":exact,
        "same_name_category_different_addresses_candidates":same_category_different_locations,
        "multi_category_honorees_count":len(multi_category),
        "multi_category_honorees":multi_category,
        "unlocated_candidates":missing_loc,
        "unknown_category_entries":unknown_category,
        "methodology":"Name+category+address yields a provisional physical identity only; 4 Apollo XI commemorative corner plaques are preserved. Different locations and official statuses require human/source verification."
    }
    DEST.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Catalog audit: {len(rows)} records, {len(physical)} unique normalized name+category+address; {len(exact)} exact duplicates; {len(same_category_different_locations)} same name+category at different addresses; {len(unknown_category)} category unknown.")
if __name__=="__main__":main()
