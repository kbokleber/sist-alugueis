from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.api.v1.router import router as api_v1_router
from app.database import init_db, ensure_property_code_column, ensure_revenue_pending_amount_column


app = FastAPI(
    title="Sistema de Controle de Aluguéis",
    description="API REST para controle financeiro de imóveis alugados por temporada",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

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
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "code": "INTERNAL_ERROR"},
    )


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/health/ready")
async def readiness_check():
    return {"status": "ready"}


@app.on_event("startup")
async def startup_event():
    await init_db()
    await ensure_property_code_column()
    await ensure_revenue_pending_amount_column()


# Mount API
app.include_router(api_v1_router, prefix="/api")
