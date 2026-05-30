from .manual import router as manual_router
from .simulation import router as simulation_router
from .view import router as view_router

__all__ = ["manual_router", "simulation_router", "view_router"]
