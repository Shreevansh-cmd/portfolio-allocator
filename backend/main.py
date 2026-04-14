import sys
import os
import pandas as pd
from datetime import datetime

# Add the parent directory to Python path for importing ML models
db_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(db_dir)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.schemas import AllocationRequest, AllocationResponse, SaveRequest, HistoryResponse
from database.db import init_db, save_allocation, get_history

# Import ML functions
from models.return_predictor import predict_returns
from utils.risk_profiler import get_risk_profile
from optimization.portfolio_optimizer import optimize_portfolio

app = FastAPI(title="AI Portfolio Allocator API")

# Initialize DB on startup
@app.on_event("startup")
def startup_event():
    init_db()

# Allow CORS so frontend can communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def calculate_portfolio_metrics(weights, returns):
    w = []
    r = []

    for asset in weights:
        w.append(weights[asset])
        r.append(returns[asset])

    w = pd.Series(w)
    r = pd.Series(r)

    expected_return = float((w * r).sum())
    volatility = float((w * (r - r.mean()) ** 2).sum() ** 0.5)

    risk_free_rate = 0.04
    sharpe_ratio = float(
        (expected_return - risk_free_rate) / volatility
        if volatility != 0 else 0
    )

    return expected_return, volatility, sharpe_ratio


@app.post("/allocate", response_model=AllocationResponse)
def allocate_portfolio(req: AllocationRequest):
    try:
        risk_profile = get_risk_profile(req.risk_level)
        predicted_returns = predict_returns()

        scenario_multiplier = {
            "Bull": 1.15,
            "Normal": 1.0,
            "Bear": 0.85
        }

        multiplier = scenario_multiplier.get(req.market_scenario, 1.0)

        adjusted_returns = {
            asset: float(ret * multiplier)
            for asset, ret in predicted_returns.items()
        }

        final_portfolio = optimize_portfolio(adjusted_returns, risk_profile)

        portfolio_return, portfolio_volatility, sharpe_ratio = calculate_portfolio_metrics(
            final_portfolio, adjusted_returns
        )

        return AllocationResponse(
            portfolio=final_portfolio,
            expected_return=portfolio_return,
            risk=portfolio_volatility,
            sharpe_ratio=sharpe_ratio,
            timestamp=datetime.now()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save")
def save_portfolio(req: SaveRequest):
    try:
        save_allocation(
            investment_amount=req.investment_amount,
            risk_level=req.risk_level,
            market_scenario=req.market_scenario,
            portfolio=req.portfolio,
            expected_return=req.expected_return,
            risk=req.risk,
            sharpe_ratio=req.sharpe_ratio
        )
        return {"status": "success", "message": "Saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history", response_model=HistoryResponse)
def get_portfolio_history():
    try:
        records = get_history()
        return {"history": records}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok"}
