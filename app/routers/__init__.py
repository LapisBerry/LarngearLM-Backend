from .resources import router as resources_router
from .generate import router as generate_router
from .notes import router as notes_router
from .lms import router as lms_router

__all__ = ["resources_router", "generate_router", "notes_router", "lms_router"]
