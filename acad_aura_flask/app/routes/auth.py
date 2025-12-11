# app/routes/auth.py - FIXED
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            # Check if user is approved (except admin)
            if user.role != 'admin' and user.status != 'approved':
                flash('⏳ Your account is pending admin approval.', 'warning')
                return render_template('auth/login.html')
            
            login_user(user)
            flash('✅ Logged in successfully!', 'success')
            
            # Redirect based on role
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'faculty':
                return redirect(url_for('faculty.dashboard'))
            else:  # student
                return redirect(url_for('student.dashboard'))
        else:
            flash('❌ Invalid email or password', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('❌ Email already exists', 'error')
            return render_template('auth/register.html')
        
        # Create new user (pending approval by default)
        user = User(
            email=email,
            name=username,
            role='student',  # Default role
            status='pending'  # Needs admin approval
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('✅ Registration successful! Please wait for admin approval.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('👋 Logged out successfully!', 'success')
    return redirect(url_for('main.index'))