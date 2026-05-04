"""AI Trading System - 策略引擎
技术指标计算、策略定义、回测、参数优化
"""
import pandas as pd
import numpy as np
import json, os, random

STRATEGIES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "strategies")

def calculate_indicators(df):
    """计算常用技术指标"""
    close = df["close"].values
    high = df["high"].values
    low = df["low"].values
    volume = df["volume"].values
    
    # SMA
    df["sma5"] = pd.Series(close).rolling(5).mean().values
    df["sma10"] = pd.Series(close).rolling(10).mean().values
    df["sma20"] = pd.Series(close).rolling(20).mean().values
    df["sma60"] = pd.Series(close).rolling(60).mean().values
    
    # EMA
    df["ema12"] = pd.Series(close).ewm(span=12).mean().values
    df["ema26"] = pd.Series(close).ewm(span=26).mean().values
    
    # MACD
    df["macd"] = df["ema12"] - df["ema26"]
    df["macd_signal"] = pd.Series(df["macd"].values).ewm(span=9).mean().values
    
    # RSI
    delta = pd.Series(close).diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["rsi14"] = (100 - (100 / (1 + rs))).values
    
    # Bollinger Bands
    sma20 = pd.Series(close).rolling(20).mean()
    std20 = pd.Series(close).rolling(20).std()
    df["bb_upper"] = (sma20 + 2 * std20).values
    df["bb_lower"] = (sma20 - 2 * std20).values
    df["bb_mid"] = sma20.values
    
    # Volume indicators
    df["volume_sma5"] = pd.Series(volume).rolling(5).mean().values
    df["volume_ratio"] = (volume / df["volume_sma5"]).values
    
    return df

class MaCrossStrategy:
    """双均线交叉策略"""
    def __init__(self, fast=5, slow=20):
        self.fast = fast
        self.slow = slow
        self.name = f"MA交叉({fast},{slow})"
    
    def generate_signals(self, df):
        df = df.copy()
        df["sma_fast"] = pd.Series(df["close"]).rolling(self.fast).mean().values
        df["sma_slow"] = pd.Series(df["close"]).rolling(self.slow).mean().values
        
        # 金叉买入，死叉卖出
        df["signal"] = 0
        df.loc[df["sma_fast"] > df["sma_slow"], "signal"] = 1
        df.loc[df["sma_fast"] <= df["sma_slow"], "signal"] = -1
        
        # 交易信号：1买入，-1卖出
        df["trade"] = df["signal"].diff().fillna(0)
        return df

class RSIStrategy:
    """RSI超买超卖策略"""
    def __init__(self, oversold=30, overbought=70):
        self.oversold = oversold
        self.overbought = overbought
        self.name = f"RSI策略({oversold},{overbought})"
    
    def generate_signals(self, df):
        df = df.copy()
        df = calculate_indicators(df)
        df["signal"] = 0
        df.loc[df["rsi14"] < self.oversold, "signal"] = 1  # 超卖买入
        df.loc[df["rsi14"] > self.overbought, "signal"] = -1  # 超买卖出
        df["trade"] = df["signal"].diff().fillna(0)
        return df

class BollingerStrategy:
    """布林带策略"""
    def __init__(self, period=20, std_dev=2):
        self.period = period
        self.std_dev = std_dev
        self.name = f"布林带({period},{std_dev})"
    
    def generate_signals(self, df):
        df = df.copy()
        df = calculate_indicators(df)
        df["signal"] = 0
        df.loc[df["close"] < df["bb_lower"], "signal"] = 1   # 下轨买入
        df.loc[df["close"] > df["bb_upper"], "signal"] = -1  # 上轨卖出
        df["trade"] = df["signal"].diff().fillna(0)
        return df

def backtest(df, strategy, initial_capital=100000):
    """回测策略"""
    result = strategy.generate_signals(df)
    capital = initial_capital
    position = 0
    trades = []
    equity_curve = []
    
    for i in range(len(result)):
        row = result.iloc[i]
        price = row["close"]
        
        if row["trade"] == 1 and capital > 0:  # 买入
            position = capital / price
            capital = 0
            trades.append({"date": str(row.name), "action": "BUY", "price": float(price), 
                          "value": float(position * price)})
        elif row["trade"] == -1 and position > 0:  # 卖出
            capital = position * price
            trades.append({"date": str(row.name), "action": "SELL", "price": float(price),
                          "value": float(capital)})
            position = 0
        
        total_value = capital + position * price
        equity_curve.append(float(total_value))
    
    # 最终资产
    final_value = capital + position * result.iloc[-1]["close"]
    total_return = (final_value - initial_capital) / initial_capital * 100
    
    # 胜率
    wins = sum(1 for t in trades if t["action"] == "SELL" and t["value"] > initial_capital / len(trades) if trades)
    win_rate = wins / max(len([t for t in trades if t["action"] == "SELL"]), 1) * 100
    
    return {
        "strategy": strategy.name,
        "initial_capital": initial_capital,
        "final_value": float(final_value),
        "total_return_pct": round(total_return, 2),
        "total_trades": len(trades),
        "win_rate": round(win_rate, 1),
        "trades": trades[-10:],
        "equity_curve": equity_curve[::max(1, len(equity_curve)//20)]
    }

def grid_search_optimize(df, strategy_class, param_grid):
    """网格搜索优化策略参数"""
    best_result = None
    best_params = None
    best_return = -float("inf")
    results = []
    
    for params in param_grid:
        strategy = strategy_class(**params)
        result = backtest(df, strategy)
        results.append({"params": params, **result})
        
        if result["total_return_pct"] > best_return:
            best_return = result["total_return_pct"]
            best_result = result
            best_params = params
    
    return {
        "best_params": best_params,
        "best_return": best_return,
        "all_results": sorted(results, key=lambda x: x["total_return_pct"], reverse=True)[:5]
    }

if __name__ == "__main__":
    # 简单测试
    print("策略引擎加载成功")
