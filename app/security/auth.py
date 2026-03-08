from functools import wraps
from flask import session, redirect, url_for, abort


ROLE_PERMISSIONS = {
    "ADMIN": "*",
    "FACTURADOR": [
        "dashboard",
        "patients",
        "services",
        "claims",
        "snapshots",
        "finances",
        "events",
        "reports",
    ],
    "RECEPCION": [
        "dashboard",
        "patients",
        "services",
        "claims",
    ],
    "DRA": [
        "dashboard",
        "claims",
        "snapshots",
    ],
}


def login_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("login"))

        return route_function(*args, **kwargs)

    return wrapper


def role_required(*allowed_roles):

    def decorator(route_function):

        @wraps(route_function)
        def wrapper(*args, **kwargs):

            role = session.get("role")

            if role is None:
                return redirect(url_for("login"))

            if role not in allowed_roles:
                abort(403)

            return route_function(*args, **kwargs)

        return wrapper

    return decorator