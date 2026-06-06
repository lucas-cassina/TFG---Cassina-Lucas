from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from .config import settings


def _get_async_url(url: str) -> str:
    """Convierte postgresql:// → postgresql+asyncpg:// para SQLAlchemy async."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


engine = create_async_engine(
    _get_async_url(settings.DATABASE_URL),
    echo=False,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def create_tables():
    async with engine.begin() as conn:
        from app.models import conductor, auditor, poliza, sesion_conduccion  # noqa
        from app.models import evento_telemetrico, indice_riesgo, alerta_conduccion  # noqa
        from app.models import incentivo, recompensa  # noqa
        await conn.run_sync(Base.metadata.create_all)
