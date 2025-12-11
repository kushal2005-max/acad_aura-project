# app/models.py - ALL MODELS IN ONE FILE
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app.extensions import db

# USER MODEL
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='student')  # admin, faculty, student
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    regno = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    profile = db.relationship('Profile', backref='user', uselist=False, cascade='all, delete-orphan')
    assignments = db.relationship('Assignment', backref='faculty', lazy=True)
    submissions = db.relationship('Submission', backref='student', lazy=True)
    attendance_records = db.relationship('Attendance', backref='student', lazy=True)
    created_events = db.relationship('CalendarEvent', backref='creator', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_faculty(self):
        return self.role == 'faculty'
    
    @property
    def is_approved(self):
        return self.status == 'approved'


# PROFILE MODEL
class Profile(db.Model):
    __tablename__ = 'profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    phone = db.Column(db.String(50))
    department = db.Column(db.String(100))
    bio = db.Column(db.Text)


# ASSIGNMENT MODEL
class Assignment(db.Model):
    __tablename__ = 'assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    subject = db.Column(db.String(150))
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    file = db.Column(db.String(255))
    start_datetime = db.Column(db.DateTime)
    end_datetime = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    submissions = db.relationship('Submission', backref='assignment', lazy=True)


# SUBMISSION MODEL
class Submission(db.Model):
    __tablename__ = 'submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    original_filename = db.Column(db.String(255))
    pdf_filename = db.Column(db.String(255))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='submitted')  # submitted, late, graded
    marks = db.Column(db.Integer)
    remark = db.Column(db.Text)


# ATTENDANCE MODEL
class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    subject = db.Column(db.String(150))
    date = db.Column(db.Date)
    status = db.Column(db.String(10))  # present, absent


# CALENDAR EVENT MODEL
class CalendarEvent(db.Model):
    __tablename__ = 'calendar_events'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    start_datetime = db.Column(db.DateTime)
    end_datetime = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)