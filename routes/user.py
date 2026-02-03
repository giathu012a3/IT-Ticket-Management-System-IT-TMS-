from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from extensions import db
from models import Ticket, User, Comment, Notification, Feedback, TicketStatus, now_vn

user_bp = Blueprint('user', __name__)

@user_bp.route('/dashboard')
@login_required
def user_dashboard():
    if current_user.role not in ['user']: # Simple RBAC check
         return redirect(url_for('main.index'))
         
    # Chart Data
    tickets = Ticket.query.filter_by(creator_id=current_user.id).all()
    status_counts = {}
    for t in tickets:
        label = t.status_label
        status_counts[label] = status_counts.get(label, 0) + 1
        
    return render_template('user/dashboard.html', 
                         total_tickets=len(tickets),
                         status_counts=status_counts)

@user_bp.route('/my-tickets')
@login_required
def user_tickets():
    if current_user.role != 'user':
        return redirect(url_for('main.index'))
        
    status_filter = request.args.get('filter', 'active')
    
    query = Ticket.query.join(TicketStatus).filter(Ticket.creator_id == current_user.id)
    
    if status_filter == 'active':
        query = query.filter(TicketStatus.name.in_(['New', 'Assigned', 'In Progress', 'Waiting']))
    elif status_filter == 'completed':
        query = query.filter(TicketStatus.name.in_(['Resolved', 'Closed', 'Rejected']))
    
    tickets = query.order_by(Ticket.updated_at.desc()).all()
    
    return render_template('user/tickets.html', tickets=tickets, current_filter=status_filter)

@user_bp.route('/ticket/create', methods=['GET', 'POST'])
@login_required
def create_ticket():
    if request.method == 'POST':
        title = request.form.get('title')
        category = request.form.get('category')
        priority = request.form.get('priority')
        description = request.form.get('description')
        
        ticket = Ticket(
            title=title,
            category=category,
            priority=priority,
            description=description,
            creator_id=current_user.id
        )
        
        # Explicitly set status to 'New' via relationship or ID
        new_status = TicketStatus.query.filter_by(name='New').first()
        if new_status:
            ticket.status_id = new_status.id
            
        db.session.add(ticket)
        db.session.commit()
        
        # Notify Leaders about new ticket
        leaders = User.query.filter_by(role='leader').all()
        for leader in leaders:
            n = Notification(user_id=leader.id, message=f"Yêu cầu mới: {title}", link=url_for('user.view_ticket', ticket_id=ticket.id))
            db.session.add(n)
        db.session.commit()
        
        flash('Tạo yêu cầu thành công!')
        return redirect(url_for('user.user_dashboard'))
        
    return render_template('user/create_ticket.html')

@user_bp.route('/ticket/<int:ticket_id>')
@login_required
def view_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    # Access control: Creator, Assigned Staff, Leader, or Admin
    if not (current_user.id == ticket.creator_id or 
            current_user.role in ['leader', 'admin'] or 
            (current_user.role == 'staff' and ticket.assigned_to_id == current_user.id)):
        flash('Bạn không có quyền truy cập')
        return redirect(url_for('main.index'))
        
    statuses = TicketStatus.query.all()
    return render_template('ticket_detail.html', ticket=ticket, statuses=statuses)

@user_bp.route('/ticket/<int:ticket_id>/comment', methods=['POST'])
@login_required
def add_comment(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    
    if ticket.status in ['Resolved', 'Closed']:
        flash('Không thể bình luận trên yêu cầu đã giải quyết hoặc đã đóng')
        return redirect(url_for('user.view_ticket', ticket_id=ticket.id))
        
    content = request.form.get('content')
    is_internal = request.form.get('is_internal') == 'on'
    
    if is_internal and current_user.role == 'user':
        is_internal = False # Users cannot make internal notes
        
    comment = Comment(
        content=content,
        is_internal=is_internal,
        ticket_id=ticket.id,
        user_id=current_user.id
    )
    
    ticket.updated_at = now_vn() # Update timestamp
    db.session.add(comment)
    
    # Notification Logic
    if not is_internal:
        if current_user.id == ticket.creator_id:
            # User commented -> Notify Assigned Staff and Leaders
            if ticket.assigned_to_id:
                n = Notification(user_id=ticket.assigned_to_id, message=f"Khách hàng phản hồi: {ticket.title}", link=url_for('user.view_ticket', ticket_id=ticket.id))
                db.session.add(n)
            leaders = User.query.filter_by(role='leader').all()
            for leader in leaders:
                if leader.id != current_user.id: # Don't notify if leader is the one commenting
                    n = Notification(user_id=leader.id, message=f"Khách hàng phản hồi: {ticket.title}", link=url_for('user.view_ticket', ticket_id=ticket.id))
                    db.session.add(n)
        else:
            # Staff/Leader commented -> Notify User
            if ticket.creator_id != current_user.id:
                n = Notification(user_id=ticket.creator_id, message=f"Cập nhật mới trên yêu cầu: {ticket.title}", link=url_for('user.view_ticket', ticket_id=ticket.id))
                db.session.add(n)
                
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'comment': {
                'content': comment.content,
                'author_name': current_user.full_name,
                'author_initial': current_user.username[0].upper(),
                'created_at': comment.created_at.strftime('%H:%M'),
                'is_internal': comment.is_internal,
                'user_id': current_user.id,
                'author_role': current_user.role_label
            }
        })
        
    return redirect(url_for('user.view_ticket', ticket_id=ticket.id))

@user_bp.route('/ticket/<int:ticket_id>/feedback', methods=['GET', 'POST'])
@login_required
def ticket_feedback(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    
    if ticket.creator_id != current_user.id:
         return redirect(url_for('main.index'))
         
    if ticket.status != 'Resolved':
        flash('Yêu cầu phải được giải quyết mới có thể đánh giá')
        return redirect(url_for('user.view_ticket', ticket_id=ticket_id))
        
    if request.method == 'POST':
        rating = request.form.get('rating')
        comment = request.form.get('comment')
        
        feedback = Feedback(
            ticket_id=ticket.id,
            rating=int(rating),
            comment=comment
        )
        ticket.status = 'Closed'
        db.session.add(feedback)
        db.session.commit()
        flash('Cảm ơn phản hồi của bạn!')
        return redirect(url_for('user.user_dashboard'))
        
    return render_template('user/feedback.html', ticket=ticket)
