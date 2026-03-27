from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import User, Ticket, Feedback, now_vn
from datetime import datetime, timedelta

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin/dashboard")
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        return redirect(url_for("main.index"))

    users = User.query.all()

    time_range = request.args.get("time_range", "this_month")

    from routes.leader import get_date_ranges

    cur_start, cur_end, prev_start, prev_end = get_date_ranges(time_range)

    query_tickets = Ticket.query
    query_feedbacks = Feedback.query

    if cur_start:
        query_tickets = query_tickets.filter(Ticket.created_at >= cur_start)
        query_feedbacks = query_feedbacks.filter(Feedback.created_at >= cur_start)
    if cur_end:
        query_tickets = query_tickets.filter(Ticket.created_at < cur_end)
        query_feedbacks = query_feedbacks.filter(Feedback.created_at < cur_end)

    tickets = query_tickets.all()
    feedbacks = query_feedbacks.all()

    from models import SystemLog

    total_users = User.query.count()

    new_users_query = User.query
    if cur_start:
        new_users_query = new_users_query.filter(User.created_at >= cur_start)
    if cur_end:
        new_users_query = new_users_query.filter(User.created_at < cur_end)
    new_users_count = new_users_query.count()

    system_logs = SystemLog.query.order_by(SystemLog.created_at.desc()).limit(10).all()

    total_tickets = len(tickets)
    avg_rating = 0
    if feedbacks:
        avg_rating = sum([f.rating for f in feedbacks]) / len(feedbacks)

    status_counts = {}
    for t in tickets:
        label = t.status_label
        status_counts[label] = status_counts.get(label, 0) + 1

    priority_counts = {}
    for t in tickets:
        priority_counts[t.priority] = priority_counts.get(t.priority, 0) + 1

    role_counts = {}
    for u in users:
        label = u.role_label if hasattr(u, "role_label") else u.role
        role_counts[label] = role_counts.get(label, 0) + 1

    category_counts = {}
    for t in tickets:
        if t.category:
            category_counts[t.category] = category_counts.get(t.category, 0) + 1

    staff_members = User.query.filter_by(role="staff").all()
    staff_performance = {}
    for staff in staff_members:
        count = Ticket.query.filter_by(assigned_to_id=staff.id).count()
        staff_performance[staff.full_name or staff.username] = count

    resolved_tickets = len([t for t in tickets if t.status in ["Resolved", "Closed"]])
    completion_rate = (
        int((resolved_tickets / total_tickets * 100)) if total_tickets > 0 else 0
    )

    return render_template(
        "admin/dashboard.html",
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
        completion_rate=completion_rate,
    )


@admin_bp.route("/admin/users")
@login_required
def admin_users():
    if current_user.role != "admin":
        return redirect(url_for("main.index"))

    role_filter = request.args.get("role", "all")
    search_query = request.args.get("search", "")

    from sqlalchemy import or_

    query = User.query
    if role_filter != "all":
        query = query.filter(User.role == role_filter)
    if search_query:
        query = query.filter(
            or_(
                User.full_name.ilike(f"%{search_query}%"),
                User.username.ilike(f"%{search_query}%"),
            )
        )

    page = request.args.get("page", 1, type=int)
    users_pagination = query.order_by(User.id.desc()).paginate(
        page=page, per_page=10, error_out=False
    )

    return render_template(
        "admin/users.html",
        users_pagination=users_pagination,
        current_role=role_filter,
        current_search=search_query,
    )


@admin_bp.route("/admin/create_user", methods=["POST"])
@login_required
def create_user():
    if current_user.role != "admin":
        return redirect(url_for("main.index"))

    username = request.form.get("username")
    password = request.form.get("password")
    full_name = request.form.get("full_name")
    role = request.form.get("role")
    department = request.form.get("department")

    if User.query.filter_by(username=username).first():
        flash("Tên đăng nhập đã tồn tại.", "error")
        return redirect(url_for("admin.admin_users"))

    new_user = User(
        username=username, full_name=full_name, role=role, department=department
    )
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    from models import log_activity

    log_activity(
        current_user.id,
        "Tạo Account",
        f"Tạo mới tài khoản @{username} thuộc phòng {department}",
    )

    flash("Tạo tài khoản thành công.", "success")
    return redirect(url_for("admin.admin_users"))


@admin_bp.route("/admin/users/toggle_status/<int:user_id>")
@login_required
def toggle_user_status(user_id):
    if current_user.role != "admin":
        return redirect(url_for("main.index"))

    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("Bạn không thể tự vô hiệu hóa tài khoản của chính mình.", "error")
        return redirect(url_for("admin.admin_users"))

    from models import log_activity

    if user.status == "inactive":
        user.status = "active"
        flash(f"Đã kích hoạt lại tài khoản {user.username}.", "success")
        log_activity(
            current_user.id,
            "Mở khóa",
            f"Khôi phục hoạt động cho tài khoản @{user.username}",
        )
    else:
        user.status = "inactive"
        flash(f"Đã vô hiệu hóa tài khoản {user.username}.", "warning")
        log_activity(
            current_user.id, "Khóa vĩnh viễn", f"Vô hiệu hóa tài khoản @{user.username}"
        )

    db.session.commit()
    return redirect(url_for("admin.admin_users"))


@admin_bp.route("/admin/users/update_password", methods=["POST"])
@login_required
def update_user_password():
    if current_user.role != "admin":
        return redirect(url_for("main.index"))

    user_id = request.form.get("user_id")
    new_password = request.form.get("password")

    if not user_id or not new_password:
        flash("Thiếu thông tin cần thiết.", "warning")
        return redirect(url_for("admin.admin_users"))

    user = User.query.get_or_404(user_id)
    user.set_password(new_password)
    db.session.commit()

    from models import log_activity

    log_activity(
        current_user.id,
        "Reset Password",
        f"Đặt lại mật khẩu cho tài khoản @{user.username}",
    )

    flash(f"Đã cập nhật mật khẩu cho user {user.username}.", "success")
    return redirect(url_for("admin.admin_users"))


@admin_bp.route("/admin/user/<int:user_id>")
@login_required
def admin_user_detail(user_id):
    if current_user.role != "admin":
        return redirect(url_for("main.index"))

    user = User.query.get_or_404(user_id)

    created_tickets = (
        Ticket.query.filter_by(creator_id=user.id)
        .order_by(Ticket.created_at.desc())
        .limit(10)
        .all()
    )

    assigned_tickets = (
        Ticket.query.filter_by(assigned_to_id=user.id)
        .order_by(Ticket.created_at.desc())
        .limit(10)
        .all()
    )

    from models import SystemLog

    recent_logs = (
        SystemLog.query.filter_by(user_id=user.id)
        .order_by(SystemLog.created_at.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "admin/user_detail.html",
        user=user,
        created_tickets=created_tickets,
        assigned_tickets=assigned_tickets,
        recent_logs=recent_logs,
    )
