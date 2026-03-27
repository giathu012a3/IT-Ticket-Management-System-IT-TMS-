from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db
from .utils import now_vn

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    full_name = db.Column(db.String(120))
    role = db.Column(db.String(20), default='user')
    status = db.Column(db.String(20), default='active')
    department = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=now_vn)

    tickets_created = db.relationship('Ticket', foreign_keys='Ticket.creator_id', backref='creator', lazy=True)
    tickets_assigned = db.relationship('Ticket', foreign_keys='Ticket.assigned_to_id', backref='assigned_to', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        if self.password.startswith('scrypt:') or self.password.startswith('pbkdf2:'):
            return check_password_hash(self.password, password)
        else:
            if self.password == password:
                self.set_password(password)
                db.session.commit()
                return True
            return False

    def __repr__(self):
        return f'<User {self.username}>'

    @property
    def role_label(self):
        roles = {
            'user': 'Người dùng',
            'leader': 'Quản lý',
            'staff': 'Kỹ thuật viên',
            'admin': 'Quản trị viên'
        }
        return roles.get(self.role, self.role)

    @property
    def active_count(self):
        from .ticket import Ticket, TicketStatus
        return Ticket.query.join(TicketStatus).filter(
            Ticket.assigned_to_id == self.id,
            TicketStatus.name.in_(['Assigned', 'In Progress', 'Waiting'])
        ).count()

    @property
    def assigned_tickets_count(self):
        from .ticket import Ticket
        return Ticket.query.filter_by(assigned_to_id=self.id).count()

class SystemLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(50), nullable=False)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=now_vn)

    user = db.relationship('User', backref=db.backref('system_logs', lazy=True))

def log_activity(user_id, action, details, ip_address=None):
    from flask import request
    if ip_address is None:
        try:
            ip_address = request.remote_addr
        except RuntimeError:
            ip_address = 'System'
            
    log = SystemLog(
        user_id=user_id,
        action=action,
        details=details,
        ip_address=ip_address
    )
    db.session.add(log)
    db.session.commit()
