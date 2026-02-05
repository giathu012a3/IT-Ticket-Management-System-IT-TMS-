from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import or_
from extensions import db
from models import Ticket, User, Notification, TicketStatus, now_vn

leader_bp = Blueprint('leader', __name__)

@leader_bp.route('/leader/dashboard')
@login_required
def leader_dashboard():
    if current_user.role not in ['leader', 'admin']:
        return redirect(url_for('main.index'))
    
    # Filter Logic
    # Filter Logic
    time_range = request.args.get('time_range', 'this_month') # Default to this_month for better dashboard view
    
    cur_start, cur_end, prev_start, prev_end = get_date_ranges(time_range)
    
    # 1. Fetch Current Period Data
    query = Ticket.query
    if cur_start:
        query = query.filter(Ticket.created_at >= cur_start, Ticket.created_at < cur_end)
        
    try:
        # Filter Logic
        time_range = request.args.get('time_range', 'this_month') # Default to this_month for better dashboard view
        
        cur_start, cur_end, prev_start, prev_end = get_date_ranges(time_range)
        
        # 1. Fetch Current Period Data
        query = Ticket.query
        if cur_start:
            query = query.filter(Ticket.created_at >= cur_start, Ticket.created_at < cur_end)
            
        # 1. Waiting for Assignment vs Assigned (Overview)
        waiting_assignment_count = Ticket.query.join(TicketStatus).filter(
            TicketStatus.name == 'New',
            Ticket.assigned_to_id == None
        ).count()
        
        assigned_count = Ticket.query.join(TicketStatus).filter(
            TicketStatus.name.in_(['Assigned', 'In Progress'])
        ).count()
        
        # 2. SLA Warnings
        # Logic: Status New > 24 hours OR Status In Progress > 48 hours
        now = now_vn()
        warning_time_new = now - timedelta(hours=24)
        warning_time_progress = now - timedelta(hours=48)
        
        sla_warnings = Ticket.query.join(TicketStatus).filter(
            or_(
                (TicketStatus.name == 'New') & (Ticket.created_at < warning_time_new),
                (TicketStatus.name == 'In Progress') & (Ticket.updated_at < warning_time_progress)
            )
        ).all()
        
        # Stats: Current
        # Resolved in Current Range
        # ... (Existing logic for stats below is fine, just cleaning up duplicates if any)

        # 1. Total Created (Current)
        total_query = Ticket.query
        if cur_start:
            total_query = total_query.filter(Ticket.created_at >= cur_start)
        if cur_end:
            total_query = total_query.filter(Ticket.created_at < cur_end)
        total_tickets = total_query.count()
        
        # 2. Total Resolved (Current)
        resolved_query = Ticket.query.join(TicketStatus).filter(
            TicketStatus.name.in_(['Resolved', 'Closed']))
        if cur_start:
            resolved_query = resolved_query.filter(Ticket.updated_at >= cur_start, Ticket.updated_at < cur_end)
        resolved_tickets = resolved_query.count()
        
        completion_rate = int((resolved_tickets / total_tickets * 100)) if total_tickets > 0 else 0

        # Delta Logic (Keep existing)
        delta_total = 0
        delta_resolved = 0
        if prev_start:
             # Prev Total
            prev_total = Ticket.query.filter(Ticket.created_at >= prev_start, Ticket.created_at < prev_end).count()
            delta_total = total_tickets - prev_total
            # Prev Resolved
            prev_resolved = Ticket.query.join(TicketStatus).filter(
                TicketStatus.name.in_(['Resolved', 'Closed']),
                Ticket.updated_at >= prev_start, 
                Ticket.updated_at < prev_end
            ).count()
            delta_resolved = resolved_tickets - prev_resolved

        # Staff Stats & Performance
        staff_members = User.query.filter_by(role='staff').all()
        
        staff_stats = []
        staff_chart_labels = []
        staff_chart_active = []
        staff_chart_resolved = []
        
        for staff in staff_members:
            # Active (Real-time snapshot)
            active_count = Ticket.query.join(TicketStatus).filter(
                Ticket.assigned_to_id == staff.id,
                TicketStatus.name == 'In Progress'
            ).count()
            
            # Resolved (In Selected Filter Range)
            r_query = Ticket.query.join(TicketStatus).filter(
                Ticket.assigned_to_id == staff.id,
                TicketStatus.name.in_(['Resolved', 'Closed'])
            )
            if cur_start:
                r_query = r_query.filter(Ticket.updated_at >= cur_start, Ticket.updated_at < cur_end)
            
            resolved_count = r_query.count()
            
            # Performance % (Resolved - relative to peers? or simple count)
            # Let's just store counts
            
            name = staff.full_name or staff.username
            staff_stats.append({
                'name': name,
                'active': active_count,
                'resolved_month': resolved_count
            })
            
            # For Chart
            staff_chart_labels.append(name)
            staff_chart_active.append(active_count)
            staff_chart_resolved.append(resolved_count)
            

        # Chart Data (Distribution)
        chart_query = Ticket.query
        if cur_start:
            chart_query = chart_query.filter(Ticket.created_at >= cur_start, Ticket.created_at < cur_end)
        chart_tickets = chart_query.all()

        # Calculate Least Busy Staff
        least_busy_staff = "N/A"
        min_active = float('inf')
        for staff_data in staff_stats:
             if staff_data['active'] < min_active:
                 min_active = staff_data['active']
                 least_busy_staff = staff_data['name']
        
        # Placeholder for overdue if used in JSON (though removed from template logic mostly, JSON requires it)
        overdue_tickets = 0 # or logic to count overdue if needed, currently 0 to satisfy keys

        
        # 1. Tickets by Status
        status_counts = {}
        for t in chart_tickets:
            label = t.status_label
            status_counts[label] = status_counts.get(label, 0) + 1
            
        # 2. Tickets by Category
        category_counts = {}
        for t in chart_tickets:
            if t.category:
                category_counts[t.category] = category_counts.get(t.category, 0) + 1

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'total_tickets': total_tickets,
                'delta_total': delta_total,
                'resolved_tickets': resolved_tickets,
                'delta_resolved': delta_resolved,
                'completion_rate': completion_rate,
                'overdue_tickets': overdue_tickets,
                'least_busy_staff': least_busy_staff,
                'status_counts': status_counts,
                'category_counts': category_counts,
                'staff_labels': staff_chart_labels,
                'staff_active': staff_chart_active,
                'staff_resolved': staff_chart_resolved
            })

        return render_template('leader/dashboard.html', 
                             staff_members=staff_members,
                             total_tickets=total_tickets,
                             delta_total=delta_total,
                             resolved_tickets=resolved_tickets,
                             delta_resolved=delta_resolved,
                             completion_rate=completion_rate,
                             waiting_assignment_count=waiting_assignment_count,
                             assigned_count=assigned_count,
                             sla_warnings=sla_warnings,
                             least_busy_staff=least_busy_staff,
                             staff_stats=staff_stats,
                             status_counts=status_counts,
                             category_counts=category_counts,
                             staff_labels=staff_chart_labels,
                             staff_active=staff_chart_active,
                             staff_resolved=staff_chart_resolved,
                             current_range=time_range)
                             
    except Exception as e:
        print(f"Error in leader_dashboard: {e}")
        import traceback
        traceback.print_exc()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
             return jsonify({'error': str(e)}), 500
        raise e

def get_date_ranges(time_range):
    now = now_vn()
    
    cur_start = None
    cur_end = None
    prev_start = None
    prev_end = None
    
    if time_range == '7d':
        cur_end = now
        cur_start = now - timedelta(days=7)
        prev_end = cur_start
        prev_start = cur_start - timedelta(days=7)
    elif time_range == '30d':
        cur_end = now
        cur_start = now - timedelta(days=30)
        prev_end = cur_start
        prev_start = cur_start - timedelta(days=30)
    elif time_range == 'this_month':
        cur_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        cur_end = now
        # Prev: 1st of prev month
        if now.month == 1:
            prev_start = now.replace(year=now.year-1, month=12, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            prev_start = now.replace(month=now.month-1, day=1, hour=0, minute=0, second=0, microsecond=0)
        prev_end = cur_start
    elif time_range == 'last_month':
        # Cur: Prev Month
        if now.month == 1:
            cur_start = now.replace(year=now.year-1, month=12, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            cur_start = now.replace(month=now.month-1, day=1, hour=0, minute=0, second=0, microsecond=0)
            
        cur_end = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Prev: Month before last
        if cur_start.month == 1:
            prev_start = cur_start.replace(year=cur_start.year-1, month=12, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            prev_start = cur_start.replace(month=cur_start.month-1, day=1, hour=0, minute=0, second=0, microsecond=0)
        prev_end = cur_start
        
    return cur_start, cur_end, prev_start, prev_end

@leader_bp.route('/leader/assignment')
@login_required
def assignment():
    if current_user.role not in ['leader', 'admin']:
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
    if current_user.role not in ['leader', 'admin']:
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
    if current_user.role not in ['leader', 'admin']:
        return redirect(url_for('main.index'))
        
    ticket = Ticket.query.get_or_404(ticket_id)
    
    if ticket.status in ['Resolved', 'Closed']:
        flash('Không thể phân công yêu cầu đã giải quyết hoặc đã đóng')
        return redirect(url_for('leader.assignment'))
        
    staff_id = request.form.get('staff_id')
    
    if staff_id:
        ticket.assigned_to_id = staff_id
        ticket.status = 'Assigned'
        ticket.updated_at = now_vn()
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
    if current_user.role not in ['leader', 'admin']:
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
    ticket.updated_at = now_vn()
    
    # Notify User
    n_user = Notification(user_id=ticket.creator_id, message=f"Yêu cầu của bạn đã bị từ chối: {reason}", link=url_for('user.view_ticket', ticket_id=ticket.id))
    db.session.add(n_user)
    
    db.session.commit()
    flash('Đã từ chối yêu cầu')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'message': 'Đã từ chối yêu cầu'})
        
    return redirect(url_for('leader.assignment'))
