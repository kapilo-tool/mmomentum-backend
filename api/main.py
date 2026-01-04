from fastapi import FastAPI

app = FastAPI(title="M-Momentum API", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/score")
def score(symbol: str = "AAPL"):
    return {
        "symbol": symbol,
        "scores": {
            "trend_score": 78,
            "momentum_score": 85,
            "volume_score": 70,
            "vcp_score": 65,
            "total_score": 80,
        }
    }
