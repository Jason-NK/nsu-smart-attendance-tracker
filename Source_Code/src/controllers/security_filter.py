"""Server-side Role & Session Security Filter (SPR-01, SPR-02, SPR-06)."""
import time
from functools import wraps
from flask import redirect, render_template, request, session, url_for
from services.log_service import LogService

SESSION_IDLE_TIMEOUT_SECONDS = 20 * 60  # 20 minutes (SPR-06)


def check_session_timeout() -> bool:
    """Checks if a logged-in session has been idle for more than 20 minutes."""
    if "user_id" not in session:
        return False

    now = time.time()
    last_activity = session.get("last_activity")
    if last_activity is not None and (now - float(last_activity)) > SESSION_IDLE_TIMEOUT_SECONDS:
        session.clear()
        return True

    session["last_activity"] = now
    return False


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if check_session_timeout():
            return redirect(url_for("auth.login", msg="Session timed out after 20 minutes of inactivity. Please log in again."))
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)

    return wrapped


def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if check_session_timeout():
                return redirect(url_for("auth.login", msg="Session timed out after 20 minutes of inactivity. Please log in again."))
            if "user_id" not in session:
                return redirect(url_for("auth.login"))
            user_role = session.get("role")
            if user_role not in allowed_roles:
                LogService().log_event(
                    "UNAUTHORIZED_ACCESS",
                    f"Role '{user_role}' attempted to access restricted route {request.path}",
                    email=session.get("email"),
                    ip_address=request.remote_addr,
                )
                return (
                    render_template(
                        "error.html",
                        title="Access Denied",
                        message="Access Denied. You do not have permission to view this page.",
                    ),
                    403,
                )
            return view_func(*args, **kwargs)

        return wrapped

    return decorator
