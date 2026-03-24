from datetime import datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

def now_vn():
    return datetime.utcnow() + timedelta(hours=7)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False) # In a real app, hash this!
    full_name = db.Column(db.String(120))
    role = db.Column(db.String(20), default='user') # admin, leader, staff, user
    status = db.Column(db.String(20), default='active') # active, inactive
    department = db.Column(db.String(100)) # e.g. IT, HR, Accounting
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
            # Legacy plaintext fallback & auto-migrate
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

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    # status column removed, relying on status_id and relationship
    priority = db.Column(db.String(20), default='Medium')
    category = db.Column(db.String(50))
    # deadline removed
    created_at = db.Column(db.DateTime, default=now_vn)
    updated_at = db.Column(db.DateTime, default=now_vn, onupdate=now_vn)
    due_date = db.Column(db.DateTime)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    rejection_reason = db.Column(db.Text)
    status_id = db.Column(db.Integer, db.ForeignKey('ticket_status.id'))
    
    # Relationships
    status_obj = db.relationship('TicketStatus', backref='tickets', lazy=True)
    comments = db.relationship('Comment', backref='ticket', lazy=True)
    feedback = db.relationship('Feedback', backref='ticket', uselist=False, lazy=True)
    attachments = db.relationship('Attachment', backref='ticket', lazy=True)

    @property
    def status(self):
        return self.status_obj.name if self.status_obj else None
        
    @status.setter
    def status(self, status_name):
        status = TicketStatus.query.filter_by(name=status_name).first()
        if status:
            self.status_id = status.id
            
    @property
    def status_label(self):
        return self.status_obj.label if self.status_obj else self.status
        
    @property
    def status_color(self):
        return self.status_obj.color_class if self.status_obj else 'bg-slate-100'

class TicketStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False) # Internal name: New, Assigned...
    label = db.Column(db.String(100), nullable=False) # Display name: Mới, Đã phân công...
    color_class = db.Column(db.String(100)) # Bootstrap/Tailwind class
    
    def __repr__(self):
        return f'<TicketStatus {self.name}>'

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=now_vn)
    is_internal = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=now_vn)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=now_vn)

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
        except RuntimeError: # Working outside of request context
            ip_address = 'System'
            
    log = SystemLog(
        user_id=user_id,
        action=action,
        details=details,
        ip_address=ip_address
    )
    db.session.add(log)
    db.session.commit()

    def __repr__(self):
        return f'<SystemLog {self.action} by User {self.user_id}>'

class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=now_vn)
