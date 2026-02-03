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
        
    # Only fetch active tickets for the main board, sorted by recent update
    tickets = Ticket.query.join(TicketStatus).filter(
        Ticket.assigned_to_id == current_user.id,
        TicketStatus.name.in_(['Assigned', 'In Progress', 'Waiting'])
    ).order_by(Ticket.updated_at.desc()).all()
    
    # Staff personal stats
    my_tickets = Ticket.query.filter_by(assigned_to_id=current_user.id).all()
    my_resolved = len([t for t in my_tickets if t.status == 'Resolved'])
    my_pending = len([t for t in my_tickets if t.status in ['Assigned', 'In Progress', 'Waiting']])
    
    # Chart Data
    status_counts = {}
    for t in my_tickets:
        label = t.status_label
        status_counts[label] = status_counts.get(label, 0) + 1
        
    return render_template('staff/dashboard.html', 
                         tickets=tickets,
                         my_resolved=my_resolved,
                         my_pending=my_pending,
                         status_counts=status_counts)

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
