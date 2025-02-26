"""
市场数据仓库SQL实现
"""

import json
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import desc

from ....domain.models.market_data import Candle, OrderBook, OrderBookEntry, Ticker
from ....domain.repositories.market_data_repository import MarketDataRepository
from ..database_manager import DatabaseManager
from ..models.market_data_model import CandleModel, OrderBookModel, TickerModel


class SQLMarketDataRepository(MarketDataRepository):
    """市场数据仓库SQL实现"""

    def __init__(self, db_manager: DatabaseManager):
        self._db_manager = db_manager

    def get_ticker(self, symbol: str, exchange_id: str) -> Optional[Ticker]:
        """获取最新行情"""
        with self._db_manager.session() as session:
            ticker_model = (
                session.query(TickerModel)
                .filter(
                    TickerModel.symbol == symbol, TickerModel.exchange_id == exchange_id
                )
                .order_by(desc(TickerModel.timestamp))
                .first()
            )

            if not ticker_model:
                return None

            return self._ticker_to_domain_entity(ticker_model)

    def get_tickers(self, exchange_id: str) -> Dict[str, Ticker]:
        """获取交易所的所有行情"""
        result = {}
        with self._db_manager.session() as session:
            # 获取每个交易对的最新行情
            # 这里的实现可能不是最高效的，实际使用时可能需要优化
            symbols = (
                session.query(TickerModel.symbol)
                .filter(TickerModel.exchange_id == exchange_id)
                .distinct()
                .all()
            )

            for (symbol,) in symbols:
                ticker_model = (
                    session.query(TickerModel)
                    .filter(
                        TickerModel.symbol == symbol,
                        TickerModel.exchange_id == exchange_id,
                    )
                    .order_by(desc(TickerModel.timestamp))
                    .first()
                )

                if ticker_model:
                    result[symbol] = self._ticker_to_domain_entity(ticker_model)

        return result

    def save_ticker(self, ticker: Ticker) -> None:
        """保存行情"""
        with self._db_manager.session() as session:
            ticker_model = TickerModel(
                id=str(ticker.timestamp.timestamp())
                + "_"
                + ticker.symbol
                + "_"
                + ticker.exchange_id,
                symbol=ticker.symbol,
                exchange_id=ticker.exchange_id,
                bid=ticker.bid,
                ask=ticker.ask,
                last=ticker.last,
                high=ticker.high if hasattr(ticker, "high") else None,
                low=ticker.low if hasattr(ticker, "low") else None,
                volume=ticker.volume if hasattr(ticker, "volume") else None,
                quote_volume=(
                    ticker.quote_volume if hasattr(ticker, "quote_volume") else None
                ),
                timestamp=ticker.timestamp,
                created_at=datetime.utcnow(),
            )
            session.add(ticker_model)

    def get_candles(
        self,
        symbol: str,
        exchange_id: str,
        timeframe: str,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Candle]:
        """获取K线数据"""
        with self._db_manager.session() as session:
            query = session.query(CandleModel).filter(
                CandleModel.symbol == symbol,
                CandleModel.exchange_id == exchange_id,
                CandleModel.timeframe == timeframe,
            )

            if since:
                query = query.filter(CandleModel.timestamp >= since)

            candle_models = (
                query.order_by(desc(CandleModel.timestamp)).limit(limit).all()
            )

            # 按时间升序排序
            candle_models.reverse()

            return [self._candle_to_domain_entity(model) for model in candle_models]

    def save_candles(self, candles: List[Candle]) -> None:
        """保存K线数据"""
        with self._db_manager.session() as session:
            for candle in candles:
                candle_model = CandleModel(
                    id=str(candle.timestamp.timestamp())
                    + "_"
                    + candle.symbol
                    + "_"
                    + candle.exchange_id
                    + "_"
                    + candle.timeframe,
                    symbol=candle.symbol,
                    exchange_id=candle.exchange_id,
                    timeframe=candle.timeframe,
                    timestamp=candle.timestamp,
                    open=candle.open,
                    high=candle.high,
                    low=candle.low,
                    close=candle.close,
                    volume=candle.volume,
                    quote_volume=(
                        candle.quote_volume if hasattr(candle, "quote_volume") else None
                    ),
                    created_at=datetime.utcnow(),
                )
                session.add(candle_model)

    def get_order_book(
        self, symbol: str, exchange_id: str, limit: int = 20
    ) -> Optional[OrderBook]:
        """获取订单簿"""
        with self._db_manager.session() as session:
            order_book_model = (
                session.query(OrderBookModel)
                .filter(
                    OrderBookModel.symbol == symbol,
                    OrderBookModel.exchange_id == exchange_id,
                )
                .order_by(desc(OrderBookModel.timestamp))
                .first()
            )

            if not order_book_model:
                return None

            return self._order_book_to_domain_entity(order_book_model, limit)

    def save_order_book(self, order_book: OrderBook) -> None:
        """保存订单簿"""
        with self._db_manager.session() as session:
            # 将买单和卖单转换为JSON格式
            bids_json = json.dumps(
                [{"price": bid.price, "amount": bid.amount} for bid in order_book.bids]
            )
            asks_json = json.dumps(
                [{"price": ask.price, "amount": ask.amount} for ask in order_book.asks]
            )

            order_book_model = OrderBookModel(
                id=str(order_book.timestamp.timestamp())
                + "_"
                + order_book.symbol
                + "_"
                + order_book.exchange_id,
                symbol=order_book.symbol,
                exchange_id=order_book.exchange_id,
                timestamp=order_book.timestamp,
                bids=bids_json,
                asks=asks_json,
                created_at=datetime.utcnow(),
            )
            session.add(order_book_model)

    def _ticker_to_domain_entity(self, model: TickerModel) -> Ticker:
        """将数据库模型转换为领域实体"""
        return Ticker(
            symbol=model.symbol,
            exchange_id=model.exchange_id,
            bid=model.bid,
            ask=model.ask,
            last=model.last,
            high=model.high,
            low=model.low,
            volume=model.volume,
            quote_volume=model.quote_volume,
            timestamp=model.timestamp,
        )

    def _candle_to_domain_entity(self, model: CandleModel) -> Candle:
        """将数据库模型转换为领域实体"""
        return Candle(
            symbol=model.symbol,
            exchange_id=model.exchange_id,
            timeframe=model.timeframe,
            timestamp=model.timestamp,
            open=model.open,
            high=model.high,
            low=model.low,
            close=model.close,
            volume=model.volume,
            quote_volume=model.quote_volume,
        )

    def _order_book_to_domain_entity(
        self, model: OrderBookModel, limit: int
    ) -> OrderBook:
        """将数据库模型转换为领域实体"""
        # 解析JSON格式的买单和卖单
        bids_data = json.loads(model.bids)
        asks_data = json.loads(model.asks)

        # 转换为OrderBookEntry对象
        bids = [
            OrderBookEntry(price=item["price"], amount=item["amount"])
            for item in bids_data[:limit]
        ]
        asks = [
            OrderBookEntry(price=item["price"], amount=item["amount"])
            for item in asks_data[:limit]
        ]

        return OrderBook(
            symbol=model.symbol,
            exchange_id=model.exchange_id,
            timestamp=model.timestamp,
            bids=bids,
            asks=asks,
        )
