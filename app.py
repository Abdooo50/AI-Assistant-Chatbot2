import streamlit as st
from Workflow.workflow import Workflow
from Workflow.utils.helper_functions import to_markdown




# Streamlit app setup
st.title("AI Medical Assistant")

st.image("mosefak.jpg", width=380)
st.write("Get medical advice, book appointments, and healthcare inquiries!")
st.divider()


# Initialize Workflow instance in session state
if "workflow" not in st.session_state:
    st.session_state.workflow = Workflow()


st.image(st.session_state.workflow.visualize_graph())


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

    # Create a placeholder for the assistant's response
    assistant_message_placeholder = st.chat_message("assistant")
    response_container = assistant_message_placeholder.empty()

    # Stream the response
    response_text = ""
    try:
        for partial_response in st.session_state.workflow.get_response(user_question):
            # Append new content to the response text
            response_text += partial_response
            # Update the placeholder with the current response
            response_container.markdown(to_markdown(response_text))
    except Exception as e:
        response_container.markdown("An error occurred while processing your request.")

    # Add full assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": to_markdown(response_text)})
