import logging
import time
import uuid

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.api.v1.router import router as api_v1_router
from app.database import (
    init_db,
    ensure_property_code_column,
    ensure_property_image_url_column,
    ensure_revenue_pending_amount_column,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("app.main")

app = FastAPI(
    title="Sistema de Controle de Aluguéis",
    description="API REST para controle financeiro de imóveis alugados por temporada",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    start_time = time.perf_counter()

    logger.info(
        "request_started request_id=%s method=%s path=%s client=%s",
        request_id,
        request.method,
        request.url.path,
        request.client.host if request.client else "-",
    )

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.exception(
            "request_failed request_id=%s method=%s path=%s duration_ms=%s",
            request_id,
            request.method,
            request.url.path,
            duration_ms,
        )
        raise

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request_finished request_id=%s method=%s path=%s status_code=%s duration_ms=%s",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "unhandled_exception method=%s path=%s error=%s",
        request.method,
        request.url.path,
        exc,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "code": "INTERNAL_ERROR"},
    )


@app.get("/health")
async def health_check():
    logger.info("health_check status=healthy app_env=%s", settings.app_env)
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/health/ready")
async def readiness_check():
    return {"status": "ready"}


@app.on_event("startup")
async def startup_event():
    logger.info(
        "startup_begin app_env=%s is_production=%s database=%s",
        settings.app_env,
        settings.is_production,
        settings.database_url.split("@")[-1],
    )
    # Production: schema vem só do Alembic (docker entrypoint). Evita 4 workers do Gunicorn
    # rodando create_all + ALTER em paralelo no Postgres (locks / startup lento → 504 no proxy).
    if settings.is_production:
        logger.info("startup_skip_dev_db_init reason=production")
        return
    await init_db()
    await ensure_property_code_column()
    await ensure_property_image_url_column()
    await ensure_revenue_pending_amount_column()
    logger.info("startup_complete dev_db_ready=true")


app.include_router(api_v1_router, prefix="/api")
