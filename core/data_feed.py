"""AI Trading System - 数据获取模块
用 akshare 获取 A 股实时行情和历史数据
"""
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import json, os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def get_realtime_quote(symbol):
    """获取个股实时行情"""
    try:
        df = ak.stock_zh_a_spot_em()
        code = symbol.split(".")[0]
        row = df[df["代码"] == code]
        if row.empty:
            return {"error": f"未找到股票 {symbol}"}
        r = row.iloc[0]
        return {
            "代码": r["代码"], "名称": r["名称"],
            "最新价": float(r["最新价"]), "涨跌幅": float(r["涨跌幅"]),
            "涨跌额": float(r["涨跌额"]), "成交量": float(r["成交量"]),
            "成交额": float(r["成交额"]), "换手率": float(r["换手率"]),
            "市盈率": float(r.get("市盈率-动态", 0)),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

def get_market_overview():
    """获取大盘概况"""
    try:
        sh = ak.stock_zh_index_daily(symbol="sh000001")
        sz = ak.stock_zh_index_daily(symbol="sz399001")
        cy = ak.stock_zh_index_daily(symbol="sz399006")
        last_sh = sh.iloc[-1] if not sh.empty else None
        last_sz = sz.iloc[-1] if not sz.empty else None
        last_cy = cy.iloc[-1] if not cy.empty else None
        result = {}
        if last_sh is not None:
            result["上证指数"] = f"{last_sh['close']:.2f}"
        if last_sz is not None:
            result["深证成指"] = f"{last_sz['close']:.2f}"
        if last_cy is not None:
            result["创业板指"] = f"{last_cy['close']:.2f}"
        return result
    except Exception as e:
        return {"error": str(e)}

def get_kline(symbol, period="daily", count=100):
    """获取K线数据"""
    try:
        code = symbol.split(".")[0]
        df = ak.stock_zh_a_hist(symbol=code, period=period, adjust="qfq")
        df = df.tail(count)
        records = []
        for _, r in df.iterrows():
            records.append({
                "date": str(r["日期"]),
                "open": float(r["开盘"]),
                "high": float(r["最高"]),
                "low": float(r["最低"]),
                "close": float(r["收盘"]),
                "volume": float(r["成交量"]),
            })
        return {"symbol": symbol, "period": period, "count": len(records), "data": records}
    except Exception as e:
        return {"error": str(e)}

def get_top_gainers(top_n=20):
    """获取涨幅榜"""
    try:
        df = ak.stock_zh_a_spot_em()
        df = df.sort_values("涨跌幅", ascending=False).head(top_n)
        return df[["代码", "名称", "最新价", "涨跌幅"]].to_dict("records")
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # 测试
    print("大盘概况:", get_market_overview())
    print("贵州茅台:", get_realtime_quote("600519.SH"))
