import streamlit as st
import requests
from openai import OpenAI
from app.config import settings
from app.services.conversation_memory import ConversationMemory
import uuid


# Configuration from app/config.py
OPENAI_API_KEY = settings.openai_api_key
FASTAPI_URL = settings.fastapi_url
SECRET_TOKEN = settings.secret_key

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize conversation memory
if "memory" not in st.session_state:
    st.session_state.memory = ConversationMemory(max_messages=10)

# Initialize session ID (unique per browser session)
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Initialize session state (for display only)
if "messages" not in st.session_state:
    st.session_state.messages = []

# Page config
st.set_page_config(page_title="RAG Chatbot", page_icon="🤖")

# Sidebar
st.sidebar.title("🤖 RAG Chatbot")
enable_rag = st.sidebar.toggle("Enable RAG", value=True)
search_limit = st.sidebar.slider("Documents", 1, 10, 3)

# Clear conversation button
if st.sidebar.button("🗑️ Clear Conversation"):
    # Clear server-side memory via API
    try:
        requests.post(
            f"{FASTAPI_URL}/agent/clear-session",
            params={"session_id": st.session_state.session_id},
            headers={"x-token": SECRET_TOKEN}
        )
    except Exception as e:
        st.sidebar.error(f"Error clearing session: {str(e)}")
    
    # Clear UI messages
    st.session_state.messages = []
    st.rerun()
    st.rerun()

# Upload file
st.sidebar.markdown("### 📄 Upload")
uploaded_file = st.sidebar.file_uploader("Upload .txt or .md", type=["txt", "md"])
if uploaded_file and st.sidebar.button("Upload"):
    with st.spinner("Uploading..."):
        try:
            files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
            response = requests.post(
                f"{FASTAPI_URL}/documents/upload-file",
                files=files,
                headers={"x-token": SECRET_TOKEN}
            )
            if response.status_code == 200:
                result = response.json()
                st.sidebar.success(f"✅ {result['chunks_created']} chunks created")
            else:
                st.sidebar.error("Upload failed")
        except Exception as e:
            st.sidebar.error(f"Error: {str(e)}")

# Show documents
if st.sidebar.button("📋 Documents"):
    try:
        response = requests.get(
            f"{FASTAPI_URL}/documents/",
            headers={"x-token": SECRET_TOKEN}
        )
        if response.status_code == 200:
            data = response.json()
            st.sidebar.markdown(f"**Total: {data['count']}**")
            for file in data['files']:
                st.sidebar.markdown(f"- {file['filename']} ({file['total_chunks']})")
    except Exception as e:
        st.sidebar.error(f"Error: {str(e)}")

# Main chat
st.title("💬 RAG Assistant")

# Display messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
if prompt := st.chat_input("Ask about your documents..."):
    # Add to display state
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    # Use agent endpoint if RAG is enabled
    if enable_rag:
        try:
            response = requests.post(
                f"{FASTAPI_URL}/agent/query",
                json={
                    "query": prompt,
                    "session_id": st.session_state.session_id
                },
                headers={"x-token": SECRET_TOKEN}
            )
            
            if response.status_code == 200:
                result = response.json()
                
                with st.chat_message("assistant"):
                    # Display agent's answer
                    st.write(result["answer"])
                    
                    # Show tool trace in expander if tools were used
                    if result.get("tool_calls") and len(result["tool_calls"]) > 0:
                        with st.expander("🔧 Agent Actions", expanded=False):
                            st.markdown(f"**Iterations:** {result['iterations']}")
                            for i, tool_call in enumerate(result["tool_calls"], 1):
                                st.markdown(f"**{i}. {tool_call['tool']}**")
                                st.json(tool_call["args"])
                                st.caption(f"Found {tool_call['result_count']} results")
                
                # Add to display state
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result["answer"]
                })
            else:
                st.error(f"Agent error: {response.status_code}")
                
        except Exception as e:
            error_msg = f"Agent error: {str(e)}"
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    else:
        # Fallback: direct OpenAI call without RAG
        with st.chat_message("assistant"):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
                reply = response.choices[0].message.content
                st.write(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
                
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
