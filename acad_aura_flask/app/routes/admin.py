# app/routes/admin.py - FIXED WITH MAKE FACULTY FEATURE
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models import User

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Get counts for dashboard
    total_users = User.query.count()
    pending_users = User.query.filter_by(status='pending').filter(User.role != 'admin').count()
    approved_users = User.query.filter_by(status='approved').count()
    total_faculty = User.query.filter_by(role='faculty').count()
    total_students = User.query.filter_by(role='student').count()
    
    return render_template('admin/dashboard.html', 
                         total_users=total_users,
                         pending_users=pending_users,
                         approved_users=approved_users,
                         total_faculty=total_faculty,
                         total_students=total_students)

@admin_bp.route('/pending')
@login_required
@admin_required
def pending_users():
    # Get pending users
    pending_users = User.query.filter_by(status='pending').filter(User.role != 'admin').all()
    return render_template('admin/pending_users.html', pending_users=pending_users)

@admin_bp.route('/approve_user/<int:user_id>')
@login_required
@admin_required
def approve_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role != 'admin':
        user.status = 'approved'
        db.session.commit()
        flash(f'✅ User {user.name or user.email} has been approved!', 'success')
    else:
        flash('Cannot modify admin users!', 'error')
    
    return redirect(url_for('admin.all_users'))

@admin_bp.route('/reject_user/<int:user_id>')
@login_required
@admin_required
def reject_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role != 'admin':
        user.status = 'rejected'
        db.session.commit()
        flash(f'❌ User {user.name or user.email} has been rejected!', 'warning')
    else:
        flash('Cannot modify admin users!', 'error')
    
    return redirect(url_for('admin.all_users'))

@admin_bp.route('/make_faculty/<int:user_id>')
@login_required
@admin_required
def make_faculty(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.role == 'admin':
        flash('Admin users are already faculty!', 'info')
    else:
        user.role = 'faculty'
        user.status = 'approved'  # Auto-approve when making faculty
        db.session.commit()
        flash(f'👨‍🏫 User {user.name or user.email} is now a faculty member!', 'success')
    
    return redirect(url_for('admin.all_users'))

@admin_bp.route('/remove_faculty/<int:user_id>')
@login_required
@admin_required
def remove_faculty(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.role == 'admin':
        flash('Cannot demote admin users!', 'error')
    elif user.role == 'faculty':
        user.role = 'student'
        db.session.commit()
        flash(f'User {user.name or user.email} is now a student.', 'info')
    
    return redirect(url_for('admin.all_users'))

@admin_bp.route('/delete_user/<int:user_id>')
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.role == 'admin':
        flash('Cannot delete admin users!', 'error')
    else:
        db.session.delete(user)
        db.session.commit()
        flash(f'🗑️ User {user.name or user.email} has been deleted!', 'success')
    
    return redirect(url_for('admin.all_users'))

@admin_bp.route('/users')
@login_required
@admin_required
def all_users():
    # Get ALL users from database
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/all_users.html', users=all_users)

@admin_bp.route('/calendar')
@login_required
@admin_required
def calendar():
    return render_template('admin/calendar.html')

# Debug route to see all users in database
@admin_bp.route('/debug_users')
@login_required
@admin_required
def debug_users():
    all_users = User.query.all()
    result = "<h2>All Users in Database:</h2><br>"
    for user in all_users:
        result += f"<strong>ID:</strong> {user.id}, <strong>Name:</strong> {user.name}, <strong>Email:</strong> {user.email}, <strong>Role:</strong> {user.role}, <strong>Status:</strong> {user.status}<br>"
    return result