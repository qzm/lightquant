"""
账户仓库SQL实现
"""

from typing import List, Optional, Dict

from sqlalchemy.orm import Session

from ....domain.models.account import Account, Balance
from ....domain.repositories.account_repository import AccountRepository
from ..models.account_model import AccountModel, BalanceModel
from ..database_manager import DatabaseManager


class SQLAccountRepository(AccountRepository):
    """账户仓库SQL实现"""
    
    def __init__(self, db_manager: DatabaseManager):
        self._db_manager = db_manager
    
    def save(self, account: Account) -> None:
        """保存账户"""
        with self._db_manager.session() as session:
            # 检查账户是否已存在
            account_model = session.query(AccountModel).filter(AccountModel.id == account.id).first()
            
            if account_model:
                # 更新现有账户
                account_model.last_updated = account.last_updated
                account_model.updated_at = account.updated_at
            else:
                # 创建新账户
                account_model = AccountModel(
                    id=account.id,
                    exchange_id=account.exchange_id,
                    created_at=account.created_at,
                    updated_at=account.updated_at,
                    last_updated=account.last_updated,
                )
                session.add(account_model)
                session.flush()  # 确保获取到ID
            
            # 更新余额
            for currency, balance in account.balances.items():
                balance_model = session.query(BalanceModel).filter(
                    BalanceModel.account_id == account.id,
                    BalanceModel.currency == currency
                ).first()
                
                if balance_model:
                    # 更新现有余额
                    balance_model.free = balance.free
                    balance_model.used = balance.used
                    balance_model.total = balance.total
                    balance_model.updated_at = account.updated_at
                else:
                    # 创建新余额
                    balance_model = BalanceModel(
                        account_id=account.id,
                        currency=currency,
                        free=balance.free,
                        used=balance.used,
                        total=balance.total,
                        created_at=account.updated_at,
                        updated_at=account.updated_at,
                    )
                    session.add(balance_model)
    
    def find_by_id(self, account_id: str) -> Optional[Account]:
        """根据ID查找账户"""
        with self._db_manager.session() as session:
            account_model = session.query(AccountModel).filter(AccountModel.id == account_id).first()
            if not account_model:
                return None
            return self._to_domain_entity(account_model, session)
    
    def find_by_exchange_id(self, exchange_id: str) -> Optional[Account]:
        """根据交易所ID查找账户"""
        with self._db_manager.session() as session:
            account_model = session.query(AccountModel).filter(AccountModel.exchange_id == exchange_id).first()
            if not account_model:
                return None
            return self._to_domain_entity(account_model, session)
    
    def find_all(self) -> List[Account]:
        """查找所有账户"""
        with self._db_manager.session() as session:
            account_models = session.query(AccountModel).all()
            return [self._to_domain_entity(model, session) for model in account_models]
    
    def delete(self, account_id: str) -> bool:
        """删除账户"""
        with self._db_manager.session() as session:
            account_model = session.query(AccountModel).filter(AccountModel.id == account_id).first()
            if not account_model:
                return False
            session.delete(account_model)
            return True
    
    def _to_domain_entity(self, model: AccountModel, session: Session) -> Account:
        """将数据库模型转换为领域实体"""
        # 获取余额
        balance_models = session.query(BalanceModel).filter(BalanceModel.account_id == model.id).all()
        balances = {
            balance_model.currency: Balance(
                currency=balance_model.currency,
                free=balance_model.free,
                used=balance_model.used,
                total=balance_model.total
            )
            for balance_model in balance_models
        }
        
        # 创建账户实体
        account = Account(
            exchange_id=model.exchange_id,
            balances=balances,
            entity_id=model.id
        )
        
        # 设置账户属性
        account._created_at = model.created_at
        account._updated_at = model.updated_at
        account._last_updated = model.last_updated
        
        return account 