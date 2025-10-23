import streamlit as st
import pandas as pd
import os
import tempfile
from datetime import datetime
from urllib.parse import urlparse
import requests
from components.sidebar import add_chat_to_sessions
from utils.session_manager import save_current_session, load_session_file_data, save_session_file_data
from services.api_client import api_client
from utils.helpers import (
    display_message_timestamp,
    prepare_chat_history_for_api
)
import plotly.graph_objects as go

def render_csv_chat():
    """Main CSV Chat Mode - AI-powered CSV data analysis interface"""
    try:
        # Handle file upload and session setup
        _handle_csv_upload_section(st.session_state.current_session)
        
        # Show dataset overview if data available
        display_df = _get_current_dataframe(st.session_state.current_session)
        if display_df is not None:
            _display_dataset_overview(display_df)
        
        st.markdown("---")
        
        # Display chat interface based on state
        if st.session_state.show_new_chat or st.session_state.current_session is None:
            _show_chat_placeholder(display_df)
        else:
            _display_chat_history(st.session_state.current_session)
        
        # Process user input
        user_input = st.chat_input("Ask about the data...")
        if user_input:
            _process_user_message(user_input, st.session_state.current_session, display_df)
            
    except Exception as e:
        st.error(f"❌ Unexpected error in CSV chat: {str(e)}")


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
        
        # Show placeholder if no messages
        if not st.session_state.current_messages:
            _show_chat_placeholder(_get_current_dataframe(current_session_id))
            return
        
        # Render all messages from session state
        for msg in st.session_state.current_messages:
            with st.chat_message(msg["role"]):
                display_message_timestamp(msg)
                st.markdown(msg["content"])
                
    except Exception as e:
        st.error(f"❌ Error displaying chat history: {str(e)}")
        _show_chat_placeholder(_get_current_dataframe(current_session_id))


def _load_messages_from_api(session_id):
    """Load messages from API only when necessary"""
    try:
        db_messages = api_client.get_session_messages(session_id)
        if db_messages:
            st.session_state.current_messages = db_messages
            st.session_state.last_session_id = session_id
        else:
            st.session_state.current_messages = []
            
    except ConnectionError as e:
        st.error("❌ Connection error: Cannot load chat history. Please check your connection.")
        st.session_state.current_messages = []
    except TimeoutError as e:
        st.error("❌ Timeout error: Server took too long to respond.")
        st.session_state.current_messages = []
    except Exception as e:
        st.error(f"❌ Error loading messages: {str(e)}")
        st.session_state.current_messages = []


def _handle_csv_upload_section(current_session_id):
    """Handle CSV file upload via file uploader or URL"""
    st.subheader("📊 Upload CSV Data")
    
    try:
        # Initialize session data if needed
        _initialize_session_data(current_session_id)
        
        # Get current data state
        current_df = _get_current_dataframe(current_session_id)
        has_temp_data = hasattr(st.session_state, 'temp_df') and st.session_state.temp_df is not None
        
        # Check if this is a large file with only metadata
        is_large_file = False
        if current_session_id and current_session_id in st.session_state.session_data:
            file_info = st.session_state.session_data[current_session_id].get('file_info', {})
            file_size_mb = file_info.get('size_mb', 0)
            row_count = file_info.get('rows', 0)
            if file_size_mb >= 10 or row_count > 1000:
                is_large_file = True
        
        # Show upload options only if no data loaded
        if current_df is None and not has_temp_data and not is_large_file:
            _show_upload_options()
        
        # Display file info if data is loaded
        if current_df is not None:
            _display_file_info(current_session_id)
            
    except Exception as e:
        st.error(f"❌ Error in upload section: {str(e)}")


def _display_file_info(current_session_id):
    """Display information about current CSV file"""
    try:
        if current_session_id and current_session_id in st.session_state.session_data:
            file_info = st.session_state.session_data[current_session_id].get('file_info', {})
            if file_info:
                filename = file_info.get('filename', 'Unknown')
                size_mb = file_info.get('size_mb', 0)
                rows = file_info.get('rows', 0)
                columns = file_info.get('columns', 0)
                
                st.info(f"📁 **Current file**: {filename} ({size_mb:.2f} MB, {rows} rows, {columns} columns)")
    except Exception as e:
        print(f"❌ Error displaying file info: {e}")


def _initialize_session_data(current_session_id):
    """Initialize session data and restore from API if available"""
    # Only initialize when session_id exists and not already in session_data
    if not current_session_id or current_session_id in st.session_state.session_data:
        return
        
    try:
        st.session_state.session_data[current_session_id] = {
            'df': None,
            'file_info': None,
            'file_path': None,
            'loaded': False
        }
        
        # Restore file info from API first
        file_info = load_session_file_data(current_session_id, 'csv_info')
        if file_info:
            st.session_state.session_data[current_session_id]['file_info'] = file_info
            
            # Show caution for large files
            file_size_mb = file_info.get('size_mb', 0)
            row_count = file_info.get('rows', 0)
            
            if file_size_mb >= 10 or row_count > 1000:
                st.error(f"⚠️ **Large file detected**: This dataset ({file_size_mb:.1f}MB, {row_count:,} rows) was too large for permanent storage. Please create a new chat and re-upload the file for analysis.")
                return
            else:
                # For small files, try to load full data
                full_data = load_session_file_data(current_session_id, 'csv_data')
                if full_data is not None:
                    st.session_state.session_data[current_session_id]['df'] = full_data
                    st.session_state.session_data[current_session_id]['loaded'] = True
                    st.success("✅ Full dataset restored from API")
            
    except Exception as e:
        st.error(f"❌ Error restoring dataset info: {str(e)}")


def _show_upload_options():
    """Display file upload and URL import options"""
    try:
        tab1, tab2 = st.tabs(["📁 File Upload", "🌐 URL Import"])
        
        with tab1:
            _handle_file_upload()
        
        with tab2:
            _handle_url_import()
            
    except Exception as e:
        st.error(f"❌ Error displaying upload options: {str(e)}")


def _handle_file_upload():
    """Handle CSV file upload"""
    try:
        uploaded_csv = st.file_uploader(
            "Upload CSV file", 
            type=["csv"], 
            help="Upload a CSV file for data analysis (max 200MB). Files under 10MB and 1000 rows will be stored permanently."
        )
        
        if uploaded_csv is not None:
            # Check file size
            file_size = uploaded_csv.size / (1024 * 1024)  # Convert to MB
            st.write(f"📊 File: {uploaded_csv.name} ({file_size:.2f} MB)")
            
            # Validate file size
            if file_size > 200:
                st.error("❌ File too large. Please upload files smaller than 200MB.")
                return
            
            if file_size == 0:
                st.error("❌ File is empty. Please upload a valid CSV file.")
                return
            
            # Read file with encoding detection and chunking for large files
            with st.spinner("📖 Reading CSV file..."):
                try:
                    # Try different encodings
                    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
                    new_df = None
                    
                    for encoding in encodings:
                        try:
                            uploaded_csv.seek(0)  # Reset file pointer
                            if file_size > 10:  # Read in chunks for large files
                                chunk_size = 10000
                                chunks = []
                                for chunk in pd.read_csv(uploaded_csv, chunksize=chunk_size, encoding=encoding):
                                    chunks.append(chunk)
                                new_df = pd.concat(chunks, ignore_index=True)
                            else:
                                new_df = pd.read_csv(uploaded_csv, encoding=encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                    
                    if new_df is None:
                        st.error("❌ Could not read file encoding. Please try saving as UTF-8.")
                        return
                    
                    # Validate DataFrame
                    if new_df.empty:
                        st.error("❌ CSV file appears to be empty or couldn't be parsed.")
                        return
                    
                    if len(new_df.columns) > 1000:
                        st.warning("⚠️ File has an unusually large number of columns. This might affect performance.")
                    
                    # Store file information
                    file_info = {
                        'filename': uploaded_csv.name,
                        'size_bytes': uploaded_csv.size,
                        'size_mb': file_size,
                        'rows': len(new_df),
                        'columns': len(new_df.columns),
                        'columns_list': new_df.columns.tolist(),
                        'encoding': 'detected',
                        'upload_timestamp': datetime.now().isoformat()
                    }
                    
                    # Store temporary data
                    st.session_state.temp_df = new_df
                    st.session_state.temp_file_info = file_info
                    st.session_state.temp_csv_name = uploaded_csv.name
                    st.session_state.temp_file_obj = uploaded_csv
                    
                    # Show storage info
                    if file_size < 10 and len(new_df) <= 1000:
                        st.success("✅ CSV file uploaded successfully! This file will be stored permanently.")
                    else:
                        st.warning(f"⚠️ **Large file**: This dataset ({file_size:.1f}MB, {len(new_df):,} rows) is too large for permanent storage. Only metadata will be saved.")
                    
                    st.rerun()
                    
                except pd.errors.ParserError as e:
                    st.error(f"❌ CSV parsing error: {str(e)}")
                    st.info("💡 **Tip**: Check if the file is a valid CSV with consistent column counts.")
                except Exception as e:
                    st.error(f"❌ Error reading CSV: {str(e)}")
                    
    except Exception as e:
        st.error(f"❌ Unexpected upload error: {str(e)}")


def _handle_url_import():
    """Handle CSV import from URL"""
    try:
        csv_url = st.text_input(
            "Paste CSV URL", 
            placeholder="https://raw.githubusercontent.com/.../data.csv", 
            help="URL must point directly to a CSV file. Files under 10MB and 1000 rows will be stored permanently.",
            key="csv_url"
        )
        
        if st.button("Load from URL", key="load_url") and csv_url:
            # Validate URL format
            parsed_url = urlparse(csv_url)
            if not parsed_url.scheme or not parsed_url.netloc:
                st.error("❌ Invalid URL format. Please enter a complete URL including http:// or https://")
                return
            
            if not csv_url.lower().endswith('.csv'):
                st.warning("⚠️ URL doesn't appear to point to a CSV file.")
            
            with st.spinner("🔍 Downloading CSV..."):
                try:
                    # Download file with timeout
                    headers = {'User-Agent': 'Mozilla/5.0 (compatible; CSV-Analyzer)'}
                    response = requests.get(csv_url, stream=True, timeout=30, headers=headers)
                    response.raise_for_status()
                    
                    # Check content type
                    content_type = response.headers.get('content-type', '').lower()
                    if 'text/csv' not in content_type and 'application/csv' not in content_type:
                        st.warning(f"⚠️ Server returned content type: {content_type}")
                    
                    # Check file size
                    content_length = response.headers.get('content-length')
                    if content_length:
                        file_size = int(content_length) / (1024 * 1024)
                        if file_size > 200:
                            st.error("❌ File too large (over 200MB). Please use a smaller file.")
                            return
                    
                    # Create temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                        downloaded_size = 0
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                tmp_file.write(chunk)
                                downloaded_size += len(chunk)
                                if downloaded_size > 200 * 1024 * 1024:
                                    st.error("❌ File exceeds 200MB limit during download.")
                                    os.unlink(tmp_file.name)
                                    return
                        tmp_file_path = tmp_file.name
                    
                    file_size = downloaded_size / (1024 * 1024)
                    
                    # Read CSV file
                    try:
                        if file_size > 10:
                            chunk_size = 10000
                            chunks = []
                            for chunk in pd.read_csv(tmp_file_path, chunksize=chunk_size):
                                chunks.append(chunk)
                            new_df = pd.concat(chunks, ignore_index=True)
                        else:
                            new_df = pd.read_csv(tmp_file_path)
                    except pd.errors.EmptyDataError:
                        st.error("❌ Downloaded file is empty.")
                        os.unlink(tmp_file_path)
                        return
                    except pd.errors.ParserError as e:
                        st.error(f"❌ Error parsing CSV: {str(e)}")
                        os.unlink(tmp_file_path)
                        return
                    
                    # Validate DataFrame
                    if new_df.empty:
                        st.error("❌ CSV file is empty or contains no data.")
                        os.unlink(tmp_file_path)
                        return
                    
                    # Store file information
                    file_info = {
                        'filename': os.path.basename(parsed_url.path) or "url_import.csv",
                        'size_bytes': downloaded_size,
                        'size_mb': file_size,
                        'rows': len(new_df),
                        'columns': len(new_df.columns),
                        'columns_list': new_df.columns.tolist(),
                        'url': csv_url,
                        'upload_timestamp': datetime.now().isoformat()
                    }
                    
                    # Store temporary data
                    st.session_state.temp_df = new_df
                    st.session_state.temp_file_info = file_info
                    st.session_state.temp_csv_name = "url_import.csv"
                    st.session_state.temp_file_path = tmp_file_path
                    
                    # Show storage info
                    if file_size < 10 and len(new_df) <= 1000:
                        st.success("✅ CSV loaded from URL successfully! This file will be stored permanently.")
                    else:
                        st.warning(f"⚠️ **Large file**: This dataset ({file_size:.1f}MB, {len(new_df):,} rows) is too large for permanent storage. Only metadata will be saved.")
                    
                    st.rerun()
                    
                except requests.exceptions.Timeout:
                    st.error("❌ Request timeout. The server took too long to respond.")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Connection error. Please check the URL and your internet connection.")
                except requests.exceptions.HTTPError as e:
                    status_code = e.response.status_code
                    if status_code == 404:
                        st.error("❌ File not found (404). Please check the URL.")
                    elif status_code == 403:
                        st.error("❌ Access forbidden (403). The server denied access.")
                    elif status_code == 401:
                        st.error("❌ Unauthorized (401). Authentication may be required.")
                    else:
                        st.error(f"❌ HTTP error {status_code}: {str(e)}")
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Network error: {str(e)}")
                    
    except Exception as e:
        st.error(f"❌ Unexpected URL import error: {str(e)}")


def _get_current_dataframe(current_session_id):
    """Get current DataFrame from session data or temporary storage"""
    try:
        df_data = None
        
        if current_session_id and current_session_id in st.session_state.session_data:
            df_data = st.session_state.session_data[current_session_id].get('df')
        else:
            df_data = getattr(st.session_state, 'temp_df', None)
        
        # Convert dict to DataFrame if needed
        if isinstance(df_data, dict):
            try:
                df_data = pd.DataFrame(df_data)
            except Exception as e:
                st.error(f"❌ Error converting stored data to DataFrame: {str(e)}")
                return None
        
        return df_data
        
    except Exception as e:
        st.error(f"❌ Error accessing dataset: {str(e)}")
        return None


def _get_full_dataframe(session_id):
    """Get full DataFrame for analysis"""
    try:
        # First check if we have temporary data
        temp_df = getattr(st.session_state, 'temp_df', None)
        if temp_df is not None:
            return temp_df
        
        if session_id and session_id in st.session_state.session_data:
            session_data = st.session_state.session_data[session_id]
            
            # Return data if available
            if session_data.get('df') is not None:
                return session_data['df']
            
            # Check if this is a large file with only metadata
            file_info = session_data.get('file_info', {})
            if file_info:
                file_size_mb = file_info.get('size_mb', 0)
                row_count = file_info.get('rows', 0)
                
                if file_size_mb >= 10 or row_count > 1000:
                    return None
            
            # For small files, try to load from csv_data
            full_data = load_session_file_data(session_id, 'csv_data')
            if full_data is not None:
                session_data['df'] = full_data
                return full_data
        
        # Fallback to current data
        return _get_current_dataframe(session_id)
        
    except Exception as e:
        st.error(f"❌ Error accessing dataset: {str(e)}")
        return _get_current_dataframe(session_id)


def _display_dataset_overview(df):
    """Display dataset overview and statistics"""
    try:
        st.subheader("📈 Dataset Overview")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Rows", len(df))
        with col2:
            st.metric("Columns", len(df.columns))
        with col3:
            st.metric("Missing Values", df.isnull().sum().sum())
        
        with st.expander("📋 Dataset Preview"):
            st.dataframe(df.head(), use_container_width=True)
        
        # Check if this is a large file with only metadata
        current_session_id = st.session_state.current_session
        if current_session_id and current_session_id in st.session_state.session_data:
            file_info = st.session_state.session_data[current_session_id].get('file_info', {})
            actual_rows = file_info.get('rows', 0)
            current_rows = len(df)
            
            if actual_rows > current_rows:
                st.warning(f"⚠️ **Large File Limitation**: Showing {current_rows} rows preview (original: {actual_rows:,} rows). Full analysis requires re-uploading the file.")
        
        # Show data quality warnings
        if df.isnull().sum().sum() > len(df) * 0.5:
            st.warning("⚠️ High percentage of missing values detected. Data quality may be affected.")
        
        if len(df) == 0:
            st.error("❌ Dataset is empty.")
        
        st.info("💡 **Tip**: Click 'New Chat' in sidebar to analyze a different dataset")
        
    except Exception as e:
        st.error(f"❌ Error displaying dataset overview: {str(e)}")


def _show_chat_placeholder(display_df):
    """Show appropriate placeholder message based on data state"""
    try:
        if display_df is not None:
            # Check if this is a large file with limitations
            current_session_id = st.session_state.current_session
            if current_session_id and current_session_id in st.session_state.session_data:
                file_info = st.session_state.session_data[current_session_id].get('file_info', {})
                file_size_mb = file_info.get('size_mb', 0)
                row_count = file_info.get('rows', 0)
                
                if file_size_mb >= 10 or row_count > 1000:
                    st.warning("🎯 **Dataset loaded (Preview Mode)**: This large dataset is in preview mode. Ask questions about the data, but note the file will need to be re-uploaded for future sessions.")
                else:
                    st.success("🎯 **Dataset loaded!** Ask questions about the data.")
            else:
                st.success("🎯 **Dataset loaded!** Ask questions about the data.")
        else:
            st.info("📊 Upload a CSV file to start data analysis")
    except Exception as e:
        st.error(f"❌ Error displaying placeholder: {str(e)}")


def _process_user_message(user_input, current_session_id, display_df):
    """Process user message and generate AI response"""
    try:
        current_time = datetime.now()
        
        # Check if this is a large file session with no data
        if current_session_id and current_session_id in st.session_state.session_data:
            file_info = st.session_state.session_data[current_session_id].get('file_info', {})
            if file_info:
                file_size_mb = file_info.get('size_mb', 0)
                row_count = file_info.get('rows', 0)
                if (file_size_mb >= 10 or row_count > 1000) and display_df is None:
                    st.error(f"❌ **Large file limitation**: This dataset ({file_size_mb:.1f}MB, {row_count:,} rows) was too large for permanent storage. Please create a new chat and re-upload the file.")
                    return
        
        # Validate data availability
        if display_df is None:
            st.error("❌ Please upload a CSV file first!")
            return
        
        # Validate user input
        if not user_input or not user_input.strip():
            st.error("❌ Please enter a question about the data.")
            return
            
        if len(user_input.strip()) > 2000:
            st.error("❌ Question too long. Please keep under 2000 characters.")
            return
        
        # Display user message
        with st.chat_message("user"):
            st.caption(f"🕒 {current_time.strftime('%H:%M • %b %d, %Y')}")
            st.markdown(user_input)
        
        # Auto-scroll to bottom
        _auto_scroll_to_bottom()
        
        # Ensure session exists
        session_id = _ensure_session_exists(user_input, current_session_id, display_df)
        if not session_id:
            return
        
        # Generate AI response
        _generate_ai_response(user_input, session_id, current_time)
        
    except Exception as e:
        st.error(f"❌ Error processing message: {str(e)}")


def _ensure_session_exists(user_input, current_session_id, display_df):
    """Create new session only when user sends first message"""
    try:
        if current_session_id is None or st.session_state.show_new_chat:
            return _create_new_session(user_input, display_df)
        return current_session_id
    except Exception as e:
        st.error(f"❌ Error creating session: {str(e)}")
        return None


def _create_new_session(user_input, display_df):
    """Create new chat session for CSV analysis"""
    try:
        chat_name = f"CSV: {user_input.strip()[:30]}..."
        
        # Create session with empty messages
        chat_id = add_chat_to_sessions(chat_name, [])
        
        if not chat_id:
            st.error("❌ Failed to create new chat session.")
            return None
        
        # Update session state
        st.session_state.current_session = chat_id
        st.session_state.show_new_chat = False
        st.session_state.current_messages = []
        
        # Initialize session data
        file_info = getattr(st.session_state, 'temp_file_info', {})
        file_path = getattr(st.session_state, 'temp_file_path', None)
        
        st.session_state.session_data[chat_id] = {
            'df': display_df,
            'file_info': file_info,
            'file_path': file_path,
            'loaded': True
        }
        
        # Save file info to API with appropriate storage strategy
        _save_csv_info_to_api(chat_id, file_info)
        
        # Clean up temporary data
        _cleanup_temp_data()
        return chat_id
        
    except Exception as e:
        st.error(f"❌ Error creating new session: {str(e)}")
        return None


def _save_csv_info_to_api(session_id, file_info):
    """Save file info to API - only save full data for small files"""
    try:
        csv_name = getattr(st.session_state, 'temp_csv_name', "uploaded_data.csv")
        
        # Save metadata (always save)
        save_session_file_data(session_id, 'csv_info', file_info, f"{csv_name}_info")
        
        # Save full data only for small files
        full_df = getattr(st.session_state, 'temp_df', None)
        if full_df is not None:
            # Check file size and row count conditions
            file_size_mb = file_info.get('size_mb', 0)
            row_count = file_info.get('rows', 0)
            
            if file_size_mb < 10 and row_count <= 1000:
                try:
                    # Convert DataFrame to CSV string
                    csv_string = full_df.to_csv(index=False)
                    file_data_to_save = {
                        'file_type': 'csv_data',
                        'csv_string': csv_string,
                        'rows': len(full_df),
                        'columns': len(full_df.columns),
                        'file_name': csv_name
                    }
                    
                    save_session_file_data(session_id, 'csv_data', file_data_to_save, f"{csv_name}_data")
                except Exception as e:
                    print(f"❌ Error saving full data as CSV: {e}")
                
    except Exception as e:
        print(f"❌ Error saving CSV info: {e}")


def _cleanup_temp_data():
    """Clean up temporary data after session creation"""
    try:
        for key in ['temp_df', 'temp_file_info', 'temp_csv_name', 'temp_file_obj', 'temp_file_path']:
            if hasattr(st.session_state, key):
                delattr(st.session_state, key)
    except Exception as e:
        print(f"❌ Error cleaning up temp data: {e}")


def _generate_ai_response(user_input, session_id, current_time):
    """Generate AI response using CSV-specific backend API with plotting support"""
    with st.chat_message("assistant"):
        try:
            response_time = datetime.now()
            st.caption(f"🕒 {response_time.strftime('%H:%M • %b %d, %Y')}")
            
            # Get full data for analysis
            full_dataframe = _get_full_dataframe(session_id)
            
            if full_dataframe is None:
                st.error("❌ Unable to load dataset for analysis.")
                error_msg = "I couldn't access the dataset for analysis. Please try uploading the file again."
                _update_chat_history(user_input, error_msg, session_id, current_time, response_time)
                return
            
            # Prepare query with CSV context
            enhanced_query = _prepare_csv_context(user_input, st.session_state.current_messages)
            
            # Show loading indicator
            with st.spinner("🤔 Analyzing data and creating visualizations..."):
                try:
                    # Call CSV analysis API
                    api_response = api_client.csv_chat(enhanced_query, full_dataframe, session_id)
                    
                    # Extract text response and plots
                    text_response = api_response.get("content", "No response received.")
                    plots_data = api_response.get("plots", [])
                    
                    # Display text response
                    st.markdown(text_response)
                    
                    # Display plots if any
                    if plots_data:
                        st.markdown("---")
                        st.subheader("📊 Visualizations")
                        
                        for i, plot_info in enumerate(plots_data):
                            try:
                                # Recreate plotly figure from data
                                fig = go.Figure(
                                    data=plot_info.get("data", []),
                                    layout=plot_info.get("layout", {})
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
                            except Exception as plot_error:
                                st.error(f"❌ Error displaying chart {i+1}: {str(plot_error)}")
                    
                    # Update chat history (only text response)
                    _update_chat_history(user_input, text_response, session_id, current_time, response_time)
                    _auto_scroll_to_bottom()
                    
                except Exception as api_error:
                    st.error(f"❌ Analysis error: {str(api_error)}")
                    error_msg = "I encountered an error while analyzing the data. Please try again or rephrase your question."
                    _update_chat_history(user_input, error_msg, session_id, current_time, response_time)
            
        except Exception as e:
            error_msg = f"❌ **System Error**: {str(e)}"
            st.caption(f"🕒 {datetime.now().strftime('%H:%M • %b %d, %Y')}")
            st.error("An unexpected error occurred during analysis.")
            _handle_response_error(user_input, session_id, current_time, e)


def _prepare_csv_context(user_input, current_messages):
    """Prepare enhanced query with CSV data context"""
    try:
        context_messages = []
        for msg in current_messages[-20:]: 
            if msg["role"] == "user":
                context_messages.append(f"User: {msg['content']}")
            elif msg["role"] == "assistant":
                context_messages.append(f"Assistant: {msg['content']}")
        
        chat_history = "\n".join(context_messages) if context_messages else "No previous conversation."

        enhanced_query = f"""
        You are a smart data analysis assistant that helps users explore and understand CSV datasets.

        DATA CONTEXT:
        The user has uploaded a CSV dataset. You can perform operations such as summarizing, describing, and reasoning over its contents.

        PLOTTING CAPABILITIES:
        You have access to plotting tools that can create visualizations. When appropriate:
        - Use plotChart tool to create charts from plotly figure data
        - Use createBarChart tool for simple bar charts
        - Create visualizations to help users understand patterns and trends
        - Always explain what the visualization shows

        PREVIOUS CONVERSATION:
        {chat_history}

        CURRENT QUESTION:
        {user_input}

        Instructions:
        1. Analyze the dataset based on the user's question
        2. When visualization would help understanding, create appropriate charts
        3. Provide clear explanations of both the data analysis and any visualizations
        4. Be concise and data-driven in your responses

        Now analyze the dataset and provide the most relevant, data-driven answer:
        """

        
        return enhanced_query
        
    except Exception as e:
        print(f"❌ Error preparing CSV context: {e}")
        return user_input  # Fallback to original query


def _update_chat_history(user_input, ai_response, session_id, user_time, ai_time):
    """Update chat history in session state and save to database"""
    try:
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
        
        # Limit message history to prevent memory issues
        if len(new_messages) > 50:
            new_messages = new_messages[-50:]
        
        # Update session state
        st.session_state.current_messages = new_messages
        
        # Save to database
        try:
            save_current_session(new_messages)
        except ConnectionError as e:
            st.error("❌ Connection error: Could not save conversation. Your messages may not be persisted.")
        except Exception as e:
            st.error("❌ Error saving conversation. Your messages may not be persisted.")
            
    except Exception as e:
        st.error(f"❌ Error updating chat history: {str(e)}")


def _handle_response_error(user_input, session_id, current_time, error):
    """Handle errors during response generation"""
    try:
        error_msg = f"❌ **System Error**: {str(error)}"
        error_time = datetime.now()
        
        st.caption(f"🕒 {error_time.strftime('%H:%M • %b %d, %Y')}")
        st.error("An unexpected error occurred. Our team has been notified.")
        
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
        
        try:
            save_current_session(new_messages)
        except Exception as save_error:
            print(f"❌ Failed to save error messages: {save_error}")
            
    except Exception as e:
        print(f"❌ Critical error in error handling: {e}")
        st.session_state.current_messages = []
        st.error("A critical error occurred. Please refresh the page.")


def _auto_scroll_to_bottom():
    """Force scroll to bottom of the chat container"""
    st.markdown(
        """
        <script>
        var chatContainer = window.parent.document.querySelector('[data-testid="stChatMessageContainer"]');
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        </script>
        """,
        unsafe_allow_html=True
    )