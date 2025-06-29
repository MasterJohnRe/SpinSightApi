import time
import threading
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Query
from sse_starlette.sse import EventSourceResponse
from typing import List, Literal, Optional, Dict
import uvicorn
from starlette.responses import HTMLResponse

from crud import (
    fetch_game_history,
    fetch_top_multipliers,
    fetch_spin_statistics,
    fetch_topslot_rounds,
    event_generator,
    watch_changes
)
from models import (
    Result,
    SpinStatistics,
    GameHistoryResponse
)
from constants import DEFAULT_SPINS_AMOUNT, DEFAULT_PAGE

app = FastAPI(title="Crazy time tracker API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://gamdom.com"],  # Or use ["*"] during testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
threading.Thread(target=watch_changes, daemon=True).start()

@app.get("/block")
def block():
    time.sleep(50000)


@app.get("/privacy-policy", response_class=HTMLResponse)
def serve_privacy_policy():
    with open("privacy_policy.html", "r", encoding="utf-8") as file:
        return file.read()


@app.get("/events")
async def events():
    return EventSourceResponse(event_generator())


@app.get("/game-history", response_model=GameHistoryResponse)
def get_game_history(
        game_id: Optional[Literal["1", "2", "5", "10", "b1", "b2", "b3", "b4"]] = Query(None),
        spins_amount: int = Query(DEFAULT_SPINS_AMOUNT, ge=1, le=10000),
        page: int = Query(DEFAULT_PAGE, ge=1, le=10000)
):
    return fetch_game_history(game_id, spins_amount, page)


@app.get("/top-multipliers", response_model=List[Result])
def get_top_multipliers(
        hours: int = Query(DEFAULT_SPINS_AMOUNT, ge=1, le=1000)):
    return fetch_top_multipliers(hours)


@app.get("/spin-statistics", response_model=List[SpinStatistics])
def get_last_spins_statistics(
        spins_amount: int = Query(DEFAULT_SPINS_AMOUNT, ge=1, le=10000)
):
    return fetch_spin_statistics(spins_amount)


@app.get("/topslot-rounds", response_model=List[Result])
def get_last_topslot_rounds(
        spins_amount: int = Query(DEFAULT_SPINS_AMOUNT, ge=1, le=10000)
):
    return fetch_topslot_rounds(spins_amount)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
