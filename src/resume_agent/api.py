import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import uuid4

import structlog
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from resume_agent import __version__
from resume_agent.config import get_settings
from resume_agent.logging import configure_logging
from resume_agent.metrics import REQUEST_COUNT, REQUEST_LATENCY
from resume_agent.models import ErrorResponse, HealthResponse, ResumeRequest, ResumeResponse
from resume_agent.orchestrator import ResumeOrchestrator
from resume_agent.providers import OllamaProvider
from resume_agent.security import InMemoryRateLimiter, rate_limit_dependency

settings = get_settings()
configure_logging(settings.log_level)
logger = structlog.get_logger()
provider = (
    OllamaProvider(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        timeout_seconds=settings.ollama_timeout_seconds,
    )
    if settings.ai_provider == "ollama"
    else None
)
orchestrator = ResumeOrchestrator(
    provider=provider, allow_fallback=settings.allow_deterministic_fallback
)
limiter = InMemoryRateLimiter(settings.rate_limit_requests, settings.rate_limit_window_seconds)
enforce_rate_limit = rate_limit_dependency(limiter)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await logger.ainfo("service_started", version=__version__, environment=settings.environment)
    yield
    await logger.ainfo("service_stopped")


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    summary="Secure multi-agent resume generation and ATS optimization API",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
    lifespan=lifespan,
)


@app.middleware("http")
async def request_context(request: Request, call_next):  # type: ignore[no-untyped-def]
    request_id = request.headers.get("X-Request-ID", str(uuid4()))[:128]
    request.state.request_id = request_id
    started = time.perf_counter()
    content_length = int(request.headers.get("content-length", "0") or 0)
    if content_length > settings.max_request_bytes:
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={
                "error": {
                    "code": "REQUEST_TOO_LARGE",
                    "message": "Request body is too large",
                    "request_id": request_id,
                }
            },
        )
    try:
        response = await call_next(request)
    except Exception:
        await logger.aexception("unhandled_error", request_id=request_id, path=request.url.path)
        response = JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An internal error occurred",
                    "request_id": request_id,
                }
            },
        )
    elapsed = time.perf_counter() - started
    route = request.scope.get("route")
    path = getattr(route, "path", request.url.path)
    REQUEST_COUNT.labels(method=request.method, path=path, status=response.status_code).inc()
    REQUEST_LATENCY.labels(method=request.method, path=path).observe(elapsed)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Cache-Control"] = "no-store"
    await logger.ainfo(
        "request_completed",
        request_id=request_id,
        method=request.method,
        path=path,
        status=response.status_code,
        duration_ms=round(elapsed * 1000, 2),
    )
    return response


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, _: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "request_id": getattr(request.state, "request_id", "unknown"),
            }
        },
    )


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
    code_by_status = {
        401: "UNAUTHORIZED",
        413: "REQUEST_TOO_LARGE",
        429: "RATE_LIMITED",
    }
    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers,
        content={
            "error": {
                "code": code_by_status.get(exc.status_code, "HTTP_ERROR"),
                "message": str(exc.detail),
                "request_id": getattr(request.state, "request_id", "unknown"),
            }
        },
    )


@app.get("/health", response_model=HealthResponse, tags=["Operations"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__)


@app.get("/ready", response_model=HealthResponse, tags=["Operations"])
async def ready() -> HealthResponse:
    return HealthResponse(status="ready", version=__version__)


@app.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post(
    "/v1/resumes/generate",
    response_model=ResumeResponse,
    responses={
        401: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
    },
    dependencies=[Depends(enforce_rate_limit)],
    tags=["Resumes"],
)
async def generate_resume(payload: ResumeRequest, request: Request) -> ResumeResponse:
    return await orchestrator.generate(payload, request.state.request_id)
