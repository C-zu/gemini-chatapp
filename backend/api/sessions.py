from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from models.schemas import SessionCreate, SessionResponse, FileCreate, FileResponse
from services.session_service import session_service
from services.chat_service import chat_service

router = APIRouter()

@router.get("/sessions", response_model=Dict[str, Any])
async def get_all_sessions():
    return session_service.get_all_sessions()

@router.post("/sessions", response_model=SessionResponse)
async def create_session(session: SessionCreate):
    from datetime import datetime
    session_data = {
        "session_id": session.session_id,
        "name": session.name,
        "mode": session.mode,
        "created_at": datetime.now().isoformat()
    }
    
    result = session_service.create_session(session_data)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create session")
    
    return result

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    success = session_service.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Session deleted successfully"}

@router.post("/sessions/{session_id}/files", response_model=FileResponse)
async def save_session_file(session_id: str, file_data: FileCreate):
    result = chat_service.save_session_file(
        session_id, 
        file_data.file_type, 
        file_data.file_data, 
        file_data.file_name
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return result

@router.get("/sessions/{session_id}/files/{file_type}", response_model=FileResponse)
async def get_session_file(session_id: str, file_type: str):
    result = chat_service.get_session_file(session_id, file_type)
    if not result:
        raise HTTPException(status_code=404, detail="File not found")
    
    return result