"""
测试导入模块
"""

import sys
import os

# 打印Python路径
print("Python路径:")
for path in sys.path:
    print(f"  - {path}")

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
    print(f"\n已添加当前目录到Python路径: {current_dir}")

# 尝试导入lightquant包
try:
    import lightquant
    print(f"\n成功导入lightquant包")
    
    # 尝试导入风险管理模块
    try:
        from lightquant.domain.risk_management import RiskManager
        print(f"成功导入RiskManager")
        
        # 尝试导入订单模块
        try:
            from lightquant.domain.models.order import Order
            print(f"成功导入Order")
        except ImportError as e:
            print(f"导入Order失败: {e}")
    except ImportError as e:
        print(f"导入RiskManager失败: {e}")
except ImportError as e:
    print(f"\n导入lightquant包失败: {e}") 