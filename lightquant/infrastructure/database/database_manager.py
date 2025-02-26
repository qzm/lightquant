"""
数据库管理器，负责管理数据库连接和会话
"""

import os
from contextlib import contextmanager
from typing import Any, Dict, Optional

from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, scoped_session, sessionmaker

Base = declarative_base()


class DatabaseManager:
    """
    数据库管理器

    负责管理数据库连接和会话
    """

    _instance = None
    _engines: Dict[str, Engine] = {}
    _session_factories: Dict[str, sessionmaker] = {}

    def __new__(cls, *args, **kwargs):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, connection_string: Optional[str] = None):
        """
        初始化数据库管理器

        Args:
            connection_string: 数据库连接字符串，如果为None则从环境变量获取
        """
        if self._initialized:
            return

        self._connection_string = connection_string or os.environ.get(
            "DATABASE_URL", "sqlite:///lightquant.db"
        )
        self._default_engine_name = "default"
        self._initialized = True

        # 创建默认引擎
        self.create_engine(self._default_engine_name, self._connection_string)

    def create_engine(self, name: str, connection_string: str, **kwargs) -> Engine:
        """
        创建数据库引擎

        Args:
            name: 引擎名称
            connection_string: 数据库连接字符串
            **kwargs: 传递给create_engine的其他参数

        Returns:
            数据库引擎
        """
        if name in self._engines:
            return self._engines[name]

        # 设置默认参数
        engine_kwargs = {
            "echo": False,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
        }
        engine_kwargs.update(kwargs)

        # 创建引擎
        engine = create_engine(connection_string, **engine_kwargs)
        self._engines[name] = engine

        # 创建会话工厂
        session_factory = sessionmaker(bind=engine)
        self._session_factories[name] = session_factory

        return engine

    def get_engine(self, name: Optional[str] = None) -> Engine:
        """
        获取数据库引擎

        Args:
            name: 引擎名称，如果为None则返回默认引擎

        Returns:
            数据库引擎
        """
        engine_name = name or self._default_engine_name
        if engine_name not in self._engines:
            raise ValueError(f"引擎 {engine_name} 不存在")
        return self._engines[engine_name]

    @contextmanager
    def session(self, name: Optional[str] = None) -> Session:
        """
        获取数据库会话

        Args:
            name: 引擎名称，如果为None则使用默认引擎

        Returns:
            数据库会话
        """
        engine_name = name or self._default_engine_name
        if engine_name not in self._session_factories:
            raise ValueError(f"引擎 {engine_name} 不存在")

        session_factory = self._session_factories[engine_name]
        session = session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def create_scoped_session(self, name: Optional[str] = None) -> scoped_session:
        """
        创建线程安全的会话工厂

        Args:
            name: 引擎名称，如果为None则使用默认引擎

        Returns:
            线程安全的会话工厂
        """
        engine_name = name or self._default_engine_name
        if engine_name not in self._session_factories:
            raise ValueError(f"引擎 {engine_name} 不存在")

        session_factory = self._session_factories[engine_name]
        return scoped_session(session_factory)

    def create_all_tables(self, name: Optional[str] = None) -> None:
        """
        创建所有表

        Args:
            name: 引擎名称，如果为None则使用默认引擎
        """
        engine = self.get_engine(name)
        Base.metadata.create_all(engine)

    def drop_all_tables(self, name: Optional[str] = None) -> None:
        """
        删除所有表

        Args:
            name: 引擎名称，如果为None则使用默认引擎
        """
        engine = self.get_engine(name)
        Base.metadata.drop_all(engine)
