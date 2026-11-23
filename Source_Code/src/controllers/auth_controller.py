"""Authentication Controller handling login and logout routes (FR-01, SPR-01)."""
import time
from flask import Blueprint, redirect, render_template, request, session, url_for
from services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__)


def _dashboard_for_role(role: str):
    if role == "professor":
        return url_for("sessions.professor_dashboard")
    if role == "admin":
        return url_for("sessions.admin_logs")
    return url_for("checkin.student_scanner")


@auth_bp.route("/")
def index():
    if "user_id" in session:
        return redirect(_dashboard_for_role(session.get("role", "student")))
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    info = request.args.get("msg")

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        auth_service = AuthService()
        user, err = auth_service.authenticate(email, password, ip_address=request.remote_addr)
        if err or not user:
            error = err
        else:
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["full_name"] = user["full_name"]
            session["email"] = user["email"]
            session["role"] = user["role"]
            session["student_id"] = user.get("student_id")
            session["last_activity"] = time.time()
            return redirect(_dashboard_for_role(user["role"]))

    return render_template("login.html", error=error, info=info)


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login", msg="You have been logged out."))
