import urllib.request, urllib.error, json, os, sys

token = os.environ.get('NOTION_TOKEN','')
db_id = os.environ.get('NOTION_DB_ID','')

if not token:
    print("ERROR: NOTION_TOKEN secret not set"); sys.exit(1)
if not db_id:
    print("ERROR: NOTION_DB_ID secret not set"); sys.exit(1)

print("Token:", token[:12] + "...")
print("DB ID:", db_id)

H = {
    "Authorization": "Bearer " + token,
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def query(ftype=None, n=50):
    body = {"page_size": n}
    if ftype:
        body["filter"] = {"property": "Type", "select": {"equals": ftype}}
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        "https://api.notion.com/v1/databases/" + db_id + "/query",
        data=data, headers=H, method="POST"
    )
    try:
        r = urllib.request.urlopen(req, timeout=15)
        rows = json.loads(r.read()).get("results", [])
        print("Query", ftype or "all", "->", len(rows), "rows")
        return rows
    except urllib.error.HTTPError as e:
        msg = e.read().decode()
        print("Notion error", e.code, ":", msg)
        sys.exit(1)

def txt(prop):
    if not prop: return ""
    for k in ["rich_text", "title"]:
        if prop.get(k) and prop[k]:
            return prop[k][0].get("plain_text", "")
    if prop.get("select") and prop["select"]:
        return prop["select"]["name"]
    if prop.get("number") is not None:
        return str(prop["number"])
    return ""

daily    = query("Daily", 1)
projects = query("Project", 50)
people   = query("Person", 20)

dash = {"score": 62, "nw": "$0.05M", "action": "", "action_div": "Commerce", "phase": "Phase 1", "burn": "$4,700/mo"}
if daily:
    p = daily[0]["properties"]
    score_raw = txt(p.get("Score"))
    dash["score"] = int(float(score_raw)) if score_raw else 62
    dash["nw"]     = txt(p.get("Net Worth"))   or "$0.05M"
    dash["action"] = txt(p.get("Next Action")) or ""

projs = []
exceptions = []
for row in projects:
    p = row["properties"]
    sig    = txt(p.get("Signal")) or "Green"
    name   = txt(p.get("Name"))
    action = txt(p.get("Next Action"))
    projs.append({"name": name, "div": txt(p.get("Division")), "signal": sig,
                  "kpi": txt(p.get("KPI")), "action": action,
                  "owner": txt(p.get("Owner")), "status": txt(p.get("Status"))})
    if sig == "Red":
        exceptions.append(name + " -- " + action)

ppl = []
for row in people:
    p = row["properties"]
    ppl.append({"name": txt(p.get("Name")), "kpi": txt(p.get("KPI")),
                "next_action": txt(p.get("Next Action")), "signal": txt(p.get("Signal"))})

out = {**dash,
       "exception1": exceptions[0] if exceptions else "",
       "exception2": exceptions[1] if len(exceptions) > 1 else "",
       "projects": projs, "people": ppl,
       "updated": daily[0].get("last_edited_time", "") if daily else ""}

with open("data.json", "w") as f:
    json.dump(out, f, indent=2)
print("SUCCESS — data.json written:", len(projs), "projects,", len(ppl), "people")
