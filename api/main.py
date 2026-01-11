import datetime
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import yfinance as yf
import certifi
import ssl
ssl_context = ssl.create_default_context(cafile=certifi.where())

# ---------------------------------------------------------
# Logging Setup
# ---------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("momentum-api")

# ---------------------------------------------------------
# FastAPI Setup
# ---------------------------------------------------------
app = FastAPI(
    title="Momentum API",
    description="Stabile, produktionsreife Analyse-API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# Utility: Normalize Close Series
# ---------------------------------------------------------
def normalize_close(data: pd.DataFrame) -> pd.Series:
    """
    Stellt sicher, dass 'Close' immer eine 1D-Series ist.
    Behandelt MultiIndex, DataFrames und inkonsistente yfinance-Ausgaben.
    """
    if "Close" not in data.columns:
        raise ValueError("Daten enthalten keine 'Close'-Spalte.")

    close = data["Close"]

    # Falls MultiIndex → flatten
    if isinstance(close, pd.DataFrame):
        logger.warning("MultiIndex erkannt – flattening angewendet.")
        close = close.iloc[:, 0]

    # Falls Series mit mehreren Ebenen → squeeze
    if hasattr(close, "columns"):
        close = close.squeeze()

    if not isinstance(close, pd.Series):
        raise ValueError("Close konnte nicht in eine Series konvertiert werden.")

    return close.dropna()


# ---------------------------------------------------------
# Utility: Compute Score
# ---------------------------------------------------------
def compute_score(history: pd.Series) -> int:
    if history is None or len(history) < 2:
        return 0

    first = float(history.iloc[0])
    last = float(history.iloc[-1])

    trend_component = 1 if last > first else -1

    volatility = history.pct_change().std()
    vol_component = -1 if volatility > 0.03 else 1

    return trend_component + vol_component


# ---------------------------------------------------------
# Route: Root
# ---------------------------------------------------------
@app.get("/")
def root():
    return {"status": "ok", "message": "Momentum API läuft."}


# ---------------------------------------------------------
# Route: Analyze Ticker
# ---------------------------------------------------------
@app.get("/analyze/{ticker}")
def analyze_ticker(ticker: str):
    logger.info(f"Analyse gestartet für Ticker: {ticker}")

    end = datetime.date.today()
    start = end - datetime.timedelta(days=180)

try:
    data = yf.download(
        ticker,
        start=start,
        end=end,
        interval="1d",
        progress=False,
        auto_adjust=True,
        threads=False,
        ssl_context=ssl_context
    )
    except Exception as e:
        logger.error(f"Fehler beim Laden von yfinance: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Abrufen der Marktdaten.")

    if data is None or data.empty:
        logger.warning(f"Keine Daten für Ticker {ticker} gefunden.")
        raise HTTPException(status_code=404, detail=f"Keine Daten für Ticker {ticker} gefunden.")

    try:
        close = normalize_close(data)
    except Exception as e:
        logger.error(f"Fehler bei der Normalisierung: {e}")
        raise HTTPException(status_code=500, detail="Fehler bei der Datenverarbeitung.")

    score = compute_score(close)

    result = {
        "ticker": ticker.upper(),
        "score": score,
        "first_close": float(close.iloc[0]),
        "last_close": float(close.iloc[-1]),
        "change_percent": float((close.iloc[-1] - close.iloc[0]) / close.iloc[0] * 100),
        "data_points": len(close)
    }

    logger.info(f"Analyse abgeschlossen für {ticker}: {result}")

    return result

