from datetime import datetime
from utils.supabase_client import supabase

class ChatRepository:
    """Repository pattern for database operations - Backend only"""
    
    def __init__(self):
        self.client = supabase.client if supabase.client else None

    def create_session(self, session_data):
        """Create new session - save basic information only"""
        if not self.client:
            return None
            
        data = {
            "session_id": session_data["session_id"],
            "name": session_data["name"],
            "mode": session_data["mode"],
            "created_at": datetime.now().isoformat()
        }
        
        response = self.client.table("chat_sessions").insert(data).execute()
        return response.data[0] if response.data else None

    def add_message(self, session_id, message_data):
        """Add one message to session"""
        if not self.client:
            return None
            
        data = {
            "session_id": session_id,
            "role": message_data["role"],
            "content": message_data["content"],
            "timestamp": message_data.get("timestamp", datetime.now().isoformat()),
            "message_type": message_data.get("type", "text")
        }
        
        response = self.client.table("chat_messages").insert(data).execute()
        return response.data[0] if response.data else None

    def get_session_messages(self, session_id):
        """Get all messages for one session"""
        if not self.client:
            return []
            
        response = self.client.table("chat_messages")\
            .select("*")\
            .eq("session_id", session_id)\
            .order("timestamp")\
            .execute()
            
        return response.data if response.data else []

    def get_all_sessions(self):
        """Get all sessions with message count"""
        if not self.client:
            return {}
            
        # Get sessions
        sessions_response = self.client.table("chat_sessions")\
            .select("*")\
            .order("created_at", desc=True)\
            .execute()
            
        sessions_data = {}
        
        for session in sessions_response.data:
            session_id = session["session_id"]
            
            # Get messages for this session
            messages = self.get_session_messages(session_id)
            
            sessions_data[session_id] = {
                "name": session["name"],
                "mode": session["mode"],
                "created_at": session["created_at"],
                "messages": messages
            }
            
        return sessions_data

    def delete_session(self, session_id):
        """Delete session and all its messages"""
        if not self.client:
            return False
            
        try:
            # Delete files first
            self.delete_session_files(session_id)
            
            # Delete messages first
            self.client.table("chat_messages")\
                .delete()\
                .eq("session_id", session_id)\
                .execute()
                
            # Delete session
            self.client.table("chat_sessions")\
                .delete()\
                .eq("session_id", session_id)\
                .execute()
                
            return True
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False

    def save_session_file(self, session_id, file_type, file_data, file_name=None):
        """Save file data (CSV/Image) for session to database with storage strategy support"""
        if not self.client:
            return None
            
        try:
            data = {
                "session_id": session_id,
                "file_type": file_type,
                "file_name": file_name,
                "file_data": file_data,
                "created_at": datetime.now().isoformat()
            }
            
            # # Check if file already exists then update, else insert
            # existing_file = self.get_session_file(session_id, file_type)
            
            # if existing_file:
            #     response = self.client.table("session_files")\
            #         .update(data)\
            #         .eq("session_id", session_id)\
            #         .eq("file_type", file_type)\
            #         .execute()
            # else:
            response = self.client.table("session_files").insert(data).execute()
                
            print(f"💾 Database save file success for session {session_id}")
            return response.data[0] if response.data else None
            
        except Exception as e:
            print(f"❌ Error saving session file: {e}")
            return None

    def get_session_file(self, session_id, file_type):
        """Get file data for session from database"""
        if not self.client:
            return None
            
        try:
            response = self.client.table("session_files")\
                .select("*")\
                .eq("session_id", session_id)\
                .eq("file_type", file_type)\
                .execute()
                
            if response.data and len(response.data) > 0:
                file_record = response.data[0]
                print(f"✅ Database get file success: {file_type} -> {file_type} for session {session_id}")
                return file_record
            else:
                print(f"📭 File not found in database: {file_type} -> {file_type} for session {session_id}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting session file: {e}")
            return None

    def delete_session_files(self, session_id, file_type=None):
        """Delete file data for session"""
        if not self.client:
            return False
            
        try:
            query = self.client.table("session_files")\
                .delete()\
                .eq("session_id", session_id)
                
            if file_type:
                query = query.eq("file_type", file_type)
                
            query.execute()
            return True
        except Exception as e:
            print(f"❌ Error deleting session files: {e}")
            return False

# Initialize repository instance
chat_repo = ChatRepository()