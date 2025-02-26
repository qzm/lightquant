"""
交易所适配器工厂
"""

from typing import Dict, Optional, Type

from .binance_adapter import BinanceAdapter
from .exchange_adapter import ExchangeAdapter


class ExchangeFactory:
    """
    交易所适配器工厂

    负责创建和管理交易所适配器实例
    """

    _adapters: Dict[str, Type[ExchangeAdapter]] = {
        "binance": BinanceAdapter,
        # 'okex': OkexAdapter,  # 将在后续实现
        # 'huobi': HuobiAdapter,  # 将在后续实现
    }

    _instances: Dict[str, ExchangeAdapter] = {}

    @classmethod
    def register_adapter(
        cls, exchange_id: str, adapter_class: Type[ExchangeAdapter]
    ) -> None:
        """
        注册交易所适配器

        Args:
            exchange_id: 交易所ID
            adapter_class: 适配器类
        """
        cls._adapters[exchange_id] = adapter_class

    @classmethod
    def create_adapter(
        cls,
        exchange_id: str,
        api_key: str = "",
        api_secret: str = "",
        passphrase: str = "",
        use_singleton: bool = True,
    ) -> Optional[ExchangeAdapter]:
        """
        创建交易所适配器

        Args:
            exchange_id: 交易所ID
            api_key: API密钥
            api_secret: API密钥
            passphrase: API密码（部分交易所需要）
            use_singleton: 是否使用单例模式

        Returns:
            交易所适配器实例，如果交易所不支持则返回None
        """
        # 检查交易所是否支持
        if exchange_id not in cls._adapters:
            print(f"不支持的交易所: {exchange_id}")
            return None

        # 如果使用单例模式且已存在实例，则返回已有实例
        instance_key = f"{exchange_id}_{api_key}"
        if use_singleton and instance_key in cls._instances:
            return cls._instances[instance_key]

        # 创建新实例
        adapter_class = cls._adapters[exchange_id]
        adapter = adapter_class(api_key, api_secret, passphrase)

        # 如果使用单例模式，则保存实例
        if use_singleton:
            cls._instances[instance_key] = adapter

        return adapter

    @classmethod
    def get_supported_exchanges(cls) -> list:
        """
        获取支持的交易所列表

        Returns:
            支持的交易所ID列表
        """
        return list(cls._adapters.keys())
