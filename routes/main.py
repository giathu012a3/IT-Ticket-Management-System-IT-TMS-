from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from extensions import db
from models import Notification

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.admin_dashboard'))
        elif current_user.role == 'leader':
            return redirect(url_for('leader.leader_dashboard'))
        elif current_user.role == 'staff':
            return redirect(url_for('staff.staff_dashboard'))
        else:
            return redirect(url_for('user.user_dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/notifications/mark_read/<int:notif_id>')
@login_required
def mark_notification_read(notif_id):
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id == current_user.id:
        notif.is_read = True
        db.session.commit()
    return redirect(notif.link or url_for('main.index'))

@main_bp.route('/notifications/mark_all_read')
@login_required
def mark_all_notifications_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return redirect(request.referrer or url_for('main.index'))


