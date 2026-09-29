"""Memory layer: Hindsight (retain/recall/reflect) with an automatic local fallback so the app never crashes.

All Hindsight calls run on one dedicated event-loop thread (run_coroutine_threadsafe).
FastAPI sync endpoints and the watcher thread otherwise use different event loops,
which makes the client's shared aiohttp session blow up with
"Timeout context manager should be used inside a task".
"""
import os,re,time,threading,asyncio,datetime as dt
from dotenv import load_dotenv
load_dotenv()
OPS=[]
def log(k,t):OPS.insert(0,{"op":k,"text":t,"t":time.strftime("%H:%M:%S")});del OPS[150:]
def new_bank():return f"foresight-{int(time.time())}"
tok=lambda s:set(re.findall(r"[a-z0-9$]+",s.lower()))
class Local:
    def __init__(s):s.items=[]
    def retain(s,content,context=""):s.items.append((content,context))
    def recall(s,query,k=8):
        q=tok(query);sc=sorted(((len(q&tok(c+" "+x)),c) for c,x in s.items),key=lambda a:-a[0]);return [c for n,c in sc if n>0][:k]
class _Loop:
    """One long-lived event loop in its own thread; every Hindsight call runs on it."""
    def __init__(s):
        s.loop=asyncio.new_event_loop()
        threading.Thread(target=s.loop.run_forever,daemon=True,name="hindsight-loop").start()
    def run(s,coro,timeout=300):return asyncio.run_coroutine_threadsafe(coro,s.loop).result(timeout)
class HS:
    def __init__(s,url,key=None):
        from hindsight_client import Hindsight
        s.L=_Loop()
        try:s.ac=Hindsight(base_url=url,api_key=key) if key else Hindsight(base_url=url)
        except TypeError:s.ac=Hindsight(base_url=url)
        s.made=set()
    def _call(s,name,**k):
        coro=getattr(s.ac,"a"+name)(**k)
        return s.L.run(coro)
    def retain(s,bank,content,context="",timestamp=None):
        if bank not in s.made:
            try:s._call("create_bank",bank_id=bank,name=bank)
            except Exception:pass
            s.made.add(bank)
        t=dt.datetime.fromisoformat(timestamp.rstrip("Z")).replace(tzinfo=dt.timezone.utc) if timestamp else None
        try:s._call("retain",bank_id=bank,content=content,context=context,timestamp=t)
        except Exception:s._call("retain",bank_id=bank,content=content,context=context)
    def recall(s,bank,query,k=8):
        r=s._call("recall",bank_id=bank,query=query);items=getattr(r,"results",r) or []
        return [getattr(i,"text",None) or str(i) for i in items][:k]
    def reflect(s,bank,query):
        r=s._call("reflect",bank_id=bank,query=query);return getattr(r,"text",None) or str(r)
class Mem:
    def __init__(s):
        s.local=Local();s.hs=None;s.err=None;u=os.getenv("HINDSIGHT_URL");s.mode="db" if os.getenv("MEMORY","").strip().lower() in ("db","local","foresight-db","foresight.db") else "hs"
        if s.mode=="db":pass
        elif not u:s.err="HINDSIGHT_URL is not set (create a .env file, see .env.example)"
        else:
            try:s.hs=HS(u,os.getenv("HINDSIGHT_API_KEY"))
            except Exception as ex:s.err=f"{type(ex).__name__}: {ex}"
    @property
    def name(s):return "foresight db" if s.mode=="db" else ("hindsight" if s.hs and not s.err else "local (fallback)")
    def _try(s,fn,*a,**k):
        if not s.hs:return False,None
        try:r=fn(*a,**k);s.err=None;return True,r
        except Exception as ex:
            s.err=f"{type(ex).__name__}: {str(ex)[:200]}";log("error",s.err);return False,None
    def retain(s,bank,content,context="",timestamp=None):
        s.local.retain(content,context);s._try(s.hs.retain if s.hs else None,bank,content,context,timestamp)
        log("retain",content)
    def recall(s,bank,query,k=8):
        ok,r=s._try(s.hs.recall if s.hs else None,bank,query,k)
        r=r if ok else s.local.recall(query,k);log("recall",f'"{query}" returned {len(r)}');return r
    def reflect(s,bank,query):
        ok,r=s._try(s.hs.reflect if s.hs else None,bank,query);log("reflect",query);return r if ok else None
MEM=Mem()
