from .recognize import router as recognize_router
from .result import router as result_router
from .manual import router as manual_router
from .user import router as user_router
from .inventory import router as inventory_router  # 新增

__all__ = ["recognize_router", "result_router", "manual_router", "user_router", "inventory_router"]