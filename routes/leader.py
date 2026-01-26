from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import or_
from extensions import db
from models import Ticket, User, Notification

leader_bp = Blueprint('leader', __name__)

@leader_bp.route('/leader/dashboard')
@login_required
def leader_dashboard():
    if current_user.role != 'leader':
        return redirect(url_for('main.index'))
    
    # Stats logic
    total_tickets = Ticket.query.count()
    resolved_tickets = Ticket.query.filter(Ticket.status.in_(['Resolved', 'Closed'])).count()
    completion_rate = int((resolved_tickets / total_tickets * 100)) if total_tickets > 0 else 0
    
    # Staff Stats
    staff_members = User.query.filter_by(role='staff').all()
    
    return render_template('leader/dashboard.html', 
                         staff_members=staff_members,
                         total_tickets=total_tickets,
                         resolved_tickets=resolved_tickets,
                         completion_rate=completion_rate)

@leader_bp.route('/leader/assignment')
@login_required
def assignment():
    if current_user.role != 'leader':
        return redirect(url_for('main.index'))
    
    # Only fetch New or Unassigned tickets
    new_tickets = Ticket.query.filter(
        or_(Ticket.status == 'New', Ticket.assigned_to_id == None)
    ).order_by(Ticket.created_at.desc()).all()
    
    staff_members = User.query.filter_by(role='staff').all()
    
    return render_template('leader/assignment.html', 
                         new_tickets=new_tickets,
                         staff_members=staff_members)

@leader_bp.route('/leader/tickets')
@login_required
def all_tickets():
    if current_user.role != 'leader':
        return redirect(url_for('main.index'))
        
    # Filter Logic
    status = request.args.get('status')
    priority = request.args.get('priority')
    search = request.args.get('search')
    
    query = Ticket.query
    
    if status and status != 'all':
        query = query.filter_by(status=status)
    if priority and priority != 'all':
        query = query.filter_by(priority=priority)
    if search:
        query = query.filter(or_(
            Ticket.title.ilike(f'%{search}%'),
            Ticket.id.ilike(f'%{search}%')
        ))
        
    tickets = query.order_by(Ticket.created_at.desc()).all()
    
    return render_template('leader/all_tickets.html', tickets=tickets)

@leader_bp.route('/assign_ticket/<int:ticket_id>', methods=['POST'])
@login_required
def assign_ticket(ticket_id):
    if current_user.role != 'leader':
        return redirect(url_for('main.index'))
        
    ticket = Ticket.query.get_or_404(ticket_id)
    
    if ticket.status in ['Resolved', 'Closed']:
        flash('Không thể phân công yêu cầu đã giải quyết hoặc đã đóng')
        return redirect(url_for('leader.assignment'))
        
    staff_id = request.form.get('staff_id')
    
    if staff_id:
        ticket.assigned_to_id = staff_id
        ticket.status = 'Assigned'
        ticket.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Notify Staff
        n = Notification(user_id=staff_id, message=f"Bạn được phân công yêu cầu: {ticket.title}", link=url_for('user.view_ticket', ticket_id=ticket.id))
        db.session.add(n)
        
        # Notify User
        n_user = Notification(user_id=ticket.creator_id, message=f"Yêu cầu đã được phân công cho kỹ thuật viên", link=url_for('user.view_ticket', ticket_id=ticket.id))
        db.session.add(n_user)
        
        db.session.commit()
        flash('Đã phân công yêu cầu thành công')
        
    return redirect(url_for('leader.assignment'))
