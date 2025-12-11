from flask import Blueprint, render_template
from flask_login import login_required, current_user

user_bp = Blueprint('user', __name__)

@user_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_approved:
        return render_template('user/pending_approval.html')
    return render_template('user/dashboard.html')

@user_bp.route('/profile')
@login_required
def profile():
    return render_template('user/profile.html')