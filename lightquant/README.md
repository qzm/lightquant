# LightQuant - 轻量级数字货币量化交易框架

LightQuant是一个基于领域驱动设计(DDD)思想的轻量级数字货币量化交易框架，支持多策略、多交易所和多模块。

## 特点

- **领域驱动设计**：使用DDD思想构建，代码结构清晰，易于扩展
- **多策略支持**：可以同时运行多个交易策略，支持策略的热插拔
- **多交易所支持**：支持连接多个交易所，统一的API接口
- **模块化设计**：各个模块之间松耦合，可以根据需要组合使用
- **实时监控**：提供实时监控和报警功能
- **回测系统**：内置回测系统，可以在历史数据上测试策略

## 项目结构

```
lightquant/
├── domain/              # 领域层：核心业务逻辑和实体
│   ├── models/          # 领域模型
│   ├── services/        # 领域服务
│   ├── repositories/    # 仓库接口
│   ├── events/          # 领域事件
│   ├── strategies/      # 交易策略
│   └── factories/       # 工厂类
├── infrastructure/      # 基础设施层：与外部系统的交互
│   ├── exchanges/       # 交易所API适配器
│   ├── database/        # 数据库访问
│   ├── messaging/       # 消息队列
│   └── logging/         # 日志系统
├── application/         # 应用层：协调领域对象和基础设施
│   ├── services/        # 应用服务
│   ├── dto/             # 数据传输对象
│   ├── commands/        # 命令处理器
│   └── queries/         # 查询处理器
├── interfaces/          # 接口层：提供用户界面和API
│   ├── cli/             # 命令行界面
│   ├── api/             # REST API
│   └── web/             # Web界面
└── config/              # 配置文件
```

## 安装

```bash
pip install -r requirements.txt
```

## 快速开始

1. 配置交易所API密钥
```python
# config/exchanges.py
exchanges = {
    'binance': {
        'api_key': 'your_api_key',
        'api_secret': 'your_api_secret'
    }
}
```

2. 创建并运行策略
```python
from lightquant.interfaces.cli import run_strategy

# 运行简单的移动平均线策略
run_strategy('moving_average', 'binance', 'BTC/USDT', {'short_window': 5, 'long_window': 20})
```

## 贡献

欢迎提交问题和拉取请求！

## 许可证

MIT 