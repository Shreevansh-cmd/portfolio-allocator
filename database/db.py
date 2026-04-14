import sqlite3
import json
import os

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "portfolio.db")

def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolio_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            investment_amount REAL,
            risk_level TEXT,
            market_scenario TEXT,
            portfolio TEXT,
            expected_return REAL,
            risk REAL,
            sharpe_ratio REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_allocation(
    investment_amount: float,
    risk_level: str,
    market_scenario: str,
    portfolio: dict,
    expected_return: float,
    risk: float,
    sharpe_ratio: float,
):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    portfolio_json = json.dumps(portfolio)
    
    cursor.execute("""
        INSERT INTO portfolio_history 
        (investment_amount, risk_level, market_scenario, portfolio, expected_return, risk, sharpe_ratio)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (investment_amount, risk_level, market_scenario, portfolio_json, expected_return, risk, sharpe_ratio))
    
    conn.commit()
    conn.close()

def get_history() -> list:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM portfolio_history ORDER BY timestamp DESC
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    # Convert rows to list of dicts and parse JSON for portfolio
    history = []
    for row in rows:
        item = dict(row)
        item['portfolio'] = json.loads(item['portfolio'])
        history.append(item)
        
    return history
