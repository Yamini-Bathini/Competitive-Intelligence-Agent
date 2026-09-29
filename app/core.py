import os,re,sqlite3,threading,datetime as dt,xml.etree.ElementTree as ET,html
import httpx
from .memory import MEM,new_bank
from .data import SEED,ME
from .collect import llm,fetch_text,diff,facts
LOCK=threading.RLock()
DB=sqlite3.connect(os.getenv("DB",":memory:"),check_same_thread=False,isolation_level=None);DB.row_factory=sqlite3.Row
DB.executescript("""create table if not exists ev(id integer primary key,date text,comp text,type text,raw text,text text,imp integer default 1,flag integer default 0,insight text default '',src text default 'manual');
create table if not exists pr(id integer primary key,made text,comp text,kind text,claim text,feat text,due text,status text default 'pending',resolved text);
create table if not exists pref(type text primary key);create table if not exists snap(k text primary key,body text);
create table if not exists watch(k text primary key,comp text,url text,signal text,last text,feed integer default 0);create table if not exists meta(k text primary key,v text);
create table if not exists seen(k text primary key,title text);
create unique index if not exists ev_uq on ev(date,comp,type,raw);""")
try:DB.execute("alter table watch add column feed integer default 0")
except Exception:pass
rows=lambda q,*a:[dict(r) for r in DB.execute(q,a)]
def getm(k,d=None):
    r=DB.execute("select v from meta where k=?",(k,)).fetchone();return r[0] if r else d
def setm(k,v):DB.execute("insert or replace into meta values(?,?)",(k,str(v)))
S={"bank":getm("bank") or new_bank()};setm("bank",S["bank"])
D=lambda a,b:(dt.date.fromisoformat(a)-dt.date.fromisoformat(b)).days

# ---------- alerts (Slack / Discord webhook) ----------
ALERTS=[]
def alert(text):
    ALERTS.insert(0,{"t":dt.datetime.now().strftime("%H:%M:%S"),"text":text});del ALERTS[50:]
    u=os.getenv("ALERT_WEBHOOK","").strip()
    if not u:return
    def post():
        try:
            if "discord.com/api" in u:payload={"content":text}
            else:payload={"text":text}
            httpx.post(u,json=payload,timeout=15)
        except Exception:pass
    threading.Thread(target=post,daemon=True).start()

def comps():return [r[0] for r in DB.execute("select distinct comp from ev order by comp")]
def events():return rows("select * from ev order by date,id")
def month():return int(getm("month",0))
def reset():
    DB.executescript("delete from ev;delete from pr;delete from pref;");S["bank"]=new_bank();setm("bank",S["bank"]);setm("month",0)
def hc_pairs(c,E):
    hs=[e for e in E if e["comp"]==c and e["type"]=="hiring" and re.search("sales|AE",e["raw"])]
    cs=[e for e in E if e["comp"]==c and e["type"]=="pricing" and "cut" in e["raw"]];out=[]
    for h in hs:
        p=next((x for x in cs if 0<D(x["date"],h["date"])<=90),None)
        if p:out.append((h,p))
    return out
feat=lambda e:e["raw"].split(" ",1)[-1]
def cp_pairs(f,l,E):
    out=[]
    for a in [e for e in E if e["comp"]==f and e["type"]=="launch"]:
        b=next((x for x in E if x["comp"]==l and x["type"]=="launch" and feat(x)==feat(a) and 0<D(a["date"],x["date"])<=90),None)
        if b:out.append((b,a))
    return out
avg=lambda P:round(sum(D(p[1]["date"],p[0]["date"]) for p in P)/len(P))
def predict(date,comp,kind,claim,f,due):
    if DB.execute("select 1 from pr where comp=? and kind=? and status='pending' and feat=?",(comp,kind,f)).fetchone():return None
    DB.execute("insert into pr(made,comp,kind,claim,feat,due) values(?,?,?,?,?,?)",(date,comp,kind,claim,f,due))
    MEM.retain(S["bank"],f"On {date} I predicted: {claim}",context="agent prediction",timestamp=date+"T00:00:00Z")
    alert(f"🔮 Hypothesis opened: {claim}")
    return claim
def learn(e):
    """Step 4: check open hypotheses against this signal, and open new ones."""
    date,comp,typ,raw=e["date"],e["comp"],e["type"],e["raw"];prior=[x for x in events() if x["id"]!=e["id"]];notes=[]
    for p in rows("select * from pr where status='pending'"):
        hit=(p["kind"]=="hire-cut" and comp==p["comp"] and typ=="pricing" and "cut" in raw) or (p["kind"]=="copy" and comp==p["comp"] and typ=="launch" and p["feat"] in raw)
        if hit or date>p["due"]:
            st="hit" if hit and date<=p["due"] else "miss"
            DB.execute("update pr set status=?,resolved=? where id=?",(st,date,p["id"]))
            MEM.retain(S["bank"],f"My prediction '{p['claim']}' was a {st} (resolved {date}).",context="prediction outcome",timestamp=date+"T00:00:00Z")
            alert(("✅" if st=="hit" else "❌")+f" Prediction {st}: {p['claim']}")
            notes.append(f"Prediction scored {st.upper()}.")
    if typ=="hiring" and re.search("sales|AE",raw):
        P=hc_pairs(comp,prior)
        if P:
            due=(dt.date.fromisoformat(date)+dt.timedelta(days=avg(P))).isoformat()
            if predict(date,comp,"hire-cut",f"{comp} will cut prices by {due} (it did so ~{avg(P)} days after earlier sales hiring)","",due):notes.append(f"Hypothesis opened: price cut by {due}.")
    if typ=="launch":
        for f in comps():
            if f==comp:continue
            P=cp_pairs(f,comp,prior)
            if P:
                due=(dt.date.fromisoformat(date)+dt.timedelta(days=avg(P))).isoformat()
                if predict(date,f,"copy",f"{f} will copy {comp}'s '{feat(e)}' by {due}",feat(e),due):notes.append(f"Hypothesis opened: {f} copies by {due}.")
    return notes
def importance(typ,raw):
    if typ=="pricing":return 5 if re.search("cut|drop|free|lower|raise",raw) else 3
    if typ=="launch":return 4
    if typ=="hiring":return 4 if re.search("enterprise|sales|AE|ML",raw) else 2
    return 3 if typ=="messaging" else 1
def sowhat(e):
    m=re.search(r"to \$(\d+)",e["raw"])
    if e["type"]=="pricing" and "cut" in e["raw"] and m:return f"Now undercuts {ME['name']} Pro by ${ME['pro_price']-int(m.group(1))}/seat. Hold price and lead with support."
    return {"pricing":"Reflect this in battlecards.","hiring":"Hiring shows where they invest next.","launch":"Check parity against your roadmap.","messaging":"Review positioning overlap."}.get(e["type"],"")
def ingest(date,comp,typ,raw,src="manual"):
    """Pipeline: 1 filter muted -> 2 atomic fact -> 3 retain -> 4 check hypotheses -> 5 flag significant -> 6 insight."""
    with LOCK:
        if DB.execute("select 1 from ev where date=? and comp=? and type=? and raw=?",(date,comp,typ,raw)).fetchone():return None
        muted={r[0] for r in DB.execute("select type from pref")};imp=importance(typ,raw);flag=int(imp>=4 and typ not in muted)
        cur=DB.execute("insert into ev(date,comp,type,raw,text,imp,flag,src) values(?,?,?,?,?,?,?,?)",(date,comp,typ,raw,f"On {date}, {comp} {raw}.",imp,flag,src))
        e={"id":cur.lastrowid,"date":date,"comp":comp,"type":typ,"raw":raw}
        MEM.retain(S["bank"],f"On {date}, {comp} {raw}.",context=f"{comp} {typ} signal",timestamp=date+"T00:00:00Z")
        notes=learn(e)
        if flag:
            ins=(sowhat(e)+" "+" ".join(notes)).strip()
            DB.execute("update ev set insight=? where id=?",(ins,e["id"]))
            alert(f"🚨 {comp} [{typ}] {raw}\nSo what: {ins}")
        return e["id"]
def replay():
    m=month()+1
    if m>6:return
    for d,c,t,r in sorted(SEED):
        if int(d[5:7])==m:ingest(d,c,t,r,"seed")
    setm("month",m)

# ---------- RSS / Atom watches ----------
def _feed_entries(xml):
    root=ET.fromstring(xml);out=[]
    for it in root.iter():
        tag=it.tag.split("}")[-1]
        if tag in ("item","entry"):
            def g(n):
                for c in it:
                    if c.tag.split("}")[-1]==n:
                        t=c.get("href") if n=="link" and c.get("href") else (c.text or "")
                        return html.unescape(re.sub("<[^>]+>","",t)).strip()
                return ""
            title=g("title");link=g("link")
            if title:out.append({"title":title,"link":link})
    return out
def feed_new(k,url):
    xml=httpx.get(url,timeout=30,follow_redirects=True,headers={"User-Agent":"ForesightBot/1.0"}).text
    cur=[e for e in _feed_entries(xml) if e["title"]][:25]
    seen={r["title"] for r in rows("select title from seen where k like ?",k.replace("%","")+"|%",) if r["title"] is not None}
    DB.executemany("insert or ignore into seen values(?,?)",[(k+"|"+e["title"],e["title"]) for e in cur])
    return [e for e in cur if e["title"] not in seen][:5]
def check(comp,url,signal="pricing"):
    with LOCK:
        k=comp+"|"+url;is_feed=signal=="feed" or bool(re.search(r"\.(xml|rss)(\?|$)|/rss|/feed|format=xml|atom",url,re.I))
        o=DB.execute("select body from snap where k=?",(k,)).fetchone() if not is_feed else None
        DB.execute("insert or replace into watch values(?,?,?,?,?,?)",(k,comp,url,signal if not is_feed else "feed",dt.datetime.now().isoformat(timespec="minutes"),int(is_feed)))
        if is_feed:
            items=feed_new(k,url)
            if not o and not DB.execute("select 1 from seen where k=?",(k+"|first",)).fetchone():
                DB.execute("insert or ignore into seen values(?,?)",(k+"|first","1"))
                return {"status":"feed baseline stored (existing posts skipped)","facts":[]}
            out=[]
            for it in items:
                ty=typeof(it["title"]) or "blog"
                if ingest(dt.date.today().isoformat(),comp,ty,f"published '{it['title'][:100]}'","rss"):out.append(it["title"])
                alert(f"📰 {comp} new {ty}: {it['title'][:100]}")
            return {"status":f"{len(out)} new item(s) ingested" if out else "no new items","facts":out}
        new=fetch_text(url)
        DB.execute("insert or replace into snap values(?,?)",(k,new))
        if not o:return {"status":"baseline stored","facts":[]}
        d=diff(o[0],new)
        if not d:return {"status":"no change","facts":[]}
        fs=facts(comp,signal,d)[:5]
        for f in fs:ingest(dt.date.today().isoformat(),comp,signal,f,"auto")
        return {"status":"changed" if fs else "changes ignored as noise","facts":fs,"diff_chars":len(d)}
def check_all():
    out=[]
    for r in rows("select * from watch"):
        try:out.append(dict(check(r["comp"],r["url"],r["signal"]),comp=r["comp"]))
        except Exception as ex:out.append({"comp":r["comp"],"status":"error: "+str(ex)[:100]})
    return out

# ---------- scheduled briefs ----------
def maybe_brief():
    hours=int(os.getenv("BRIEF_HOURS","168") or 0)
    if hours<=0 or not events():return None
    last=getm("brief_last")
    now=dt.datetime.now().timestamp()
    if last and now-float(last)<hours*3600:return None
    setm("brief_last",now)
    b=brief()
    if b.get("empty"):return None
    lines=[f"📋 Weekly competitor brief (to {b['until']})"]
    for e in b["recent"][:5]:lines.append(f"• {e['comp']} [{e['type']}] {e['raw']}")
    for p in b["patterns"][:3]:lines.append(f"Pattern: {p['text']}")
    text="\n".join(lines)
    alert(text)
    if b["narrative"]:alert("🧠 "+str(b["narrative"])[:400])
    setm("brief_last_text",text)
    return {"sent":True,"text":text}

# ---------- patterns with confidence ----------
def _hitrate(comp,kind=None):
    q,par="select status from pr where status!='pending' and comp=?",(comp,)
    if kind:q+=" and kind=?";par=par+(kind,)
    done=rows(q,*par)
    if not done:return None
    return round(100*sum(d["status"]=="hit" for d in done)/len(done))
def patterns():
    E=events();P=[]
    if not E:return P
    C=comps()
    for c in C:
        hc=hc_pairs(c,E)
        if len(hc)>=2:
            hr=_hitrate(c,"hire-cut");conf=f"seen {len(hc)}x"+(f" · predictions {hr}% hit" if hr is not None else "")
            P.append({"comp":c,"conf":conf,"text":f"{c} cuts prices about {avg(hc)} days after it hires sales staff (seen {len(hc)} times).","act":f"Watch {c}'s job board: new sales hires signal a price cut within ~6 weeks."})
        up=[e for e in E if e["comp"]==c and re.search("enterprise",e["raw"],re.I) and e["type"]!="blog"]
        if len(up)>=2:P.append({"comp":c,"conf":f"seen {len(up)}x","text":f"{c} is moving upmarket: {len(up)} signals across hiring, messaging and launches point to enterprise.","act":f"Expect {c} in your enterprise deals."})
        for l in C:
            cp=cp_pairs(c,l,E) if l!=c else []
            if len(cp)>=2:
                hr=_hitrate(c,"copy");conf=f"seen {len(cp)}x"+(f" · predictions {hr}% hit" if hr is not None else "")
                P.append({"comp":c,"conf":conf,"text":f"{c} copies {l}'s launches about {avg(cp)} days later (seen {len(cp)} times).","act":f"Whatever {l} ships next, {c} will likely follow within {avg(cp)} days."})
        last=[e for e in E if e["comp"]==c][-1]
        if D(E[-1]["date"],last["date"])>30:P.append({"comp":c,"conf":None,"text":f"{c} has been quiet for {D(E[-1]['date'],last['date'])} days.","act":f"Check {c} manually: quiet stretches often precede a release."})
    return P
def typeof(s):
    for t,r in [("pricing","pric|cost|cut|\\$"),("hiring","hir|job|recruit"),("launch","launch|ship|feature|releas"),("messaging","messag|homepage|tagline"),("blog","blog|post|content")]:
        if re.search(r,s.lower()):return t
def ask(q):
    ql=q.lower();m=re.search(r"(ignore|skip|mute|hide)\s+(?:the\s+)?(blog|pricing|hiring|launch|messaging)",ql);empty={"events":[],"evidence":[],"patterns":[]}
    if m:
        DB.execute("insert or ignore into pref values(?)",(m.group(2),));MEM.retain(S["bank"],f"Preference: user wants {m.group(2)} signals left out of briefs and alerts.",context="user preference")
        return dict(empty,answer=f"Learned. {m.group(2)} signals will no longer be flagged or shown in briefs.")
    if not events():return dict(empty,answer="Memory is empty. Ingest a month of signals or add a signal first.")
    comp=next((c for c in comps() if c.lower().split()[0] in ql),None);ty=typeof(ql)
    evid=MEM.recall(S["bank"],q);E=[e for e in events() if (not comp or e["comp"]==comp) and (not ty or e["type"]==ty)]
    if not comp and not ty and re.search("what|change|new|latest|happen",ql):E=E[-8:]
    P=[p for p in patterns() if not comp or p["comp"]==comp]
    a=llm(f"Question: {q}\nMemories:\n"+"\n".join(evid)+"\nPatterns:\n"+"\n".join(p["text"] for p in P))
    return {"answer":a or (f"{len(E)} signals found."+(" See patterns below." if P else "")),"events":E,"evidence":evid,"patterns":P}
def brief():
    E=events()
    if not E:return {"empty":True}
    L=E[-1]["date"];mute={r["type"] for r in rows("select * from pref")}
    rec=[dict(e,sowhat=sowhat(e)) for e in E if D(L,e["date"])<=45 and e["type"] not in mute]
    nar=MEM.reflect(S["bank"],"Summarize competitor changes in the last 45 days, name repeated patterns with dates, recommend actions.") or llm("Write a 4 sentence competitor brief:\n"+"\n".join(e["text"] for e in rec))
    return {"until":L,"recent":rec,"patterns":patterns(),"narrative":nar,"muted":sorted(mute)}
def ledger():
    P=rows("select * from pr order by made desc,id desc");done=[p for p in P if p["status"]!="pending"];h=sum(p["status"]=="hit" for p in done)
    return {"predictions":P,"hit_rate":round(100*h/len(done)) if done else None,"resolved":len(done),"open":len(P)-len(done)}
