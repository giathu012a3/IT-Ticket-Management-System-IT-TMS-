from datetime import datetime
from flask_login import UserMixin
from extensions import db

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False) # In a real app, hash this!
    full_name = db.Column(db.String(120))
    role = db.Column(db.String(20), default='user') # admin, leader, staff, user
    status = db.Column(db.String(20), default='active') # active, inactive

    tickets_created = db.relationship('Ticket', foreign_keys='Ticket.creator_id', backref='creator', lazy=True)
    tickets_assigned = db.relationship('Ticket', foreign_keys='Ticket.assigned_to_id', backref='assigned_to', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='New')
    priority = db.Column(db.String(20), default='Medium')
    category = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    rejection_reason = db.Column(db.Text)
    status_id = db.Column(db.Integer, db.ForeignKey('ticket_status.id'))
    
    # Relationships
    status_obj = db.relationship('TicketStatus', backref='tickets', lazy=True)
    comments = db.relationship('Comment', backref='ticket', lazy=True)
    feedback = db.relationship('Feedback', backref='ticket', uselist=False, lazy=True)

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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_internal = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
