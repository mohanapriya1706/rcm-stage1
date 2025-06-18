import streamlit as st
import requests

# Backend endpoints
AUTH_URL = "http://your-backend.com/auth"
CHAT_URL = "http://your-backend.com/get_response"

st.set_page_config(page_title="RCM Healthcare Chatbot", layout="centered")

# Session state setup
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "credentials" not in st.session_state:
    st.session_state.credentials = {}

# Login form
def show_login():
    st.title("RCM Healthcare Login")
    role = st.selectbox("Select Role", ["Patient", "Frontdesk"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        payload = {
            "username": username,
            "password": password,
            "role": role.lower()
        }
        try:
            response = requests.post(AUTH_URL, json=payload)
            if response.status_code == 200 and response.json().get("status") == "success":
                st.session_state.logged_in = True
                st.session_state.credentials = payload
                st.success("Login successful!")
            else:
                st.error("Invalid credentials or role.")
        except Exception as e:
            st.error(f"Error connecting to backend: {e}")

# Chat interface
def show_chat():
    st.title("RCM Healthcare Chatbot")
    st.write("Ask about pre-registration or appointment scheduling.")

    for role, message in st.session_state.chat_history:
        if role == "user":
            st.chat_message("user").write(message)
        else:
            st.chat_message("assistant").write(message)

    user_input = st.chat_input("Type your message here...")
    if user_input:
        st.session_state.chat_history.append(("user", user_input))
        try:
            payload = {
                "query": user_input,
                **st.session_state.credentials
            }
            response = requests.post(CHAT_URL, json=payload)
            if response.status_code == 200:
                reply = response.json().get("response", "Sorry, I didn't get that.")
            else:
                reply = "Error from backend."
        except Exception as e:
            reply = f"Error: {e}"

        st.session_state.chat_history.append(("assistant", reply))

# Render appropriate UI
if not st.session_state.logged_in:
    show_login()
else:
    show_chat()
