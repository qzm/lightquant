# LightQuant - 数字货币量化交易框架

LightQuant是一个基于Python的数字货币量化交易框架，采用领域驱动设计(DDD)架构，提供了一套完整的工具和接口，用于开发、测试和部署数字货币交易策略。

## 架构设计

LightQuant采用领域驱动设计(DDD)架构，将系统分为以下几个层次：

### 领域层 (Domain Layer)

包含核心业务逻辑和实体模型，如订单、交易、账户、市场数据等。这些模型是系统的核心，不依赖于任何外部系统或框架。

主要组件：
- 实体模型：Order, Trade, Account, Balance, Strategy等
- 值对象：OrderParams, StrategyConfig等
- 仓库接口：OrderRepository, AccountRepository等
- 领域服务：OrderService, AccountService等
- 策略引擎：StrategyEngine, BaseStrategy等
- 回测引擎：BacktestEngine等
- 风险管理：RiskManager, RiskRule等

### 应用层 (Application Layer)

协调领域对象完成用户的请求，实现用例和应用服务。

主要组件：
- 应用服务：StrategyAppService, BacktestAppService等
- 用例实现：CreateStrategy, RunBacktest等

### 基础设施层 (Infrastructure Layer)

提供技术能力，实现领域层定义的接口，如数据库访问、外部API调用等。

主要组件：
- 数据库访问：SQLOrderRepository, SQLAccountRepository等
- 交易所API：BinanceExchange, OKExExchange等
- 数据源：CSVDataSource, DatabaseDataSource等

### 接口层 (Interface Layer)

负责与外部系统交互，如Web API、命令行界面等。

主要组件：
- Web API：RESTful API, WebSocket API等
- CLI：命令行工具
- GUI：Web界面

## 目录结构

```
lightquant/
├── domain/                 # 领域层
│   ├── models/             # 领域模型
│   ├── services/           # 领域服务
│   ├── repositories/       # 仓库接口
│   ├── strategies/         # 策略引擎
│   ├── risk_management/    # 风险管理
│   └── events/             # 领域事件
├── application/            # 应用层
│   ├── services/           # 应用服务
│   └── use_cases/          # 用例实现
├── infrastructure/         # 基础设施层
│   ├── database/           # 数据库访问
│   ├── exchanges/          # 交易所API
│   └── data_sources/       # 数据源
└── interface/              # 接口层
    ├── web/                # Web API
    ├── cli/                # 命令行界面
    └── gui/                # 图形界面
```

## 安装

```bash
# 克隆仓库
git clone https://github.com/lightquant/lightquant.git
cd lightquant

# 安装依赖
pip install -e .
```

## 使用示例

### 使用策略引擎

```python
from lightquant.domain.models.strategy import StrategyConfig
from lightquant.domain.strategies import BaseStrategy, StrategyResult
from lightquant.domain.strategies.strategy_engine import StrategyEngine

# 创建策略类
class MyStrategy(BaseStrategy):
    def initialize(self) -> None:
        # 初始化策略
        pass
        
    def on_candle(self, candle) -> StrategyResult:
        # 处理K线数据
        result = StrategyResult()
        # 添加交易逻辑
        return result

# 创建策略配置
config = StrategyConfig(
    name="我的策略",
    symbols=["BTC/USDT"],
    exchange_ids=["binance"],
    timeframes=["1h"],
    params={"param1": 10, "param2": 20}
)

# 创建策略引擎
strategy_engine = StrategyEngine(...)

# 注册策略类
strategy_engine.register_strategy_class(MyStrategy)

# 创建策略实例
strategy_id = strategy_engine.create_strategy(MyStrategy, config)

# 启动策略
strategy_engine.start_strategy(strategy_id)
```

### 使用回测引擎

```python
from datetime import datetime
from lightquant.domain.strategies.backtest_engine import BacktestEngine

# 创建回测引擎
backtest_engine = BacktestEngine(...)

# 创建策略
strategy_id = backtest_engine.create_strategy(MyStrategy, config)

# 运行回测
results = backtest_engine.run_backtest(
    strategy_id=strategy_id,
    start_time=datetime(2023, 1, 1),
    end_time=datetime(2023, 12, 31)
)

# 分析回测结果
print(f"总收益: {results['metrics']['total_return']}%")
print(f"最大回撤: {results['metrics']['max_drawdown']}%")
print(f"夏普比率: {results['metrics']['sharpe_ratio']}")
```

### 使用风险管理模块

风险管理模块是LightQuant框架中的重要组成部分，用于控制交易风险，防止过度交易和资金损失。风险管理模块包含风险管理器（RiskManager）和多种风险控制规则（RiskRule）。

#### 风险管理模块结构

- **RiskManager**：风险管理器，负责管理和应用风险控制规则
- **RiskRule**：风险控制规则抽象基类
  - **PositionSizeRule**：仓位大小规则，控制单笔交易的仓位大小
  - **MaxDrawdownRule**：最大回撤规则，当账户回撤超过阈值时停止交易
  - **MaxTradesPerDayRule**：每日最大交易次数规则，限制每日交易次数

#### 使用示例

```python
from lightquant.domain.risk_management import RiskManager
from lightquant.domain.risk_management import PositionSizeRule, MaxDrawdownRule, MaxTradesPerDayRule

# 创建风险管理器
risk_manager = RiskManager()

# 添加仓位大小规则
position_rule = PositionSizeRule(
    max_position_value=1000.0,  # 最大仓位价值1000 USDT
    max_position_percentage=5.0,  # 最大仓位占账户权益的5%
    max_position_amount=0.05  # 最大仓位数量0.05 BTC
)
risk_manager.add_rule(position_rule)

# 添加最大回撤规则
drawdown_rule = MaxDrawdownRule(
    max_drawdown_percentage=10.0  # 最大回撤10%
)
risk_manager.add_rule(drawdown_rule)

# 添加每日最大交易次数规则
trades_rule = MaxTradesPerDayRule(
    max_trades=5  # 每日最多5笔交易
)
risk_manager.add_rule(trades_rule)

# 检查订单是否符合风险控制规则
if risk_manager.check_order(order, account):
    # 订单符合风险控制规则，可以执行
    execute_order(order)
else:
    # 订单不符合风险控制规则，拒绝执行
    reject_order(order)

# 启用/禁用规则
risk_manager.disable_rule(position_rule.name)
risk_manager.enable_rule(position_rule.name)

# 更新规则参数
risk_manager.update_rule_params(position_rule.name, {"max_position_value": 2000.0})

# 更新上下文信息（如当前回撤）
risk_manager.update_context({"drawdown": 5.0})
```

#### 在策略中使用风险管理

风险管理模块已经集成到策略引擎和回测引擎中，可以在策略中直接使用：

```python
class RiskAwareStrategy(BaseStrategy):
    def initialize(self) -> None:
        # 设置风险管理规则
        if self.context and self.context.risk_manager:
            # 添加仓位大小规则
            position_rule = PositionSizeRule(
                max_position_value=1000.0,
                max_position_percentage=5.0
            )
            self.context.risk_manager.add_rule(position_rule)
            
            # 添加最大回撤规则
            drawdown_rule = MaxDrawdownRule(
                max_drawdown_percentage=10.0
            )
            self.context.risk_manager.add_rule(drawdown_rule)
    
    def on_candle(self, candle) -> StrategyResult:
        result = StrategyResult()
        
        # 计算当前回撤并更新风险管理器上下文
        drawdown = calculate_drawdown(candle)
        if self.context and self.context.risk_manager:
            self.context.risk_manager.update_context({'drawdown': drawdown})
        
        # 创建订单（会自动进行风险检查）
        order = self.create_market_order(...)
        
        if order:
            # 订单通过风险检查
            result.add_order(order)
        else:
            # 订单被风险管理器拒绝
            result.add_log("订单被风险管理器拒绝")
        
        return result
```

## 开发计划

- [x] 核心领域模型
- [x] 策略引擎
- [x] 回测引擎
- [x] 风险管理模块
- [ ] 交易所适配器
- [ ] 性能分析模块
- [ ] Web界面
- [ ] 实时监控系统

## 贡献

欢迎贡献代码、报告问题或提出建议。请遵循以下步骤：

1. Fork仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

## 许可证

本项目采用MIT许可证。详见[LICENSE](LICENSE)文件。 