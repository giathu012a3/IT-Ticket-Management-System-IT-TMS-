from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import User
from extensions import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password: # Plain text for demo as requested
            login_user(user)
            return redirect(url_for('main.index'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng')
            
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not current_password or not new_password or not confirm_password:
            flash('Vui lòng điền đầy đủ thông tin')
        elif current_user.password != current_password:
            flash('Mật khẩu hiện tại không đúng')
        elif new_password != confirm_password:
            flash('Mật khẩu mới không khớp')
        else:
            # In a real app, hash this!
            current_user.password = new_password
            db.session.commit()
            flash('Đổi mật khẩu thành công!')
            return redirect(url_for('user.user_dashboard')) # Or stay on page
            
    return render_template('change_password.html')
