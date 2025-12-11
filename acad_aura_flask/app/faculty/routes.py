from flask import (
    render_template, request, redirect, url_for, flash
)
from flask_login import login_required, current_user
from datetime import datetime
from . import faculty_bp
from ..extensions import db
from ..models import Assignment, Submission


# ---- FACULTY ROLE CHECK ----
def faculty_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "faculty":
            flash("Faculty access required.", "danger")
            return redirect(url_for("auth.login"))
        return fn(*args, **kwargs)
    return wrapper


# ---- DASHBOARD ----
@faculty_bp.route("/dashboard")
@login_required
@faculty_required
def dashboard():
    total_assignments = Assignment.query.filter_by(faculty_id=current_user.id).count()
    total_submissions = Submission.query.join(Assignment).filter(
        Assignment.faculty_id == current_user.id
    ).count()

    return render_template(
        "faculty/dashboard.html",
        total_assignments=total_assignments,
        total_submissions=total_submissions
    )


# ---- CREATE ASSIGNMENT ----
@faculty_bp.route("/assignment/create", methods=["GET", "POST"])
@login_required
@faculty_required
def create_assignment():
    if request.method == "POST":
        subject = request.form.get("subject").strip()
        title = request.form.get("title").strip()
        description = request.form.get("description").strip()
        start_time = request.form.get("start_datetime")
        end_time = request.form.get("end_datetime")

        assignment = Assignment(
            faculty_id=current_user.id,
            subject=subject,
            title=title,
            description=description,
            start_datetime=datetime.fromisoformat(start_time),
            end_datetime=datetime.fromisoformat(end_time)
        )

        db.session.add(assignment)
        db.session.commit()

        flash("Assignment created successfully!", "success")
        return redirect(url_for("faculty.dashboard"))

    return render_template("faculty/create_assignment.html")


# ---- VIEW ALL ASSIGNMENTS ----
@faculty_bp.route("/assignments")
@login_required
@faculty_required
def list_assignments():
    assigns = Assignment.query.filter_by(faculty_id=current_user.id).order_by(
        Assignment.created_at.desc()
    ).all()
    return render_template("faculty/assignments.html", assignments=assigns)


# ---- VIEW SUBMISSIONS FOR AN ASSIGNMENT ----
@faculty_bp.route("/assignment/<int:aid>/submissions")
@login_required
@faculty_required
def view_submissions(aid):
    subs = Submission.query.filter_by(assignment_id=aid).order_by(
        Submission.submitted_at.desc()
    ).all()
    return render_template("faculty/submissions.html", submissions=subs)
