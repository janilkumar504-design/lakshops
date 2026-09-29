"""FastAPI server + web UI.  Run: uvicorn server:app --port 8000"""
import os
import laksh_ops  # loads .env first
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from laksh_ops.memory import make_memory, LocalMemory, SafeMemory
from laksh_ops.brain import OpsBrain
from laksh_ops import triage as T
from laksh_ops.seed_data import seed

ROOT = Path(__file__).parent
TOKEN = os.getenv("LAKSH_ACCESS_TOKEN", "")
app = FastAPI(title="LAKSH Ops")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.middleware("http")
async def guard(request: Request, call_next):
    """If LAKSH_ACCESS_TOKEN is set (do this whenever the app is on the internet), /api needs it."""
    if TOKEN and request.url.path.startswith("/api/") and request.headers.get("x-access-token") != TOKEN:
        return JSONResponse({"detail": "bad or missing access token"}, status_code=401)
    return await call_next(request)
mem = make_memory()
brain = OpsBrain(mem)
ENG = os.getenv("LAKSH_ENGINEER", "Asha")


class Msg(BaseModel):
    text: str
    engineer: str = ENG
    use_memory: bool = True


class Resolve(BaseModel):
    service: str
    symptom: str
    cause: str = ""
    fix: str = ""
    ttr: int = 0
    failed: list[str] = []
    engineer: str = ENG


@app.get("/")
def index():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/sw.js")
def sw():
    return FileResponse(ROOT / "static" / "sw.js", media_type="application/javascript")


@app.get("/api/status")
def status():
    return {"backend": mem.name, "engineer": ENG, "auth": bool(TOKEN)}


@app.post("/api/chat")
def chat(m: Msg):
    return brain.handle(m.text, m.engineer, m.use_memory)


@app.post("/api/compare")
def compare(m: Msg):
    """Same alert, with and without memory - the demo's money shot."""
    return {"without": T.generic_plan(m.text), "with": T.memory_plan(mem, m.text, m.engineer)}


@app.post("/api/resolve")
def resolve(r: Resolve):
    T.log_resolution(mem, r.service, r.symptom, r.cause or None, r.fix or None, r.ttr or None,
                     r.engineer, r.failed, T.detect_trigger(r.symptom))
    return {"ok": True}


@app.get("/api/brief")
def brief(service: str = ""):
    return {"text": T.weekly_brief(mem, service or None), "backend": mem.name}


@app.post("/api/seed")
def do_seed():
    return {"seeded": seed(mem)}


@app.post("/api/reset")
def reset():
    if isinstance(mem, (LocalMemory, SafeMemory)) and (isinstance(mem, LocalMemory) or mem.failed):
        mem.reset()
        return {"ok": True}
    return {"ok": False, "detail": "Hindsight bank not reset from the UI - use a fresh HINDSIGHT_BANK id."}
