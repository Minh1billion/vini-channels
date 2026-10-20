from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from vinichannels.adapters.inbound.http.error_handlers import register_error_handlers
from vinichannels.adapters.inbound.http.routers import (
    analytics,
    audit,
    auth,
    channels,
    notifications,
    partners,
    providers,
    reports,
    scoring,
    search,
    sync,
    users,
    videos,
)
from vinichannels.adapters.inbound.http.wiring import Hook, HttpConfig, UseCases


def create_app(
    use_cases: UseCases,
    config: HttpConfig,
    on_startup: Hook | None = None,
    on_shutdown: Hook | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        if on_startup is not None:
            await on_startup()
        try:
            yield
        finally:
            if on_shutdown is not None:
                await on_shutdown()

    app = FastAPI(title="ViniChannels", version="0.1.0", lifespan=lifespan)
    app.state.use_cases = use_cases
    app.state.config = config

    if config.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(config.cors_origins),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    register_error_handlers(app)

    api = APIRouter(prefix="/api/v1")
    modules = (
        auth,
        users,
        partners,
        channels,
        videos,
        analytics,
        providers,
        scoring,
        reports,
        notifications,
        search,
        sync,
        audit,
    )
    for module in modules:
        api.include_router(module.router)
    app.include_router(api)

    @app.get("/healthz", include_in_schema=False)
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app
