from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers.auth import router as auth_router
from app.routers.signals import router as signals_router
from app.routers.webhooks import router as webhooks_router
from app.routers.analytics import router as analytics_router
from app.routers.api_keys import router as api_keys_router
from app.routers.subscriptions import router as subscriptions_router
from app.routers.websocket import router as websocket_router
from app.routers.admin import router as admin_router
from app.routers.broker import router as broker_router
from app.routers.markets import router as markets_router

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Trading signal generation, distribution, and analytics API",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(signals_router)
app.include_router(webhooks_router)
app.include_router(analytics_router)
app.include_router(api_keys_router)
app.include_router(subscriptions_router)
app.include_router(websocket_router)
app.include_router(admin_router)
app.include_router(broker_router)
app.include_router(markets_router)


@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.app_name}", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
