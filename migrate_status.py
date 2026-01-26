from app import create_app
from extensions import db
from models import Ticket, TicketStatus
from sqlalchemy import text

app = create_app()

STATUS_DATA = [
    {
        'name': 'New',
        'label': 'Mới',
        'color_class': 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-500'
    },
    {
        'name': 'Assigned',
        'label': 'Đã phân công',
        'color_class': 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-500'
    },
    {
        'name': 'In Progress',
        'label': 'Đang xử lý',
        'color_class': 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-500'
    },
    {
        'name': 'Waiting',
        'label': 'Chờ phản hồi',
        'color_class': 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-500'
    },
    {
        'name': 'Resolved',
        'label': 'Đã giải quyết',
        'color_class': 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-500'
    },
    {
        'name': 'Closed',
        'label': 'Hoàn thành',
        'color_class': 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-400'
    },
    {
        'name': 'Rejected',
        'label': 'Đã từ chối',
        'color_class': 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-500'
    }
]

with app.app_context():
    try:
        # 0. Alter table manually because create_all doesn't update existing tables
        with db.engine.connect() as conn:
            try:
                conn.execute(text("ALTER TABLE ticket ADD COLUMN status_id INTEGER REFERENCES ticket_status(id)"))
                conn.commit()
                print("Added status_id column.")
            except Exception as e:
                print(f"Column might exist: {e}")

        # 1. Create table (TicketStatus)
        db.create_all()
        print("Ensured tables exist.")

        # 2. Populate Statuses
        print("Populating TicketStatus...")
        for data in STATUS_DATA:
            existing = TicketStatus.query.filter_by(name=data['name']).first()
            if not existing:
                new_status = TicketStatus(
                    name=data['name'],
                    label=data['label'],
                    color_class=data['color_class']
                )
                db.session.add(new_status)
        db.session.commit()
        print("Statuses populated.")

        # 3. Migrate Data
        print("Migrating Ticket Data...")
        tickets = Ticket.query.all()
        
        # Cache statuses for lookup
        status_map = {s.name: s.id for s in TicketStatus.query.all()}
        
        count = 0
        for ticket in tickets:
            # Check old status column (SQLAlchemy might still map it if we haven't removed it, 
            # but we can access it if the model definition still has it or via raw SQL if not.
            # In this case, I updated the model but KEPT 'status' column in DB (implied), 
            # but removed it from Model definition? 
            # Wait, I removed 'status' from model definition? 
            # Let's check models.py edit. I removed it? 
            # Ah, in the replace_file_content I removed 'status = db.Column...' 
            # So `ticket.status` might fail if I try to access it via ORM?
            # Actually, if the column exists in DB but not in model, I can't access it via ORM easily.
            # I should use raw SQL to get the old status.
            pass
        
        # Use raw SQL to update to be safe and independent of Model definition
        with db.engine.connect() as conn:
            # We need to read the old status. 
            # Since I modified the model class, `ticket.status` attribute is gone from the Python side 
            # unless I revert or use raw SQL.
            
            # Let's read all tickets with raw sql
            result = conn.execute(text("SELECT id, status FROM ticket"))
            tickets_raw = result.fetchall()
            
            for t_row in tickets_raw:
                t_id = t_row[0]
                t_status_str = t_row[1]
                
                if t_status_str in status_map:
                    new_id = status_map[t_status_str]
                    conn.execute(
                        text("UPDATE ticket SET status_id = :sid WHERE id = :tid"),
                        {"sid": new_id, "tid": t_id}
                    )
                    count += 1
            
            conn.commit()
            
        print(f"Migrated {count} tickets.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
