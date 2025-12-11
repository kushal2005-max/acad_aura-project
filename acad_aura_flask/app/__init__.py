# app/__init__.py - FIXED VERSION
from flask import Flask
from app.extensions import db, login_manager
from app.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Import models (AFTER db is initialized)
    from app.models import User, Profile, Assignment, Submission, Attendance, CalendarEvent
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints - NO DUPLICATES
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.main import main_bp
    from app.routes.user import user_bp
    from app.routes.faculty import faculty_bp
    
    # NEW: Additional blueprints for full functionality
    from app.student.routes import student_bp
    from app.assignments.routes import assignments_bp
    from app.attendance.routes import attendance_bp
    from app.calendar.routes import calendar_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(faculty_bp, url_prefix='/faculty')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(assignments_bp, url_prefix='/assignments')
    app.register_blueprint(attendance_bp, url_prefix='/attendance')
    app.register_blueprint(calendar_bp, url_prefix='/calendar')

    return app