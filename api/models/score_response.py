from pydantic import BaseModel

class ScoreResponse(BaseModel):
    symbol: str
    score: int
    status: str

