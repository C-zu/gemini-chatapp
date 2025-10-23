from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

# Existing schemas
class PlotData(BaseModel):
    data: Dict[str, Any]
    layout: Optional[Dict[str, Any]] = None

class CSVAnalysisResponse(BaseModel):
    content: str
    plots: List[PlotData] = []

class SessionCreate(BaseModel):
    session_id: str
    name: str
    mode: str

class SessionResponse(BaseModel):
    session_id: str
    name: str
    mode: str
    created_at: datetime

class MessageCreate(BaseModel):
    role: str
    content: str
    timestamp: datetime

class MessageResponse(BaseModel):
    id: int
    session_id: str
    role: str
    content: str
    timestamp: datetime

class FileCreate(BaseModel):
    file_type: str
    file_data: Dict[str, Any]
    file_name: Optional[str] = None

class FileResponse(BaseModel):
    id: int
    session_id: str
    file_type: str
    file_name: Optional[str]
    file_data: Dict[str, Any]
    created_at: datetime

# New AI schemas
class ChatMessage(BaseModel):
    role: str
    content: str
    def to_dict(self):
        return {
            "role": self.role,
            "content": self.content
        }

class ChatRequest(BaseModel):
    user_input: str
    chat_history: List[ChatMessage]

class ImageChatRequest(BaseModel):
    user_input: str
    image_data: str
    chat_history: List[ChatMessage]
    
class CSVAnalysisRequest(BaseModel):
    enhanced_query: str
    csv_data: Any
    session_id: Optional[str] = None