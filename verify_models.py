from app import create_app
from extensions import db
from models import User, Ticket

app = create_app()

with app.app_context():
    try:
        db.create_all()
        print("Database created successfully.")
        
        # Test relationships
        if not User.query.filter_by(username='test').first():
            u = User(username='test', password='pw')
            db.session.add(u)
            db.session.commit()
        else:
            u = User.query.filter_by(username='test').first()
        
        t = Ticket(title='Test', description='Desc', creator_id=u.id)
        db.session.add(t)
        db.session.commit()
        
        print(f"User tickets created: {u.tickets_created}")
        
        # Test assigned tickets
        t.assigned_to_id = u.id
        db.session.commit()
        print(f"User tickets assigned: {u.tickets_assigned}")
        
        print(f"Ticket creator: {t.creator}")
        
    except Exception as e:
        print(f"Error: {e}")
