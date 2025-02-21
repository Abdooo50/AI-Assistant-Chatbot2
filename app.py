# streamlit_app.py
import streamlit as st
import requests

# FastAPI backend URL
FASTAPI_URL = "http://127.0.0.1:8000"

# Streamlit app setup
st.title("AI Medical Assistant")

st.image("mosefak.jpg", width=380)
st.write("Get medical advice, book appointments, and healthcare inquiries!")
st.divider()

# Initialize session state to store chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    role, content = message["role"], message["content"]
    with st.chat_message(role):
        st.markdown(content)

# Accept user input
if user_question := st.chat_input("Ask your medical question here:"):
    # Add user question to chat history
    st.session_state.messages.append({"role": "user", "content": user_question})

    # Display user question
    with st.chat_message("user"):
        st.markdown(user_question)

    # Send the question to the FastAPI backend
    try:
        response = requests.post(
            f"{FASTAPI_URL}/ask",
            json={"question": user_question}
        )
        if response.status_code == 200:
            assistant_response = response.json().get("response", "No response received.")
        else:
            assistant_response = f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        assistant_response = f"An error occurred: {str(e)}"

    # Display assistant response
    with st.chat_message("assistant"):
        st.markdown(assistant_response)

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})