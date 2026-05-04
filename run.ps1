# AI Trading System - OpenClaw Automated Trading System
# Architecture: Agent-driven + Skill composition + Self-iteration

param(
    [string]$Action = "help",
    [string]$Symbol = "",
    [int]$Quantity = 100
)

$env:PYTHONIOENCODING = "utf-8"
$python = "python"
$BaseDir = $PSScriptRoot

if ($env:AI_TRADING_PROXY) {
    $env:HTTPS_PROXY = $env:AI_TRADING_PROXY
    $env:HTTP_PROXY = $env:AI_TRADING_PROXY
}

function Invoke-Py {
    param([string]$Code)
    & $python -c $Code 2>&1
}

switch ($Action.ToLower()) {
    "init" {
        Write-Host "`n[Init] Initializing paper account..." -ForegroundColor Cyan
        Invoke-Py "import sys; sys.path.insert(0, r'$BaseDir'); from core.paper_trader import init_account; print(init_account(100000))"
    }
    "market" {
        Write-Host "`n[Market] Fetching market overview..." -ForegroundColor Cyan
        Invoke-Py "import sys; sys.path.insert(0, r'$BaseDir'); from core.data_feed import get_market_overview; import json; print(json.dumps(get_market_overview(), ensure_ascii=False))"
    }
    "quote" {
        Write-Host "`n[Quote] Querying $Symbol ..." -ForegroundColor Cyan
        Invoke-Py "import sys; sys.path.insert(0, r'$BaseDir'); from core.data_feed import get_realtime_quote; import json; print(json.dumps(get_realtime_quote('$Symbol'), ensure_ascii=False))"
    }
    "buy" {
        Write-Host "`n[Buy] Buying $Quantity x $Symbol ..." -ForegroundColor Green
        Invoke-Py "import sys; sys.path.insert(0, r'$BaseDir'); from core.data_feed import get_realtime_quote; from core.paper_trader import buy; q=get_realtime_quote('$Symbol'); p=q['最新价']; print(buy('$Symbol', q.get('名称',''), p, $Quantity))"
    }
    "sell" {
        Write-Host "`n[Sell] Selling $Symbol ..." -ForegroundColor Yellow
        Invoke-Py "import sys; sys.path.insert(0, r'$BaseDir'); from core.paper_trader import sell; from core.data_feed import get_realtime_quote; q=get_realtime_quote('$Symbol'); p=q['最新价']; print(sell('$Symbol', p, $Quantity))"
    }
    "portfolio" {
        Write-Host "`n[Portfolio] Checking holdings..." -ForegroundColor Cyan
        Invoke-Py "import sys; sys.path.insert(0, r'$BaseDir'); from core.paper_trader import get_portfolio; import json; print(json.dumps(get_portfolio(), ensure_ascii=False))"
    }
    "journal" {
        Write-Host "`n[Journal] Trading diary..." -ForegroundColor Cyan
        Invoke-Py "import sys; sys.path.insert(0, r'$BaseDir'); from core.paper_trader import get_journal; import json; print(json.dumps(get_journal(), ensure_ascii=False, indent=2))"
    }
    "run" {
        Write-Host "`n[Cycle] Running trading cycle..." -ForegroundColor Cyan
        Invoke-Py "import sys; sys.path.insert(0, r'$BaseDir'); from core.trading_agent import TradingAgent; TradingAgent().run_cycle()"
    }
    "evolve" {
        Write-Host "`n[Evolve] Strategy evolution analysis..." -ForegroundColor Magenta
        Invoke-Py "import sys; sys.path.insert(0, r'$BaseDir'); from core.trading_agent import TradingAgent; TradingAgent().analyze_and_evolve()"
    }
    "backtest" {
        Write-Host "`n[Backtest] Backtesting $Symbol ..." -ForegroundColor Yellow
        Invoke-Py @"
import sys, json; sys.path.insert(0, r'$BaseDir')
from core.strategy_engine import MaCrossStrategy, RSIStrategy, BollingerStrategy, backtest, grid_search_optimize
from core.data_feed import get_kline
import pandas as pd
df = pd.DataFrame(get_kline('$Symbol', count=120)['data'])
r1 = backtest(df, MaCrossStrategy(5, 20))
r2 = backtest(df, RSIStrategy(30, 70))
r3 = backtest(df, BollingerStrategy())
print(f"MA(5,20): return={r1['total_return_pct']}% win_rate={r1['win_rate']}% trades={r1['total_trades']}")
print(f"RSI(30,70): return={r2['total_return_pct']}% win_rate={r2['win_rate']}% trades={r2['total_trades']}")
print(f"Bollinger: return={r3['total_return_pct']}% win_rate={r3['win_rate']}% trades={r3['total_trades']}")
"@
    }
    "dashboard" {
        Write-Host "[Dashboard] Generating..." -ForegroundColor Cyan
        Invoke-Py "import sys; sys.path.insert(0, r'$BaseDir'); from core.dashboard import generate_dashboard; open(r'$BaseDir\data\dashboard.html','w',encoding='utf-8').write(generate_dashboard()); print('Dashboard updated')"
        Start-Process "$BaseDir\data\dashboard.html"
    }
    default {
        Write-Host @"
=============================
 AI Trading System Commands
=============================
  .\run.ps1 init         Init account (100k virtual)
  .\run.ps1 market       Market overview (indices)
  .\run.ps1 quote -Symbol 600519.SH   Stock quote
  .\run.ps1 buy -Symbol 600519.SH -Quantity 100   Buy
  .\run.ps1 sell -Symbol 600519.SH -Quantity 100  Sell
  .\run.ps1 portfolio    View portfolio
  .\run.ps1 journal      View trading journal
  .\run.ps1 run          Run one trading cycle
  .\run.ps1 backtest -Symbol 600519.SH   Backtest
  .\run.ps1 evolve       Strategy evolution
  .\run.ps1 dashboard    Open dashboard HTML
=============================
"@ -ForegroundColor White
    }
}
