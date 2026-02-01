from app import app, db
from models import User

def init_db():
    with app.app_context():
        db.create_all()
        
        # Seed Ticket Statuses
        from models import TicketStatus
        statuses = [
            {'name': 'New', 'label': 'Mới', 'color_class': 'bg-blue-100 text-blue-800'},
            {'name': 'Assigned', 'label': 'Đã phân công', 'color_class': 'bg-indigo-100 text-indigo-800'},
            {'name': 'In Progress', 'label': 'Đang xử lý', 'color_class': 'bg-yellow-100 text-yellow-800'},
            {'name': 'Resolved', 'label': 'Đã giải quyết', 'color_class': 'bg-green-100 text-green-800'},
            {'name': 'Closed', 'label': 'Đóng', 'color_class': 'bg-gray-100 text-gray-800'},
            {'name': 'Rejected', 'label': 'Từ chối', 'color_class': 'bg-red-100 text-red-800'},
            {'name': 'Waiting', 'label': 'Đang chờ', 'color_class': 'bg-orange-100 text-orange-800'}
        ]
        
        for status_data in statuses:
            if not TicketStatus.query.filter_by(name=status_data['name']).first():
                new_status = TicketStatus(**status_data)
                db.session.add(new_status)
        
        # Check if users exist
        if not User.query.filter_by(username='user').first():
            user = User(username='user', password='password', full_name='Regular User', role='user')
            db.session.add(user)
            
        if not User.query.filter_by(username='leader').first():
            leader = User(username='leader', password='password', full_name='IT Leader', role='leader')
            db.session.add(leader)
            
        if not User.query.filter_by(username='staff').first():
            staff = User(username='staff', password='password', full_name='IT Staff', role='staff')
            db.session.add(staff)
            
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', password='password', full_name='System Admin', role='admin')
            db.session.add(admin)
            
        db.session.commit()
        print("Database initialized, statuses seeded, and default users created.")

if __name__ == '__main__':
    init_db()
