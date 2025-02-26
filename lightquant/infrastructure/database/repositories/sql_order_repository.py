"""
订单仓库SQL实现
"""

import json
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from ....domain.models.order import Order, OrderType, OrderStatus, OrderSide, OrderParams
from ....domain.repositories.order_repository import OrderRepository
from ..models.order_model import OrderModel, OrderTypeEnum, OrderStatusEnum, OrderSideEnum
from ..database_manager import DatabaseManager


class SQLOrderRepository(OrderRepository):
    """订单仓库SQL实现"""
    
    def __init__(self, db_manager: DatabaseManager):
        self._db_manager = db_manager
    
    def save(self, order: Order) -> None:
        """保存订单"""
        with self._db_manager.session() as session:
            # 检查订单是否已存在
            order_model = session.query(OrderModel).filter(OrderModel.id == order.id).first()
            
            if order_model:
                # 更新现有订单
                order_model.status = self._map_order_status(order.status)
                order_model.filled_amount = order.filled_amount
                order_model.average_price = order.average_price
                order_model.exchange_order_id = order.exchange_order_id
                order_model.is_closed = order.is_closed
                order_model.submitted_at = order.submitted_at
                order_model.closed_at = order.closed_at
                order_model.error_message = order.error_message
            else:
                # 创建新订单
                order_model = OrderModel(
                    id=order.id,
                    strategy_id=order.strategy_id,
                    exchange_id=order.exchange_id,
                    symbol=order.params.symbol,
                    order_type=self._map_order_type(order.params.order_type),
                    side=self._map_order_side(order.params.side),
                    amount=order.params.amount,
                    price=order.params.price,
                    stop_price=order.params.stop_price,
                    filled_amount=order.filled_amount,
                    average_price=order.average_price,
                    status=self._map_order_status(order.status),
                    exchange_order_id=order.exchange_order_id,
                    client_order_id=order.client_order_id,
                    params=json.dumps(order.params.params) if order.params.params else None,
                    error_message=order.error_message,
                    is_closed=order.is_closed,
                    created_at=order.created_at,
                    updated_at=order.updated_at,
                    submitted_at=order.submitted_at,
                    closed_at=order.closed_at,
                )
                session.add(order_model)
    
    def find_by_id(self, order_id: str) -> Optional[Order]:
        """根据ID查找订单"""
        with self._db_manager.session() as session:
            order_model = session.query(OrderModel).filter(OrderModel.id == order_id).first()
            if not order_model:
                return None
            return self._to_domain_entity(order_model)
    
    def find_by_exchange_order_id(self, exchange_id: str, exchange_order_id: str) -> Optional[Order]:
        """根据交易所订单ID查找订单"""
        with self._db_manager.session() as session:
            order_model = session.query(OrderModel).filter(
                OrderModel.exchange_id == exchange_id,
                OrderModel.exchange_order_id == exchange_order_id
            ).first()
            if not order_model:
                return None
            return self._to_domain_entity(order_model)
    
    def find_by_strategy_id(self, strategy_id: str) -> List[Order]:
        """查找策略的所有订单"""
        with self._db_manager.session() as session:
            order_models = session.query(OrderModel).filter(
                OrderModel.strategy_id == strategy_id
            ).all()
            return [self._to_domain_entity(model) for model in order_models]
    
    def find_open_by_strategy_id(self, strategy_id: str) -> List[Order]:
        """查找策略的未完成订单"""
        with self._db_manager.session() as session:
            order_models = session.query(OrderModel).filter(
                OrderModel.strategy_id == strategy_id,
                OrderModel.is_closed == False
            ).all()
            return [self._to_domain_entity(model) for model in order_models]
    
    def find_by_exchange_id(self, exchange_id: str) -> List[Order]:
        """查找交易所的所有订单"""
        with self._db_manager.session() as session:
            order_models = session.query(OrderModel).filter(
                OrderModel.exchange_id == exchange_id
            ).all()
            return [self._to_domain_entity(model) for model in order_models]
    
    def find_open_by_exchange_id(self, exchange_id: str) -> List[Order]:
        """查找交易所的未完成订单"""
        with self._db_manager.session() as session:
            order_models = session.query(OrderModel).filter(
                OrderModel.exchange_id == exchange_id,
                OrderModel.is_closed == False
            ).all()
            return [self._to_domain_entity(model) for model in order_models]
    
    def find_by_symbol(self, symbol: str) -> List[Order]:
        """查找交易对的所有订单"""
        with self._db_manager.session() as session:
            order_models = session.query(OrderModel).filter(
                OrderModel.symbol == symbol
            ).all()
            return [self._to_domain_entity(model) for model in order_models]
    
    def delete(self, order_id: str) -> bool:
        """删除订单"""
        with self._db_manager.session() as session:
            order_model = session.query(OrderModel).filter(OrderModel.id == order_id).first()
            if not order_model:
                return False
            session.delete(order_model)
            return True
    
    def _to_domain_entity(self, model: OrderModel) -> Order:
        """将数据库模型转换为领域实体"""
        # 创建订单参数
        params = OrderParams(
            symbol=model.symbol,
            order_type=self._map_to_order_type(model.order_type),
            side=self._map_to_order_side(model.side),
            amount=model.amount,
            price=model.price,
            stop_price=model.stop_price,
            params=json.loads(model.params) if model.params else {}
        )
        
        # 创建订单实体
        order = Order(
            params=params,
            strategy_id=model.strategy_id,
            exchange_id=model.exchange_id,
            entity_id=model.id
        )
        
        # 设置订单属性
        order._status = self._map_to_order_status(model.status)
        order._filled_amount = model.filled_amount
        order._average_price = model.average_price
        order._exchange_order_id = model.exchange_order_id
        order._client_order_id = model.client_order_id
        order._error_message = model.error_message
        order._created_at = model.created_at
        order._updated_at = model.updated_at
        order._submitted_at = model.submitted_at
        order._closed_at = model.closed_at
        
        return order
    
    def _map_order_type(self, order_type: OrderType) -> OrderTypeEnum:
        """将领域枚举映射为数据库枚举"""
        mapping = {
            OrderType.MARKET: OrderTypeEnum.MARKET,
            OrderType.LIMIT: OrderTypeEnum.LIMIT,
            OrderType.STOP: OrderTypeEnum.STOP,
            OrderType.STOP_LIMIT: OrderTypeEnum.STOP_LIMIT,
            OrderType.TRAILING_STOP: OrderTypeEnum.TRAILING_STOP,
        }
        return mapping.get(order_type, OrderTypeEnum.LIMIT)
    
    def _map_to_order_type(self, order_type: OrderTypeEnum) -> OrderType:
        """将数据库枚举映射为领域枚举"""
        mapping = {
            OrderTypeEnum.MARKET: OrderType.MARKET,
            OrderTypeEnum.LIMIT: OrderType.LIMIT,
            OrderTypeEnum.STOP: OrderType.STOP,
            OrderTypeEnum.STOP_LIMIT: OrderType.STOP_LIMIT,
            OrderTypeEnum.TRAILING_STOP: OrderType.TRAILING_STOP,
        }
        return mapping.get(order_type, OrderType.LIMIT)
    
    def _map_order_status(self, status: OrderStatus) -> OrderStatusEnum:
        """将领域枚举映射为数据库枚举"""
        mapping = {
            OrderStatus.CREATED: OrderStatusEnum.CREATED,
            OrderStatus.SUBMITTED: OrderStatusEnum.SUBMITTED,
            OrderStatus.PARTIAL: OrderStatusEnum.PARTIAL,
            OrderStatus.FILLED: OrderStatusEnum.FILLED,
            OrderStatus.CANCELED: OrderStatusEnum.CANCELED,
            OrderStatus.REJECTED: OrderStatusEnum.REJECTED,
            OrderStatus.EXPIRED: OrderStatusEnum.EXPIRED,
        }
        return mapping.get(status, OrderStatusEnum.CREATED)
    
    def _map_to_order_status(self, status: OrderStatusEnum) -> OrderStatus:
        """将数据库枚举映射为领域枚举"""
        mapping = {
            OrderStatusEnum.CREATED: OrderStatus.CREATED,
            OrderStatusEnum.SUBMITTED: OrderStatus.SUBMITTED,
            OrderStatusEnum.PARTIAL: OrderStatus.PARTIAL,
            OrderStatusEnum.FILLED: OrderStatus.FILLED,
            OrderStatusEnum.CANCELED: OrderStatus.CANCELED,
            OrderStatusEnum.REJECTED: OrderStatus.REJECTED,
            OrderStatusEnum.EXPIRED: OrderStatus.EXPIRED,
        }
        return mapping.get(status, OrderStatus.CREATED)
    
    def _map_order_side(self, side: OrderSide) -> OrderSideEnum:
        """将领域枚举映射为数据库枚举"""
        mapping = {
            OrderSide.BUY: OrderSideEnum.BUY,
            OrderSide.SELL: OrderSideEnum.SELL,
        }
        return mapping.get(side, OrderSideEnum.BUY)
    
    def _map_to_order_side(self, side: OrderSideEnum) -> OrderSide:
        """将数据库枚举映射为领域枚举"""
        mapping = {
            OrderSideEnum.BUY: OrderSide.BUY,
            OrderSideEnum.SELL: OrderSide.SELL,
        }
        return mapping.get(side, OrderSide.BUY) 