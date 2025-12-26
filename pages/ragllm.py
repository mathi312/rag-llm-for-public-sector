"""Streamlit-based user interface for the RAG document assistant.

This module provides the web interface for uploading documents, building
or loading vector indexes, and interacting with the document corpus via
natural language queries.
"""

import streamlit as st
from pathlib import Path

from loaders import load_files_to_documents, load_directory_documents, split_documents
from models import get_embeddings, get_llm
from indexing import load_index, build_index_from_documents
from chat import create_rag_chain, answer_question

# Define the static data directory (mounted via Docker)
DATA_DIR = Path(__file__).parent / "data"

st.set_page_config(page_title="Digital Assistant - RAG-LLM", layout="wide")
st.title("🤖 Digital Assistants - RAG-LLM (Hybrid)")

# --- SIDEBAR UI ---
with st.sidebar:
    st.header("1. AI Provider Configuration")
    
    provider = st.radio("Select Provider", ["Local (Ollama)", "OpenAI"], index=0)
    
    api_key = None
    selected_model = ""
    
    if provider == "OpenAI":
        api_key = st.text_input("OpenAI API Key", type="password")
        selected_model = st.selectbox("Select OpenAI Model", ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"], index=1)
        # We hardcode the embedding model for OpenAI to be consistent
        embedding_model_name = "text-embedding-3-small"
    else:
        selected_model = st.selectbox("Select Local Model", ["llama3.2", "llama3", "mistral"], index=0)
        embedding_model_name = selected_model  # Ollama uses the same model tag usually

    st.divider()

    st.header("2. Data Sources")
    
    # Static Files Check
    static_files = []
    if DATA_DIR.exists():
        static_files = [f for f in DATA_DIR.iterdir() if f.suffix.lower() in ['.pdf', '.docx']]
    
    if static_files:
        st.success(f"✅ Found {len(static_files)} static files in /data")
        include_static = st.checkbox("Include static files", value=True)
    else:
        st.info("No static files found in /data")
        include_static = False

    # Upload Files
    uploaded_files = st.file_uploader(
        "Upload additional files",
        type=["pdf", "docx"],
        accept_multiple_files=True
    )

    st.divider()
    
    build_mode = st.radio(
        "Index mode",
        ["Use existing index", "Rebuild index"],
        index=0
    )

    process_btn = st.button("Build / Update Index")

# --- SESSION STATE ---
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- INITIALIZATION CHECK ---
if provider == "OpenAI" and not api_key:
    st.warning("⚠️ Please enter your OpenAI API Key in the sidebar to continue.")
    st.stop()

# Initialize Embeddings based on selection
try:
    embeddings = get_embeddings(provider, embedding_model_name, api_key)
except Exception as e:
    st.error(f"Error initializing embeddings: {e}")
    st.stop()

# Auto-load existing index
if st.session_state.vector_store is None:
    vs = load_index(embeddings)
    if vs:
        st.session_state.vector_store = vs
        st.sidebar.success("Loaded existing index.")

# --- BUILD LOGIC ---
if process_btn:
    if build_mode == "Rebuild index" or not st.session_state.vector_store:
        
        all_docs = []
        status_msg = st.sidebar.empty()
        
        # Load Static Files
        if include_static and static_files:
            status_msg.info("Loading static files from /data ...")
            static_docs = load_directory_documents(DATA_DIR)
            all_docs.extend(static_docs)
            
        # Load Uploaded Files
        if uploaded_files:
            status_msg.info("Loading uploaded files...")
            upload_docs = load_files_to_documents(uploaded_files)
            all_docs.extend(upload_docs)
            
        if not all_docs:
            st.sidebar.warning("No documents found.")
        else:
            status_msg.info(f"Processing {len(all_docs)} documents...")
            splits = split_documents(all_docs)
            
            status_msg.info("Building vector index...")
            # Batch size 5 is safe for local; OpenAI can handle larger but 5 is fine for both
            st.session_state.vector_store = build_index_from_documents(splits, embeddings, batch_size=5)
            
            status_msg.success(f"Index built successfully!")
            st.sidebar.success("Index Ready.")
    else:
        st.sidebar.success("Using existing index.")

# --- CHAT UI ---
if st.session_state.vector_store:
    st.divider()
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("Ask a question..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        try:
            llm = get_llm(provider, selected_model, api_key=api_key)
            chain = create_rag_chain(st.session_state.vector_store, llm)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    ans = answer_question(chain, prompt)
                    st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
        except Exception as e:
            st.error(f"An error occurred: {e}")
else:
    st.info("Please build the index to start chatting.")
