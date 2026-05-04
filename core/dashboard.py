"""AI Trading System - 交易看板
生成 HTML 页面展示持仓、收益、交易记录
"""
import sys, os, json
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from core.data_feed import get_market_overview, get_realtime_quote, get_top_gainers
from core.paper_trader import get_portfolio, get_journal
from core.strategy_engine import calculate_indicators

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def generate_dashboard():
    """生成交易看板 HTML"""
    portfolio = get_portfolio()
    journal = get_journal()
    market = get_market_overview()
    
    style = """
    <style>
        * { margin:0; padding:0; box-sizing:border-box; font-family:'Segoe UI',sans-serif; }
        body { background:#0d1117; color:#c9d1d9; padding:20px; }
        .container { max-width:900px; margin:0 auto; }
        h1 { color:#58a6ff; font-size:24px; margin-bottom:5px; }
        .subtitle { color:#8b949e; font-size:13px; margin-bottom:20px; }
        .grid { display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px; margin-bottom:20px; }
        .card { background:#161b22; border:1px solid #30363d; border-radius:8px; padding:16px; }
        .card h3 { font-size:13px; color:#8b949e; margin-bottom:8px; }
        .card .value { font-size:28px; font-weight:bold; }
        .card .value.green { color:#3fb950; }
        .card .value.red { color:#f85149; }
        .card .value.white { color:#c9d1d9; }
        table { width:100%; border-collapse:collapse; margin-top:10px; }
        th { text-align:left; padding:8px 12px; border-bottom:1px solid #30363d; color:#8b949e; font-size:12px; }
        td { padding:8px 12px; border-bottom:1px solid #21262d; font-size:13px; }
        .profit { color:#3fb950 } .loss { color:#f85149 }
        .section-title { font-size:16px; color:#58a6ff; margin:20px 0 10px; }
        .market-grid { display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px; margin-bottom:15px; }
        .market-item { background:#161b22; border:1px solid #30363d; border-radius:6px; padding:10px; text-align:center; }
        .market-item .idx { font-size:20px; font-weight:bold; }
        .market-item .label { font-size:11px; color:#8b949e; }
        .badge { display:inline-block; padding:2px 8px; border-radius:12px; font-size:11px; }
        .badge.buy { background:#0d4429; color:#3fb950; }
        .badge.sell { background:#441010; color:#f85149; }
        .status-bar { background:#161b22; border:1px solid #30363d; border-radius:8px; padding:12px; margin-bottom:15px; }
        .status-bar span { color:#58a6ff; }
    </style>
    """
    
    # 资产卡片
    pnl_color = "green" if portfolio["total_profit"] >= 0 else "red"
    pnl_icon = "📈" if portfolio["total_profit"] >= 0 else "📉"
    
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">{style}</head><body>
<div class="container">
<h1>🤖 AI 交易系统看板</h1>
<p class="subtitle">更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | v1.0</p>

<div class="status-bar">
🟢 系统运行中 | 策略: 双均线交叉 | 循环间隔: 10分钟
</div>

<div class="grid">
    <div class="card">
        <h3>💰 总资产</h3>
        <div class="value white">¥{portfolio['total_value']:,.2f}</div>
    </div>
    <div class="card">
        <h3>{pnl_icon} 总盈亏</h3>
        <div class="value {pnl_color}">{portfolio['total_profit_pct']:+.2f}%</div>
    </div>
    <div class="card">
        <h3>💵 可用现金</h3>
        <div class="value white">¥{portfolio['cash']:,.2f}</div>
    </div>
</div>

<h3 class="section-title">📊 大盘指数</h3>
<div class="market-grid">
"""
    for name, val in market.items():
        html += f'<div class="market-item"><div class="idx">{val}</div><div class="label">{name}</div></div>'
    
    # 持仓
    html += '</div><h3 class="section-title">📋 持仓</h3>'
    if portfolio["positions"]:
        html += '<table><tr><th>股票</th><th>数量</th><th>买入价</th><th>市值</th></tr>'
        for p in portfolio["positions"]:
            mkt_val = p["quantity"] * p["current_price"]
            html += f'<tr><td>{p["name"]} ({p["symbol"]})</td><td>{p["quantity"]}</td><td>{p["buy_price"]}</td><td>{mkt_val:.2f}</td></tr>'
        html += '</table>'
    else:
        html += '<p style="color:#8b949e;margin-top:10px;">暂无持仓</p>'
    
    # 最近交易
    html += '<h3 class="section-title">📝 最近交易</h3>'
    trades = journal.get("trades", [])[-10:]
    if trades:
        html += '<table><tr><th>时间</th><th>操作</th><th>股票</th><th>价格</th><th>数量</th><th>盈亏</th></tr>'
        for t in reversed(trades):
            action = t["action"]
            badge_class = "buy" if action == "BUY" else "sell"
            profit_str = ""
            if t.get("profit") is not None:
                pf = t["profit"]
                pfc = "profit" if pf >= 0 else "loss"
                profit_str = f'<span class="{pfc}">¥{pf:+.2f}</span>'
            html += f'<tr><td style="font-size:11px;color:#8b949e;">{t["time"][:16]}</td><td><span class="badge {badge_class}">{action}</span></td><td>{t.get("name", t["symbol"])}</td><td>{t["price"]}</td><td>{t["quantity"]}</td><td>{profit_str}</td></tr>'
        html += '</table>'
    else:
        html += '<p style="color:#8b949e;margin-top:10px;">暂无交易记录</p>'
    
    # 交易日记摘要
    html += '<h3 class="section-title">📔 交易日记</h3>'
    diaries = journal.get("diaries", [])[-5:]
    if diaries:
        for d in reversed(diaries):
            html += f'<p style="color:#8b949e;font-size:12px;margin:4px 0;">[{d["time"][:16]}] {d["content"][:80]}</p>'
    else:
        html += '<p style="color:#8b949e;">暂无日记</p>'
    
    html += '</div></body></html>'
    return html

if __name__ == "__main__":
    html = generate_dashboard()
    path = os.path.join(DATA_DIR, "dashboard.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ 看板已生成: {path}")
