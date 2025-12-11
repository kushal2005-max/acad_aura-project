import os
import zipfile
from flask import (
    render_template, request, redirect, url_for, flash,
    send_from_directory, current_app
)
from flask_login import login_required, current_user
from datetime import datetime
from . import assignments_bp
from ..extensions import db
from ..models import Assignment, Submission, User


# --------------- HELPER ---------------
def faculty_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "faculty":
            flash("Faculty access required.", "danger")
            return redirect(url_for("auth.login"))
        return fn(*args, **kwargs)
    return wrapper


# --------------- VIEW ASSIGNMENT DETAILS ---------------
@assignments_bp.route("/<int:aid>")
@login_required
def view_assignment(aid):
    assignment = Assignment.query.get_or_404(aid)
    submissions = Submission.query.filter_by(assignment_id=aid).all()
    return render_template(
        "assignments/view_assignment.html",
        assignment=assignment,
        submissions=submissions
    )


# --------------- FACULTY: GRADE A SUBMISSION ---------------
@assignments_bp.route("/grade/<int:sid>", methods=["POST"])
@login_required
@faculty_required
def grade_submission(sid):
    marks = request.form.get("marks")
    remark = request.form.get("remark")

    sub = Submission.query.get_or_404(sid)
    sub.marks = int(marks)
    sub.remark = remark
    db.session.commit()

    flash("Marks updated.", "success")
    return redirect(url_for("assignments.view_assignment", aid=sub.assignment_id))


# --------------- FACULTY: DOWNLOAD SINGLE PDF ---------------
@assignments_bp.route("/download/<filename>")
@login_required
def download_pdf(filename):
    pdf_dir = current_app.config.get("PDF_FOLDER", "uploads/pdf")
    return send_from_directory(pdf_dir, filename, as_attachment=True)


# --------------- FACULTY: DOWNLOAD ALL PDFs AS ZIP ---------------
@assignments_bp.route("/download-all/<int:aid>")
@login_required
@faculty_required
def download_all(aid):
    pdf_dir = current_app.config.get("PDF_FOLDER", "uploads/pdf")
    zip_name = f"assignment_{aid}_submissions.zip"
    zip_path = os.path.join(pdf_dir, zip_name)

    # Create ZIP
    submissions = Submission.query.filter_by(assignment_id=aid).all()

    with zipfile.ZipFile(zip_path, "w") as zipf:
        for sub in submissions:
            if sub.pdf_filename:
                file_path = os.path.join(pdf_dir, sub.pdf_filename)
                if os.path.exists(file_path):
                    zipf.write(file_path, arcname=sub.pdf_filename)

    return send_from_directory(pdf_dir, zip_name, as_attachment=True)
