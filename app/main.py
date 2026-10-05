from flask import Flask, jsonify, render_template
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException

from .database import WAREHOUSE_ID, Base, init_db, make_engine
from .errors import ApiError
from .routers import inventory, products


def create_app(engine=None) -> Flask:
    app = Flask(__name__)
    app.json.sort_keys = False
    engine = engine or make_engine()
    init_db(app, engine)

    app.register_blueprint(products.bp)
    app.register_blueprint(inventory.bp)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/")
    def index():
        return render_template("index.html", warehouse_id=WAREHOUSE_ID)

    @app.errorhandler(ApiError)
    def handle_api_error(e: ApiError):
        return jsonify(detail=e.detail), e.status_code

    @app.errorhandler(ValidationError)
    def handle_validation(e: ValidationError):
        return jsonify(detail=e.errors(include_url=False, include_context=False)), 422

    @app.errorhandler(HTTPException)
    def handle_http(e: HTTPException):
        return jsonify(detail=e.description), e.code

    return app


def create_tables(app: Flask) -> None:
    Base.metadata.create_all(bind=app.extensions["engine"])
