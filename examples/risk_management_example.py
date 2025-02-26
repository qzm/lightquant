"""
风险管理示例

本示例展示如何使用LightQuant的风险管理模块来控制交易风险。
"""

import logging
import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from lightquant.domain.models.account import Account, Balance
from lightquant.domain.models.order import Order, OrderParams, OrderSide, OrderType
from lightquant.domain.risk_management import (
    MaxDrawdownRule,
    MaxTradesPerDayRule,
    PositionSizeRule,
    RiskManager,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def create_test_account():
    """创建测试账户"""
    account = Account("binance")
    account.update_balance("BTC", 1.0)
    account.update_balance("USDT", 50000.0)
    return account


def create_test_order(
    symbol="BTC/USDT",
    order_type=OrderType.LIMIT,
    side=OrderSide.BUY,
    amount=0.1,
    price=50000.0,
):
    """创建测试订单"""
    params = OrderParams(
        symbol=symbol, order_type=order_type, side=side, amount=amount, price=price
    )
    return Order(params, strategy_id="test_strategy", exchange_id="binance")


def test_position_size_rule():
    """测试仓位大小规则"""
    print("\n=== 测试仓位大小规则 ===")

    # 创建风险管理器
    risk_manager = RiskManager()

    # 创建仓位大小规则
    position_rule = PositionSizeRule(
        max_position_value=10000.0,  # 最大仓位价值10000 USDT
        max_position_percentage=20.0,  # 最大仓位占账户权益的20%
        max_position_amount=0.5,  # 最大仓位数量0.5 BTC
    )

    # 添加规则到风险管理器
    risk_manager.add_rule(position_rule)

    # 创建测试账户
    account = create_test_account()

    # 更新上下文信息
    context = {"ticker": {"BTC/USDT": {"last": 50000.0}}}
    risk_manager.update_context(context)

    # 测试符合规则的订单
    order1 = create_test_order(amount=0.1, price=50000.0)  # 价值5000 USDT
    result1 = risk_manager.check_order(order1, account)
    print(f"订单1 (0.1 BTC, 价值5000 USDT): {'通过' if result1 else '拒绝'}")

    # 测试超过最大仓位价值的订单
    order2 = create_test_order(amount=0.3, price=50000.0)  # 价值15000 USDT
    result2 = risk_manager.check_order(order2, account)
    print(f"订单2 (0.3 BTC, 价值15000 USDT): {'通过' if result2 else '拒绝'}")

    # 测试超过最大仓位数量的订单
    order3 = create_test_order(amount=0.6, price=50000.0)  # 0.6 BTC
    result3 = risk_manager.check_order(order3, account)
    print(f"订单3 (0.6 BTC, 价值30000 USDT): {'通过' if result3 else '拒绝'}")

    # 更新规则参数
    risk_manager.update_rule_params(position_rule.name, {"max_position_value": 20000.0})

    # 再次测试之前被拒绝的订单
    result4 = risk_manager.check_order(order2, account)
    print(
        f"更新规则后，订单2 (0.3 BTC, 价值15000 USDT): {'通过' if result4 else '拒绝'}"
    )


def test_max_drawdown_rule():
    """测试最大回撤规则"""
    print("\n=== 测试最大回撤规则 ===")

    # 创建风险管理器
    risk_manager = RiskManager()

    # 创建最大回撤规则
    drawdown_rule = MaxDrawdownRule(max_drawdown_percentage=10.0)  # 最大回撤10%

    # 添加规则到风险管理器
    risk_manager.add_rule(drawdown_rule)

    # 创建测试账户
    account = create_test_account()

    # 测试不同回撤情况
    for drawdown in [5.0, 10.0, 15.0]:
        # 更新上下文信息
        context = {"drawdown": drawdown}
        risk_manager.update_context(context)

        # 创建测试订单
        order = create_test_order()

        # 检查订单
        result = risk_manager.check_order(order, account)
        print(f"当前回撤 {drawdown}%: {'通过' if result else '拒绝'}")


def test_max_trades_per_day_rule():
    """测试每日最大交易次数规则"""
    print("\n=== 测试每日最大交易次数规则 ===")

    # 创建风险管理器
    risk_manager = RiskManager()

    # 创建每日最大交易次数规则
    trades_rule = MaxTradesPerDayRule(max_trades=3)  # 每日最多3笔交易

    # 添加规则到风险管理器
    risk_manager.add_rule(trades_rule)

    # 创建测试账户
    account = create_test_account()

    # 测试多个订单
    for i in range(5):
        # 创建测试订单
        order = create_test_order()

        # 检查订单
        result = risk_manager.check_order(order, account)
        print(f"订单 {i+1}: {'通过' if result else '拒绝'}")


def test_multiple_rules():
    """测试多个规则组合"""
    print("\n=== 测试多个规则组合 ===")

    # 创建风险管理器
    risk_manager = RiskManager()

    # 创建多个规则
    position_rule = PositionSizeRule(
        max_position_value=10000.0, max_position_percentage=20.0
    )

    drawdown_rule = MaxDrawdownRule(max_drawdown_percentage=10.0)

    trades_rule = MaxTradesPerDayRule(max_trades=5)

    # 添加规则到风险管理器
    risk_manager.add_rule(position_rule)
    risk_manager.add_rule(drawdown_rule)
    risk_manager.add_rule(trades_rule)

    # 创建测试账户
    account = create_test_account()

    # 更新上下文信息
    context = {"ticker": {"BTC/USDT": {"last": 50000.0}}, "drawdown": 5.0}
    risk_manager.update_context(context)

    # 测试符合所有规则的订单
    order1 = create_test_order(amount=0.1, price=50000.0)
    result1 = risk_manager.check_order(order1, account)
    print(f"订单1 (符合所有规则): {'通过' if result1 else '拒绝'}")

    # 禁用仓位大小规则
    risk_manager.disable_rule(position_rule.name)

    # 测试超过仓位限制但其他规则符合的订单
    order2 = create_test_order(amount=0.5, price=50000.0)  # 价值25000 USDT
    result2 = risk_manager.check_order(order2, account)
    print(f"订单2 (禁用仓位规则后): {'通过' if result2 else '拒绝'}")

    # 更新回撤超过限制
    context["drawdown"] = 15.0
    risk_manager.update_context(context)

    # 测试回撤超过限制的订单
    order3 = create_test_order()
    result3 = risk_manager.check_order(order3, account)
    print(f"订单3 (回撤15%): {'通过' if result3 else '拒绝'}")


def main():
    """主函数"""
    print("=== LightQuant风险管理示例 ===")

    # 运行测试
    test_position_size_rule()
    test_max_drawdown_rule()
    test_max_trades_per_day_rule()
    test_multiple_rules()

    print("\n=== 示例完成 ===")


if __name__ == "__main__":
    main()
