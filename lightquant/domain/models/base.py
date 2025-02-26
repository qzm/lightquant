"""
基础领域模型类，包括实体、值对象和聚合根
"""

import uuid
from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, Set, TypeVar

T = TypeVar("T")


class Entity(ABC):
    """实体基类"""

    def __init__(self, entity_id: Optional[str] = None):
        self.id = entity_id or str(uuid.uuid4())
        self._created_at = datetime.now()
        self._updated_at = self._created_at

    def __eq__(self, other):
        if not isinstance(other, Entity):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    def update(self):
        """更新实体的更新时间"""
        self._updated_at = datetime.now()


class DomainEvent:
    """领域事件基类"""

    def __init__(self):
        self.id = str(uuid.uuid4())
        self.occurred_on = datetime.now()


class AggregateRoot(Entity):
    """聚合根基类"""

    def __init__(self, entity_id: Optional[str] = None):
        super().__init__(entity_id)
        self._domain_events: List[DomainEvent] = []

    def add_domain_event(self, event: DomainEvent):
        """添加领域事件"""
        self._domain_events.append(event)

    def clear_domain_events(self):
        """清除领域事件"""
        self._domain_events.clear()

    def get_domain_events(self) -> List[DomainEvent]:
        """获取领域事件"""
        return self._domain_events.copy()


@dataclass
class ValueObject:
    """值对象基类"""

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))
