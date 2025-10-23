import streamlit as st
from datetime import datetime
from components.sidebar import add_chat_to_sessions
from utils.session_manager import save_current_session
from services.api_client import api_client
from utils.helpers import (
    display_message_timestamp,
    prepare_chat_history_for_api,
    generate_fallback_response
)


def render_core_chat():
    """Core Chat Mode - Multi-turn text conversations with AI assistant"""
    try:
        # Show welcome message for new chat, otherwise display chat history
        if st.session_state.show_new_chat or st.session_state.current_session is None:
            _show_welcome_message()
        else:
            _display_chat_history(st.session_state.current_session)
        
        # Chat input handler
        user_input = st.chat_input("Type your message here...")
        if user_input:
            _process_user_message(user_input, st.session_state.current_session)
            
    except Exception as e:
        st.error(f"❌ Unexpected error in core chat: {str(e)}")
        print(f"❌ Core chat render error: {e}")


def _display_chat_history(current_session_id):
    """Display chat messages from session state without API calls"""
    try:
        # Initialize messages array if not exists
        if "current_messages" not in st.session_state:
            st.session_state.current_messages = []
        
        # Load from API only when needed (new session or session changed)
        if current_session_id and (not st.session_state.current_messages or 
                                  st.session_state.get("last_session_id") != current_session_id):
            _load_messages_from_api(current_session_id)
        
        # Show welcome message if no messages
        if not st.session_state.current_messages:
            _show_welcome_message()
            return
        
        # Render all messages from session state
        for msg in st.session_state.current_messages:
            with st.chat_message(msg["role"]):
                display_message_timestamp(msg)
                st.markdown(msg["content"])
                
    except Exception as e:
        st.error(f"❌ Error displaying chat history: {str(e)}")
        _show_welcome_message()


def _load_messages_from_api(session_id):
    """Load messages from API only when necessary"""
    try:
        db_messages = api_client.get_session_messages(session_id)
        if db_messages:
            st.session_state.current_messages = db_messages
            st.session_state.last_session_id = session_id
            print(f"✅ Loaded {len(db_messages)} messages from API")
        else:
            st.session_state.current_messages = []
            print(f"ℹ️ No messages found for session {session_id}")
            
    except ConnectionError as e:
        st.error("❌ Connection error: Cannot connect to server. Please check your internet connection.")
        st.session_state.current_messages = []
        print(f"❌ Connection error loading messages: {e}")
        
    except TimeoutError as e:
        st.error("❌ Timeout error: Server took too long to respond.")
        st.session_state.current_messages = []
        print(f"❌ Timeout error loading messages: {e}")
        
    except Exception as e:
        st.error(f"❌ Error loading messages: {str(e)}")
        st.session_state.current_messages = []
        print(f"❌ Error loading messages: {e}")


def _show_welcome_message():
    """Display welcome message for new chat sessions"""
    st.info("""
    💬 **Welcome to Core Chat Mode!**
    
    Start a conversation with the AI assistant. This mode supports:
    - Multi-turn conversations with full history
    - Markdown rendering in responses
    - Persistent chat sessions
    - Message timestamps
    - Real-time streaming responses
    """)


def _process_user_message(user_input, current_session_id):
    """Process user message and generate AI response"""
    try:
        current_time = datetime.now()
        
        # Validate user input
        if not user_input or not user_input.strip():
            st.error("❌ Please enter a message.")
            return
            
        if len(user_input.strip()) > 4000:
            st.error("❌ Message too long. Please keep messages under 4000 characters.")
            return
        
        # Display user message
        with st.chat_message("user"):
            st.caption(f"🕒 {current_time.strftime('%H:%M • %b %d, %Y')}")
            st.markdown(user_input)
        _auto_scroll_to_bottom()
        
        # Create new session if needed
        session_id = _ensure_session_exists(user_input, current_session_id)
        if not session_id:
            st.error("❌ Failed to create chat session. Please try again.")
            return
        
        # Generate AI response
        _generate_ai_response(user_input, session_id, current_time)
        
    except Exception as e:
        st.error(f"❌ Error processing message: {str(e)}")
        print(f"❌ Message processing error: {e}")


def _ensure_session_exists(user_input, current_session_id):
    """Create new session only when user sends first message"""
    try:
        if current_session_id is None or st.session_state.show_new_chat:
            # Create session name from user input
            if not user_input or not user_input.strip():
                chat_name = "New Chat"
            else:
                chat_name = user_input.strip()[:40] + ("…" if len(user_input.strip()) > 40 else "")
            
            chat_id = add_chat_to_sessions(chat_name, [])
            
            if not chat_id:
                st.error("❌ Failed to create new chat session.")
                return None
            
            # Update session state
            st.session_state.current_session = chat_id
            st.session_state.show_new_chat = False
            st.session_state.current_messages = []
            
            print(f"🆕 Created session from first message: {chat_id}")
            return chat_id
        
        return current_session_id
        
    except Exception as e:
        st.error(f"❌ Error creating session: {str(e)}")
        print(f"❌ Session creation error: {e}")
        return None


def _generate_ai_response(user_input, session_id, current_time):
    """Generate AI response via backend API with comprehensive error handling"""
    with st.chat_message("assistant"):
        try:
            response_time = datetime.now()
            st.caption(f"🕒 {response_time.strftime('%H:%M • %b %d, %Y')}")
            
            message_placeholder = st.empty()
            full_response = ""
            
            # Show loading indicator
            message_placeholder.markdown("🤔 Thinking...")
            
            # Prepare chat history for API
            try:
                chat_history = prepare_chat_history_for_api(st.session_state.current_messages)
                print(f"📝 Prepared chat history: {len(chat_history)} messages")
            except Exception as e:
                st.error("❌ Error preparing conversation history")
                chat_history = []
                print(f"❌ Chat history preparation error: {e}")
            
            # Call API with timeout handling
            try:
                response = api_client.stream_chat(user_input, chat_history)
                
                if response and response.status_code == 200:
                    # Process streaming response
                    try:
                        for chunk in response.iter_content(decode_unicode=True, chunk_size=1024):
                            if chunk:
                                full_response += chunk
                                message_placeholder.markdown(full_response + "▌")
                        
                        message_placeholder.markdown(full_response)
                        
                        # Validate response content
                        if not full_response.strip():
                            full_response = "I received an empty response. Please try again."
                            message_placeholder.markdown(full_response)
                            
                    except UnicodeDecodeError as e:
                        st.error("❌ Encoding error in response stream")
                        full_response = "I encountered an encoding error. Please try again."
                        message_placeholder.markdown(full_response)
                        
                    except Exception as e:
                        st.error("❌ Error reading response stream")
                        full_response = "I encountered an error while processing the response. Please try again."
                        message_placeholder.markdown(full_response)
                        
                else:
                    # Handle HTTP status codes
                    status_code = response.status_code if response else "Unknown"
                    
                    if status_code == 400:
                        error_msg = "❌ Bad request. Please check your input and try again."
                    elif status_code == 401:
                        error_msg = "❌ Authentication error. Please check your API credentials."
                    elif status_code == 403:
                        error_msg = "❌ Access forbidden. Please check your permissions."
                    elif status_code == 404:
                        error_msg = "❌ Service not found. Please check the endpoint URL."
                    elif status_code == 429:
                        error_msg = "❌ Rate limit exceeded. Please wait a moment and try again."
                    elif status_code == 500:
                        error_msg = "❌ Server error. Please try again later."
                    elif status_code == 502:
                        error_msg = "❌ Bad gateway. The server is temporarily unavailable."
                    elif status_code == 503:
                        error_msg = "❌ Service unavailable. Please try again later."
                    else:
                        error_msg = f"❌ Request failed with status {status_code}. Please try again."
                    
                    st.error(error_msg)
                    full_response = "Sorry, I couldn't process your request at this time. Please try again."
                    message_placeholder.markdown(full_response)
                    
            except ConnectionError as e:
                st.error("❌ Connection error: Cannot connect to the AI service. Please check your internet connection.")
                full_response = "I'm having trouble connecting to the AI service. Please check your internet connection and try again."
                message_placeholder.markdown(full_response)
                
            except TimeoutError as e:
                st.error("❌ Timeout error: The AI service took too long to respond.")
                full_response = "The request timed out. Please try again with a shorter message or try again later."
                message_placeholder.markdown(full_response)
                
            except Exception as e:
                st.error(f"❌ Unexpected API error: {str(e)}")
                full_response = "An unexpected error occurred. Please try again."
                message_placeholder.markdown(full_response)
            
            # Update chat history
            _update_chat_history(user_input, full_response, session_id, current_time, response_time)
            
        except Exception as e:
            # Critical error handling
            critical_error_msg = "❌ **Critical Error**: Unable to generate response. Please refresh the page and try again."
            st.caption(f"🕒 {datetime.now().strftime('%H:%M • %b %d, %Y')}")
            st.error("A critical error occurred.")
            _handle_response_error(user_input, session_id, current_time, e)


def _update_chat_history(user_input, ai_response, session_id, user_time, ai_time):
    """Update chat history in session state and save to database"""
    try:
        # Add new messages to session state
        new_messages = st.session_state.current_messages + [
            {
                "role": "user", 
                "content": user_input,
                "timestamp": user_time.isoformat()
            },
            {
                "role": "assistant", 
                "content": ai_response,
                "timestamp": ai_time.isoformat()
            }
        ]
        
        # Limit message history to prevent memory issues (keep last 50 messages)
        if len(new_messages) > 50:
            new_messages = new_messages[-50:]
            print(f"ℹ️ Truncated chat history to 50 messages")
        
        # Update session state
        st.session_state.current_messages = new_messages
        
        # Save to database with error handling
        try:
            save_current_session(new_messages)
            print(f"💾 Saved {len(new_messages)} messages to database")
        except ConnectionError as e:
            st.error("❌ Connection error: Could not save conversation. Your messages may not be persisted.")
            print(f"❌ Database connection error: {e}")
        except Exception as e:
            st.error("❌ Error saving conversation. Your messages may not be persisted.")
            print(f"❌ Database save error: {e}")
            
    except Exception as e:
        st.error(f"❌ Error updating chat history: {str(e)}")
        print(f"❌ Chat history update error: {e}")


def _update_session_name(user_input, session_id):
    """Update session name based on first user message"""
    try:
        if not user_input or not user_input.strip():
            return
            
        new_name = user_input.strip()[:40] + ("…" if len(user_input.strip()) > 40 else "")
        
        if session_id in st.session_state.all_sessions:
            st.session_state.all_sessions[session_id]["name"] = new_name
            print(f"📝 Updated session name to: {new_name}")
            
    except Exception as e:
        print(f"❌ Error updating session name: {e}")


def _handle_response_error(user_input, session_id, current_time, error):
    """Handle errors during response generation"""
    try:
        error_msg = f"❌ **System Error**: {str(error)}"
        error_time = datetime.now()
        
        # Display error message
        st.caption(f"🕒 {error_time.strftime('%H:%M • %b %d, %Y')}")
        st.error("An unexpected error occurred. Our team has been notified.")
        
        # Update session state with error message
        new_messages = st.session_state.current_messages + [
            {
                "role": "user", 
                "content": user_input,
                "timestamp": current_time.isoformat()
            },
            {
                "role": "assistant", 
                "content": error_msg,
                "timestamp": error_time.isoformat()
            }
        ]
        
        st.session_state.current_messages = new_messages
        
        # Save to database
        try:
            save_current_session(new_messages)
        except Exception as save_error:
            print(f"❌ Failed to save error messages: {save_error}")
            
    except Exception as e:
        print(f"❌ Critical error in error handling: {e}")
        # Reset state to avoid infinite error loops
        st.session_state.current_messages = []
        st.error("A critical error occurred. Please refresh the page.")
        
    
def _auto_scroll_to_bottom():
    """Force scroll to bottom of the chat container."""
    st.markdown(
        """
        <script>
        var chatContainer = window.parent.document.querySelector('.stChatMessageContainer');
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        </script>
        """,
        unsafe_allow_html=True
    )