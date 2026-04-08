from fastapi import FastAPI

from routes.auth import router as auth_router
from routes.dashboard import router as dashboard_router
from routes.plants import router as plants_router
from routes.system import router as system_router


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(system_router)
    app.include_router(auth_router)
    app.include_router(dashboard_router)
    app.include_router(plants_router)
    return app


app = create_app()
