from flask import (
    render_template, request, redirect, url_for, flash, jsonify
)
from flask_login import login_required, current_user
from datetime import date, datetime
from . import attendance_bp
from ..extensions import db
from ..models import User, Attendance

# Role checks
def faculty_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "faculty":
            flash("Faculty access required.", "danger")
            return redirect(url_for("auth.login"))
        return fn(*args, **kwargs)
    return wrapper

def student_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "student":
            flash("Student access required.", "danger")
            return redirect(url_for("auth.login"))
        return fn(*args, **kwargs)
    return wrapper


# -----------------------
# Faculty: list students (to mark)
# -----------------------
@attendance_bp.route("/faculty/mark", methods=["GET"])
@login_required
@faculty_required
def mark_index():
    # show form to choose subject and date
    # We'll display all students to mark for a subject
    students = User.query.filter_by(role="student").order_by(User.name).all()
    return render_template("attendance/mark_index.html", students=students, today=date.today())


# -----------------------
# Faculty: submit attendance for a date & subject
# -----------------------
@attendance_bp.route("/faculty/mark", methods=["POST"])
@login_required
@faculty_required
def submit_mark():
    subject = request.form.get("subject").strip()
    session_date = request.form.get("date")
    if not session_date:
        flash("Date is required", "danger")
        return redirect(url_for("attendance.mark_index"))
    try:
        session_date_obj = datetime.strptime(session_date, "%Y-%m-%d").date()
    except Exception:
        flash("Invalid date format", "danger")
        return redirect(url_for("attendance.mark_index"))

    # present_ids is list of student_id strings for present students
    present_ids = request.form.getlist("present")
    # Mark each student for this date; if entry exists update it
    all_students = User.query.filter_by(role="student").all()

    for student in all_students:
        status = "present" if str(student.id) in present_ids else "absent"
        # avoid duplicate: check existing
        att = Attendance.query.filter_by(
            student_id=student.id,
            subject=subject,
            date=session_date_obj
        ).first()
        if att:
            att.status = status
        else:
            att = Attendance(
                student_id=student.id,
                subject=subject,
                date=session_date_obj,
                status=status
            )
            db.session.add(att)
    db.session.commit()
    flash("Attendance saved for " + session_date, "success")
    return redirect(url_for("attendance.mark_index"))


# -----------------------
# Faculty: view attendance report for a subject / date range
# -----------------------
@attendance_bp.route("/faculty/report", methods=["GET", "POST"])
@login_required
@faculty_required
def faculty_report():
    students = User.query.filter_by(role="student").order_by(User.name).all()
    report = None
    subject = None
    start = None
    end = None
    if request.method == "POST":
        subject = request.form.get("subject").strip()
        start = request.form.get("start_date")
        end = request.form.get("end_date")
        try:
            start_date = datetime.strptime(start, "%Y-%m-%d").date() if start else None
            end_date = datetime.strptime(end, "%Y-%m-%d").date() if end else None
        except Exception:
            flash("Invalid dates", "danger")
            return redirect(url_for("attendance.faculty_report"))

        # Build report per student
        report = []
        for s in students:
            q = Attendance.query.filter_by(student_id=s.id, subject=subject)
            if start_date:
                q = q.filter(Attendance.date >= start_date)
            if end_date:
                q = q.filter(Attendance.date <= end_date)
            total = q.count()
            present = q.filter_by(status="present").count()
            absent = q.filter_by(status="absent").count()
            percent = (present / total * 100) if total > 0 else None
            report.append({
                "student": s,
                "total": total,
                "present": present,
                "absent": absent,
                "percent": round(percent,2) if percent is not None else None
            })
    return render_template("attendance/faculty_report.html", students=students, report=report, subject=subject, start=start, end=end)


# -----------------------
# Student: view attendance summary (per-subject)
# -----------------------
@attendance_bp.route("/student/summary")
@login_required
@student_required
def student_summary():
    # get distinct subjects the student has attendance records for
    rows = db.session.query(Attendance.subject).filter_by(student_id=current_user.id).distinct().all()
    subjects = [r[0] for r in rows]
    summary = []
    for subj in subjects:
        q = Attendance.query.filter_by(student_id=current_user.id, subject=subj)
        total = q.count()
        present = q.filter_by(status="present").count()
        absent = q.filter_by(status="absent").count()
        percent = (present / total * 100) if total > 0 else None
        summary.append({
            "subject": subj,
            "total": total,
            "present": present,
            "absent": absent,
            "percent": round(percent,2) if percent is not None else None
        })
    return render_template("attendance/student_summary.html", summary=summary)


# -----------------------
# Small JSON API for calendar events (attendance history)
# -----------------------
@attendance_bp.route("/api/events")
@login_required
def attendance_events():
    # returns attendance entries for current user (student) as events
    events = []
    if current_user.role == "student":
        rows = Attendance.query.filter_by(student_id=current_user.id).all()
        for r in rows:
            events.append({
                "title": f"{r.subject}: {r.status}",
                "start": r.date.isoformat()
            })
    elif current_user.role == "faculty":
        # faculty can view events for subjects they teach (here we simply return all attendance dates)
        rows = Attendance.query.order_by(Attendance.date.desc()).limit(500).all()
        for r in rows:
            events.append({
                "title": f"{r.subject} - {r.status} (S:{r.student_id})",
                "start": r.date.isoformat()
            })
    return jsonify(events)
