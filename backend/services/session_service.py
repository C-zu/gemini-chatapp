from typing import List, Dict, Any
from .chat_repository import chat_repo

class SessionService:
    def __init__(self):
        self.repository = chat_repo
    
    def get_all_sessions(self) -> Dict[str, Any]:
        return self.repository.get_all_sessions()
    
    def create_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.repository.create_session(session_data)
    
    def delete_session(self, session_id: str) -> bool:
        return self.repository.delete_session(session_id)

session_service = SessionService()