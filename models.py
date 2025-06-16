from pydantic import BaseModel, Field
from typing import Optional, List
from bson import ObjectId  # optional, if you need to use _id


class Winner(BaseModel):
    screenName: str
    winnings: float
    multiplier: Optional[int] = None


class BonusGameExtraInfo(BaseModel):
    coinPlacement: Optional[str] = None
    headsMultiplier: Optional[int] = None
    tailsMultiplier: Optional[int] = None
    coinSideResult: Optional[str] = None
    dropZone: Optional[int] = None
    landingZone: Optional[int] = None
    maxMultiplier: Optional[int] = None
    minMultiplier: Optional[int] = None
    result: Optional[int] = None
    totalResult: Optional[int] = None
    greenResults: Optional[List[str]] = None
    blueResults: Optional[List[str]] = None
    yellowResults: Optional[List[str]] = None


class TopSlot(BaseModel):
    result: str
    multiplier: str


class Result(BaseModel):
    gameId: str = Field(..., alias="gameId")
    gameTime: int
    topSlot: TopSlot
    bonusGameExtraInfo: Optional[BonusGameExtraInfo] = None
    result: str
    totalMultiplierHit: Optional[int] = None
    totalBettors: int
    totalMoneyWon: float
    totalWinners: int
    winners: List[Winner]


class SpinStatistics(BaseModel):
    result: str
    frequency: float
    lastOccurrence: Optional[int]

class GameHistoryResponse(BaseModel):
    hasNextPage: bool
    results: List[Result]