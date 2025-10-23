import requests
import streamlit as st
import json
from typing import Dict
class APIClient:
    def __init__(self, base_url="http://localhost:8000/api/v1"):
        self.base_url = base_url
    
    def create_session(self, session_data):
        """Create new chat session"""
        try:
            response = requests.post(f"{self.base_url}/sessions", json=session_data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"API Error creating session: {e}")
            return None
    
    def get_session_messages(self, session_id):
        """Get messages for a session"""
        try:
            response = requests.get(f"{self.base_url}/sessions/{session_id}/messages")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"API Error getting messages: {e}")
            return []
    
    def add_message(self, session_id, message_data):
        """Add message to session"""
        try:
            response = requests.post(f"{self.base_url}/sessions/{session_id}/messages", json=message_data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"API Error adding message: {e}")
            return None
    
    def delete_session(self, session_id):
        """Delete session"""
        try:
            response = requests.delete(f"{self.base_url}/sessions/{session_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"API Error deleting session: {e}")
            return None
    
    def get_all_sessions(self):
        """Get all sessions"""
        try:
            response = requests.get(f"{self.base_url}/sessions")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"API Error getting sessions: {e}")
            return {}
    
    def save_session_file(self, session_id, file_type, file_data, file_name=None):
        """Save file data for session with storage strategy support"""
        try:
            # Prepare payload based on file type and storage strategy
            payload = {
                "file_type": file_type,
                "file_data": file_data,
                "file_name": file_name,
            }
            
            
            response = requests.post(f"{self.base_url}/sessions/{session_id}/files", json=payload)
            response.raise_for_status()
            
            result = response.json()
            print(f"💾 API save file success: {file_type} for session {session_id}")
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ API Error saving file {file_type}: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error saving file {file_type}: {e}")
            return None

    def get_session_file(self, session_id, file_type):
        """Get file data for session with storage strategy support"""
        try:
            response = requests.get(f"{self.base_url}/sessions/{session_id}/files/{file_type}")
            
            if response.status_code == 404:
                print(f"📭 File not found: {file_type} for session {session_id}")
                return None
                
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ API get file success: {file_type} for session {session_id}")
            return result
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                print(f"📭 File not found: {file_type} for session {session_id}")
                return None
            else:
                print(f"❌ API HTTP Error getting file {file_type}: {e}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"❌ API Connection Error getting file {file_type}: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error getting file {file_type}: {e}")
            return None
    
    def stream_chat(self, user_input, chat_history):
        """Stream chat response from backend - FIXED"""
        try:
            payload = {
                "user_input": user_input,
                "chat_history": chat_history, 
            }

            response = requests.post(
                f"{self.base_url}/ai/chat",
                json=payload,
                stream=True,
                timeout=100
            )
            
            # DEBUG: check response
            print(f"🔍 API Response status: {response.status_code}")
            if response.status_code != 200:
                print(f"❌ API Error: {response.text}")
            
            return response

        except Exception as e:
            print(f"[AIClient] Streaming error: {e}")
            return None

    def stream_image_chat(self, user_input, image_data, chat_history):
        """Stream image chat response from backend AI"""
        try:
            payload = {
                "user_input": user_input,
                "image_data": image_data,
                "chat_history": chat_history
            }
            response = requests.post(
                f"{self.base_url}/ai/chat/image", 
                json=payload, 
                stream=True,
                timeout=120
            )
            
            print(f"🔍 API Response status: {response.status_code}")
            if response.status_code != 200:
                print(f"❌ API Error: {response.text}")
            
            return response
            
        except Exception as e:
            print(f"API Error streaming image chat: {e}")
            return None
    def csv_chat(self, query: str, dataframe, session_id: str) -> Dict:
        """Send CSV analysis request using CSV string format"""
        try:
            # Convert dataframe to CSV string (more reliable)
            csv_data = ""
            if dataframe is not None and hasattr(dataframe, 'to_csv'):
                csv_data = dataframe.to_csv(index=False)
                print(f"📤 Sending CSV data: {len(csv_data)} characters, {len(dataframe)} rows")
            
            payload = {
                "enhanced_query": query,
                "session_id": session_id,
                "csv_data": csv_data
            }
            
            response = requests.post(
                f"{self.base_url}/ai/chat/csv",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ API Request failed: {e}")
            # Display error details
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"❌ Error details: {error_detail}")
                except:
                    print(f"❌ Status code: {e.response.status_code}")
            
            return {
                "content": f"❌ API Error: {str(e)}",
                "plots": []
            }
# Global instance
api_client = APIClient()