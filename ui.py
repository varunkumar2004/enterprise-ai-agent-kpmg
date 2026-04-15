import streamlit as st
import requests

API_URL = "http://localhost:8000/ask"

# streamlit config and UI setup
st.set_page_config(page_title="KPMG Internal AI Agent", page_icon="🏢", layout="centered")
st.title("🏢 KPMG Internal AI Agent")
st.markdown("Ask me questions about internal guidelines, security protocols, or general finance concepts.")
st.divider()

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Type your question here..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("Analysing securely..."):
        try:
            payload = {"user_input": prompt}
            response = requests.post(API_URL, json=payload)
            response.raise_for_status() # raise an error for bad responses

            data = response.json()
            bot_reply = data.get("response", "Error: No response from server.")

        except requests.exceptions.ConnectionError:
            bot_reply = "⚠️ Cannot connect to the backend. Is your FastAPI server running on port 8000?"
        except Exception as e:
            bot_reply = f"⚠️ An error occurred: {str(e)}"

    with st.chat_message("assistant"):
        st.markdown(bot_reply)

    st.session_state.messages.append({"role": "assistant", "content": bot_reply})