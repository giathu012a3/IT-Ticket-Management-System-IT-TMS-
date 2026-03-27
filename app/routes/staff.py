from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from ..extensions import db
from ..models import Ticket, Notification, TicketStatus, now_vn

staff_bp = Blueprint("staff", __name__)


@staff_bp.route("/staff/dashboard")
@login_required
def staff_dashboard():
    if current_user.role != "staff":
        return redirect(url_for("main.index"))

    my_active_tickets_count = (
        Ticket.query.join(TicketStatus)
        .filter(
            Ticket.assigned_to_id == current_user.id,
            TicketStatus.name.in_(["Assigned", "In Progress", "Waiting"]),
        )
        .count()
    )

    unread_messages_count = Notification.query.filter_by(
        user_id=current_user.id, is_read=False
    ).count()

    task_queue = (
        Ticket.query.join(TicketStatus)
        .filter(
            Ticket.assigned_to_id == current_user.id,
            TicketStatus.name.in_(["Assigned", "In Progress", "Waiting"]),
        )
        .all()
    )

    priority_map = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    task_queue.sort(key=lambda x: priority_map.get(x.priority, 4))

    recent_conversations = (
        Ticket.query.filter(Ticket.assigned_to_id == current_user.id)
        .order_by(Ticket.updated_at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "staff/dashboard.html",
        my_active_tickets_count=my_active_tickets_count,
        unread_messages_count=unread_messages_count,
        task_queue=task_queue,
        recent_conversations=recent_conversations,
    )


@staff_bp.route("/staff/history")
@login_required
def staff_history():
    if current_user.role != "staff":
        return redirect(url_for("main.index"))

    page = request.args.get("page", 1, type=int)

    history_pagination = (
        Ticket.query.join(TicketStatus)
        .filter(
            Ticket.assigned_to_id == current_user.id,
            TicketStatus.name.in_(["Resolved", "Closed", "Rejected"]),
        )
        .order_by(Ticket.updated_at.desc())
        .paginate(page=page, per_page=10, error_out=False)
    )

    return render_template("staff/history.html", history_pagination=history_pagination)


@staff_bp.route("/ticket/<int:ticket_id>/update_status", methods=["POST"])
@login_required
def update_ticket_status(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    if ticket.status in ["Closed", "Rejected"]:
        flash("Không thể cập nhật trạng thái yêu cầu đã đóng hoặc từ chối", "error")
        return redirect(url_for("user.view_ticket", ticket_id=ticket.id))

    if ticket.assigned_to_id != current_user.id and current_user.role != "leader":
        flash("Không có quyền thực hiện", "error")
        return redirect(url_for("main.index"))

    new_status = request.form.get("status")
    if new_status:
        if not ticket.assigned_to_id and new_status not in ["New", "Rejected", "Closed"]:
            flash("Lỗi: Yêu cầu này chưa được phân công nhân sự xử lý!", "error")
            return redirect(url_for("user.view_ticket", ticket_id=ticket.id))

        ticket.status = new_status
        ticket.updated_at = now_vn()
        db.session.commit()

        status_label = (
            TicketStatus.query.filter_by(name=new_status).first().label
            if TicketStatus.query.filter_by(name=new_status).first()
            else new_status
        )
        n = Notification(
            user_id=ticket.creator_id,
            message=f"Trạng thái yêu cầu chuyển sang: {status_label}",
            link=url_for("user.view_ticket", ticket_id=ticket.id),
        )
        db.session.add(n)

        flash(f"Đã cập nhật trạng thái thành: {status_label}", "success")
        db.session.commit()

    return redirect(url_for("user.view_ticket", ticket_id=ticket_id))
