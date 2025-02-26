"""
风险管理器模块，负责管理和应用风险控制规则。
"""

import logging
from typing import Dict, List, Any, Optional, Type, Union

from ..models.order import Order
from ..models.account import Account
from .risk_rule import RiskRule


class RiskManager:
    """
    风险管理器类
    
    负责管理和应用风险控制规则，检查订单是否符合风险控制要求。
    """
    
    def __init__(self):
        """初始化风险管理器"""
        self.rules: Dict[str, RiskRule] = {}
        self.context: Dict[str, Any] = {}
        self.logger = logging.getLogger("risk_manager")
    
    def add_rule(self, rule: RiskRule) -> None:
        """
        添加风险控制规则
        
        Args:
            rule: 要添加的风险控制规则
        """
        self.rules[rule.name] = rule
        self.logger.info(f"添加风险规则: {rule.name}")
    
    def remove_rule(self, rule_name: str) -> bool:
        """
        移除风险控制规则
        
        Args:
            rule_name: 要移除的规则名称
            
        Returns:
            bool: 是否成功移除
        """
        if rule_name in self.rules:
            del self.rules[rule_name]
            self.logger.info(f"移除风险规则: {rule_name}")
            return True
        else:
            self.logger.warning(f"找不到风险规则: {rule_name}")
            return False
    
    def enable_rule(self, rule_name: str) -> bool:
        """
        启用风险控制规则
        
        Args:
            rule_name: 要启用的规则名称
            
        Returns:
            bool: 是否成功启用
        """
        if rule_name in self.rules:
            self.rules[rule_name].enable()
            return True
        else:
            self.logger.warning(f"找不到风险规则: {rule_name}")
            return False
    
    def disable_rule(self, rule_name: str) -> bool:
        """
        禁用风险控制规则
        
        Args:
            rule_name: 要禁用的规则名称
            
        Returns:
            bool: 是否成功禁用
        """
        if rule_name in self.rules:
            self.rules[rule_name].disable()
            return True
        else:
            self.logger.warning(f"找不到风险规则: {rule_name}")
            return False
    
    def update_rule_params(self, rule_name: str, params: Dict[str, Any]) -> bool:
        """
        更新风险控制规则参数
        
        Args:
            rule_name: 要更新的规则名称
            params: 新的参数
            
        Returns:
            bool: 是否成功更新
        """
        if rule_name in self.rules:
            self.rules[rule_name].update_params(params)
            return True
        else:
            self.logger.warning(f"找不到风险规则: {rule_name}")
            return False
    
    def update_context(self, context: Dict[str, Any]) -> None:
        """
        更新上下文信息
        
        Args:
            context: 新的上下文信息
        """
        self.context.update(context)
    
    def check_order(self, order: Order, account: Account) -> bool:
        """
        检查订单是否符合所有启用的风险控制规则
        
        Args:
            order: 要检查的订单
            account: 账户信息
            
        Returns:
            bool: 如果订单符合所有启用的规则返回True，否则返回False
        """
        self.logger.info(f"检查订单 {order.id} 是否符合风险规则")
        
        for rule_name, rule in self.rules.items():
            if rule.enabled:
                if not rule.check_order(order, account, self.context):
                    self.logger.warning(f"订单 {order.id} 被风险规则拒绝: {rule_name}")
                    return False
        
        self.logger.info(f"订单 {order.id} 通过所有风险检查")
        return True
    
    def get_rule(self, rule_name: str) -> Optional[RiskRule]:
        """
        获取指定名称的风险控制规则
        
        Args:
            rule_name: 规则名称
            
        Returns:
            Optional[RiskRule]: 找到的规则，如果不存在则返回None
        """
        return self.rules.get(rule_name)
    
    def get_rules(self) -> Dict[str, RiskRule]:
        """
        获取所有风险控制规则
        
        Returns:
            Dict[str, RiskRule]: 所有规则的字典
        """
        return self.rules.copy()
    
    def get_enabled_rules(self) -> Dict[str, RiskRule]:
        """
        获取所有启用的风险控制规则
        
        Returns:
            Dict[str, RiskRule]: 所有启用的规则的字典
        """
        return {name: rule for name, rule in self.rules.items() if rule.enabled} 