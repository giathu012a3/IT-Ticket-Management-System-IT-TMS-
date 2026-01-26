from app import app, db
from models import User

def init_db():
    with app.app_context():
        db.create_all()
        
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
        print("Database initialized and default users created.")

if __name__ == '__main__':
    init_db()
