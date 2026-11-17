import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import create_tables, AsyncSessionLocal
from app.services.tokens import limpiar_tokens_expirados
from app.api.routers import auth, telemetria, indice, incentivos, auditor, reportes, conductor


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    async with AsyncSessionLocal() as db:
        await limpiar_tokens_expirados(db)

    async def _cleanup_loop():
        """Limpieza horaria de tokens revocados expirados."""
        while True:
            await asyncio.sleep(3600)
            try:
                async with AsyncSessionLocal() as db:
                    await limpiar_tokens_expirados(db)
            except Exception:
                pass

    cleanup_task = asyncio.create_task(_cleanup_loop())
    yield
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="CIAS — Sistema Telemático de Gestión del Riesgo Asegurador",
    version="1.0.0",
    description="TFG Lucas V. Cassina · Universidad Siglo 21 · Ingeniería en Software",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # B1: usa la config en vez de wildcard hardcodeado
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(telemetria.router)
app.include_router(indice.router)
app.include_router(incentivos.router)
app.include_router(conductor.router)
app.include_router(auditor.router)
app.include_router(reportes.router)


@app.get("/health", tags=["sistema"])
async def health():
    return {"status": "ok", "sistema": "CIAS", "version": "1.0.0"}
