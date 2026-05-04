@echo off
set PYTHONIOENCODING=utf-8
set BASE_DIR=%~dp0..
cd /d "%BASE_DIR%"
python -c "import os, sys; base=os.getcwd(); sys.path.insert(0, base); from core.trading_agent import TradingAgent; from core.dashboard import generate_dashboard; a=TradingAgent(); a.run_cycle(); open(os.path.join(base, 'data', 'dashboard.html'),'w',encoding='utf-8').write(generate_dashboard())"
