from ..extensions import db
from .utils import now_vn

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default='Medium')
    category = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=now_vn)
    updated_at = db.Column(db.DateTime, default=now_vn, onupdate=now_vn)
    due_date = db.Column(db.DateTime)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    rejection_reason = db.Column(db.Text)
    status_id = db.Column(db.Integer, db.ForeignKey('ticket_status.id'))
    
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
    name = db.Column(db.String(50), unique=True, nullable=False)
    label = db.Column(db.String(100), nullable=False)
    color_class = db.Column(db.String(100))
    
    def __repr__(self):
        return f'<TicketStatus {self.name}>'

class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=now_vn)
