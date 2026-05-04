"""AI Trading System - 模拟交易执行模块
支持模拟买卖、持仓管理、交易日志
"""
import json, os, time
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
JOURNAL_FILE = os.path.join(DATA_DIR, "trading_journal.json")
PORTFOLIO_FILE = os.path.join(DATA_DIR, "portfolio.json")

def _load_json(path, default=None):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return default if default else {}

def _save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def init_account(capital=100000):
    """初始化模拟账户"""
    portfolio = {
        "cash": capital,
        "positions": [],
        "total_value": capital,
        "initial_capital": capital,
        "created_at": datetime.now().isoformat(),
    }
    _save_json(PORTFOLIO_FILE, portfolio)
    _save_json(JOURNAL_FILE, {"trades": [], "diaries": []})
    return {"status": "ok", "capital": capital, "message": f"账户初始化成功，初始资金 {capital} 元"}

def buy(symbol, name, price, quantity):
    """买入股票"""
    portfolio = _load_json(PORTFOLIO_FILE, {"cash": 100000, "positions": [], "initial_capital": 100000})
    cost = price * quantity
    
    if cost > portfolio["cash"]:
        return {"error": f"资金不足，需要 {cost:.2f}，可用 {portfolio['cash']:.2f}"}
    
    portfolio["cash"] -= cost
    portfolio["positions"].append({
        "symbol": symbol, "name": name,
        "quantity": quantity, "buy_price": price,
        "current_price": price, "buy_time": datetime.now().isoformat()
    })
    portfolio["total_value"] = portfolio["cash"] + sum(p["quantity"] * p["current_price"] for p in portfolio["positions"])
    _save_json(PORTFOLIO_FILE, portfolio)
    
    # 记录交易
    _record_trade("BUY", symbol, name, price, quantity, cost)
    
    return {
        "status": "ok", "action": "买入",
        "symbol": symbol, "name": name,
        "price": price, "quantity": quantity,
        "cost": cost, "cash_remaining": portfolio["cash"]
    }

def sell(symbol, price, quantity=None):
    """卖出股票"""
    portfolio = _load_json(PORTFOLIO_FILE, {"cash": 100000, "positions": [], "initial_capital": 100000})
    
    pos = None
    for p in portfolio["positions"]:
        if p["symbol"] == symbol:
            pos = p
            break
    
    if not pos:
        return {"error": f"未持有 {symbol}"}
    
    qty = quantity if quantity else pos["quantity"]
    if qty > pos["quantity"]:
        return {"error": f"持仓不足，持有 {pos['quantity']} 股，尝试卖出 {qty} 股"}
    
    value = price * qty
    portfolio["cash"] += value
    pos["quantity"] -= qty
    
    # 计算盈亏
    buy_cost = pos["buy_price"] * qty
    profit = value - buy_cost
    profit_pct = (price - pos["buy_price"]) / pos["buy_price"] * 100
    
    if pos["quantity"] <= 0:
        portfolio["positions"] = [p for p in portfolio["positions"] if p["symbol"] != symbol]
    
    portfolio["total_value"] = portfolio["cash"] + sum(p["quantity"] * p["current_price"] for p in portfolio["positions"])
    _save_json(PORTFOLIO_FILE, portfolio)
    
    _record_trade("SELL", symbol, pos["name"], price, qty, value, profit)
    
    return {
        "status": "ok", "action": "卖出",
        "symbol": symbol, "name": pos["name"],
        "price": price, "quantity": qty,
        "value": value, "profit": round(profit, 2),
        "profit_pct": round(profit_pct, 2),
        "cash_remaining": portfolio["cash"]
    }

def _record_trade(action, symbol, name, price, qty, value, profit=None):
    journal = _load_json(JOURNAL_FILE, {"trades": [], "diaries": []})
    trade = {
        "time": datetime.now().isoformat(),
        "action": action, "symbol": symbol, "name": name,
        "price": price, "quantity": qty, "value": value,
    }
    if profit is not None:
        trade["profit"] = profit
    journal["trades"].append(trade)
    _save_json(JOURNAL_FILE, journal)

def get_portfolio():
    """获取持仓"""
    portfolio = _load_json(PORTFOLIO_FILE, {"cash": 100000, "positions": [], "initial_capital": 100000})
    total_value = portfolio["cash"]
    for p in portfolio["positions"]:
        total_value += p["quantity"] * p["current_price"]
    
    profit = total_value - portfolio["initial_capital"]
    profit_pct = profit / portfolio["initial_capital"] * 100
    
    return {
        "cash": portfolio["cash"],
        "positions": portfolio["positions"],
        "total_value": round(total_value, 2),
        "total_profit": round(profit, 2),
        "total_profit_pct": round(profit_pct, 2),
        "position_count": len(portfolio["positions"])
    }

def write_diary(content):
    """写交易日记"""
    journal = _load_json(JOURNAL_FILE, {"trades": [], "diaries": []})
    journal["diaries"].append({
        "time": datetime.now().isoformat(),
        "content": content
    })
    _save_json(JOURNAL_FILE, journal)
    return {"status": "ok", "entry_count": len(journal["diaries"])}

def get_journal():
    """获取交易日记"""
    return _load_json(JOURNAL_FILE, {"trades": [], "diaries": []})

if __name__ == "__main__":
    print(init_account())
    print(get_portfolio())
