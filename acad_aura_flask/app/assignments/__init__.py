from flask import Blueprint

assignments_bp = Blueprint(
    "assignments",
    __name__,
    template_folder="templates/assignments",
    static_folder="../../static"
)

from . import routes
