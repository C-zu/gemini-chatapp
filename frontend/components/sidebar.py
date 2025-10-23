import streamlit as st
from utils.session_manager import (
    add_chat_to_sessions, 
    delete_chat_session, 
    clear_all_chats,
    create_new_chat,
    load_sessions_from_database
)
from services.api_client import api_client

def render_sidebar():
    st.sidebar.markdown("""
    <style>
    .sidebar-chat-list {
        max-height: 400px;
        overflow-y: auto;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 4px;
    }
    .sidebar-chat-item {
        margin: 2px 0;
        transition: all 0.2s ease;
    }
    .sidebar-chat-item:hover {
        transform: translateX(2px);
    }
    .active-chat {
        background-color: #f0f2f6;
        border-left: 3px solid #ff4b4b;
    }
    </style>
    """, unsafe_allow_html=True)

    # Initialize session state
    if "all_sessions" not in st.session_state:
        st.session_state.all_sessions = {}
    if "current_session" not in st.session_state:
        st.session_state.current_session = None
    if "show_new_chat" not in st.session_state:
        st.session_state.show_new_chat = True
    if "current_mode" not in st.session_state:
        st.session_state.current_mode = "core"
    if "sessions_loaded" not in st.session_state:
        load_sessions_from_database()
        st.session_state.sessions_loaded = True

    with st.sidebar:
        status_text = "🟢 API Connected" if api_client.base_url else "🟡 Local"
        st.caption(status_text)
        
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        
        # Mode selection with auto new chat
        mode_cols = st.columns(3)
        modes = [("💬", "core"), ("🖼️", "image"), ("📊", "csv")]
        
        current_mode = st.session_state.current_mode
        
        for i, (icon, mode) in enumerate(modes):
            with mode_cols[i]:
                if st.button(
                    icon, 
                    key=f"mode_{mode}",
                    use_container_width=True,
                    type="primary" if current_mode == mode else "secondary"
                ):
                    if mode != current_mode:
                        # Switch mode and create new chat in that mode
                        switch_mode_and_create_chat(mode)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Remove model selection since it's now in backend
        st.info("AI Model: Gemini 2.5 Flash (Backend)")
        
        # New Chat button - creates chat in current mode
        if st.button("✨ New Chat", use_container_width=True, key="new_chat_main"):
            create_new_chat()  # This will use the current mode
            st.rerun()
        
        st.markdown("---")
        
        st.markdown("**Chats**")
        
        if st.session_state.all_sessions:
            st.markdown('<div class="sidebar-chat-list">', unsafe_allow_html=True)
            
            # Get sorted chats - ALWAYS sort when rendering
            sorted_chats = get_sorted_sessions()
            
            for chat_id, chat_data in sorted_chats[:15]:  # Show only top 15
                render_chat_item_fast(chat_id, chat_data)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            total_chats = len(st.session_state.all_sessions)
            if total_chats > 15:
                st.caption(f"... and {total_chats - 15} more chats")
        else:
            st.info("No chats yet", icon="💬")
        
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        
        if st.session_state.all_sessions:
            if st.button("🗑️ Clear All", use_container_width=True, type="secondary", key="clear_all_main"):
                clear_all_chats()
                
        st.markdown('</div>', unsafe_allow_html=True)

def get_sorted_sessions():
    """Get sessions sorted by creation time (newest first) with caching"""
    if not st.session_state.all_sessions:
        return []
    
    # Check cache to avoid unnecessary sorting
    current_session_count = len(st.session_state.all_sessions)
    if (hasattr(st.session_state, 'cached_sorted_sessions') and 
        st.session_state.cached_sorted_sessions_count == current_session_count):
        return st.session_state.cached_sorted_sessions
    
    # Sort by created_at timestamp, newest first
    sorted_sessions = sorted(
        list(st.session_state.all_sessions.items()),
        key=lambda x: x[1].get("created_at", ""), 
        reverse=True
    )
    
    # Cache results
    st.session_state.cached_sorted_sessions = sorted_sessions
    st.session_state.cached_sorted_sessions_count = current_session_count
    
    return sorted_sessions

def switch_mode_and_create_chat(new_mode):
    """Switch to new mode and prepare for new chat"""
    # Only switch mode and reset state, DO NOT create chat_id
    st.session_state.current_mode = new_mode
    st.session_state.current_session = None
    st.session_state.show_new_chat = True
    
    # Reset messages and temp data
    if "current_messages" in st.session_state:
        st.session_state.current_messages = []
    
    # Reset temp data
    temp_keys = ['temp_image_data', 'uploaded_image_name', 'temp_df', 'temp_csv_name']
    for key in temp_keys:
        if hasattr(st.session_state, key):
            delattr(st.session_state, key)
    
    st.rerun()

def render_chat_item_fast(chat_id, chat_data):
    """Render chat item with mode awareness"""
    name = chat_data.get("name", "Untitled")
    mode = chat_data.get("mode", "core")
    
    mode_icons = {"core": "💬", "image": "🖼️", "csv": "📊"}
    icon = mode_icons.get(mode, "💭")
    
    display_name = name[:20] + "..." if len(name) > 20 else name
    
    is_active = chat_id == st.session_state.current_session
    
    col1, col2 = st.columns([0.85, 0.15])
    
    with col1:
        with st.container():
            if st.button(
                f"{icon} {display_name}", 
                key=f"btn_{chat_id}",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                load_chat_session_fast(chat_id, chat_data)
    
    with col2:
        if st.button(
            "❌", 
            key=f"del_{chat_id}",
            help=f"Delete {name}",
            use_container_width=True
        ):
            delete_chat_session(chat_id, name)
            st.rerun()

def load_chat_session_fast(chat_id, chat_data):
    """Load session and update corresponding mode"""
    try:
        st.session_state.current_session = chat_id
        st.session_state.show_new_chat = False
        
        # Update mode from the loaded chat
        mode = chat_data.get("mode", "core")
        st.session_state.current_mode = mode
        
        st.rerun()
        
    except Exception as e:
        st.error(f"Error loading chat")
        create_new_chat() 
        st.rerun()