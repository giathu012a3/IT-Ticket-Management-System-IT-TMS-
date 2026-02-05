from app import app
from extensions import db
from models import SystemLog

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("Database migration completed: SystemLog table created.")
