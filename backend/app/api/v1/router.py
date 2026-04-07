from fastapi import APIRouter
from app.api.v1 import auth, users, properties, revenues, expenses, categories, dashboard, audit


router = APIRouter(prefix="/v1")

router.include_router(auth.router)
router.include_router(users.router)
router.include_router(properties.router)
router.include_router(revenues.router)
router.include_router(expenses.router)
router.include_router(categories.router)
router.include_router(dashboard.router)
router.include_router(audit.router)
