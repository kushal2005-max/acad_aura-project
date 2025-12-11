from flask import Blueprint

attendance_bp = Blueprint(
    "attendance",
    __name__,
    template_folder="templates/attendance",
    static_folder="../../static"
)

from . import routes  # noqa: F401
