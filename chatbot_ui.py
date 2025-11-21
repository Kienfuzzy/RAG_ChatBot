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
    st.session_state.memory.clear_session(st.session_state.session_id)
    st.session_state.messages = []
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
    
    # Get context from RAG if enabled
    context = ""
    query_info = ""
    if enable_rag:
        try:
            response = requests.post(
                f"{FASTAPI_URL}/documents/search-hybrid",
                json={
                    "query": prompt, 
                    "limit": search_limit,
                    "qdrant_weight": 0.5,
                    "elasticsearch_weight": 0.5
                },
                headers={"x-token": SECRET_TOKEN}
            )
            if response.status_code == 200:
                results = response.json()
                
                # Show cache status
                if results.get('cached'):
                    query_info = "⚡ **Cached result** (fast!)\n\n"
                
                if results['results']:
                    context_parts = []
                    for result in results['results']:
                        context_parts.append(f"[{result['title']}]\n{result['content']}")
                    context = "\n\n".join(context_parts)
        except Exception as e:
            st.error(f"Search error: {str(e)}")
    
    # Generate response
    with st.chat_message("assistant"):
        # Show query processing info if available
        if query_info:
            st.markdown(query_info)
        
        messages = [{
            "role": "system", 
            "content": "You are a helpful assistant. When users ask about what you said earlier, refer to your previous messages in this conversation."
        }]
        
        if context:
            messages.append({
                "role": "system",
                "content": f"Context:\n{context}\n\nUse this to answer."
            })
        
        # Add conversation history from memory (previous turns only)
        conversation_history = st.session_state.memory.get_history(st.session_state.session_id)
        messages.extend(conversation_history)
        
        # Add current user message
        messages.append({"role": "user", "content": prompt})

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7
            )
            reply = response.choices[0].message.content
            st.write(reply)
            
            # Add both user message and assistant reply to memory
            st.session_state.memory.add_message(st.session_state.session_id, "user", prompt)
            st.session_state.memory.add_message(st.session_state.session_id, "assistant", reply)
            
            # Add to display state
            st.session_state.messages.append({"role": "assistant", "content": reply})
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
