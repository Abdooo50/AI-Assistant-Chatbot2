import streamlit as st
import requests
import json
import time
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import markdown

# Load environment variables
load_dotenv()

# Configuration
API_URL = "https://ai-medical-assistant-production.up.railway.app"
AUTH_URL = os.getenv("AUTH_URL", "https://mosefakapiss.runasp.net/api/Authentication/Login")

# Initialize session state
if "token" not in st.session_state:
    st.session_state.token = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "current_thread_id" not in st.session_state:
    st.session_state.current_thread_id = None
if "chats" not in st.session_state:
    st.session_state.chats = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pagination" not in st.session_state:
    st.session_state.pagination = {}
if "suggested_questions" not in st.session_state:
    st.session_state.suggested_questions = []
if "login_error" not in st.session_state:
    st.session_state.login_error = None
if "question_to_ask" not in st.session_state:
    st.session_state.question_to_ask = None
if "refresh_needed" not in st.session_state:
    st.session_state.refresh_needed = False
if "loading_older_messages" not in st.session_state:
    st.session_state.loading_older_messages = False
if "scroll_position" not in st.session_state:
    st.session_state.scroll_position = 0
if "auto_scroll_enabled" not in st.session_state:
    st.session_state.auto_scroll_enabled = True

# Custom CSS for ChatGPT-like UI
st.markdown("""
<style>
    /* Main container styling */
    .main {
        background-color: #f7f7f8;
    }
    
    /* Chat container */
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
    }
    
    /* Message styling */
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    
    /* User message styling */
    .user-message {
        background-color: #ffffff;
        border: 1px solid #e5e5e5;
    }
    
    /* Assistant message styling */
    .assistant-message {
        background-color: #f0f4f9;
        border: 1px solid #d9e2ec;
    }
    
    /* Message header */
    .message-header {
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    
    /* User header */
    .user-header {
        color: #2d3748;
    }
    
    /* Assistant header */
    .assistant-header {
        color: #2b6cb0;
    }
    
    /* Message content */
    .message-content {
        line-height: 1.5;
    }
    
    /* Code blocks */
    pre {
        background-color: #1e1e1e;
        color: #d4d4d4;
        padding: 1rem;
        border-radius: 0.3rem;
        overflow-x: auto;
    }
    
    code {
        font-family: 'Courier New', monospace;
    }
    
    /* Suggested questions */
    .suggested-question {
        display: inline-block;
        background-color: #e2e8f0;
        color: #2d3748;
        padding: 0.5rem 1rem;
        border-radius: 1rem;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    
    .suggested-question:hover {
        background-color: #cbd5e0;
    }
    
    /* Pagination controls */
    .pagination-controls {
        display: flex;
        justify-content: space-between;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: #f8fafc;
    }
    
    /* Chat list item */
    .chat-list-item {
        padding: 0.75rem;
        border-radius: 0.3rem;
        margin-bottom: 0.5rem;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    
    .chat-list-item:hover {
        background-color: #e2e8f0;
    }
    
    .chat-list-item.active {
        background-color: #e2e8f0;
        font-weight: bold;
    }
    
    /* Input area */
    .input-area {
        display: flex;
        margin-top: 1rem;
    }
    
    .stTextInput {
        flex-grow: 1;
    }
    
    /* Login form */
    .login-form {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background-color: #ffffff;
        border-radius: 0.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .login-header {
        text-align: center;
        margin-bottom: 1.5rem;
    }
    
    .login-button {
        width: 100%;
    }
    
    .login-error {
        color: #e53e3e;
        margin-top: 0.5rem;
        text-align: center;
    }
    
    /* Time period headers */
    .time-period-header {
        font-size: 0.9rem;
        color: #718096;
        font-weight: 600;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
        padding-left: 0.5rem;
        border-bottom: 1px solid #e2e8f0;
        padding-bottom: 0.25rem;
    }
    
    /* Empty state */
    .empty-state {
        color: #718096;
        font-style: italic;
        padding: 0.5rem;
        text-align: center;
        font-size: 0.9rem;
    }
    
    /* Loading indicator */
    .loading-container {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .loading-spinner {
        border: 4px solid #f3f3f3;
        border-top: 4px solid #3498db;
        border-radius: 50%;
        width: 30px;
        height: 30px;
        animation: spin 1s linear infinite;
        margin-right: 10px;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .loading-text {
        color: #718096;
        font-size: 0.9rem;
    }
    
    /* Scroll to bottom button */
    .scroll-button {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background-color: #4a5568;
        color: white;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        display: flex;
        justify-content: center;
        align-items: center;
        cursor: pointer;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        z-index: 1000;
    }
    
    .scroll-button:hover {
        background-color: #2d3748;
    }
    
    /* Auto-scroll toggle */
    .auto-scroll-toggle {
        display: flex;
        align-items: center;
        margin-top: 0.5rem;
        margin-bottom: 1rem;
    }
    
    .auto-scroll-toggle input {
        margin-right: 0.5rem;
    }
    
    /* Infinite scroll trigger */
    .infinite-scroll-trigger {
        height: 20px;
        margin-top: 2rem;
        margin-bottom: 2rem;
    }
</style>

<script>
function scrollToBottom() {
    const chatContainer = document.querySelector('.main');
    if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}

function observeScrollPosition() {
    const chatContainer = document.querySelector('.main');
    if (chatContainer) {
        chatContainer.addEventListener('scroll', function() {
            // If we're near the top of the container and have more messages to load
            if (chatContainer.scrollTop < 200) {
                // Trigger loading more messages
                window.parent.postMessage({
                    type: 'streamlit:loadMoreMessages'
                }, '*');
            }
            
            // Save scroll position
            window.parent.postMessage({
                type: 'streamlit:saveScrollPosition',
                scrollTop: chatContainer.scrollTop,
                scrollHeight: chatContainer.scrollHeight
            }, '*');
        });
    }
}

// Initialize when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Set up scroll observation
    observeScrollPosition();
    
    // Initial scroll to bottom if needed
    setTimeout(scrollToBottom, 100);
});
</script>
""", unsafe_allow_html=True)

# Helper functions
def format_message(role, content):
    """Format a message with proper styling based on role"""
    role_class = "user" if role == "user" else "assistant"
    role_display = "You" if role == "user" else "Assistant"
    
    # Convert markdown to HTML for assistant messages
    if role == "assistant":
        content = markdown.markdown(content)
    
    return f"""
    <div class="chat-message {role_class}-message">
        <div class="message-header {role_class}-header">{role_display}</div>
        <div class="message-content">
            {content}
        </div>
    </div>
    """

def display_suggested_questions():
    """Display suggested follow-up questions"""
    if st.session_state.suggested_questions:
        st.markdown("<div style='margin-top: 1rem;'>", unsafe_allow_html=True)
        for i, question in enumerate(st.session_state.suggested_questions):
            if st.button(f"{question['text']}", key=f"suggested_{i}"):
                st.session_state.question_to_ask = question['text']
                st.session_state.refresh_needed = True
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

def handle_login():
    """Handle user login"""
    st.markdown("""
    <div class="login-form">
        <div class="login-header">
            <h1>Medical Assistant Login</h1>
        </div>
    """, unsafe_allow_html=True)
    
    email = st.text_input("Email", placeholder="Enter your email")
    password = st.text_input("Password", type="password", placeholder="Enter your password")
    
    # Optional FCM token field
    fcm_token = st.text_input("FCM Token (Optional)", value="", placeholder="Leave empty if not needed")
    
    if st.button("Login", use_container_width=True):
        try:
            # Prepare login payload
            login_payload = {
                "email": email,
                "password": password
            }
            
            # Add FCM token if provided
            if fcm_token:
                login_payload["fcmToken"] = fcm_token
            
            # Clear previous login error
            st.session_state.login_error = None
            
            # Show loading message
            with st.spinner("Logging in..."):
                # Make the login request to the authentication endpoint
                response = requests.post(
                    AUTH_URL,
                    json=login_payload,
                    headers={"Content-Type": "application/json"}
                )
                
                # Check response status
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if token is in the response
                    if "token" in data:
                        st.session_state.token = data["token"]
                        
                        # Extract user_id from token
                        token_parts = st.session_state.token.split('.')
                        if len(token_parts) >= 2:
                            import base64
                            import json
                            
                            # Add padding if needed
                            padding = '=' * (4 - len(token_parts[1]) % 4)
                            try:
                                payload = json.loads(base64.urlsafe_b64decode(token_parts[1] + padding).decode('utf-8'))
                                
                                if "nameid" in payload:
                                    st.session_state.user_id = payload["nameid"]
                                
                                st.success("Login successful!")
                                time.sleep(1)  # Short delay to show success message
                                st.rerun()
                            except Exception as e:
                                st.session_state.login_error = f"Error decoding token: {str(e)}"
                    else:
                        st.session_state.login_error = "Token not found in response"
                else:
                    # Try to extract error message from response
                    try:
                        error_data = response.json()
                        error_message = error_data.get("message", "Unknown error")
                        st.session_state.login_error = f"Login failed: {error_message}"
                    except:
                        st.session_state.login_error = f"Login failed with status code: {response.status_code}"
        except Exception as e:
            st.session_state.login_error = f"Error during login: {str(e)}"
    
    # Display login error if any
    if st.session_state.login_error:
        st.markdown(f"""
        <div class="login-error">
            {st.session_state.login_error}
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

def fetch_chats():
    """Fetch chat threads for the current user"""
    if not st.session_state.token:
        return
    
    try:
        with st.spinner("Loading chats..."):
            response = requests.post(
                f"{API_URL}/chats",
                headers={"Authorization": f"Bearer {st.session_state.token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                st.session_state.chats = data["chats"]
                st.session_state.pagination = data["pagination"]
            else:
                st.error(f"Error fetching chats: {response.text}")
    except Exception as e:
        st.error(f"Error fetching chats: {str(e)}")

def fetch_chat_history(thread_id, cursor=None, direction="before"):
    """Fetch chat history for a specific thread"""
    if not st.session_state.token or not thread_id:
        return
    
    try:
        # Set loading state
        if direction == "before":
            st.session_state.loading_older_messages = True
        
        payload = {
            "thread_id": thread_id,
            "limit": 20
        }
        
        if cursor:
            # Convert cursor to integer if it's a timestamp
            try:
                # Try to convert to integer if it's a numeric string
                if isinstance(cursor, str) and cursor.isdigit():
                    cursor = int(cursor)
                payload["cursor"] = cursor
                payload["direction"] = direction
            except (ValueError, TypeError):
                # If conversion fails, don't include cursor in payload
                if direction == "before":
                    st.session_state.loading_older_messages = False
                return
        
        response = requests.post(
            f"{API_URL}/chat",
            json=payload,
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # If loading newer messages (after), prepend to existing history
            if direction == "after" and cursor:
                st.session_state.chat_history = data["history"] + st.session_state.chat_history
            # If loading older messages (before), append to existing history
            elif direction == "before" and cursor:
                st.session_state.chat_history = st.session_state.chat_history + data["history"]
            # Initial load
            else:
                st.session_state.chat_history = data["history"]
            
            st.session_state.pagination = data["pagination"]
        else:
            st.error(f"Error fetching chat history: {response.text}")
    except Exception as e:
        st.error(f"Error fetching chat history: {str(e)}")
    finally:
        # Reset loading state
        if direction == "before":
            st.session_state.loading_older_messages = False

def create_new_chat(chat_name):
    """Create a new chat thread"""
    if not st.session_state.token:
        return
    
    try:
        with st.spinner("Creating new chat..."):
            response = requests.post(
                f"{API_URL}/chat/new",
                json={"chat_name": chat_name},
                headers={"Authorization": f"Bearer {st.session_state.token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                st.session_state.current_thread_id = data["thread_id"]
                fetch_chats()
                fetch_chat_history(data["thread_id"])
                return data["thread_id"]
            else:
                st.error(f"Error creating chat: {response.text}")
                return None
    except Exception as e:
        st.error(f"Error creating chat: {str(e)}")
        return None

def on_send_button_click():
    """Handle send button click"""
    question = st.session_state.question_input
    if question:
        st.session_state.question_to_ask = question
        st.session_state.refresh_needed = True
        st.rerun()

def ask_question(question):
    """Send a question to the backend and get a response"""
    if not st.session_state.token or not st.session_state.current_thread_id:
        st.warning("Please select or create a chat first.")
        return
    
    # Add user message to UI immediately
    st.session_state.chat_history.insert(0, {
        "message_id": int(time.time() * 1000),
        "role": "user",
        "content": question,
        "created_at": datetime.now().isoformat()
    })
    
    try:
        with st.spinner("Getting response..."):
            # Use non-streaming response for simplicity and reliability
            response = requests.post(
                f"{API_URL}/ask",
                json={
                    "question": question,
                    "thread_id": st.session_state.current_thread_id,
                    "stream": False
                },
                headers={"Authorization": f"Bearer {st.session_state.token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Add assistant message to UI
                st.session_state.chat_history.insert(0, {
                    "message_id": int(time.time() * 1000),
                    "role": "assistant",
                    "content": data["response"],
                    "created_at": datetime.now().isoformat()
                })
                
                # Update suggested questions
                if "suggested_questions" in data:
                    st.session_state.suggested_questions = data["suggested_questions"]
                else:
                    st.session_state.suggested_questions = []
                
                # Refresh chat list to update last_updated_at
                fetch_chats()
            else:
                st.error(f"Error asking question: {response.text}")
    except Exception as e:
        st.error(f"Error asking question: {str(e)}")

def delete_chat(thread_id):
    """Delete a chat thread"""
    if not st.session_state.token:
        return
    
    try:
        with st.spinner("Deleting chat..."):
            response = requests.delete(
                f"{API_URL}/chat",
                json={"thread_id": thread_id},
                headers={"Authorization": f"Bearer {st.session_state.token}"}
            )
            
            if response.status_code == 200:
                # If the deleted chat was the current one, clear it
                if st.session_state.current_thread_id == thread_id:
                    st.session_state.current_thread_id = None
                    st.session_state.chat_history = []
                
                # Refresh chat list
                fetch_chats()
                st.success("Chat deleted successfully.")
            else:
                st.error(f"Error deleting chat: {response.text}")
    except Exception as e:
        st.error(f"Error deleting chat: {str(e)}")

def delete_all_chats():
    """Delete all chat threads for the current user"""
    if not st.session_state.token:
        return
    
    try:
        with st.spinner("Deleting all chats..."):
            response = requests.delete(
                f"{API_URL}/chats",
                headers={"Authorization": f"Bearer {st.session_state.token}"}
            )
            
            if response.status_code == 200:
                # Clear current chat
                st.session_state.current_thread_id = None
                st.session_state.chat_history = []
                
                # Refresh chat list
                fetch_chats()
                st.success("All chats deleted successfully.")
            else:
                st.error(f"Error deleting all chats: {response.text}")
    except Exception as e:
        st.error(f"Error deleting all chats: {str(e)}")

def refresh_chat_data():
    """Refresh chat data periodically"""
    if st.session_state.current_thread_id:
        fetch_chat_history(st.session_state.current_thread_id)
    fetch_chats()

def group_chats_by_time_period():
    """Group chats by time period (Today, Yesterday, Previous 7 Days, Previous 30 Days)"""
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    last_week = today - timedelta(days=7)
    last_month = today - timedelta(days=30)
    
    # Initialize groups
    groups = {
        "Today": [],
        "Yesterday": [],
        "Previous 7 Days": [],
        "Previous 30 Days": [],
        "Older": []
    }
    
    # Group chats by time period
    for chat in st.session_state.chats:
        chat_date = None
        if chat.get("last_updated_at"):
            try:
                # Parse the ISO format date
                dt = datetime.fromisoformat(chat["last_updated_at"])
                chat_date = dt.date()
            except:
                # If parsing fails, use current date as fallback
                chat_date = today
        else:
            # If no date is available, use current date as fallback
            chat_date = today
        
        # Assign to appropriate group
        if chat_date == today:
            groups["Today"].append(chat)
        elif chat_date == yesterday:
            groups["Yesterday"].append(chat)
        elif chat_date >= last_week:
            groups["Previous 7 Days"].append(chat)
        elif chat_date >= last_month:
            groups["Previous 30 Days"].append(chat)
        else:
            groups["Older"].append(chat)
    
    return groups

def check_scroll_for_more_messages():
    """Check if we need to load more messages based on scroll position"""
    # This function is called when the infinite scroll trigger is visible
    if (st.session_state.current_thread_id and 
        st.session_state.pagination.get("has_more_before", False) and 
        not st.session_state.loading_older_messages):
        
        # Get the next cursor
        cursor = st.session_state.pagination.get("next_cursor")
        if cursor:
            # Convert cursor to integer if it's a numeric string
            if isinstance(cursor, str) and cursor.isdigit():
                cursor = int(cursor)
            
            # Fetch older messages
            fetch_chat_history(st.session_state.current_thread_id, cursor, "before")
            return True
    
    return False

# Main application
def main():
    # Process any pending question
    if st.session_state.question_to_ask:
        question = st.session_state.question_to_ask
        st.session_state.question_to_ask = None
        ask_question(question)
    
    # Check if refresh is needed
    if st.session_state.refresh_needed:
        st.session_state.refresh_needed = False
        # No need to do anything else, the rerun will handle it
    
    # Check if user is logged in
    if not st.session_state.token:
        handle_login()
        return
    
    # Sidebar for chat list
    with st.sidebar:
        st.title("Medical Assistant")
        
        # New chat button
        new_chat_name = st.text_input("New Chat Name", value="New Chat")
        if st.button("Create New Chat"):
            create_new_chat(new_chat_name)
        
        st.divider()
        
        # Fetch chats if not already loaded
        if not st.session_state.chats:
            fetch_chats()
        
        # Display chat list grouped by time period
        st.subheader("Your Chats")
        
        # Group chats by time period
        grouped_chats = group_chats_by_time_period()
        
        # Display chats by group
        for group_name, chats in grouped_chats.items():
            if chats:  # Only show groups that have chats
                st.markdown(f"<div class='time-period-header'>{group_name}</div>", unsafe_allow_html=True)
                
                for chat in chats:
                    # Format chat name
                    chat_name = chat["chat_name"]
                    
                    # Create a unique key for each chat button
                    chat_key = f"chat_{chat['thread_id']}"
                    
                    # Check if this is the active chat
                    is_active = st.session_state.current_thread_id == chat["thread_id"]
                    
                    # Create a container for the chat item
                    chat_container = st.container()
                    
                    with chat_container:
                        col1, col2 = st.columns([4, 1])
                        
                        # Chat selection button
                        if col1.button(f"{chat_name}", key=chat_key):
                            st.session_state.current_thread_id = chat["thread_id"]
                            fetch_chat_history(chat["thread_id"])
                            st.rerun()
                        
                        # Delete button
                        if col2.button("🗑️", key=f"delete_{chat_key}"):
                            if st.session_state.current_thread_id == chat["thread_id"]:
                                st.session_state.current_thread_id = None
                                st.session_state.chat_history = []
                            delete_chat(chat["thread_id"])
        
        # Show empty state if no chats
        if not st.session_state.chats:
            st.markdown("<div class='empty-state'>No chats yet. Create a new chat to get started.</div>", unsafe_allow_html=True)
        
        # Pagination for chat list
        if st.session_state.pagination.get("has_more_before", False):
            if st.button("Load More Chats"):
                # Get the last chat's timestamp as cursor
                last_chat = st.session_state.chats[-1]
                cursor = last_chat.get("last_updated_at")
                
                # Fetch more chats
                try:
                    with st.spinner("Loading more chats..."):
                        response = requests.post(
                            f"{API_URL}/chats",
                            json={"cursor": cursor},
                            headers={"Authorization": f"Bearer {st.session_state.token}"}
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            st.session_state.chats.extend(data["chats"])
                            st.session_state.pagination = data["pagination"]
                            st.rerun()
                        else:
                            st.error(f"Error loading more chats: {response.text}")
                except Exception as e:
                    st.error(f"Error loading more chats: {str(e)}")
        
        st.divider()
        
        # Refresh button
        if st.button("Refresh"):
            refresh_chat_data()
            st.rerun()
        
        # Delete all chats button
        if st.button("Delete All Chats"):
            if st.session_state.chats:
                delete_all_chats()
        
        # Logout button
        if st.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Main chat area
    if st.session_state.current_thread_id:
        # Get current chat name
        current_chat_name = "Chat"
        for chat in st.session_state.chats:
            if chat["thread_id"] == st.session_state.current_thread_id:
                current_chat_name = chat["chat_name"]
                break
        
        st.title(current_chat_name)
        
        # Chat input area
        st.text_input("Ask a question", key="question_input", on_change=on_send_button_click)
        
        # Display suggested questions
        display_suggested_questions()
        
        # Auto-scroll toggle
        col1, col2 = st.columns([1, 3])
        with col1:
            st.session_state.auto_scroll_enabled = st.checkbox("Auto-scroll", value=st.session_state.auto_scroll_enabled)
        
        # Chat history container
        chat_container = st.container()
        
        # Infinite scroll trigger at the top
        if st.session_state.pagination.get("has_more_before", False):
            # Create a placeholder for the loading indicator
            loading_placeholder = st.empty()
            
            # If we're loading older messages, show the loading indicator
            if st.session_state.loading_older_messages:
                with loading_placeholder:
                    st.markdown("""
                    <div class="loading-container">
                        <div class="loading-spinner"></div>
                        <div class="loading-text">Loading older messages...</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Create an invisible element that triggers loading more messages when it becomes visible
            trigger = st.empty()
            if trigger.button("Load More", key="infinite_scroll_trigger", help="This button is invisible and automatically triggered when you scroll to the top"):
                # This will be triggered when the user scrolls to the top
                if check_scroll_for_more_messages():
                    st.rerun()
        
        with chat_container:
            # Display chat history
            for message in st.session_state.chat_history:
                role = message.get("role", "assistant")
                content = message.get("content", "")
                
                # Display message
                st.markdown(
                    format_message(role, content),
                    unsafe_allow_html=True
                )
        
        # Add JavaScript to handle scrolling
        st.markdown("""
        <script>
            // Function to check if element is in viewport
            function isInViewport(element) {
                const rect = element.getBoundingClientRect();
                return (
                    rect.top >= 0 &&
                    rect.left >= 0 &&
                    rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
                );
            }
            
            // Function to handle infinite scrolling
            function handleInfiniteScroll() {
                const trigger = document.querySelector('[data-testid="baseButton-secondary"]');
                if (trigger && isInViewport(trigger)) {
                    trigger.click();
                }
            }
            
            // Set up scroll event listener
            document.addEventListener('scroll', handleInfiniteScroll);
            
            // Initial check
            setTimeout(handleInfiniteScroll, 500);
        </script>
        """, unsafe_allow_html=True)
    else:
        # No chat selected
        st.title("Medical Assistant")
        st.write("Select a chat from the sidebar or create a new one to get started.")

if __name__ == "__main__":
    main()
