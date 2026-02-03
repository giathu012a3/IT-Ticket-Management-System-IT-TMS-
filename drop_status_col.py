from app import app, db
from sqlalchemy import text

def drop_status_column():
    with app.app_context():
        print("Checking schema...")
        
        # Check if column exists
        try:
            result = db.session.execute(text("PRAGMA table_info(ticket)"))
            # Row format: (cid, name, type, notnull, dflt_value, pk)
            columns = [row[1] for row in result.fetchall()]
        except Exception as e:
            print(f"Error checking schema: {e}")
            return
            
        if 'status' not in columns:
            print("Column 'status' is already removed from 'ticket' table.")
            return

        print(f"Current columns: {columns}")
        print("Starting table recreation to drop 'status' column...")

        try:
            # 1. Rename old table
            print("Step 1: Renaming 'ticket' to 'ticket_old'")
            try:
                db.session.execute(text("ALTER TABLE ticket RENAME TO ticket_old"))
            except Exception as e:
                if 'already exists' in str(e):
                    print("ticket_old already exists. Assuming previous rename worked.")
                else:
                    raise e
            
            # 2. Create new table
            print("Step 2: Creating new 'ticket' table from model")
            db.create_all()
            
            # 3. Copy data
            print("Step 3: Copying data")
            # Explicitly map columns shared between old and new schema
            # Old schema has 'status', new does not.
            # We select strict list of columns that exist in new model.
            
            # Note: We assume 'ticket_old' has all these columns.
            cols = [
                'id', 'title', 'description', 'priority', 'category', 'deadline', 
                'created_at', 'updated_at', 'creator_id', 'assigned_to_id', 
                'rejection_reason', 'status_id'
            ]
            
            cols_str = ", ".join(cols)
            # SQL: INSERT INTO ticket (col1, col2) SELECT col1, col2 FROM ticket_old
            sql = f"INSERT INTO ticket ({cols_str}) SELECT {cols_str} FROM ticket_old"
            db.session.execute(text(sql))
            
            # 4. Drop old table
            print("Step 4: Dropping 'ticket_old'")
            db.session.execute(text("DROP TABLE ticket_old"))
            
            db.session.commit()
            print("SUCCESS: 'status' column dropped via recreation.")
            
        except Exception as e:
            db.session.rollback()
            print(f"FAILED: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    drop_status_column()
