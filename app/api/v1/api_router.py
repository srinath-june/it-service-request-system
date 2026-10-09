from fastapi import APIRouter
from app.api.v1.endpoints import requests, users, categories, sla, reports

api_router = APIRouter()
api_router.include_router(requests.router)
api_router.include_router(users.router)
api_router.include_router(categories.router)
api_router.include_router(sla.router)
api_router.include_router(reports.router)
