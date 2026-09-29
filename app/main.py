import os,time,threading,datetime as dt
from pathlib import Path
from fastapi import FastAPI,HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from . import core
from .memory import OPS,MEM
app=FastAPI(title="Foresight")
STATIC_DIR=Path(__file__).resolve().parent.parent/"static"
TYPES={"pricing","hiring","launch","messaging","blog"}
class Q(BaseModel):
    q:str
class Sig(BaseModel):
    date:str
    competitor:str
    type:str
    text:str
class Watch(BaseModel):
    competitor:str
    url:str
    signal:str="pricing"
def loop():
    while True:
        time.sleep(max(1,int(os.getenv("CHECK_MINUTES","60")))*60)
        try:core.check_all()
        except Exception:pass
        try:core.maybe_brief()
        except Exception:pass
@app.on_event("startup")
def start():
    if os.getenv("VERCEL") == "1" and core.month() == 0:
        bank = os.getenv("HINDSIGHT_BANK_ID", "foresight-production")
        core.S["bank"] = bank
        core.setm("bank", bank)
        marker = "foresight-production-seed-v1-complete"
        seeded = any(marker in item for item in MEM.recall(bank, marker, k=10))
        hindsight = MEM.hs
        if seeded:
            MEM.hs = None
        try:
            for _ in range(6):
                core.replay()
            if not seeded:
                MEM.retain(bank, marker, context="deployment seed marker")
        finally:
            MEM.hs = hindsight
    threading.Thread(target=loop,daemon=True).start()
@app.get("/")
def index():return FileResponse(STATIC_DIR/"index.html")
@app.get("/api/state")
def state():return {"backend":MEM.name,"error":MEM.err,"bank":core.S["bank"],"month":core.month(),"events":len(core.events()),"ops":OPS[:60],"competitors":core.comps()}
@app.post("/api/replay")
def replay(all:bool=False):
    while core.month()<6:
        core.replay()
        if not all:break
    return state()
@app.post("/api/reset")
def reset():core.reset();OPS.clear();return state()
@app.post("/api/ask")
def ask(b:Q):return core.ask(b.q)
@app.post("/api/signal")
def signal(b:Sig):
    if b.type not in TYPES:raise HTTPException(400,"type must be one of: "+", ".join(sorted(TYPES)))
    try:dt.date.fromisoformat(b.date)
    except ValueError:raise HTTPException(400,"date must look like 2026-09-20")
    if not b.competitor.strip() or not b.text.strip():raise HTTPException(400,"competitor and text are required")
    return {"id":core.ingest(b.date,b.competitor.strip(),b.type,b.text.strip())}
@app.post("/api/collect")
def collect(b:Watch):
    try:return core.check(b.competitor,b.url,b.signal)
    except Exception as ex:raise HTTPException(400,f"could not fetch page: {str(ex)[:120]}")
@app.get("/api/watch")
def watch():return core.rows("select comp,url,signal,last from watch")
@app.post("/api/check-all")
def check_all():return core.check_all()
@app.post("/api/test-alert")
def test_alert():core.alert("🧪 Foresight test alert — the webhook path works.");return {"sent":bool(os.getenv("ALERT_WEBHOOK","")),"webhook_configured":bool(os.getenv("ALERT_WEBHOOK",""))}
@app.get("/api/signals")
def signals(limit:int=8):return core.rows("select * from ev order by date desc,id desc limit ?",limit)
@app.get("/api/timeline")
def timeline():return {"events":core.events(),"patterns":core.patterns(),"competitors":core.comps()}
@app.get("/api/brief")
def brief():return core.brief()
@app.get("/api/predictions")
def preds():return core.ledger()
