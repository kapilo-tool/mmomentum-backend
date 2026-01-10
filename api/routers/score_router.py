from fastapi import APIRouter, HTTPException
from services.score_service import calculate_score
from models.score_response import ScoreResponse
from models.error_response import ErrorResponse
import logging
import re

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get(
    "/score/{symbol}",
    response_model=ScoreResponse,
    responses={400: {"model": ErrorResponse}}
)
def get_score(symbol: str):
    logger.info(f"Score requested for symbol: {symbol}")

    # Symbol darf nur Buchstaben und Zahlen enthalten
    if not re.match(r"^[A-Za-z0-9]+$", symbol):
        raise HTTPException(status_code=400, detail="Symbol not valid")

    score = calculate_score(symbol)

    return ScoreResponse(
        symbol=symbol.upper(),
        score=score,
        status="success"
    )

