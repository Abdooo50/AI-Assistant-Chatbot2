"""
Enhanced UI Components for Medical Assistant

This module provides enhanced UI components for the Streamlit frontend,
including ChatGPT-like styling, typing indicators, and streaming response handling.
Compatible with the existing project structure.
"""

import streamlit as st
import time
from datetime import datetime

def apply_chatgpt_styling():
    """
    Apply ChatGPT-like styling to the Streamlit app.
    """
    # Custom CSS for ChatGPT-like styling
    st.markdown("""
    <style>
        /* Main container styling */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        /* Chat message styling */
        .chat-message {
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            display: flex;
            flex-direction: column;
        }
        
        /* User message styling */
        .chat-message.user {
            background-color: #f0f2f6;
            border: 1px solid #e0e2e6;
        }
        
        /* Assistant message styling */
        .chat-message.assistant {
            background-color: #e6f7ff;
            border: 1px solid #d6e7ff;
        }
        
        /* Message header styling */
        .chat-header {
            display: flex;
            align-items: center;
            margin-bottom: 0.5rem;
        }
        
        /* Avatar styling */
        .avatar {
            width: 2rem;
            height: 2rem;
            border-radius: 50%;
            margin-right: 0.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: white;
        }
        
        /* User avatar */
        .avatar.user {
            background-color: #6c757d;
        }
        
        /* Assistant avatar */
        .avatar.assistant {
            background-color: #0084ff;
        }
        
        /* Message content styling */
        .chat-content {
            margin-left: 2.5rem;
        }
        
        /* Typing indicator styling */
        .typing-indicator {
            display: flex;
            align-items: center;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            background-color: #e6f7ff;
            border: 1px solid #d6e7ff;
        }
        
        /* Typing dots animation */
        .typing-dots {
            display: flex;
        }
        
        .typing-dot {
            width: 8px;
            height: 8px;
            margin: 0 2px;
            background-color: #0084ff;
            border-radius: 50%;
            opacity: 0.6;
            animation: typing-dot-animation 1.4s infinite ease-in-out;
        }
        
        .typing-dot:nth-child(1) {
            animation-delay: 0s;
        }
        
        .typing-dot:nth-child(2) {
            animation-delay: 0.2s;
        }
        
        .typing-dot:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        @keyframes typing-dot-animation {
            0%, 100% {
                opacity: 0.6;
                transform: scale(1);
            }
            50% {
                opacity: 1;
                transform: scale(1.2);
            }
        }
        
        /* Timestamp styling */
        .timestamp {
            font-size: 0.75rem;
            color: #6c757d;
            margin-top: 0.25rem;
            text-align: right;
        }
        
        /* Chat input styling */
        .chat-input {
            display: flex;
            margin-top: 1rem;
        }
        
        /* Suggested questions styling */
        .suggested-question {
            padding: 0.5rem 1rem;
            margin: 0.25rem;
            border-radius: 1rem;
            background-color: #f0f2f6;
            border: 1px solid #e0e2e6;
            cursor: pointer;
            font-size: 0.875rem;
            transition: background-color 0.2s;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 100%;
        }
        
        .suggested-question:hover {
            background-color: #e0e2e6;
        }
        
        /* Sidebar styling */
        .chat-sidebar-item {
            padding: 0.75rem;
            border-radius: 0.5rem;
            margin-bottom: 0.5rem;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        
        .chat-sidebar-item:hover {
            background-color: #f0f2f6;
        }
        
        .chat-sidebar-item.active {
            background-color: #e6f7ff;
            border-left: 3px solid #0084ff;
        }
        
        /* Code block styling */
        pre {
            background-color: #f8f9fa;
            border-radius: 0.5rem;
            padding: 1rem;
            overflow-x: auto;
            margin: 1rem 0;
            border: 1px solid #e0e2e6;
        }
        
        code {
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.875rem;
        }
        
        /* Markdown styling */
        .chat-content h1, .chat-content h2, .chat-content h3, 
        .chat-content h4, .chat-content h5, .chat-content h6 {
            margin-top: 1rem;
            margin-bottom: 0.5rem;
        }
        
        .chat-content ul, .chat-content ol {
            margin-left: 1.5rem;
        }
        
        .chat-content table {
            border-collapse: collapse;
            width: 100%;
            margin: 1rem 0;
        }
        
        .chat-content th, .chat-content td {
            border: 1px solid #e0e2e6;
            padding: 0.5rem;
        }
        
        .chat-content th {
            background-color: #f0f2f6;
        }
        
        /* Mobile responsiveness */
        @media (max-width: 768px) {
            .chat-message {
                padding: 0.75rem;
            }
            
            .chat-content {
                margin-left: 2rem;
            }
            
            .avatar {
                width: 1.5rem;
                height: 1.5rem;
            }
        }
    </style>
    """, unsafe_allow_html=True)

def format_timestamp(timestamp_str=None):
    """
    Format timestamp for display.
    
    Args:
        timestamp_str: ISO format timestamp string
        
    Returns:
        Formatted timestamp string
    """
    if not timestamp_str:
        timestamp = datetime.now()
    else:
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            timestamp = datetime.now()
    
    return timestamp.strftime("%I:%M %p · %b %d, %Y")

def display_chat_message(role, content, message_id=None, timestamp=None):
    """
    Display a chat message with proper styling.
    
    Args:
        role: Message role ('user' or 'assistant')
        content: Message content
        message_id: Optional message ID
        timestamp: Optional timestamp
    """
    avatar_letter = "U" if role == "user" else "A"
    avatar_class = "user" if role == "user" else "assistant"
    message_class = "user" if role == "user" else "assistant"
    
    formatted_timestamp = format_timestamp(timestamp)
    
    # Check if content contains code blocks and format them
    content_with_code_formatting = content
    
    message_html = f"""
    <div class="chat-message {message_class}" id="message-{message_id}">
        <div class="chat-header">
            <div class="avatar {avatar_class}">{avatar_letter}</div>
            <div><strong>{"You" if role == "user" else "Assistant"}</strong></div>
        </div>
        <div class="chat-content">
            {content_with_code_formatting}
            <div class="timestamp">{formatted_timestamp}</div>
        </div>
    </div>
    """
    
    st.markdown(message_html, unsafe_allow_html=True)

def display_typing_indicator():
    """
    Display a typing indicator while the assistant is generating a response.
    """
    typing_indicator = """
    <div class="typing-indicator">
        <div class="avatar assistant">A</div>
        <div class="typing-dots">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    </div>
    """
    
    st.markdown(typing_indicator, unsafe_allow_html=True)

def display_chat_sidebar(chats, active_chat_id=None, on_chat_selected=None, on_delete_chat=None):
    """
    Display the chat sidebar with a list of chats.
    
    Args:
        chats: List of chat objects
        active_chat_id: Currently active chat ID
        on_chat_selected: Callback function when a chat is selected
        on_delete_chat: Callback function when a chat is deleted
    """
    for chat in chats:
        chat_id = chat.get("thread_id")
        chat_name = chat.get("chat_name", "Unnamed Chat")
        is_active = chat_id == active_chat_id
        
        chat_class = "active" if is_active else ""
        
        chat_html = f"""
        <div class="chat-sidebar-item {chat_class}" id="chat-{chat_id}">
            <div>{chat_name}</div>
        </div>
        """
        
        if st.markdown(chat_html, unsafe_allow_html=True):
            if on_chat_selected:
                on_chat_selected(chat_id)

def create_enhanced_chat_input(placeholder="Type your message here..."):
    """
    Create an enhanced chat input with better styling.
    
    Args:
        placeholder: Placeholder text for the input
        
    Returns:
        User input text
    """
    # Use Streamlit's built-in chat input
    return st.chat_input(placeholder)

def display_suggested_questions(questions, on_question_selected=None):
    """
    Display suggested follow-up questions.
    
    Args:
        questions: List of suggested question objects
        on_question_selected: Callback function when a question is selected
    """
    if not questions:
        return
    
    st.markdown("<div style='margin-top: 1rem;'><strong>Suggested questions:</strong></div>", unsafe_allow_html=True)
    
    # Create a horizontal container for the questions
    cols = st.columns(len(questions))
    
    for i, question in enumerate(questions):
        with cols[i]:
            if st.button(question.get("text", ""), key=f"suggested_{i}"):
                if on_question_selected:
                    on_question_selected(question.get("text", ""))

def display_streaming_response(placeholder, response_chunks):
    """
    Display a streaming response in the given placeholder.
    
    Args:
        placeholder: Streamlit placeholder to update
        response_chunks: Iterator of response chunks
    """
    full_response = ""
    
    # Display initial empty message
    with placeholder:
        display_chat_message("assistant", full_response)
    
    # Update with each chunk
    for chunk in response_chunks:
        full_response += chunk
        with placeholder:
            display_chat_message("assistant", full_response)
    
    return full_response
