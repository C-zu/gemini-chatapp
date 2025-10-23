import streamlit as st
import base64
from datetime import datetime
from components.sidebar import add_chat_to_sessions
from utils.session_manager import save_current_session, load_session_file_data, save_session_file_data
from services.api_client import api_client
from utils.helpers import (
    display_message_timestamp,
    prepare_chat_history_for_api,
    generate_fallback_response
)


def render_image_chat():
    """Image Chat Mode - Analyze images with AI assistant"""
    try:
        # Handle image upload and session initialization
        _handle_image_upload_section(st.session_state.current_session)
        
        # Display image preview if available
        display_image_data = _get_current_image_data(st.session_state.current_session)
        if display_image_data:
            _display_image_preview(display_image_data)
        
        st.markdown("---")
        
        # Show placeholder for new chat, otherwise display chat history
        if st.session_state.show_new_chat or st.session_state.current_session is None:
            _show_chat_placeholder(display_image_data)
        else:
            _display_chat_history(st.session_state.current_session, display_image_data)
        
        # Handle user input if image is loaded
        if display_image_data:
            user_input = st.chat_input("Ask about the image...")
            if user_input:
                _process_user_message(user_input, st.session_state.current_session, display_image_data)
                
    except Exception as e:
        st.error(f"❌ Unexpected error in image chat: {str(e)}")
        print(f"❌ Image chat render error: {e}")


def _handle_image_upload_section(current_session_id):
    """Handle image file upload section with error handling"""
    st.subheader("🖼️ Upload Image")
    
    try:
        _initialize_image_session_data(current_session_id)
        
        current_image_data = _get_current_image_data(current_session_id)
        has_temp_image = hasattr(st.session_state, 'temp_image_data') and st.session_state.temp_image_data is not None
        
        if not current_image_data and not has_temp_image:
            _show_image_uploader()
        else:
            # Display file info if image is loaded
            _display_image_file_info(current_session_id)
            
    except Exception as e:
        st.error(f"❌ Error in upload section: {str(e)}")


def _display_image_file_info(current_session_id):
    """Display information about image file"""
    try:
        if current_session_id and current_session_id in st.session_state.session_data:
            file_info = st.session_state.session_data[current_session_id].get('file_info', {})
            if file_info:
                file_name = file_info.get('file_name', 'Unknown')
                size_mb = file_info.get('size_mb', 0)
                st.info(f"📁 **Current image**: {file_name} ({size_mb:.1f} MB)")
    except Exception as e:
        print(f"❌ Error displaying image file info: {e}")


def _initialize_image_session_data(current_session_id):
    """Initialize session data and restore image from API if available"""
    if not current_session_id or current_session_id in st.session_state.session_data:
        return
        
    try:
        print(f"🔄 Loading image from API for session: {current_session_id}")
        
        # Load image metadata first
        file_info = load_session_file_data(current_session_id, 'image_info')
        if file_info:
            st.session_state.session_data[current_session_id] = {
                'file_info': file_info,
                'loaded': True
            }
            
            # Load actual image data
            current_image_data = load_session_file_data(current_session_id, 'image')
            if current_image_data:
                st.session_state.session_data[current_session_id]['image_data'] = current_image_data
                st.success("✅ Image initialized from API")
            else:
                st.warning("⚠️ Image data not found in storage")
            
            print(f"✅ Loaded image info from API for session: {current_session_id}")
            
    except Exception as e:
        st.error(f"❌ Error restoring image session: {str(e)}")
        print(f"❌ Session initialization error: {e}")


def _show_image_uploader():
    """Display image file uploader"""
    try:
        uploaded_image = st.file_uploader(
            "Choose an image file", 
            type=["jpg", "jpeg", "png", "webp", "gif"],
            help="Supported formats: JPG, PNG, WebP, GIF. Maximum size: 10MB.",
            key="image_uploader"
        )
        
        if uploaded_image is not None:
            # Check file size
            file_size = uploaded_image.size / (1024 * 1024)  # Convert to MB
            max_size = 10  # 10MB limit
            
            if file_size > max_size:
                st.error(f"❌ Image too large ({file_size:.1f}MB). Maximum size is {max_size}MB.")
                return
                
            if file_size == 0:
                st.error("❌ File is empty. Please upload a valid image.")
                return
            
            # Show file info
            st.write(f"📊 Image: {uploaded_image.name} ({file_size:.1f}MB)")
            
            # Process image
            with st.spinner("🖼️ Processing image..."):
                try:
                    image_bytes = uploaded_image.read()
                    
                    # Compress image if larger than 2MB for better performance
                    if file_size > 2:
                        st.info("🔄 Compressing image for better performance...")
                        image_bytes = _compress_image_data(image_bytes, uploaded_image.type)
                    
                    encoded_image = base64.b64encode(image_bytes).decode("utf-8")
                    
                    # Store file information
                    file_info = {
                        'file_name': uploaded_image.name,
                        'size_bytes': uploaded_image.size,
                        'size_mb': file_size,
                        'format': uploaded_image.type,
                        'upload_timestamp': datetime.now().isoformat()
                    }
                    
                    # Store temporary data
                    st.session_state.temp_image_data = encoded_image
                    st.session_state.temp_file_info = file_info
                    st.session_state.uploaded_image_name = uploaded_image.name
                    st.session_state.original_file_size = file_size
                    
                    st.success("✅ Image uploaded successfully!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Image processing error: {str(e)}")
                    print(f"❌ Image processing error: {e}")
                    
    except Exception as e:
        st.error(f"❌ Upload error: {str(e)}")


def _compress_image_data(image_bytes, image_type, max_size_mb=2):
    """Compress image data to reduce file size"""
    try:
        from PIL import Image
        import io
        
        # Open image from bytes
        image = Image.open(io.BytesIO(image_bytes))
        
        # Calculate current size
        current_size_mb = len(image_bytes) / (1024 * 1024)
        
        if current_size_mb <= max_size_mb:
            return image_bytes  # No compression needed
            
        # Determine output format and quality
        if image_type in ['image/jpeg', 'image/jpg']:
            output_format = 'JPEG'
            quality = 85  # Reduce quality for JPEG
        elif image_type == 'image/png':
            output_format = 'PNG'
            quality = 95  # PNG compression is different
        elif image_type == 'image/webp':
            output_format = 'WEBP'
            quality = 85
        else:
            output_format = 'JPEG'  # Default to JPEG
            quality = 85
        
        # Compress image
        output_buffer = io.BytesIO()
        
        # For very large images, resize if necessary
        max_dimension = 2048
        if max(image.size) > max_dimension:
            ratio = max_dimension / max(image.size)
            new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            st.info(f"📐 Resized image to {new_size[0]}x{new_size[1]} for better performance")
        
        # Save with compression
        if output_format == 'PNG':
            image.save(output_buffer, format=output_format, optimize=True)
        else:
            image.save(output_buffer, format=output_format, quality=quality, optimize=True)
        
        compressed_bytes = output_buffer.getvalue()
        compressed_size_mb = len(compressed_bytes) / (1024 * 1024)
        
        print(f"📊 Image compressed: {current_size_mb:.1f}MB → {compressed_size_mb:.1f}MB")
        
        return compressed_bytes
        
    except Exception as e:
        print(f"❌ Image compression error: {e}")
        return image_bytes  # Return original if compression fails


def _get_current_image_data(current_session_id):
    """Get current image data from session data or temporary storage"""
    try:
        # First check temporary data (for current session)
        temp_image_data = getattr(st.session_state, 'temp_image_data', None)
        if temp_image_data is not None:
            return temp_image_data
            
        # Then check session data
        if current_session_id and current_session_id in st.session_state.session_data:
            return st.session_state.session_data[current_session_id].get('image_data')
        
        return None
    except Exception as e:
        print(f"❌ Error getting image data: {e}")
        return None


def _get_image_data_for_analysis(session_id):
    """Get image data for analysis"""
    try:
        # First check temporary data (for current session)
        temp_image_data = getattr(st.session_state, 'temp_image_data', None)
        if temp_image_data is not None:
            return temp_image_data
            
        if session_id and session_id in st.session_state.session_data:
            return st.session_state.session_data[session_id].get('image_data')
        
        return None
    except Exception as e:
        print(f"❌ Error getting image data for analysis: {e}")
        return None


def _display_image_preview(image_data):
    """Display image preview with success message"""
    try:
        st.success("✅ Image loaded!")
        
        if isinstance(image_data, dict):
            image_base64 = image_data.get('data', image_data.get('image_data', image_data))
        else:
            image_base64 = image_data
        
        if isinstance(image_base64, str):
            if not image_base64.startswith('data:image'):
                image_base64 = f"data:image/jpeg;base64,{image_base64}"
            
            # Display image with responsive sizing
            st.image(image_base64, use_container_width=True, caption="Uploaded Image Preview")
            
            # Show file size info if available
            original_size = getattr(st.session_state, 'original_file_size', None)
            if original_size:
                current_size = len(image_base64) / (1024 * 1024) * 0.75  # Approximate base64 size
                st.caption(f"📊 File size: {original_size:.1f}MB → {current_size:.1f}MB (base64)")
        else:
            st.error("❌ Invalid image data format")
            
    except Exception as e:
        st.error(f"❌ Error displaying image: {str(e)}")
    
    st.info("💡 **Tip**: Click 'New Chat' in sidebar to chat with a different image")


def _display_chat_history(current_session_id, display_image_data):
    """Display chat messages from session state"""
    try:
        if "current_messages" not in st.session_state:
            st.session_state.current_messages = []
        
        # Load from API only when needed
        if current_session_id and (not st.session_state.current_messages or 
                                  st.session_state.get("last_session_id") != current_session_id):
            _load_messages_from_api(current_session_id)
        
        if not st.session_state.current_messages:
            _show_chat_placeholder(display_image_data)
            return
        
        for msg in st.session_state.current_messages:
            with st.chat_message(msg["role"]):
                display_message_timestamp(msg)
                st.markdown(msg["content"])
                
    except Exception as e:
        st.error(f"❌ Error displaying chat history: {str(e)}")
        _show_chat_placeholder(display_image_data)


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
            
    except ConnectionError as e:
        st.error("❌ Connection error: Cannot load chat history. Please check your connection.")
        st.session_state.current_messages = []
    except TimeoutError as e:
        st.error("❌ Timeout error: Server took too long to respond.")
        st.session_state.current_messages = []
    except Exception as e:
        st.error(f"❌ Error loading messages: {str(e)}")
        st.session_state.current_messages = []


def _show_chat_placeholder(display_image_data):
    """Show appropriate placeholder message based on image state"""
    try:
        if display_image_data:
            st.success("🎯 Image ready! Ask questions about the image.")
        else:
            st.info("📸 Upload an image to start chatting")
    except Exception as e:
        st.error(f"❌ Error displaying placeholder: {str(e)}")


def _process_user_message(user_input, current_session_id, display_image_data):
    """Process user message and generate AI response"""
    try:
        current_time = datetime.now()
        
        # Validate input
        if not user_input or not user_input.strip():
            st.error("❌ Please enter a question about the image.")
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
        session_id = _ensure_session_exists(user_input, current_session_id, display_image_data)
        if not session_id:
            st.error("❌ Failed to create chat session. Please try again.")
            return
        
        # Generate AI response
        _generate_ai_response(user_input, session_id, current_time)
        
    except Exception as e:
        st.error(f"❌ Error processing message: {str(e)}")
        print(f"❌ Message processing error: {e}")


def _ensure_session_exists(user_input, current_session_id, display_image_data):
    """Create new session only when user sends first message"""
    try:
        if current_session_id is None or st.session_state.show_new_chat:
            return _create_new_image_session(user_input, display_image_data)
        return current_session_id
    except Exception as e:
        st.error(f"❌ Error creating session: {str(e)}")
        return None


def _create_new_image_session(user_input, display_image_data):
    """Create new chat session for image analysis"""
    try:
        chat_name = f"Image: {user_input.strip()[:30]}..."
        
        # Create session with empty messages
        chat_id = add_chat_to_sessions(chat_name, [])
        
        if not chat_id:
            st.error("❌ Failed to create new chat session.")
            return None
        
        # Update session state
        st.session_state.current_session = chat_id
        st.session_state.show_new_chat = False
        st.session_state.current_messages = []
        
        print(f"🆕 Created image session: {chat_id}")
        
        # Save image data
        if hasattr(st.session_state, 'temp_image_data'):
            image_data = st.session_state.temp_image_data
            file_info = getattr(st.session_state, 'temp_file_info', {})
            image_name = st.session_state.uploaded_image_name
            
            print(f"💾 Saving image to API for new session: {chat_id}")
            
            # Extract base64 from data URL if needed
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            
            # Save file info to API
            _save_image_info_to_api(chat_id, file_info)
            
            # Save actual image data
            result = save_session_file_data(chat_id, 'image', image_data, image_name)
            print(f"💾 Save session file result: {result is not None}")
            
            # Update session data
            st.session_state.session_data[chat_id] = {
                'image_data': image_data,
                'file_info': file_info,
                'loaded': True
            }
            
            # Clean up temporary data
            _cleanup_temp_image_data()
        
        return chat_id
        
    except Exception as e:
        st.error(f"❌ Error creating image session: {str(e)}")
        print(f"❌ Session creation error: {e}")
        return None


def _save_image_info_to_api(session_id, file_info):
    """Save image metadata to API"""
    try:
        image_name = getattr(st.session_state, 'uploaded_image_name', "uploaded_image")
        
        print(f"💾 Saving image info to API for session: {session_id}")
        
        # Save metadata
        result = save_session_file_data(session_id, 'image_info', file_info, f"{image_name}_info")
        print(f"💾 Save image info result: {result is not None}")
                
    except Exception as e:
        print(f"❌ Error saving image info: {e}")


def _cleanup_temp_image_data():
    """Clean up temporary image data after session creation"""
    try:
        for key in ['temp_image_data', 'temp_file_info', 'uploaded_image_name', 'original_file_size']:
            if hasattr(st.session_state, key):
                delattr(st.session_state, key)
    except Exception as e:
        print(f"❌ Error cleaning up temp data: {e}")


def _generate_ai_response(user_input, session_id, current_time):
    """Generate AI response using backend API with comprehensive error handling"""
    with st.chat_message("assistant"):
        try:
            response_time = datetime.now()
            st.caption(f"🕒 {response_time.strftime('%H:%M • %b %d, %Y')}")
            
            message_placeholder = st.empty()
            full_response = ""
            
            # Show loading indicator
            message_placeholder.markdown("🔍 Analyzing image...")
            
            # Prepare chat history
            try:
                chat_history = prepare_chat_history_for_api(st.session_state.current_messages)
                print(f"📝 Prepared chat history: {len(chat_history)} messages")
            except Exception as e:
                st.error("❌ Error preparing conversation history")
                chat_history = []
            
            # Get image data for analysis
            image_data = _get_image_data_for_analysis(session_id)
            if not image_data:
                st.error("❌ No image data available for analysis")
                error_msg = "I couldn't access the image for analysis. Please try uploading again."
                _update_chat_history(user_input, error_msg, current_time, response_time)
                return
            
            # Check image size for processing
            image_size = len(image_data)
            if image_size > 5 * 1024 * 1024:  # 5MB base64
                st.warning("⚠️ Large image detected. Analysis may take longer than usual.")
            
            # Call API with timeout handling
            try:
                response = api_client.stream_image_chat(user_input, image_data, chat_history)
                
                if response and response.status_code == 200:
                    # Process streaming response
                    try:
                        for chunk in response.iter_content(decode_unicode=True, chunk_size=1024):
                            if chunk:
                                full_response += chunk

                                message_placeholder.markdown(full_response + "▌")
                        
                        message_placeholder.markdown(full_response)
                        
                        # Validate response
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
                    # Handle HTTP errors
                    status_code = response.status_code if response else "Unknown"
                    error_msg = _get_http_error_message(status_code)
                    st.error(error_msg)
                    full_response = "Sorry, I couldn't analyze the image at this time. Please try again."
                    message_placeholder.markdown(full_response)
                    
            except ConnectionError as e:
                st.error("❌ Connection error: Cannot connect to the vision service.")
                full_response = "I'm having trouble connecting to the vision service. Please check your internet connection."
                message_placeholder.markdown(full_response)
            except TimeoutError as e:
                st.error("❌ Timeout error: Image analysis took too long.")
                full_response = "The image analysis timed out. Please try with a smaller image or try again later."
                message_placeholder.markdown(full_response)
            except Exception as e:
                st.error(f"❌ Analysis error: {str(e)}")
                full_response = "An unexpected error occurred during image analysis. Please try again."
                message_placeholder.markdown(full_response)
            
            # Update chat history
            _update_chat_history(user_input, full_response, current_time, response_time)
            _auto_scroll_to_bottom()
            
        except Exception as e:
            # Critical error handling
            st.caption(f"🕒 {datetime.now().strftime('%H:%M • %b %d, %Y')}")
            st.error("A critical error occurred during image analysis.")
            _handle_response_error(user_input, session_id, current_time, e)


def _get_http_error_message(status_code):
    """Get user-friendly error message for HTTP status codes"""
    error_messages = {
        400: "❌ Bad request. The image format might not be supported.",
        401: "❌ Authentication error. Please check your API credentials.",
        403: "❌ Access forbidden. Please check your permissions.",
        404: "❌ Vision service not found.",
        413: "❌ Image too large. Please try with a smaller image.",
        429: "❌ Rate limit exceeded. Please wait a moment and try again.",
        500: "❌ Server error. Please try again later.",
        502: "❌ Bad gateway. The vision service is temporarily unavailable.",
        503: "❌ Service unavailable. Please try again later.",
    }
    return error_messages.get(status_code, f"❌ Request failed with status {status_code}")


def _update_chat_history(user_input, ai_response, user_time, ai_time):
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
        
        # Limit message history (keep last 40 messages)
        if len(new_messages) > 40:
            new_messages = new_messages[-40:]
            print(f"ℹ️ Truncated chat history to 40 messages")
        
        # Update session state
        st.session_state.current_messages = new_messages
        
        # Save to database
        try:
            save_current_session(new_messages)
            print(f"💾 Saved {len(new_messages)} messages to database")
        except Exception as e:
            st.error("❌ Error saving conversation. Your messages may not be persisted.")
            print(f"❌ Database save error: {e}")
            
    except Exception as e:
        st.error(f"❌ Error updating chat history: {str(e)}")
        print(f"❌ Chat history update error: {e}")


def _handle_response_error(user_input, session_id, current_time, error):
    """Handle errors during response generation"""
    try:
        error_msg = f"❌ **System Error**: {str(error)}"
        error_time = datetime.now()
        
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