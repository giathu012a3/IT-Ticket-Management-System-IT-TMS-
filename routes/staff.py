from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from extensions import db
from models import Ticket, Notification, TicketStatus, now_vn

staff_bp = Blueprint('staff', __name__)

@staff_bp.route('/staff/dashboard')
@login_required
def staff_dashboard():
    if current_user.role != 'staff':
        return redirect(url_for('main.index'))
        
    # 1. My Active Tickets Count
    my_active_tickets_count = Ticket.query.join(TicketStatus).filter(
        Ticket.assigned_to_id == current_user.id,
        TicketStatus.name.in_(['Assigned', 'In Progress', 'Waiting'])
    ).count()

    # 2. Unread Messages Count (Notifications specific to tickets)
    unread_messages_count = Notification.query.filter_by(
        user_id=current_user.id, is_read=False
    ).count()

    # 3. Task Queue (Prioritized)
    # Custom sort order: Critical (0), High (1), Medium (2), Low (3)
    # SQL Order By Case...
    # For simplicitly, fetch all active and sort in python
    task_queue = Ticket.query.join(TicketStatus).filter(
        Ticket.assigned_to_id == current_user.id,
        TicketStatus.name.in_(['Assigned', 'In Progress', 'Waiting'])
    ).all()
    
    priority_map = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}
    task_queue.sort(key=lambda x: priority_map.get(x.priority, 4))

    # 4. Recent Conversations (Tickets recently updated)
    recent_conversations = Ticket.query.filter(
        Ticket.assigned_to_id == current_user.id
    ).order_by(Ticket.updated_at.desc()).limit(5).all()

    return render_template('staff/dashboard.html', 
                         my_active_tickets_count=my_active_tickets_count,
                         unread_messages_count=unread_messages_count,
                         task_queue=task_queue,
                         recent_conversations=recent_conversations)

@staff_bp.route('/ticket/<int:ticket_id>/update_status', methods=['POST'])
@login_required
def update_ticket_status(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    
    if ticket.status in ['Resolved', 'Closed']:
        flash('Không thể cập nhật trạng thái yêu cầu đã giải quyết hoặc đã đóng')
        return redirect(url_for('user.view_ticket', ticket_id=ticket_id))
        
    # Check permission
    if not (current_user.role == 'staff' and ticket.assigned_to_id == current_user.id) and current_user.role != 'leader':
         flash('Không có quyền thực hiện')
         return redirect(url_for('user.view_ticket', ticket_id=ticket_id))
         
    new_status = request.form.get('status')
    if new_status:
        ticket.status = new_status
        ticket.updated_at = now_vn()
        db.session.commit()
        
        # Notify User about status change
        n = Notification(user_id=ticket.creator_id, message=f"Trạng thái yêu cầu cập nhật: {new_status}", link=url_for('user.view_ticket', ticket_id=ticket.id))
        db.session.add(n)
        db.session.commit()
        
    return redirect(url_for('user.view_ticket', ticket_id=ticket_id))
