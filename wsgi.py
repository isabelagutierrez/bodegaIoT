"""Punto de entrada para gunicorn: `gunicorn --preload wsgi:app`."""
from app.main import create_app, create_tables

app = create_app()
create_tables(app)  # Fase 1: crea las tablas una sola vez (--preload: antes de lanzar los workers)
app.extensions["engine"].dispose()  # no heredar conexiones abiertas en los workers (fork)
