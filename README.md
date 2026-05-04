# AI Trading System

基于 OpenClaw AI Agent 构建的 A 股模拟交易系统，覆盖行情获取、策略回测、多策略决策、风控、模拟下单、交易日志和策略自迭代。

## 在线演示

- GitHub 仓库: [AITradingSystem](https://github.com/ma3203947426/AITradingSystem)
- 演示页: `https://ma3203947426.github.io/AITradingSystem/`

## 项目亮点

- 实时获取 A 股大盘和个股行情
- 内置双均线、RSI、布林带等策略
- 支持回测和网格参数优化
- 本地模拟账户、持仓管理和盈亏统计
- Agent 主循环自动记录交易日记并分析结果
- 输出 HTML 看板，便于展示和复盘

## 核心流程

```text
行情获取 -> 指标计算 -> 多策略投票 -> 风控检查 -> 模拟执行 -> 写入日记 -> 策略进化
```

### Agent 驱动逻辑

每一轮交易由 `TradingAgent` 统一调度：

1. 拉取大盘和标的行情
2. 读取持仓和历史交易
3. 生成策略信号
4. 执行风险校验
5. 进行模拟买卖
6. 写入交易日志
7. 根据胜率和盈亏判断是否升级策略版本

## 核心模块

- `core/data_feed.py`: akshare 行情数据层
- `core/strategy_engine.py`: 策略、回测和参数优化
- `core/decision_engine.py`: 多策略加权决策与风险控制
- `core/paper_trader.py`: 模拟交易、持仓和日志
- `core/trading_agent.py`: 主 Agent 循环与策略自迭代
- `core/dashboard.py`: HTML 看板生成

## 快速开始

```powershell
cd AITradingSystem
.\run.ps1 init
.\run.ps1 market
.\run.ps1 quote -Symbol 600519.SH
.\run.ps1 run
.\run.ps1 dashboard
```

## 支持的策略

- 双均线交叉
- RSI 超买超卖
- 布林带上下轨
- 趋势跟随 + 成交量确认
- 多策略投票决策

## 目录结构

```text
AITradingSystem\
├── core\                  # 核心代码
├── data\                  # 持仓、日志和看板
├── docs\                  # GitHub Pages 演示页
├── scripts\               # 定时任务脚本
├── strategies\            # 自定义策略
├── run.ps1                # 主启动脚本
└── README.md
```

## 环境依赖

- Python 3.10+
- akshare
- pandas
- numpy
- ta

安装：

```bash
pip install -r requirements.txt
```

## 风控说明

本项目仅用于技术研究和模拟交易演示，不构成任何投资建议。实际交易存在风险，请自行判断。

## 参考

- [akshare 文档](https://akshare.akfamily.xyz/)
- [OpenClaw 文档](https://docs.openclaw.ai)
