import os
from dotenv import load_dotenv

# Load các biến từ file .env
load_dotenv()

class Config:
    # Lấy SECRET_KEY từ .env, nếu không có thì dùng mặc định
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'default-secret-key'
    
    # Đường dẫn Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///instance/tickets.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Cấu hình Upload
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or os.path.join('app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max limit
