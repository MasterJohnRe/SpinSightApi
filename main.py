import threading
from fastapi import FastAPI, Query
from sse_starlette.sse import EventSourceResponse
from typing import List, Literal
import uvicorn

from crud import (
    fetch_bonus_game_history,
    fetch_top_multipliers,
    fetch_spin_statistics,
    fetch_topslot_rounds,
    event_generator2,
    watch_changes
)
from models import (
    Result,
    SpinStatistics
)
from constants import DEFAULT_SPINS_AMOUNT

app = FastAPI(title="Crazy time tracker API", version="1.0.0")
threading.Thread(target=watch_changes, daemon=True).start()


@app.get("/events")
async def events():
    async def event_generator():
        return EventSourceResponse(event_generator2())


@app.get("/bonus-game-history", response_model=List[Result])
def get_bonus_game_history(
        bonus_game_id: Literal["b1", "b2", "b3", "b4"],
        spins_amount: int = Query(DEFAULT_SPINS_AMOUNT, ge=1, le=10000)
):
    return fetch_bonus_game_history(bonus_game_id, spins_amount)


@app.get("/top-multipliers", response_model=List[Result])
def get_top_multipliers(
        spins_amount: int = Query(DEFAULT_SPINS_AMOUNT, ge=1, le=10000)):
    return fetch_top_multipliers(spins_amount)


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
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
