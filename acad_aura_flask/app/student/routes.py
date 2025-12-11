import os
from flask import (
    render_template, request, redirect, url_for, flash, current_app, send_from_directory
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
from . import student_bp
from ..extensions import db
from ..models import Assignment, Submission, User
from ..utils.convert_file_to_pdf import convert_to_pdf

ALLOWED_EXT = {"doc", "docx", "ppt", "pptx", "xls", "xlsx", "txt", "csv", "pdf", "png", "jpg", "jpeg", "bmp"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


@student_bp.route("/dashboard")
@login_required
def dashboard():
    # student dashboard summary
    # count active assignments that are within start and end date
    now = datetime.utcnow()
    active_assignments = Assignment.query.filter(
        Assignment.start_datetime <= now, Assignment.end_datetime >= now
    ).order_by(Assignment.end_datetime.asc()).all()
    total_submitted = Submission.query.filter_by(student_id=current_user.id).count()
    return render_template("student/dashboard.html", assignments=active_assignments, total_submitted=total_submitted)


@student_bp.route("/assignments")
@login_required
def assignments_list():
    # show assignments (active + upcoming)
    now = datetime.utcnow()
    assigns = Assignment.query.order_by(Assignment.start_datetime.desc()).all()
    return render_template("student/assignments.html", assignments=assigns)


@student_bp.route("/assignment/<int:aid>/submit", methods=["GET", "POST"])
@login_required
def submit_assignment(aid):
    assignment = Assignment.query.get_or_404(aid)

    # check if within window (optional allow late but mark late)
    now = datetime.utcnow()
    is_open = (assignment.start_datetime is None or assignment.start_datetime <= now)
    # deadline passed?
    deadline_passed = (assignment.end_datetime is not None and assignment.end_datetime < now)

    if request.method == "POST":
        file = request.files.get("file")
        if not file or file.filename == "":
            flash("Please choose a file to upload.", "danger")
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash("File type not allowed.", "danger")
            return redirect(request.url)

        filename = secure_filename(file.filename)
        upload_dir = current_app.config.get("UPLOAD_FOLDER", "uploads")
        pdf_dir = current_app.config.get("PDF_FOLDER", os.path.join(upload_dir, "pdf"))

        os.makedirs(upload_dir, exist_ok=True)
        os.makedirs(pdf_dir, exist_ok=True)

        # Save original
        base_name = f"{current_user.id}_{int(datetime.utcnow().timestamp())}_{filename}"
        original_path = os.path.join(upload_dir, base_name)
        file.save(original_path)

        # Build desired pdf filename: {student_name}_{regno}_{assignment_title}.pdf
        student_name = (current_user.name or "student").replace(" ", "_")
        regno = (current_user.regno or str(current_user.id)).replace(" ", "_")
        assignment_title = (assignment.title or "assignment").replace(" ", "_")
        pdf_filename = f"{student_name}_{regno}_{assignment_title}.pdf"
        pdf_path = os.path.join(pdf_dir, pdf_filename)

        # Convert to PDF
        try:
            convert_to_pdf(original_path, pdf_path)
        except Exception as e:
            flash(f"Conversion failed: {e}", "danger")
            # optionally keep original file for admin review
            return redirect(request.url)

        # Save submission record
        sub = Submission(
            assignment_id=assignment.id,
            student_id=current_user.id,
            original_filename=filename,
            pdf_filename=pdf_filename,
            submitted_at=datetime.utcnow(),
            status="submitted" if not deadline_passed else "late"
        )
        db.session.add(sub)
        db.session.commit()

        flash("Assignment submitted successfully.", "success")
        return redirect(url_for("student.submissions"))

    return render_template(
        "student/submit_assignment.html",
        assignment=assignment,
        is_open=is_open,
        deadline_passed=deadline_passed
    )


@student_bp.route("/submissions")
@login_required
def submissions():
    subs = Submission.query.filter_by(student_id=current_user.id).order_by(Submission.submitted_at.desc()).all()
    return render_template("student/submissions.html", submissions=subs)


# Serve PDF files (optional: served from static in production; this is a helper)
@student_bp.route("/pdf/<path:filename>")
@login_required
def serve_pdf(filename):
    pdf_dir = current_app.config.get("PDF_FOLDER", "uploads/pdf")
    return send_from_directory(pdf_dir, filename)
