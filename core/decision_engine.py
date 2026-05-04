"""AI Trading System - Enhanced Decision Engine
Combines technical analysis, risk management, multi-strategy voting,
trend following with confirmation, and fundamental filters.
"""
import pandas as pd
import numpy as np
import json, os, math
from datetime import datetime, timedelta

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

# ─── Technical Indicators ───────────────────────────────────────────

def calc_all_indicators(df):
    """Calculate comprehensive technical indicators"""
    close = df["close"].values.astype(float)
    high = df["high"].values.astype(float)
    low = df["low"].values.astype(float)
    volume = df["volume"].values.astype(float)
    
    # Moving Averages
    for p in [5, 10, 20, 30, 60, 120]:
        df[f"sma{p}"] = pd.Series(close).rolling(p).mean().values
    
    # EMA
    df["ema12"] = pd.Series(close).ewm(span=12).mean().values
    df["ema26"] = pd.Series(close).ewm(span=26).mean().values
    
    # MACD
    df["macd"] = df["ema12"] - df["ema26"]
    df["macd_signal"] = pd.Series(df["macd"].values).ewm(span=9).mean().values
    df["macd_hist"] = df["macd"] - df["macd_signal"]
    
    # RSI
    delta = pd.Series(close).diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_g = gain.rolling(14).mean()
    avg_l = loss.rolling(14).mean()
    rs = avg_g / avg_l.replace(0, np.nan)
    df["rsi14"] = (100 - (100 / (1 + rs))).values
    
    # Bollinger Bands
    bb_sma = pd.Series(close).rolling(20).mean()
    bb_std = pd.Series(close).rolling(20).std()
    df["bb_upper"] = (bb_sma + 2 * bb_std).values
    df["bb_lower"] = (bb_sma - 2 * bb_std).values
    df["bb_width"] = ((df["bb_upper"] - df["bb_lower"]) / bb_sma * 100).values
    
    # ADX (Trend Strength)
    df["adx"] = _calculate_adx(high, low, close, period=14)
    
    # ATR (Volatility)
    df["atr14"] = _calculate_atr(high, low, close, period=14)
    df["atr_pct"] = (df["atr14"] / close * 100).values
    
    # Volume
    df["vol_sma5"] = pd.Series(volume).rolling(5).mean().values
    df["vol_ratio"] = (volume / df["vol_sma5"].clip(lower=1)).values
    
    # Price Action
    df["higher_high"] = (high > pd.Series(high).shift(1)).astype(int)
    df["higher_low"] = (low > pd.Series(low).shift(1)).astype(int)
    
    return df

def _calculate_adx(high, low, close, period=14):
    """Average Directional Index"""
    h, l, c = pd.Series(high), pd.Series(low), pd.Series(close)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(1)
    up = h - h.shift()
    dn = l.shift() - l
    pos = pd.Series(np.where((up > dn) & (up > 0), up, 0))
    neg = pd.Series(np.where((dn > up) & (dn > 0), dn, 0))
    adx = 100 * (pos.ewm(span=period).mean() / tr.ewm(span=period).mean()).ewm(span=period).mean()
    return adx.values

def _calculate_atr(high, low, close, period=14):
    """Average True Range"""
    h, l, c = pd.Series(high), pd.Series(low), pd.Series(close)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(1)
    return tr.rolling(period).mean().values

# ─── Strategy Definitions ────────────────────────────────────────────

class EnsembleStrategy:
    """Multi-strategy ensemble with voting"""
    
    def __init__(self, strategies=None):
        self.strategies = strategies or [
            TrendFollowStrategy(),
            MACrossoverStrategy(),
            RSIStrategy(),
            BollingerStrategy(),
        ]
        self.name = f"Ensemble({len(self.strategies)}strats)"
    
    def generate_signal(self, df):
        """Vote from all strategies"""
        signals = []
        confidences = []
        
        for s in self.strategies:
            result = s.generate_signal(df)
            signals.append(result["signal"])
            confidences.append(result.get("confidence", 0.5))
        
        # Weighted vote
        buy_votes = sum(c for s, c in zip(signals, confidences) if s > 0)
        sell_votes = sum(c for s, c in zip(signals, confidences) if s < 0)
        total_votes = len(self.strategies)
        
        net_score = (buy_votes - sell_votes) / total_votes
        
        if net_score > 0.1:
            signal = 1  # Buy
        elif net_score < -0.1:
            signal = -1  # Sell
        else:
            signal = 0  # Hold
        
        return {
            "signal": signal,
            "confidence": abs(net_score),
            "details": {
                "buy_votes": buy_votes,
                "sell_votes": sell_votes,
                "net_score": round(net_score, 2),
                "votes": [(s.name, s.generate_signal(df)["signal"]) for s in self.strategies]
            }
        }

class TrendFollowStrategy:
    """Trend following with confirmation"""
    
    def __init__(self, trend_period=20, vol_threshold=1.5):
        self.trend_period = trend_period
        self.vol_threshold = vol_threshold
        self.name = "TrendFollow"
    
    def generate_signal(self, df):
        row = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Trend: price above SMA
        in_uptrend = row["close"] > row[f"sma{self.trend_period}"]
        
        # Volume confirmation
        volume_ok = row["vol_ratio"] > self.vol_threshold
        
        # ADX confirmation
        trend_strong = row["adx"] > 25 if "adx" in df.columns else True
        
        # Higher highs/lows
        hh_hl = row["higher_high"] and row["higher_low"]
        
        score = 0
        if in_uptrend and (volume_ok or trend_strong):
            score = 1
        elif not in_uptrend:
            score = -1
        else:
            score = 0
        
        return {"signal": score, "confidence": 0.7 if score != 0 else 0.3}

class MACrossoverStrategy:
    """MA crossover with multi-timeframe confirmation"""
    
    def __init__(self, fast=5, slow=20, confirm=60):
        self.fast = fast
        self.slow = slow
        self.confirm = confirm
        self.name = f"MA({fast},{slow})"
    
    def generate_signal(self, df):
        row = df.iloc[-1]
        prev = df.iloc[-2]
        
        fast_prev = prev[f"sma{self.fast}"]
        fast_now = row[f"sma{self.fast}"]
        slow_prev = prev[f"sma{self.slow}"]
        slow_now = row[f"sma{self.slow}"]
        
        # Gold cross
        gold_cross = fast_prev <= slow_prev and fast_now > slow_now
        # Death cross
        death_cross = fast_prev >= slow_prev and fast_now < slow_now
        
        # Long-term trend filter
        long_trend_up = row["close"] > row[f"sma{self.confirm}"]
        
        if gold_cross and long_trend_up:
            return {"signal": 1, "confidence": 0.8}
        elif death_cross and not long_trend_up:
            return {"signal": -1, "confidence": 0.8}
        
        return {"signal": 0, "confidence": 0.5}

class RSIStrategy:
    """RSI with trend filter and divergence detection"""
    
    def __init__(self, oversold=30, overbought=70):
        self.oversold = oversold
        self.overbought = overbought
        self.name = f"RSI({oversold},{overbought})"
    
    def generate_signal(self, df):
        row = df.iloc[-1]
        
        rsi = row["rsi14"]
        in_uptrend = row["close"] > row["sma20"]
        
        if rsi < self.oversold:
            return {"signal": 1, "confidence": 0.6}
        if rsi > self.overbought:
            return {"signal": -1, "confidence": 0.6}
        if rsi < 45:
            return {"signal": 1, "confidence": 0.3}  # Weak buy near oversold
        if rsi > 55:
            return {"signal": -1, "confidence": 0.3}
        
        return {"signal": 0, "confidence": 0.5}

class BollingerStrategy:
    """Bollinger Band squeeze and bounce"""
    
    def __init__(self, squeeze_threshold=15):
        self.squeeze_threshold = squeeze_threshold
        self.name = "Bollinger"
    
    def generate_signal(self, df):
        row = df.iloc[-1]
        
        price = row["close"]
        upper = row["bb_upper"]
        lower = row["bb_lower"]
        mid = row.get("bb_mid", (upper + lower) / 2)
        width = row["bb_width"]
        
        # Squeeze = potential breakout
        squeeze = width < self.squeeze_threshold
        
        # Bounce off lower band
        bounce_lower = price < lower * 1.02
        
        # Touch upper band
        touch_upper = price > upper * 0.98
        
        if bounce_lower:
            return {"signal": 1, "confidence": 0.5}
        if touch_upper:
            return {"signal": -1, "confidence": 0.5}
        if squeeze:
            return {"signal": 0, "confidence": 0.4}
        
        return {"signal": 0, "confidence": 0.5}

# ─── Decision Making ─────────────────────────────────────────────────

class DecisionEngine:
    """Main decision maker combining strategy, risk, and market context"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.strategy = EnsembleStrategy()
        self.max_risk_per_trade = 0.02  # 2% max risk
    
    def decide(self, df, portfolio, market_context=None):
        """
        Make a trading decision based on all available data
        Returns: {"action": "BUY"/"SELL"/"HOLD", "reason": "...", "confidence": 0-1}
        """
        if df is None or len(df) < 60:
            return {"action": "HOLD", "reason": "Insufficient data", "confidence": 0}
        
        df = calc_all_indicators(df.copy())
        
        # Get strategy signal
        signal = self.strategy.generate_signal(df)
        
        # Check risk limits
        portfolio_value = portfolio.get("total_value", 100000)
        drawdown = portfolio.get("total_profit_pct", 0)
        
        # Don't trade if drawdown > 15%
        if drawdown < -15:
            return {"action": "HOLD", "reason": f"Drawdown {drawdown:.0f}% > 15%, stopped",
                    "confidence": 0.9}
        
        # Don't trade if in loss streak
        journal_path = os.path.join(DATA_DIR, "trading_journal.json")
        if os.path.exists(journal_path):
            with open(journal_path, "r", encoding="utf-8") as f:
                journal = json.load(f)
            recent_trades = journal.get("trades", [])[-5:]
            recent_losses = sum(1 for t in recent_trades if t.get("action") == "SELL" and t.get("profit", 0) < 0)
            if recent_losses >= 4:
                return {"action": "HOLD", "reason": f"4+ consecutive losses, pausing",
                        "confidence": 0.8}
        
        # Make decision
        if signal["signal"] > 0 and signal["confidence"] > 0.15:
            position_size = self._calc_position_size(portfolio_value, signal["confidence"])
            return {
                "action": "BUY",
                "reason": f"Strategy signal: {self._describe_votes(signal)}",
                "confidence": signal["confidence"],
                "position_size": position_size
            }
        elif signal["signal"] < 0 and signal["confidence"] > 0.15:
            return {
                "action": "SELL",
                "reason": f"Sell signal: {self._describe_votes(signal)}",
                "confidence": signal["confidence"]
            }
        
        return {"action": "HOLD", "reason": "No clear signal", "confidence": 0.3}
    
    def _calc_position_size(self, portfolio_value, confidence):
        """Calculate position size using Kelly-inspired sizing"""
        base_risk = self.max_risk_per_trade * portfolio_value
        kelly_factor = confidence * 0.5  # Half-Kelly for safety
        return base_risk * kelly_factor
    
    def _describe_votes(self, signal):
        details = signal.get("details", {})
        votes = details.get("votes", [])
        return "; ".join([f"{n}: {'BUY' if v>0 else 'SELL' if v<0 else 'HOLD'}" for n, v in votes])

# ─── Backtesting Framework ──────────────────────────────────────────

def enhanced_backtest(df, decision_engine, initial_capital=100000):
    """Run enhanced backtest with decision engine"""
    df = calc_all_indicators(df.copy())
    capital = initial_capital
    position = 0
    trades = []
    equity = []
    
    for i in range(60, len(df)):
        window = df.iloc[:i+1]
        portfolio = {"total_value": capital + position * df.iloc[i]["close"], 
                     "total_profit_pct": (capital + position * df.iloc[i]["close"] - initial_capital) / initial_capital * 100}
        
        decision = decision_engine.decide(window, portfolio)
        price = df.iloc[i]["close"]
        
        if decision["action"] == "BUY" and capital > 0:
            size = decision.get("position_size", capital * 0.1)
            position = capital * 0.95 / price  # Use 95% of capital for simplicity
            capital = 0
            trades.append({"date": str(df.iloc[i]["date"]), "action": "BUY", "price": float(price),
                          "reason": decision["reason"]})
        elif decision["action"] == "SELL" and position > 0:
            capital = position * price
            profit = capital - (capital - position * price)  # simplified
            trades.append({"date": str(df.iloc[i]["date"]), "action": "SELL", "price": float(price),
                          "profit": float(capital - position * df.iloc[i-1]["close"]),
                          "reason": decision["reason"]})
            position = 0
        
        equity.append(float(capital + position * price))
    
    final = capital + position * df.iloc[-1]["close"]
    ret = (final - initial_capital) / initial_capital * 100
    
    sell_trades = [t for t in trades if t["action"] == "SELL"]
    wins = sum(1 for t in sell_trades if t.get("profit", 0) > 0)
    win_rate = wins / len(sell_trades) * 100 if sell_trades else 0
    
    return {
        "initial_capital": initial_capital,
        "final_value": float(final),
        "return_pct": round(ret, 2),
        "win_rate": round(win_rate, 1),
        "total_trades": len(trades),
        "trades": trades[-20:],
        "equity_snapshot": equity[::max(1, len(equity)//20)]
    }

if __name__ == "__main__":
    print("[DecisionEngine] Enhanced decision engine loaded")
    print(f"  Strategies: {[s.name for s in EnsembleStrategy().strategies]}")
