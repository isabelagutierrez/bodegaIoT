import os

from flask import g
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://warehouse:warehouse@localhost:5432/warehouse",
)
WAREHOUSE_ID = os.getenv("WAREHOUSE_ID", "WH-001")


class Base(DeclarativeBase):
    pass


def make_engine(url: str = DATABASE_URL, **kwargs):
    return create_engine(url, pool_pre_ping=True, **kwargs)


def init_db(app, engine):
    """Registra el engine en la app y abre/cierra una sesión por request (g.db)."""
    app.extensions["engine"] = engine
    session_factory = sessionmaker(bind=engine, autoflush=False)

    @app.before_request
    def _open_session():
        g.db = session_factory()

    @app.teardown_request
    def _close_session(exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()


def get_db():
    return g.db
