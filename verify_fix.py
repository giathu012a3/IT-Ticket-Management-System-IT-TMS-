from app import app, db
from models import Ticket, User, TicketStatus

def verify_ticket_creation():
    with app.app_context():
        # Ensure 'New' status exists
        new_status = TicketStatus.query.filter_by(name='New').first()
        if not new_status:
            print("FAIL: 'New' status not found!")
            return

        # Get a user
        user = User.query.filter_by(username='user').first()
        if not user:
            print("FAIL: No user found to create ticket.")
            return

        # 1. Test Creation
        print("Testing Ticket Creation...")
        t = Ticket(
            title="Verification Ticket",
            description="Testing status fix",
            creator_id=user.id
        )
        # Emulate the route logic
        t.status_id = new_status.id
        
        db.session.add(t)
        db.session.commit()
        
        # reload
        t_id = t.id
        db.session.expire_all()
        t_loaded = Ticket.query.get(t_id)
        
        print(f"Ticket ID: {t_loaded.id}")
        print(f"Status ID: {t_loaded.status_id}")
        print(f"Status Property: {t_loaded.status}") # Should be 'New'
        print(f"Status Label: {t_loaded.status_label}")
        
        if t_loaded.status_id == new_status.id and t_loaded.status == 'New':
            print("PASS: Ticket creation set status correctly.")
        else:
            print(f"FAIL: Expected status ID {new_status.id}, got {t_loaded.status_id}")

        # 2. Test Partial Update (Setter)
        print("\nTesting Status Update via Setter...")
        # Try setting status to 'In Progress'
        # The setter: status = TicketStatus.query.filter_by(name=status_name).first(); self.status_id = status.id
        t_loaded.status = 'In Progress' 
        db.session.commit()
        
        db.session.expire_all()
        t_updated = Ticket.query.get(t_id)
        print(f"Updated Status ID: {t_updated.status_id}")
        print(f"Updated Status: {t_updated.status}")
        
        in_progress = TicketStatus.query.filter_by(name='In Progress').first()
        if t_updated.status_id == in_progress.id and t_updated.status == 'In Progress':
            print("PASS: Ticket status update via setter worked.")
        else:
            print("FAIL: Ticket status update failed.")

        # Cleanup
        db.session.delete(t_loaded)
        db.session.commit()
        print("\nCleanup verification ticket done.")

if __name__ == '__main__':
    verify_ticket_creation()
