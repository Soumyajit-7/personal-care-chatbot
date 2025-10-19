from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    user_id: str
    requires_human: bool = False
    contact_info: Optional[str] = None

class ScraperInput(BaseModel):
    url: str
    output_csv: str

class ProductInfo(BaseModel):
    name: str
    brand: str
    price: str
    link: str
    image: str
    description: str
    breadcrumbs: str
    rating: str = "" 
    review_count: str = "" 
    reviews: str = "" 

class ConversationHistory(BaseModel):
    id: int
    session_id: str
    user_id: str
    role: str
    content: str
    timestamp: datetime
    csv_file: Optional[str] = None
