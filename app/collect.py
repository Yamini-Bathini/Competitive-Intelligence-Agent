"""Collectors: fetch a page, diff it, keep only meaningful changes as atomic facts."""
import os,re,json,httpx,difflib
from bs4 import BeautifulSoup
from dotenv import load_dotenv
load_dotenv()
def llm(prompt,system="You are a competitive intelligence analyst. Cite dates. Be concise."):
    k=os.getenv("GROQ_API_KEY")
    if not k:return None
    try:
        r=httpx.post("https://api.groq.com/openai/v1/chat/completions",headers={"Authorization":"Bearer "+k},
        json={"model":os.getenv("LLM_MODEL","openai/gpt-oss-120b"),"messages":[{"role":"system","content":system},{"role":"user","content":prompt}]},timeout=40)
        return r.json()["choices"][0]["message"]["content"]
    except Exception:return None
def fetch_text(url):
    h=httpx.get(url,timeout=30,follow_redirects=True,headers={"User-Agent":"ForesightBot/1.0"}).text
    return BeautifulSoup(h,"html.parser").get_text("\n",strip=True)
def diff(old,new):
    return "\n".join(l for l in difflib.unified_diff((old or "").splitlines(),new.splitlines(),lineterm="",n=0) if l[:1] in "+-" and l[:3] not in("+++","---"))
NOISE=re.compile(r"cookie|©|copyright|privacy|subscribe|sign in|log in|\b20\d\d\b\s*$",re.I)
def facts(comp,signal,d):
    out=llm(f'Competitor {comp}, signal {signal}. From this page diff return ONLY JSON {{"facts":["one self-contained sentence with old and new values"]}}. Return an empty list if the change is trivial (cookie banners, dates, layout).\n{d[:3000]}')
    try:return [f for f in json.loads(out[out.index("{"):out.rindex("}")+1])["facts"] if f]
    except Exception:return [f"changed its {signal} page: {l[1:].strip()[:140]}" for l in d.splitlines() if l.startswith("+") and len(l)>18 and not NOISE.search(l)][:5]
