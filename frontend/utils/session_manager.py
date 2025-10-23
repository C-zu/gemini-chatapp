import streamlit as st
import uuid
import pandas as pd
import base64
from services.api_client import api_client
from datetime import datetime

def add_chat_to_sessions(chat_name, messages):
    """Add new chat to all_sessions and API"""
    chat_id = str(uuid.uuid4())
    
    session_data = {
        "name": chat_name,
        "messages": messages.copy(),
        "mode": st.session_state.current_mode
    }
    
    # Add to local state
    st.session_state.all_sessions[chat_id] = session_data
    st.session_state.current_session = chat_id
    st.session_state.show_new_chat = False
    
    # Save to API
    if api_client.base_url:
        try:
            db_data = {
                "session_id": chat_id,
                "name": chat_name,
                "mode": st.session_state.current_mode,
            }
            result = api_client.create_session(db_data)
            
            if result:
                # Update session ID with server ID if needed
                # chat_id = result.get("session_id", chat_id)
                
                # Save each message if available
                for msg in messages:
                    api_client.add_message(chat_id, msg)
                    
        except Exception as e:
            print(f"❌ Error saving session via API: {e}")
    
    return chat_id

def save_session_file_data(session_id, file_type, file_data, file_name=None):
    """Save file data (CSV/Image) for session to API"""
    print(f"🔍 save_session_file_data called: session_id={session_id}, file_type={file_type}, file_name={file_name}")
    
    if not api_client.base_url or not session_id:
        print(f"❌ Cannot save: client={api_client.base_url is not None}, session_id={session_id}")
        return False
        
    try:
        print(f"💾 Starting save_session_file_data...")
        
        # CSV INFO (metadata only)
        if file_type == 'csv_info' and isinstance(file_data, dict):
            print("📊 Storing CSV info metadata...")
            file_data_to_save = {
                'file_type': 'csv_info',
                'metadata': file_data,
                'has_full_data': False
            }
        
        # CSV DATA (full data as CSV string)
        elif file_type == 'csv_data' and isinstance(file_data, dict):
            print("📊 Storing CSV full data as CSV string...")
            file_data_to_save = {
                'file_type': 'csv_full',
                'csv_string': file_data.get('csv_string', ''),
                'rows': file_data.get('rows', 0),
                'columns': file_data.get('columns', 0),
                'file_name': file_data.get('file_name', 'data.csv'),
                'has_full_data': True
            }
        
        # IMAGE INFO (metadata only)
        elif file_type == 'image_info' and isinstance(file_data, dict):
            print("🖼️ Storing image info metadata...")
            file_data_to_save = {
                'file_type': 'image_info',
                'metadata': file_data,
                'has_full_data': False
            }
        
        # IMAGE DATA (full image for small files)
        elif file_type == 'image' and isinstance(file_data, str):
            print("🖼️ Storing image data...")
            
            # Extract base64 from data URL if needed
            if file_data.startswith('data:image'):
                file_data = file_data.split(',')[1] if ',' in file_data else file_data
            
            print(f"🖼️ Storing full image data...")
            
            file_data_to_save = {
                'image_data': file_data,
                'file_type': 'image_base64',
                'format': 'base64',
                'metadata': {
                    'file_name': file_name or 'image.jpg',
                    'size_bytes': int(len(file_data) / 0.75),  # Approximate original size
                    'size_mb': len(file_data) / (1024 * 1024) * 0.75
                },
                'has_full_data': True
            }
        else:
            # FALLBACK: save directly if not specific type
            print(f"📁 Storing generic file data...")
            file_data_to_save = file_data

        print(f"💾 Calling api_client.save_session_file...")
        
        result = api_client.save_session_file(
            session_id=session_id,
            file_type=file_type,
            file_data=file_data_to_save,
            file_name=file_name
        )
        
        print(f"💾 API save result: {result is not None}")
        
        print(f"✅ Saved {file_type} file to API for session {session_id}")
        return result is not None
        
    except Exception as e:
        print(f"❌ Error saving session file data: {e}")
        import traceback
        traceback.print_exc()
        return False

def load_session_file_data(session_id, file_type):
    """Load file data (CSV/Image) from API"""
    if not api_client.base_url or not session_id:
        return None
        
    try:
        file_record = api_client.get_session_file(session_id, file_type)
        if file_record and file_record.get('file_data'):
            file_data = file_record['file_data']
            
            # CSV INFO (metadata only)
            if file_type == 'csv_info' and isinstance(file_data, dict):
                if 'metadata' in file_data:
                    print(f"📊 Loaded CSV info: {file_data['metadata']}")
                    return file_data['metadata']
                return file_data
           
            # CSV DATA (full data from CSV string)
            elif file_type == 'csv_data' and isinstance(file_data, dict):
                if 'csv_string' in file_data:
                    try:
                        from io import StringIO
                        csv_string = file_data['csv_string']
                        full_df = pd.read_csv(StringIO(csv_string))
                        print(f"✅ Restored full DataFrame from CSV string: {full_df.shape}")
                        return full_df
                    except Exception as e:
                        print(f"❌ Error parsing full CSV string: {e}")
                        return None
                return file_data
            
            # IMAGE INFO (metadata only)
            elif file_type == 'image_info' and isinstance(file_data, dict):
                if 'metadata' in file_data:
                    print(f"🖼️ Loaded image info: {file_data['metadata']}")
                    return file_data['metadata']
                return file_data
            
            # IMAGE DATA (full image for small files)
            elif file_type == 'image' and isinstance(file_data, dict):
                if 'image_data' in file_data:
                    image_base64 = file_data['image_data']
                    print(f"✅ Restored image from base64: {len(image_base64)} bytes")
                    return image_base64
                return file_data
            
            print(f"✅ Loaded {file_type} file from API for session {session_id}")
            return file_data
        
        print(f"❌ No file data found for session {session_id}, type {file_type}")
        return None
        
    except Exception as e:
        print(f"❌ Error loading session file data: {e}")
        import traceback
        traceback.print_exc()
        return None



def delete_chat_session(chat_id, name):
    """Delete chat session"""
    if chat_id in st.session_state.all_sessions:
        del st.session_state.all_sessions[chat_id]
        
        if api_client.base_url:
            try:
                api_client.delete_session(chat_id)
            except Exception as e:
                print(f"❌ Error deleting session: {e}")
        
        if st.session_state.current_session == chat_id:
            create_new_chat()
    
    st.toast(f"🗑️ Deleted: {name}")
    st.rerun()

def clear_all_chats():
    """Delete all chats"""
    if api_client.base_url:
        try:
            for chat_id in list(st.session_state.all_sessions.keys()):
                api_client.delete_session(chat_id)
        except Exception as e:
            print(f"❌ Error deleting sessions: {e}")
    
    st.session_state.all_sessions.clear()
    create_new_chat()
    st.toast("🗑️ Deleted all chats")
    st.rerun()

def load_sessions_from_database():
    """Load sessions from API"""
    if api_client.base_url:
        try:
            db_sessions = api_client.get_all_sessions()
            if db_sessions:
                st.session_state.all_sessions = db_sessions
                print(f"✅ Loaded {len(db_sessions)} sessions from API")
        except Exception as e:
            st.error(f"❌ Error loading sessions: {e}")

def save_current_session(db_messages):
    """Save current session to API - ONLY save new messages"""
    if not api_client.base_url or not st.session_state.current_session:
        return
    
    try:
        current_id = st.session_state.current_session
        
        # Get current messages from API to compare
        existing_db_messages = api_client.get_session_messages(current_id)
        
        # Only save new messages (not already in API)
        if len(db_messages) > len(existing_db_messages):
            new_messages = db_messages[len(existing_db_messages):]
            
            for msg in new_messages:
                api_client.add_message(current_id, {
                    "role": msg["role"],
                    "content": msg["content"],
                    "timestamp": msg.get("timestamp"),
                })
            print(f"💾 Saved {len(new_messages)} new messages for session {current_id}")
                
    except Exception as e:
        print(f"⚠️ Error saving session: {e}")

def create_new_chat():
    """Prepare for new chat - DO NOT create chat_id here"""
    st.session_state.current_session = None
    st.session_state.show_new_chat = True
    
    # Reset messages
    if "current_messages" in st.session_state:
        st.session_state.current_messages = []
    
    print("🆕 Prepared for new chat - waiting for user input")

# Helper functions for image processing
def encode_image_to_base64(image_file):
    """Encode image file to base64 string"""
    try:
        image_bytes = image_file.read()
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        return encoded_image
    except Exception as e:
        print(f"❌ Error encoding image: {e}")
        return None

def get_image_data_url(base64_string, mime_type="image/jpeg"):
    """Convert base64 string to data URL for display"""
    return f"data:{mime_type};base64,{base64_string}"