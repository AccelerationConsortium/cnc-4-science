"""Lightweight FastAPI frontend for the vacuum pick-and-place tic-tac-toe demo.

Shares the same :class:`game_session.GameSession` the CLI protocol uses, so
the browser and the terminal can't end up out of sync. One process, one
``GameSession``, one CNC — the session's internal ``threading.Lock`` prevents
two concurrent HTTP requests from driving the gantry at the same time.

Run::

    cd examples/vacuum_pick_and_place
    uvicorn web.app:app --host 0.0.0.0 --port 8000

Then open http://localhost:8000/ in a browser.
"""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Make the demo root importable so we can reach game_session / app_runtime.
WEB_DIR = Path(__file__).resolve().parent
DEMO_ROOT = WEB_DIR.parent
sys.path.insert(0, str(DEMO_ROOT))

from app_runtime import build_session, load_configs, shutdown  # noqa: E402


class StartRequest(BaseModel):
    mode: int  # 1 or 2
    human_symbol: str | None = None  # "X" or "O" — required when mode == 1
    ai_difficulty: str | None = None  # "easy" | "medium" | "hard" — required when mode == 1


class MoveRequest(BaseModel):
    position: str  # "A1".."C3"


@asynccontextmanager
async def lifespan(app: FastAPI):
    cnc_cfg, _ = load_configs()
    session, cnc, gripper = build_session()
    app.state.session = session
    app.state.cnc = cnc
    app.state.gripper = gripper
    app.state.virtual = cnc_cfg.get("virtual", False)
    app.state.move_speed = cnc_cfg.get("move_speed", 2500)
    try:
        yield
    finally:
        shutdown(
            app.state.cnc,
            app.state.gripper,
            virtual=app.state.virtual,
            move_speed=app.state.move_speed,
        )


app = FastAPI(title="CNC Tic-Tac-Toe", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")


@app.get("/")
def index():
    return FileResponse(WEB_DIR / "static" / "index.html")


@app.get("/api/state")
def get_state():
    return app.state.session.snapshot()


@app.post("/api/start")
def start_game(req: StartRequest):
    try:
        state = app.state.session.start(
            mode=req.mode,
            human_symbol=req.human_symbol,
            ai_difficulty=req.ai_difficulty,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "Game started", "state": state}


@app.post("/api/move")
def make_move(req: MoveRequest):
    try:
        state = app.state.session.make_move(req.position)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"message": "Move accepted", "state": state}


@app.post("/api/reset")
def reset_board():
    state = app.state.session.reset()
    return {"message": "Board reset", "state": state}
