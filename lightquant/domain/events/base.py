"""
基础领域事件类
"""

from abc import ABC
from datetime import datetime
from typing import Any, Dict
import uuid


class DomainEvent(ABC):
    """
    领域事件基类
    
    领域事件表示领域中发生的事情，通常是过去时态的动词
    """
    
    def __init__(self):
        self._id = str(uuid.uuid4())
        self._occurred_on = datetime.utcnow()
    
    @property
    def id(self) -> str:
        """事件ID"""
        return self._id
    
    @property
    def occurred_on(self) -> datetime:
        """事件发生时间"""
        return self._occurred_on
    
    def to_dict(self) -> Dict[str, Any]:
        """将事件转换为字典"""
        return {
            "id": self._id,
            "type": self.__class__.__name__,
            "occurred_on": self._occurred_on.isoformat(),
        } 