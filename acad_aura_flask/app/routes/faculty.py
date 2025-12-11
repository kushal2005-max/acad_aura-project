# app/routes/faculty.py - FIXED WITH DEBUG OUTPUT
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import User, Assignment, Submission

faculty_bp = Blueprint('faculty', __name__)

def faculty_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or (current_user.role not in ['faculty', 'admin']):
            flash('Faculty access required.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@faculty_bp.route('/dashboard')
@login_required
@faculty_required
def dashboard():
    # Count assignments created by this faculty
    total_assignments = Assignment.query.filter_by(faculty_id=current_user.id).count()
    
    # Count submissions to this faculty's assignments
    total_submissions = Submission.query.join(Assignment).filter(
        Assignment.faculty_id == current_user.id
    ).count()
    
    # Count total students
    total_students = User.query.filter_by(role='student', status='approved').count()
    
    return render_template('faculty/dashboard.html',
                         total_assignments=total_assignments,
                         total_submissions=total_submissions,
                         total_students=total_students)

@faculty_bp.route('/students')
@login_required
@faculty_required
def students():
    # GET ALL APPROVED STUDENTS - WITH DEBUG
    print("=" * 50)
    print("DEBUG: Faculty Students Route Called")
    print(f"Current User: {current_user.name} (ID: {current_user.id}, Role: {current_user.role})")
    
    # Query students
    all_students = User.query.filter_by(role='student', status='approved').all()
    
    print(f"Found {len(all_students)} approved students:")
    for s in all_students:
        print(f"  - {s.name} ({s.email}) - Status: {s.status}, Role: {s.role}")
    
    # Also check total users in database
    total_users = User.query.count()
    print(f"Total users in database: {total_users}")
    
    # Check all students (approved and pending)
    all_student_records = User.query.filter_by(role='student').all()
    print(f"Total student records: {len(all_student_records)}")
    for s in all_student_records:
        print(f"  - {s.name} - Status: {s.status}")
    
    print("=" * 50)
    
    return render_template('faculty/students.html', students=all_students)

@faculty_bp.route('/my_courses')
@login_required
@faculty_required
def my_courses():
    return render_template('faculty/my_courses.html')

@faculty_bp.route('/attendance')
@login_required
@faculty_required
def attendance():
    return render_template('faculty/attendance.html')

@faculty_bp.route('/grades')
@login_required
@faculty_required
def grades():
    return render_template('faculty/grades.html')

@faculty_bp.route('/assignment/create', methods=['GET', 'POST'])
@login_required
@faculty_required
def create_assignment():
    if request.method == 'POST':
        from datetime import datetime
        
        subject = request.form.get('subject', '').strip()
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        start_time = request.form.get('start_datetime')
        end_time = request.form.get('end_datetime')

        assignment = Assignment(
            faculty_id=current_user.id,
            subject=subject,
            title=title,
            description=description,
            start_datetime=datetime.fromisoformat(start_time) if start_time else None,
            end_datetime=datetime.fromisoformat(end_time) if end_time else None
        )

        db.session.add(assignment)
        db.session.commit()

        flash('✅ Assignment created successfully!', 'success')
        return redirect(url_for('faculty.list_assignments'))

    return render_template('faculty/create_assignment.html')

@faculty_bp.route('/assignments')
@login_required
@faculty_required
def list_assignments():
    assigns = Assignment.query.filter_by(faculty_id=current_user.id).order_by(
        Assignment.created_at.desc()
    ).all()
    return render_template('faculty/assignments.html', assignments=assigns)

@faculty_bp.route('/assignment/<int:aid>/submissions')
@login_required
@faculty_required
def view_submissions(aid):
    assignment = Assignment.query.get_or_404(aid)
    
    # Check if this faculty owns this assignment
    if assignment.faculty_id != current_user.id and current_user.role != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('faculty.dashboard'))
    
    subs = Submission.query.filter_by(assignment_id=aid).order_by(
        Submission.submitted_at.desc()
    ).all()
    return render_template('faculty/submissions.html', submissions=subs, assignment=assignment)