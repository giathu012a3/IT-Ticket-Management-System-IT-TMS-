from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from extensions import db
from models import (
    Ticket,
    User,
    Comment,
    Notification,
    Feedback,
    TicketStatus,
    now_vn,
    Attachment,
)
import os
from werkzeug.utils import secure_filename
from flask import current_app
from datetime import timedelta

user_bp = Blueprint("user", __name__)


@user_bp.route("/dashboard")
@login_required
def user_dashboard():
    if current_user.role not in ["user"]:  # Simple RBAC check
        return redirect(url_for("main.index"))

    active_tickets_count = (
        Ticket.query.join(TicketStatus)
        .filter(
            Ticket.creator_id == current_user.id,
            ~TicketStatus.name.in_(["Resolved", "Closed", "Rejected"]),
        )
        .count()
    )

    pending_response_count = (
        Notification.query.filter_by(user_id=current_user.id, is_read=False)
        .filter(Notification.message.ilike("%phản hồi%"))
        .count()
    )

    recent_tickets = (
        Ticket.query.filter_by(creator_id=current_user.id)
        .order_by(Ticket.updated_at.desc())
        .limit(5)
        .all()
    )

    resolved_tickets = (
        Ticket.query.join(TicketStatus)
        .filter(Ticket.creator_id == current_user.id, TicketStatus.name == "Resolved")
        .all()
    )

    tickets_needing_rating = [t for t in resolved_tickets if not t.feedback]

    return render_template(
        "user/dashboard.html",
        active_tickets_count=active_tickets_count,
        pending_response_count=pending_response_count,
        recent_tickets=recent_tickets,
        tickets_needing_rating=tickets_needing_rating,
    )


@user_bp.route("/my-tickets")
@login_required
def user_tickets():
    if current_user.role != "user":
        return redirect(url_for("main.index"))

    status_filter = request.args.get("filter", "active")

    query = Ticket.query.join(TicketStatus).filter(Ticket.creator_id == current_user.id)

    if status_filter == "active":
        query = query.filter(
            TicketStatus.name.in_(["New", "Assigned", "In Progress", "Waiting"])
        )
    elif status_filter == "completed":
        query = query.filter(TicketStatus.name.in_(["Resolved", "Closed", "Rejected"]))

    page = request.args.get("page", 1, type=int)
    tickets_pagination = query.order_by(Ticket.updated_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )

    return render_template(
        "user/tickets.html",
        tickets_pagination=tickets_pagination,
        current_filter=status_filter,
    )


@user_bp.route("/ticket/create", methods=["GET", "POST"])
@login_required
def create_ticket():
    if request.method == "POST":
        title = request.form.get("title")
        category = request.form.get("category")
        priority = request.form.get("priority")
        description = request.form.get("description")
        department = request.form.get("department")

        if department:
            current_user.department = department

        # Tính toán SLA (Service Level Agreement)
        sla_hours = {"Low": 72, "Medium": 24, "High": 4, "Critical": 1}
        due_date = now_vn() + timedelta(hours=sla_hours.get(priority, 24))

        ticket = Ticket(
            title=title,
            category=category,
            priority=priority,
            description=description,
            due_date=due_date,
            creator_id=current_user.id,
        )

        new_status = TicketStatus.query.filter_by(name="New").first()
        if new_status:
            ticket.status_id = new_status.id

        db.session.add(ticket)
        db.session.commit()

        attachment_file = request.files.get("attachment")
        if attachment_file and attachment_file.filename != "":
            ALLOWED_EXTENSIONS = {
                "png",
                "jpg",
                "jpeg",
                "gif",
                "pdf",
                "doc",
                "docx",
                "xls",
                "xlsx",
                "txt",
            }
            filename = secure_filename(attachment_file.filename)
            extension = filename.rsplit(".", 1)[1].lower() if "." in filename else ""

            if extension not in ALLOWED_EXTENSIONS:
                db.session.rollback()
                flash(
                    f"Định dạng file .{extension} không được hệ thống cho phép. Vui lòng tải lên ảnh hoặc tài liệu.",
                    "error",
                )
                return redirect(url_for("user.create_ticket"))

            upload_dir = current_app.config["UPLOAD_FOLDER"]
            os.makedirs(upload_dir, exist_ok=True)

            saved_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            file_path = os.path.join(upload_dir, saved_filename)
            attachment_file.save(file_path)

            new_attachment = Attachment(
                filename=saved_filename, original_filename=filename, ticket_id=ticket.id
            )
            db.session.add(new_attachment)
            db.session.commit()

        leaders = User.query.filter_by(role="leader").all()
        for leader in leaders:
            n = Notification(
                user_id=leader.id,
                message=f"Yêu cầu mới: {title}",
                link=url_for("user.view_ticket", ticket_id=ticket.id),
            )
            db.session.add(n)
        db.session.commit()

        from models import log_activity

        log_activity(
            current_user.id, "Create Ticket", f"Tạo mới vé #{ticket.id} - {title}"
        )

        flash("Yêu cầu của bạn đã được gửi thành công!", "success")
        return redirect(url_for("user.user_dashboard"))

    return render_template("user/create_ticket.html")


@user_bp.route("/ticket/<int:ticket_id>")
@login_required
def view_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if not (
        current_user.id == ticket.creator_id
        or current_user.role in ["leader", "admin"]
        or (current_user.role == "staff" and ticket.assigned_to_id == current_user.id)
    ):
        flash("Bạn không có quyền truy cập", "error")
        return redirect(url_for("main.index"))

    statuses = TicketStatus.query.all()
    return render_template("ticket_detail.html", ticket=ticket, statuses=statuses)


@user_bp.route("/ticket/<int:ticket_id>/comment", methods=["POST"])
@login_required
def add_comment(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    if ticket.status in ["Resolved", "Closed"]:
        flash("Không thể bình luận trên yêu cầu đã giải quyết hoặc đã đóng", "error")
        return redirect(url_for("user.view_ticket", ticket_id=ticket.id))

    content = request.form.get("content")
    is_internal = request.form.get("is_internal") == "on"

    if is_internal and current_user.role == "user":
        is_internal = False  # Users cannot make internal notes

    comment = Comment(
        content=content,
        is_internal=is_internal,
        ticket_id=ticket.id,
        user_id=current_user.id,
    )

    ticket.updated_at = now_vn()
    db.session.add(comment)

    if not is_internal:
        if current_user.id == ticket.creator_id:
            # User commented -> Notify Assigned Staff and Leaders
            if ticket.assigned_to_id:
                n = Notification(
                    user_id=ticket.assigned_to_id,
                    message=f"Khách hàng phản hồi: {ticket.title}",
                    link=url_for("user.view_ticket", ticket_id=ticket.id),
                )
                db.session.add(n)
            leaders = User.query.filter_by(role="leader").all()
            for leader in leaders:
                if (
                    leader.id != current_user.id
                ):  # Don't notify if leader is the one commenting
                    n = Notification(
                        user_id=leader.id,
                        message=f"Khách hàng phản hồi: {ticket.title}",
                        link=url_for("user.view_ticket", ticket_id=ticket.id),
                    )
                    db.session.add(n)
        else:
            # Staff/Leader commented -> Notify User
            if ticket.creator_id != current_user.id:
                n = Notification(
                    user_id=ticket.creator_id,
                    message=f"Cập nhật mới trên yêu cầu: {ticket.title}",
                    link=url_for("user.view_ticket", ticket_id=ticket.id),
                )
                db.session.add(n)

    db.session.commit()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(
            {
                "success": True,
                "comment": {
                    "id": comment.id,
                    "content": comment.content,
                    "author_name": current_user.full_name,
                    "author_initial": current_user.username[0].upper(),
                    "created_at": comment.created_at.strftime("%H:%M"),
                    "is_internal": comment.is_internal,
                    "user_id": current_user.id,
                    "author_role": current_user.role_label,
                },
            }
        )

    return redirect(url_for("user.view_ticket", ticket_id=ticket.id))


@user_bp.route("/ticket/<int:ticket_id>/comments/poll", methods=["GET"])
@login_required
def poll_comments(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    if not (
        current_user.id == ticket.creator_id
        or current_user.role in ["leader", "admin"]
        or (current_user.role == "staff" and ticket.assigned_to_id == current_user.id)
    ):
        return jsonify({"error": "Unauthorized"}), 403

    last_id = request.args.get("last_id", 0, type=int)

    query = Comment.query.filter(Comment.ticket_id == ticket.id, Comment.id > last_id)

    if current_user.role == "user":
        query = query.filter(Comment.is_internal == False)

    new_comments = query.order_by(Comment.id.asc()).all()

    comments_data = []
    for c in new_comments:
        comments_data.append(
            {
                "id": c.id,
                "content": c.content,
                "author_name": c.author.full_name,
                "author_initial": c.author.username[0].upper(),
                "created_at": c.created_at.strftime("%H:%M"),
                "is_internal": c.is_internal,
                "user_id": c.user_id,
                "author_role": c.author.role_label,
            }
        )

    return jsonify(
        {
            "comments": comments_data,
            "latest_id": comments_data[-1]["id"] if comments_data else last_id,
        }
    )


@user_bp.route("/ticket/<int:ticket_id>/feedback", methods=["GET", "POST"])
@login_required
def ticket_feedback(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    if ticket.creator_id != current_user.id:
        return redirect(url_for("main.index"))

    if ticket.status != "Resolved":
        flash("Yêu cầu phải được giải quyết mới có thể đánh giá", "warning")
        return redirect(url_for("user.view_ticket", ticket_id=ticket_id))

    if request.method == "POST":
        rating = request.form.get("rating")
        comment = request.form.get("comment")

        feedback = Feedback(ticket_id=ticket.id, rating=int(rating), comment=comment)
        ticket.status = "Closed"
        db.session.add(feedback)
        db.session.commit()
        flash("Cảm ơn phản hồi của bạn!", "success")
        return redirect(url_for("user.user_dashboard"))

    return render_template("user/feedback.html", ticket=ticket)


@user_bp.route("/ticket/<int:ticket_id>/skip_feedback", methods=["POST"])
@login_required
def skip_ticket_feedback(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    if ticket.creator_id != current_user.id:
        return redirect(url_for("main.index"))

    if ticket.status != "Resolved":
        return redirect(url_for("user.view_ticket", ticket_id=ticket_id))

    ticket.status = "Closed"
    ticket.updated_at = now_vn()
    db.session.commit()

    from models import log_activity

    log_activity(
        current_user.id,
        "Close Ticket",
        f"Hệ thống tự động đóng vé #{ticket.id} không qua ý kiến",
    )

    flash("Yêu cầu đã được đóng hoàn toàn!", "success")
    return redirect(url_for("user.user_dashboard"))
