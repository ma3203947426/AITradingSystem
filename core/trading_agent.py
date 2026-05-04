"""AI Trading System - Trading Agent
Orchestrates data, strategies, execution, journaling, and self-evolution.
"""
import sys, os, json, time
from datetime import datetime

# Windows GBK console compatibility
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from core.data_feed import get_realtime_quote, get_kline, get_market_overview, get_top_gainers
from core.strategy_engine import MaCrossStrategy, RSIStrategy, BollingerStrategy, backtest, grid_search_optimize, calculate_indicators
from core.paper_trader import *

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

class TradingAgent:
    def __init__(self, config=None):
        self.config = config or {}
        self.current_strategy = None
        self.version = 1
        self.status = "stopped"
        print(f"[Agent] v{self.version} initialized")
    
    def run_cycle(self):
        """Execute one complete trading cycle"""
        print(f"\n[Cycle] [{datetime.now().strftime('%H:%M:%S')}] Start")
        self.status = "running"
        
        # 1. Market overview
        print("[Data] Fetching market...")
        market = get_market_overview()
        print(f"   Index: {market}")
        
        # 2. Check portfolio
        print("[Portfolio] Checking...")
        portfolio = get_portfolio()
        print(f"   Value: {portfolio['total_value']} | Cash: {portfolio['cash']} | PnL: {portfolio['total_profit_pct']}%")
        
        # 3. Write journal
        diary_entry = (f"Cycle v{self.version} @ {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
                       f"Value: {portfolio['total_value']} | PnL: {portfolio['total_profit_pct']}%")
        write_diary(diary_entry)
        
        # 4. Analyze recent trades
        journal = get_journal()
        recent_trades = journal.get("trades", [])[-5:]
        if recent_trades:
            losing = [t for t in recent_trades if t.get("profit", 1) is not None and t.get("profit", 1) < 0]
            if len(losing) >= 3:
                print(f"[Warn] {len(losing)}/{len(recent_trades)} recent losses, consider pausing")
        
        self.status = "idle"
        print(f"[Done] Cycle complete\n")
        return portfolio
    
    def upgrade_strategy(self, analysis="auto"):
        """Upgrade strategy version"""
        self.version += 1
        diary = {
            "version": self.version,
            "upgrade_time": datetime.now().isoformat(),
            "analysis": analysis,
        }
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(os.path.join(DATA_DIR, f"strategy_v{self.version}.json"), "w", encoding="utf-8") as f:
            json.dump(diary, f, ensure_ascii=False)
        write_diary(f"Strategy upgraded to v{self.version}: {analysis[:50]}...")
        print(f"[Evolve] Strategy v{self.version} deployed")
        return {"version": self.version, "status": "upgraded"}
    
    def analyze_and_evolve(self):
        """Analyze trading data and evolve strategy"""
        print(f"\n[Analysis] [{datetime.now().strftime('%H:%M:%S')}] Analyzing...")
        journal = get_journal()
        trades = journal.get("trades", [])
        
        if not trades:
            print("   No trades yet, skip")
            return
        
        winning_trades = [t for t in trades if t.get("profit", 0) is not None and t.get("profit", 0) > 0]
        losing_trades = [t for t in trades if t.get("profit", 0) is not None and t.get("profit", 0) <= 0]
        
        total = len(trades)
        win_rate = len(winning_trades) / total * 100 if total > 0 else 0
        total_profit = sum(t.get("profit", 0) for t in trades if t.get("profit") is not None)
        
        analysis = (
            f"Stats: {total} trades, win rate {win_rate:.0f}%, "
            f"total PnL {total_profit:.2f}\n"
        )
        
        if win_rate < 40:
            analysis += "Low win rate, adjust params or change strategy"
            self.upgrade_strategy(analysis)
        elif total_profit < 0:
            analysis += "Negative PnL, reduce position or add stop-loss"
            self.upgrade_strategy(analysis)
        else:
            analysis += "Stable, continue monitoring"
        
        print(f"   {analysis}")
        return analysis

def main():
    import argparse
    parser = argparse.ArgumentParser(description="AI Trading System")
    parser.add_argument("--init", action="store_true", help="Init account")
    parser.add_argument("--run", action="store_true", help="Run one cycle")
    parser.add_argument("--portfolio", action="store_true", help="View portfolio")
    parser.add_argument("--journal", action="store_true", help="View journal")
    parser.add_argument("--evolve", action="store_true", help="Strategy evolution")
    parser.add_argument("--backtest", type=str, help="Backtest a symbol")
    args = parser.parse_args()
    
    agent = TradingAgent()
    
    if args.init:
        print(init_account())
    elif args.run:
        agent.run_cycle()
    elif args.portfolio:
        print(json.dumps(get_portfolio(), ensure_ascii=False, indent=2))
    elif args.journal:
        print(json.dumps(get_journal(), ensure_ascii=False, indent=2))
    elif args.evolve:
        agent.analyze_and_evolve()

if __name__ == "__main__":
    agent = TradingAgent()
    agent.run_cycle()
