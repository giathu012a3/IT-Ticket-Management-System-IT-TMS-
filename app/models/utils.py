from datetime import datetime, timedelta

def now_vn():
    return datetime.utcnow() + timedelta(hours=7)
