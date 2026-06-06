from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import create_tables
from app.api.routers import auth, telemetria, indice, incentivos, auditor, reportes


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


app = FastAPI(
    title="CIAS — Sistema Telemático de Gestión del Riesgo Asegurador",
    version="1.0.0",
    description="TFG Lucas V. Cassina · Universidad Siglo 21 · Ingeniería en Software",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(telemetria.router)
app.include_router(indice.router)
app.include_router(incentivos.router)
app.include_router(auditor.router)
app.include_router(reportes.router)


@app.get("/health", tags=["sistema"])
async def health():
    return {"status": "ok", "sistema": "CIAS", "version": "1.0.0"}
