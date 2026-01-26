from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import User, Ticket, Feedback

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('main.index'))
        
    users = User.query.all()
    tickets = Ticket.query.all()
    feedbacks = Feedback.query.all()
    
    # Stats
    total_tickets = len(tickets)
    avg_rating = 0
    if feedbacks:
        avg_rating = sum([f.rating for f in feedbacks]) / len(feedbacks)
        
    return render_template('admin/dashboard.html', 
                         users=users,
                         total_tickets=total_tickets,
                         avg_rating=round(avg_rating, 1))

@admin_bp.route('/admin/create_user', methods=['POST'])
@login_required
def create_user():
    if current_user.role != 'admin':
        return redirect(url_for('main.index'))
        
    username = request.form.get('username')
    password = request.form.get('password')
    full_name = request.form.get('full_name')
    role = request.form.get('role')
    
    if User.query.filter_by(username=username).first():
        flash('Tên đăng nhập đã tồn tại.')
        return redirect(url_for('admin.admin_dashboard'))
        
    new_user = User(username=username, password=password, full_name=full_name, role=role)
    db.session.add(new_user)
    db.session.commit()
    flash('Tạo tài khoản thành công.')
    return redirect(url_for('admin.admin_dashboard'))
