from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.routes.auth_routes import router as auth_router
from app.routes.games_routes import router as game_router
from app.routes.players_routes import router as players_router
from app.routes.events_routes import router as events_router
from app.routes.routes import router as system_router


def create_app() -> FastAPI:
    setup_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.debug_enabled,
    )

    cors_origins = settings.cors_origins_list
    allow_all_origins = not cors_origins

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins or ["*"],
        allow_origin_regex=settings.cors_origin_regex,
        allow_credentials=not allow_all_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(players_router)
    app.include_router(system_router)
    app.include_router(events_router)
    app.include_router(game_router)
    return app


app = create_app()
