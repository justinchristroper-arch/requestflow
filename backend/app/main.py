from contextlib import asynccontextmanager
import logging
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config import Settings
from app.database import create_database
from app.api.auth import router as auth_router
from app.api.requests import router as request_router
from app.api.analytics import router as analytics_router


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str = "requestflow-api"


class ReadyResponse(HealthResponse):
    database: Literal["connected"] = "connected"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    engine, session_factory = create_database(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        engine.dispose()

    app = FastAPI(title="RequestFlow API", version="1.0.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Content-Type", "Authorization"],
    )
    app.include_router(auth_router)
    app.include_router(request_router)
    app.include_router(analytics_router)

    @app.middleware("http")
    async def private_response_headers(request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        # FastAPI's default errors include submitted input (possibly a password).
        errors = [{"loc": error["loc"], "msg": error["msg"], "type": error["type"]} for error in exc.errors()]
        return JSONResponse(status_code=422, content={"detail": errors})

    @app.exception_handler(Exception)
    async def unexpected_error(request, exc):
        logging.getLogger("requestflow").error("Unhandled API error", exc_info=exc)
        return JSONResponse(status_code=500, content={"detail": "The service could not complete your request. Please try again."},
                            headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer"})

    @app.get("/api/health", response_model=HealthResponse, tags=["Health"])
    def health():
        return HealthResponse()

    @app.get("/api/health/ready", response_model=ReadyResponse, tags=["Health"])
    def ready():
        try:
            with app.state.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except SQLAlchemyError:
            raise HTTPException(status_code=503, detail="Database unavailable") from None
        return ReadyResponse()

    return app


app = create_app()
