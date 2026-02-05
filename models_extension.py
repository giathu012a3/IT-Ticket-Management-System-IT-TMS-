from extensions import db
from models import now_vn

class SystemLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(50), nullable=False)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=now_vn)

    user = db.relationship('User', backref=db.backref('system_logs', lazy=True))

    def __repr__(self):
        return f'<SystemLog {self.action} by User {self.user_id}>'
