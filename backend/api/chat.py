from fastapi import APIRouter, HTTPException
from typing import List
from models.schemas import MessageCreate, MessageResponse
from services.chat_service import chat_service

router = APIRouter()

@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(session_id: str):
    messages = chat_service.get_session_messages(session_id)
    return messages

@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
async def add_message(session_id: str, message: MessageCreate):
    message_data = {
        "role": message.role,
        "content": message.content,
        "timestamp": message.timestamp.isoformat() if message.timestamp else None
    }
    
    result = chat_service.add_message(session_id, message_data)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return result