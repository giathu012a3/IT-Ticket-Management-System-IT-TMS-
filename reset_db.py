from app import app, db, User

with app.app_context():
    print("Dropping all tables...")
    db.drop_all()
    print("Creating all tables with new schema...")
    db.create_all()
    
    print("Seeding default users...")
    # Create default users
    admin = User(username='admin', password='password', full_name='System Admin', role='admin')
    leader = User(username='leader', password='password', full_name='Team Leader', role='leader')
    staff = User(username='staff', password='password', full_name='Sarah Jenkins', role='staff')
    user = User(username='user', password='password', full_name='Nguyen Van A', role='user')
    
    db.session.add(admin)
    db.session.add(leader)
    db.session.add(staff)
    db.session.add(user)
    
    db.session.commit()
    print("Database reset successfully! You can now log in.")
