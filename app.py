import streamlit as st
import requests
import random
import string

FASTAPI_URL = "http://127.0.0.1:8000"

# Initialize session state
if "selected_chat" not in st.session_state:
    st.session_state.selected_chat = None
if "chats" not in st.session_state:
    st.session_state.chats = []
if "messages" not in st.session_state:
    st.session_state.messages = []
if "token" not in st.session_state:
    st.session_state.token = ""

def load_chats(token):
    try:
        response = requests.get(f"{FASTAPI_URL}/chats", headers={"Authorization": f"Bearer {token}"})
        if response.status_code == 200:
            st.session_state.chats = response.json().get("chats", [])
        else:
            st.error(f"Failed to load chats: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"Error loading chats: {str(e)}")

def load_chat_history(thread_id, token):
    try:
        response = requests.post(
            f"{FASTAPI_URL}/chat",
            json={"thread_id": thread_id},
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            st.session_state.messages = response.json().get("history", [])
        else:
            st.error(f"Failed to load chat history: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"Error loading chat history: {str(e)}")

def generate_random_chat_name():
    letters = ''.join(random.choices(string.ascii_uppercase, k=3))
    numbers = ''.join(random.choices(string.digits, k=3))
    return f"Chat-{letters}{numbers}"

def create_new_chat(token):
    chat_name = generate_random_chat_name()
    try:
        response = requests.post(
            f"{FASTAPI_URL}/chat/new",
            json={"chat_name": chat_name},
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            new_chat = response.json()
            st.session_state.chats.append(new_chat)
            st.session_state.selected_chat = new_chat["thread_id"]
            st.session_state.messages = []
            load_chats(token)  # Refresh chat list
        else:
            st.error(f"Failed to create chat: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"Error creating chat: {str(e)}")

def delete_chat(thread_id, token):
    try:
        response = requests.delete(
            f"{FASTAPI_URL}/chat",
            json={"thread_id": thread_id},
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            st.session_state.chats = [chat for chat in st.session_state.chats if chat["thread_id"] != thread_id]
            if st.session_state.selected_chat == thread_id:
                st.session_state.selected_chat = None
                st.session_state.messages = []
            load_chats(token)
        else:
            st.error(f"Failed to delete chat: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"Error deleting chat: {str(e)}")

def delete_all_chats(token):
    try:
        response = requests.delete(
            f"{FASTAPI_URL}/chats",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            st.session_state.chats = []
            st.session_state.selected_chat = None
            st.session_state.messages = []
            load_chats(token)  # Refresh chat list
        else:
            st.error(f"Failed to delete all chats: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"Error deleting all chats: {str(e)}")

def get_display_name(chat, token):
    thread_id = chat["thread_id"]
    response = requests.post(
        f"{FASTAPI_URL}/chat",
        json={"thread_id": thread_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 200:
        history = response.json().get("history", [])
        for msg in history:
            if msg["role"] == "user":
                return msg["content"][:50]  # Truncate for brevity
    return chat["chat_name"]

# Token input at the top of the UI
st.title("AI Medical Assistant")
st.session_state.token = st.text_input("Enter your API Token", value=st.session_state.token, type="password")
st.image("mosefak.jpg", width=380)
st.write("Get medical advice, book appointments, and healthcare inquiries!")
st.divider()

if not st.session_state.token:
    st.warning("Please enter a valid API token to proceed.")
else:
    if not st.session_state.chats:
        load_chats(st.session_state.token)

    # Sidebar
    with st.sidebar:
        st.subheader("Chats")
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("Create New Chat"):
                create_new_chat(st.session_state.token)
        with col2:
            if st.button("Delete All", type="secondary"):
                if st.dialog("Are you sure you want to delete all chats?"):
                    delete_all_chats(st.session_state.token)
        
        # Display chats as a clickable list with delete buttons
        for chat in st.session_state.chats:
            chat_name = get_display_name(chat, st.session_state.token)
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(chat_name, key=f"select_{chat['thread_id']}"):
                    st.session_state.selected_chat = chat["thread_id"]
                    load_chat_history(chat["thread_id"], st.session_state.token)
            with col2:
                if st.button("🗑️", key=f"delete_{chat['thread_id']}"):
                    delete_chat(chat["thread_id"], st.session_state.token)

    if st.session_state.selected_chat:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if user_question := st.chat_input("Ask your medical question here:"):
            st.session_state.messages.append({"role": "user", "content": user_question})
            with st.chat_message("user"):
                st.markdown(user_question)
            
            try:
                thread_id = st.session_state.selected_chat
                payload = {"question": user_question, "thread_id": thread_id}
                response = requests.post(
                    f"{FASTAPI_URL}/ask",
                    json=payload,
                    headers={"Authorization": f"Bearer {st.session_state.token}"}
                )
                if response.status_code == 200:
                    assistant_response = response.json().get("response", "No response received.")
                else:
                    assistant_response = f"Error: {response.status_code} - {response.text}"
            except Exception as e:
                assistant_response = f"An error occurred: {str(e)}"
            
            with st.chat_message("assistant"):
                st.markdown(assistant_response)
            st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    else:
        st.info("Please select or create a chat to start messaging.")