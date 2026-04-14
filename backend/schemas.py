from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, List
from datetime import datetime

class AllocationRequest(BaseModel):
    investment_amount: float
    risk_level: str
    market_scenario: str

class AllocationResponse(BaseModel):
    portfolio: dict
    expected_return: float
    risk: float
    sharpe_ratio: float
    timestamp: datetime = None
    
    model_config = ConfigDict(from_attributes=True)

class HistoryItem(BaseModel):
    id: int
    investment_amount: float
    risk_level: str
    market_scenario: str
    portfolio: dict
    expected_return: float
    risk: float
    sharpe_ratio: float
    timestamp: str

class HistoryResponse(BaseModel):
    history: List[HistoryItem]

class SaveRequest(BaseModel):
    investment_amount: float
    risk_level: str
    market_scenario: str
    portfolio: dict
    expected_return: float
    risk: float
    sharpe_ratio: float
