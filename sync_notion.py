import urllib.request, urllib.error, json, os, sys

token = os.environ.get('NOTION_TOKEN', '')
db_id = os.environ.get('NOTION_DB_ID', '')

print(f"Token: {token[:15]}..." if token else "No token")
print(f"DB ID: {db_id}" if db_id else "No DB ID")

if not token or not db_id:
    print("Secrets missing — keeping existing data.json")
    sys.exit(0)

H = {
    "Authorization": "Bearer " + token,
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def query(ftype=None, n=50):
    body = {"page_size": n}
    if ftype:
        body["filter"] = {"property": "Type", "select": {"equals": ftype}}
    req = urllib.request.Request(
        "https://api.notion.com/v1/databases/" + db_id + "/query",
        data=json.dumps(body).encode(), headers=H, method="POST"
    )
    try:
        r = urllib.request.urlopen(req, timeout=15)
        rows = json.loads(r.read()).get("results", [])
        print(f"  {ftype or 'all'}: {len(rows)} rows")
        return rows
    except urllib.error.HTTPError as e:
        print(f"  Notion {e.code}: {e.read().decode()[:200]}")
        return None  # signal failure
    except Exception as ex:
        print(f"  Error: {ex}")
        return None

def txt(p):
    if not p: return ""
    for k in ["rich_text", "title"]:
        if p.get(k) and p[k]:
            return p[k][0].get("plain_text", "")
    if p.get("select") and p["select"]: return p["select"]["name"]
    if p.get("number") is not None: return str(p["number"])
    return ""

# Try to query — if any query fails, keep existing data.json
print("Querying Notion...")
daily    = query("Daily", 1)
projects = query("Project", 50)
people   = query("Person", 20)

if daily is None or projects is None or people is None:
    print("Notion not accessible — keeping existing data.json unchanged")
    sys.exit(0)  # exit 0 = workflow shows green

# Build data.json from Notion data
dash = {"score": 62, "nw": "$0.05M", "action": "", "action_div": "Commerce · Veritan", "phase": "Phase 1", "burn": "$4,700/mo"}
if daily:
    p = daily[0]["properties"]
    raw = txt(p.get("Score"))
    dash["score"]  = int(float(raw)) if raw else 62
    dash["nw"]     = txt(p.get("Net Worth"))   or "$0.05M"
    dash["action"] = txt(p.get("Next Action")) or ""

projs, exceptions = [], []
for row in projects:
    p   = row["properties"]
    sig = txt(p.get("Signal")) or "Green"
    n2  = txt(p.get("Name"))
    a   = txt(p.get("Next Action"))
    projs.append({"name": n2, "div": txt(p.get("Division")), "signal": sig,
                  "kpi": txt(p.get("KPI")), "action": a,
                  "owner": txt(p.get("Owner")), "status": txt(p.get("Status"))})
    if sig == "Red": exceptions.append(n2 + " — " + a)

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

print(f"SUCCESS — {len(projs)} projects, {len(ppl)} people synced")
