import sqlite3
from app import create_app
from extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        with db.engine.connect() as conn:
            # Check if column exists
            result = conn.execute(text("PRAGMA table_info(ticket)")).fetchall()
            columns = [row[1] for row in result]
            
            if 'deadline' not in columns:
                conn.execute(text("ALTER TABLE ticket ADD COLUMN deadline DATETIME"))
                conn.commit()
                print("Added 'deadline' column to 'ticket' table.")
            else:
                print("'deadline' column already exists.")
    except Exception as e:
        print(f"Error: {e}")
