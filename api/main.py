from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

app = FastAPI(
    title="Momentum API",
    description="Berechnet Momentum-, Trend- und Volatilitätskennzahlen für Aktien.",
    version="1.0.0",
)

# CORS – später passen wir die Origin auf dein Frontend an
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # für Produktion später enger machen
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PricePoint(BaseModel):
    date: str
    close: float


class AnalyzeResponse(BaseModel):
    ticker: str
    score: float
    trend: str
    momentum: str
    volatility: str
    current_price: float
    change_percent: float
    chart: list[PricePoint]


def compute_score(history: pd.Series) -> float:
    """Einfache Score-Logik für MVP."""
    if len(history) < 30:
        return 0.0

    last_30 = history[-30:]
    perf_30 = (last_30.iloc[-1] / last_30.iloc[0] - 1) * 100

    returns = last_30.pct_change().dropna()
    vol = returns.std() * (252**0.5) * 100  # annualisierte Volatilität

    trend_component = 1 if history.iloc[-1] > history.iloc[0] else -1

    raw_score = perf_30 * 0.6 + (20 - min(vol, 40)) * 0.3 + trend_component * 10

    return round(max(min(raw_score, 100), 0), 2)


def classify_trend(history: pd.Series) -> str:
    if history.iloc[-1] > history.iloc[0]:
        return "up"
    elif history.iloc[-1] < history.iloc[0]:
        return "down"
    return "sideways"


def classify_momentum(history: pd.Series) -> str:
    if len(history) < 10:
        return "weak"

    last_10 = history[-10:]
    perf_10 = (last_10.iloc[-1] / last_10.iloc[0] - 1) * 100

    if perf_10 > 10:
        return "strong"
    elif perf_10 > 3:
        return "medium"
    elif perf_10 > 0:
        return "weak"
    else:
        return "negative"


def classify_volatility(history: pd.Series) -> str:
    if len(history) < 30:
        return "unknown"

    returns = history.pct_change().dropna()
    vol = returns.std() * (252**0.5) * 100

    if vol < 20:
        return "low"
    elif vol < 40:
        return "medium"
    else:
        return "high"


@app.get("/analyze/{ticker}", response_model=AnalyzeResponse)
def analyze_ticker(ticker: str):
    ticker = ticker.upper().strip()
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker darf nicht leer sein.")

    end = datetime.utcnow()
    start = end - timedelta(days=200)

    try:
        data = yf.download(ticker, start=start, end=end)
    except Exception:
        raise HTTPException(status_code=500, detail="Fehler beim Abruf von Marktdaten.")

    if data.empty or "Close" not in data.columns:
        raise HTTPException(status_code=404, detail=f"Keine Daten für Ticker {ticker} gefunden.")

    close = data["Close"].dropna()

    if len(close) < 10:
        raise HTTPException(status_code=400, detail="Nicht genug historische Daten für eine Analyse.")

    score = compute_score(close)
    trend = classify_trend(close)
    momentum = classify_momentum(close)
    volatility = classify_volatility(close)

    current_price = float(close.iloc[-1])
    first_price = float(close.iloc[0])
    change_percent = round((current_price / first_price - 1) * 100, 2)

    chart_points = [
        PricePoint(date=index.strftime("%Y-%m-%d"), close=float(price))
        for index, price in close[-90:].items()
    ]

    return AnalyzeResponse(
        ticker=ticker,
        score=score,
        trend=trend,
        momentum=momentum,
        volatility=volatility,
        current_price=current_price,
        change_percent=change_percent,
        chart=chart_points,
    )


@app.get("/")
def root():
    return {"status": "ok", "message": "Momentum API läuft."}
