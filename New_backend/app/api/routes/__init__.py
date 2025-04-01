from fastapi import APIRouter
from .scanner_routes import router as scanner_router
from .report_routes import router as report_router

# Main API router
router = APIRouter()

# Include scanner router
router.include_router(scanner_router, prefix="/scanner", tags=["scanner"])

# Include report router
router.include_router(report_router, prefix="/reports", tags=["reports"]) 