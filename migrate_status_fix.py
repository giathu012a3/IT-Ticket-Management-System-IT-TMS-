from app import app, db
from models import Ticket, TicketStatus
import sqlalchemy
from sqlalchemy import text

def migrate_statuses():
    with app.app_context():
        # First ensure statuses exist
        statuses = [
            {'name': 'New', 'label': 'Mới'},
            {'name': 'Assigned', 'label': 'Đã phân công'},
            {'name': 'In Progress', 'label': 'Đang xử lý'},
            {'name': 'Resolved', 'label': 'Đã giải quyết'},
            {'name': 'Closed', 'label': 'Đóng'},
            {'name': 'Rejected', 'label': 'Từ chối'},
            {'name': 'Waiting', 'label': 'Đang chờ'}
        ]
        
        status_map = {}
        for s_data in statuses:
            s_obj = TicketStatus.query.filter_by(name=s_data['name']).first()
            if not s_obj:
                print(f"Status {s_data['name']} missing! Run init_db.py first or we can create it here.")
                # Fallback create
                s_obj = TicketStatus(name=s_data['name'], label=s_data['label'])
                db.session.add(s_obj)
                db.session.commit()
            status_map[s_data['name']] = s_obj.id
            
        print("Status map built:", status_map)
        
        # Now try to read raw status from DB if possible using raw SQL
        # We can't access Ticket.status column via ORM anymore
        
        try:
            result = db.session.execute(text("SELECT id, status FROM ticket"))
            rows = result.fetchall()
            
            count = 0
            for row in rows:
                t_id = row[0]
                old_status = row[1]
                
                if old_status and old_status in status_map:
                    # Update status_id
                    db.session.execute(
                        text("UPDATE ticket SET status_id = :sid WHERE id = :tid"),
                        {'sid': status_map[old_status], 'tid': t_id}
                    )
                    count += 1
            
            db.session.commit()
            print(f"Migrated {count} tickets from string status to status_id.")
            
        except Exception as e:
            print(f"Error accessing raw status column (maybe it's already gone?): {e}")
            # If we can't read old status, set default 'New' for those with null status_id
            print("Setting default 'New' for tickets with missing status_id...")
            
            new_id = status_map.get('New')
            if new_id:
                db.session.execute(
                    text("UPDATE ticket SET status_id = :sid WHERE status_id IS NULL"),
                    {'sid': new_id}
                )
                db.session.commit()

if __name__ == '__main__':
    migrate_statuses()
