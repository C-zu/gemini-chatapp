from datetime import datetime
import streamlit as st
import json

def display_message_timestamp(msg):
    """Display formatted timestamp for chat messages"""
    if "timestamp" not in msg or not msg["timestamp"]:
        return
        
    try:
        if isinstance(msg["timestamp"], str):
            timestamp = datetime.fromisoformat(msg["timestamp"])
        else:
            timestamp = msg["timestamp"]
        
        formatted_time = timestamp.strftime("%H:%M")
        formatted_date = timestamp.strftime("%b %d, %Y")
        st.caption(f"🕒 {formatted_time} • {formatted_date}")
    except (ValueError, AttributeError):
        st.caption("🕒 Recent")

def prepare_chat_history_for_api(messages):
    """Convert messages to API-friendly format - FIXED"""
    if not messages:
        return []
    
    api_messages = []
    for msg in messages:
        # ENSURE always simple dict
        if isinstance(msg, dict):
            clean_msg = {
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            }
        else:
            # If object, extract data
            clean_msg = {
                "role": getattr(msg, "role", "user"),
                "content": getattr(msg, "content", str(msg))
            }
        
        # Only keep necessary fields
        api_messages.append(clean_msg)
    
    print(f"🔍 Prepared {len(api_messages)} clean messages for API")
    return api_messages

def stream_api_response(api_response, message_placeholder):
    """Stream response from API"""
    full_response = ""
    
    try:
        for line in api_response.iter_lines():
            if line:
                line_text = line.decode('utf-8').strip()
                if line_text.startswith('data: '):
                    data_str = line_text[6:]  # Remove 'data: ' prefix
                    try:
                        data = json.loads(data_str)
                        if 'content' in data:
                            full_response += data['content']
                            message_placeholder.markdown(full_response + "▌")
                    except json.JSONDecodeError:
                        continue
    
    except Exception as e:
        print(f"Stream reading error: {e}")
    
    return full_response

def generate_fallback_response(message_placeholder, fallback_text="I'm sorry, I couldn't process your request. Please try again."):
    """Generate fallback response when API fails"""
    message_placeholder.markdown(fallback_text)
    return fallback_text