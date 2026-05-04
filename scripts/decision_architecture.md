### 决策层架构

#### 决策引擎 (`core/decision_engine.py`)

**多策略投票系统：**
- TrendFollowStrategy — 趋势跟踪（ADX + 成交量确认 + 高低点排列）
- MACrossoverStrategy — 均线交叉（金叉/死叉 + 长期趋势过滤）
- RSIStrategy — RSI 超买超卖
- BollingerStrategy — 布林带挤压/反弹

**风控层：**
- 最大回撤 15% 停止交易
- 连亏 4 笔暂停
- 凯利公式仓位计算
- 每笔最多 2% 风险

**决策流程：**
数据 → 技术指标计算 → 4策略分别输出信号 → 加权投票 → 风控检查 → 最终决策 + 理由
