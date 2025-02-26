"""
数据库初始化脚本
"""

import argparse
import os
from typing import Optional

from .database_manager import Base, DatabaseManager
from .models import (
    AccountModel,
    BalanceModel,
    CandleModel,
    OrderBookModel,
    OrderModel,
    StrategyModel,
    TickerModel,
    TradeModel,
)


def init_database(
    connection_string: Optional[str] = None, drop_all: bool = False
) -> None:
    """
    初始化数据库

    Args:
        connection_string: 数据库连接字符串，如果为None则从环境变量获取
        drop_all: 是否删除所有表
    """
    # 创建数据库管理器
    db_manager = DatabaseManager(connection_string)

    # 如果需要，删除所有表
    if drop_all:
        print("删除所有表...")
        db_manager.drop_all_tables()

    # 创建所有表
    print("创建所有表...")
    db_manager.create_all_tables()

    print("数据库初始化完成！")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="初始化LightQuant数据库")
    parser.add_argument("--connection-string", help="数据库连接字符串")
    parser.add_argument("--drop-all", action="store_true", help="删除所有表")

    args = parser.parse_args()

    # 如果命令行没有提供连接字符串，则尝试从环境变量获取
    connection_string = args.connection_string or os.environ.get("DATABASE_URL")

    init_database(connection_string, args.drop_all)
