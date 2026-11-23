"""Main Flask application entrypoint for NSU Smart Attendance Tracker."""
import os
import sys
from pathlib import Path
from typing import Optional

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from dotenv import load_dotenv
from flask import Flask, render_template

from controllers.auth_controller import auth_bp
from controllers.checkin_controller import checkin_bp
from controllers.session_controller import session_bp
from repositories.db import ensure_database_initialized


def create_app(test_config: Optional[dict] = None) -> Flask:
    load_dotenv()
    app = Flask(__name__, template_folder=str(SRC_DIR / "views"))

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-in-env-file")
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    if test_config:
        app.config.update(test_config)

    ensure_database_initialized(seed=True)

    app.register_blueprint(auth_bp)
    app.register_blueprint(session_bp)
    app.register_blueprint(checkin_bp)

    @app.errorhandler(404)
    def not_found(_err):
        return (
            render_template(
                "error.html",
                title="Page Not Found",
                message="The page you requested could not be found.",
            ),
            404,
        )

    @app.errorhandler(500)
    def server_error(_err):
        return (
            render_template(
                "error.html",
                title="Something Went Wrong",
                message="We ran into an unexpected problem. Please try again or contact NSU IT Support.",
            ),
            500,
        )

    return app


if __name__ == "__main__":
    application = create_app()
    debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    application.run(host="127.0.0.1", port=5000, debug=debug_mode)
