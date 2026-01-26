from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import or_
from extensions import db
from models import Ticket, User, Notification, TicketStatus

leader_bp = Blueprint('leader', __name__)

@leader_bp.route('/leader/dashboard')
@login_required
def leader_dashboard():
    if current_user.role != 'leader':
        return redirect(url_for('main.index'))
    
    # Filter Logic
    time_range = request.args.get('time_range', 'all')
    
    query = Ticket.query
    if time_range == '7d':
        start_date = datetime.utcnow() - timedelta(days=7)
        query = query.filter(Ticket.created_at >= start_date)
    elif time_range == '30d':
        start_date = datetime.utcnow() - timedelta(days=30)
        query = query.filter(Ticket.created_at >= start_date)
    elif time_range == '3m':
        start_date = datetime.utcnow() - timedelta(days=90)
        query = query.filter(Ticket.created_at >= start_date)
    elif time_range == '1y':
        start_date = datetime.utcnow() - timedelta(days=365)
        query = query.filter(Ticket.created_at >= start_date)
        
    all_tickets = query.all()
    
    # Stats logic
    total_tickets = len(all_tickets)
    resolved_tickets = len([t for t in all_tickets if t.status in ['Resolved', 'Closed']])
    completion_rate = int((resolved_tickets / total_tickets * 100)) if total_tickets > 0 else 0
    
    # Staff Stats
    staff_members = User.query.filter_by(role='staff').all()

    # Chart Data
    # 1. Tickets by Status
    status_counts = {}
    for t in all_tickets:
        label = t.status_label
        status_counts[label] = status_counts.get(label, 0) + 1
        
    # 2. Tickets by Category
    category_counts = {}
    for t in all_tickets:
        if t.category:
            category_counts[t.category] = category_counts.get(t.category, 0) + 1
            
    # 3. Staff Performance (Tickets assigned)
    staff_performance = {}
    for staff in staff_members:
        count = Ticket.query.filter_by(assigned_to_id=staff.id).count()
        staff_performance[staff.full_name or staff.username] = count

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'total_tickets': total_tickets,
            'resolved_tickets': resolved_tickets,
            'completion_rate': completion_rate,
            'status_counts': status_counts,
            'category_counts': category_counts,
            'staff_performance': staff_performance
        })

    return render_template('leader/dashboard.html', 
                         staff_members=staff_members,
                         total_tickets=total_tickets,
                         resolved_tickets=resolved_tickets,
                         completion_rate=completion_rate,
                         status_counts=status_counts,
                         category_counts=category_counts,
                         staff_performance=staff_performance,
                         current_range=time_range)

@leader_bp.route('/leader/assignment')
@login_required
def assignment():
    if current_user.role != 'leader':
        return redirect(url_for('main.index'))
    
    # Only fetch New or Unassigned tickets
    # Only fetch New or Unassigned tickets
    # Join TicketStatus to filter by name
    new_tickets = Ticket.query.join(TicketStatus).filter(
        or_(TicketStatus.name == 'New', Ticket.assigned_to_id == None),
        ~TicketStatus.name.in_(['Resolved', 'Closed', 'Rejected'])
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
    
    query = Ticket.query.join(TicketStatus)
    
    if status and status != 'all':
        query = query.filter(TicketStatus.name == status)
    if priority and priority != 'all':
        query = query.filter(Ticket.priority == priority)
    if search:
        query = query.filter(or_(
            Ticket.title.ilike(f'%{search}%'),
            Ticket.id.ilike(f'%{search}%')
        ))
        
    tickets = query.order_by(Ticket.created_at.desc()).all()
    statuses = TicketStatus.query.all()
    
    return render_template('leader/all_tickets.html', tickets=tickets, statuses=statuses)

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
        
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'message': 'Đã phân công yêu cầu thành công'})
        
    return redirect(url_for('leader.assignment'))

@leader_bp.route('/reject_ticket/<int:ticket_id>', methods=['POST'])
@login_required
def reject_ticket(ticket_id):
    if current_user.role != 'leader':
        return redirect(url_for('main.index'))
        
    ticket = Ticket.query.get_or_404(ticket_id)
    
    if ticket.status in ['Resolved', 'Closed']:
        flash('Không thể từ chối yêu cầu đã giải quyết hoặc đã đóng')
        return redirect(url_for('leader.assignment'))
        
    reason = request.form.get('reason')
    if not reason:
        flash('Vui lòng nhập lý do từ chối')
        return redirect(url_for('leader.assignment'))
        
    ticket.status = 'Rejected'
    ticket.rejection_reason = reason
    ticket.updated_at = datetime.utcnow()
    
    # Notify User
    n_user = Notification(user_id=ticket.creator_id, message=f"Yêu cầu của bạn đã bị từ chối: {reason}", link=url_for('user.view_ticket', ticket_id=ticket.id))
    db.session.add(n_user)
    
    db.session.commit()
    flash('Đã từ chối yêu cầu')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'message': 'Đã từ chối yêu cầu'})
        
    return redirect(url_for('leader.assignment'))
