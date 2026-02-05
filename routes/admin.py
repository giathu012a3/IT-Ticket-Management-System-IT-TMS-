from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import User, Ticket, Feedback, now_vn
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('main.index'))
        
    users = User.query.all()
    
    # Filter Logic
    time_range = request.args.get('time_range', 'all')
    
    query_tickets = Ticket.query
    query_feedbacks = Feedback.query
    
    if time_range == '7d':
        start_date = now_vn() - timedelta(days=7)
        query_tickets = query_tickets.filter(Ticket.created_at >= start_date)
        query_feedbacks = query_feedbacks.filter(Feedback.created_at >= start_date)
    elif time_range == '30d':
        start_date = now_vn() - timedelta(days=30)
        query_tickets = query_tickets.filter(Ticket.created_at >= start_date)
        query_feedbacks = query_feedbacks.filter(Feedback.created_at >= start_date)
    elif time_range == '3m':
        start_date = now_vn() - timedelta(days=90)
        query_tickets = query_tickets.filter(Ticket.created_at >= start_date)
        query_feedbacks = query_feedbacks.filter(Feedback.created_at >= start_date)
    elif time_range == '1y':
        start_date = now_vn() - timedelta(days=365)
        query_tickets = query_tickets.filter(Ticket.created_at >= start_date)
        query_feedbacks = query_feedbacks.filter(Feedback.created_at >= start_date)
        
    tickets = query_tickets.all()
    feedbacks = query_feedbacks.all()
    
    from models import SystemLog
    
    # User Stats (Global, not filtered by time usually, or maybe "New Users" in time range)
    total_users = User.query.count()
    
    # New Users (in selected range)
    new_users_query = User.query
    if time_range != 'all' and 'start_date' in locals():
         new_users_query = new_users_query.filter(User.created_at >= start_date)
    new_users_count = new_users_query.count()

    # System Logs (Recent 10)
    system_logs = SystemLog.query.order_by(SystemLog.created_at.desc()).limit(10).all()
    
    # Stats
    total_tickets = len(tickets)
    avg_rating = 0
    if feedbacks:
        avg_rating = sum([f.rating for f in feedbacks]) / len(feedbacks)
        
    # Chart Data Preparation
    # 1. Tickets by Status
    status_counts = {}
    for t in tickets:
        label = t.status_label
        status_counts[label] = status_counts.get(label, 0) + 1
        
    # 2. Tickets by Priority
    priority_counts = {}
    for t in tickets:
        priority_counts[t.priority] = priority_counts.get(t.priority, 0) + 1
        
    # 3. User Role Distribution
    role_counts = {}
    for u in users:
        label = u.role_label if hasattr(u, 'role_label') else u.role
        role_counts[label] = role_counts.get(label, 0) + 1
        
    # --- LEADER STATS MERGED ---
    # 4. Tickets by Category
    category_counts = {}
    for t in tickets:
        if t.category:
            category_counts[t.category] = category_counts.get(t.category, 0) + 1
            
    # 5. Staff Performance (Tickets assigned)
    staff_members = User.query.filter_by(role='staff').all()
    staff_performance = {}
    for staff in staff_members:
        count = Ticket.query.filter_by(assigned_to_id=staff.id).count()
        staff_performance[staff.full_name or staff.username] = count

    # 6. Resolution Stats
    resolved_tickets = len([t for t in tickets if t.status in ['Resolved', 'Closed']])
    completion_rate = int((resolved_tickets / total_tickets * 100)) if total_tickets > 0 else 0

    return render_template('admin/dashboard.html', 
                         total_tickets=total_tickets,
                         avg_rating=round(avg_rating, 1),
                         total_users=total_users,
                         new_users_count=new_users_count,
                         system_logs=system_logs,
                         status_counts=status_counts,
                         priority_counts=priority_counts,
                         role_counts=role_counts,
                         current_range=time_range,
                         category_counts=category_counts,
                         staff_performance=staff_performance,
                         resolved_tickets=resolved_tickets,
                         completion_rate=completion_rate)

@admin_bp.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        return redirect(url_for('main.index'))
    
    users = User.query.all()
    return render_template('admin/users.html', users=users)

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
        return redirect(url_for('admin.admin_users'))
        
    new_user = User(username=username, password=password, full_name=full_name, role=role)
    db.session.add(new_user)
    db.session.commit()
    flash('Tạo tài khoản thành công.')
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/admin/users/toggle_status/<int:user_id>')
@login_required
def toggle_user_status(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('main.index'))
        
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Bạn không thể tự vô hiệu hóa tài khoản của chính mình.')
        return redirect(url_for('admin.admin_users'))
        
    if user.status == 'inactive':
        user.status = 'active'
        flash(f'Đã kích hoạt lại tài khoản {user.username}.')
    else:
        user.status = 'inactive'
        flash(f'Đã vô hiệu hóa tài khoản {user.username}.')
        
    db.session.commit()
    return redirect(url_for('admin.admin_users'))
