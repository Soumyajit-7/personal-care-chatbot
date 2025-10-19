import uuid
from datetime import datetime

def generate_session_id() -> str:
    """Generate a unique session ID"""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"session_{timestamp}_{unique_id}"

def generate_user_id() -> str:
    """Generate a unique user ID"""
    return f"user_{uuid.uuid4()}"

def get_csv_filename(session_id: str, user_id: str) -> str:
    """Generate CSV filename based on session and user"""
    return f"{user_id}_{session_id}_products.csv"
