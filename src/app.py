from fastapi import FastAPI

from routes.auth import create_router as create_auth_router
from routes.dashboard import create_router as create_dashboard_router
from routes.plants import create_router as create_plants_router
from routes.system import create_router as create_system_router


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(create_system_router())
    app.include_router(create_auth_router())
    app.include_router(create_dashboard_router())
    app.include_router(create_plants_router())
    return app
