from flask import (
    render_template, request, redirect, url_for, flash, jsonify
)
from flask_login import login_required, current_user
from datetime import datetime
from . import calendar_bp
from ..extensions import db
from ..models import CalendarEvent, Assignment, Attendance


# --------- ALL USERS CAN SEE CALENDAR ---------
@calendar_bp.route("/")
@login_required
def view_calendar():
    return render_template("calendar/calendar.html")


# --------- ADMIN & FACULTY CAN ADD EVENTS ---------
@calendar_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_event():
    if current_user.role not in ("faculty", "admin"):
        flash("Only faculty/admin can create calendar events.", "danger")
        return redirect(url_for("calendar.view_calendar"))

    if request.method == "POST":
        title = request.form.get("title")
        desc = request.form.get("description")
        start = request.form.get("start_datetime")
        end = request.form.get("end_datetime")

        event = CalendarEvent(
            title=title,
            description=desc,
            start_datetime=datetime.fromisoformat(start),
            end_datetime=datetime.fromisoformat(end),
            created_by=current_user.id
        )

        db.session.add(event)
        db.session.commit()
        flash("Event added!", "success")
        return redirect(url_for("calendar.view_calendar"))

    return render_template("calendar/add_event.html")


# --------- JSON EVENTS FEED FOR FULLCALENDAR ---------
@calendar_bp.route("/api/events")
@login_required
def calendar_events():
    events = []

    # BASIC EVENTS (admin/faculty created)
    evs = CalendarEvent.query.all()
    for e in evs:
        events.append({
            "title": e.title,
            "start": e.start_datetime.isoformat(),
            "end": e.end_datetime.isoformat(),
            "color": "#0d6efd"
        })

    # ASSIGNMENT DEADLINES (for everyone)
    assigns = Assignment.query.all()
    for a in assigns:
        events.append({
            "title": f"Deadline: {a.title}",
            "start": a.end_datetime.isoformat(),
            "color": "#dc3545"
        })

    # STUDENT ATTENDANCE (student only)
    if current_user.role == "student":
        atts = Attendance.query.filter_by(student_id=current_user.id).all()
        for a in atts:
            color = "#28a745" if a.status == "present" else "#dc3545"
            events.append({
                "title": f"{a.subject}: {a.status}",
                "start": a.date.isoformat(),
                "color": color
            })

    return jsonify(events)
