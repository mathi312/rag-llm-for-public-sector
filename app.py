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
from extensions.report_generator import *

import time

from extensions.idprovider import *
from extensions.pocketbase import *

# Define the static data directory (mounted via Docker)
DATA_DIR = Path(__file__).parent / "data"

st.set_page_config(page_title="Digital Assistant - RAG-LLM", layout="wide")
st.title("🤖 Digital Assistant - RAG-LLM (Hybrid)")

# --- SIDEBAR UI ---
with st.sidebar:
    st.header("Current User")
    is_logged_in()

    st.divider()
                
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

    # Citizen ID Upload Section
    st.header("3. Citizen ID Upload")

    citizen_id = st.selectbox("Select Citizen ID", ["ID Card", "Passport", "Residence Permit"], index=0)

    upload_citizen_file = st.button("Upload Citizen ID Document")

    if upload_citizen_file:
        # Mappe den gewählten Ausweis auf die Mock-Daten
        def get_selected_id_data(selection: str) -> dict:
            if selection == "ID Card":
                return id_card
            if selection == "Passport":
                return passport
            if selection == "Residence Permit":
                return residence_permit
            return {}

        st.session_state["id_document"] = {
            "type": citizen_id,
            "data": get_selected_id_data(citizen_id)
        }
        st.session_state["id_uploaded"] = True

        # Show success message for 5 seconds
        msg = st.empty()
        msg.success(f"{citizen_id} document uploaded successfully!")
        time.sleep(2)
        msg.empty()

        st.text(process_id_document())

    st.divider()

    build_mode = st.radio(
        "Index mode",
        ["Use existing index", "Rebuild index"],
        index=0
    )

    process_btn = st.button("Build / Update Index")

    st.divider()

    @st.dialog("Enter your email address")
    def email_dialog(exception: str):
        st.error(exception)
        st.write("Please provide your email to receive the report.")
        email = st.text_input("Email")

        if st.button("Send email"):
            try:
                send_report_via_email(st.session_state.report, email)
                st.success("Email sent successfully.")
            except (EmptyReportError, EmptyEmailAddressError) as e:
                st.warning(str(e))
            except Exception as e:
                st.exception(e)

    if st.button("Print Report"):
        try:
            print_report(st.session_state.report)

            st.success("Report printed successfully.")
        except EmptyReportError as e:
            st.warning(str(e))
        except PrinterBrokenError as e:
            email_dialog(str(e))
        except Exception as e:
            st.exception(e)

# --- SESSION STATE ---
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "id_uploaded" not in st.session_state:
    st.session_state.id_uploaded = False
if "id_document" not in st.session_state:
    st.session_state.id_document = None
if "report" not in st.session_state:
    st.session_state.report = None
if "active_source" not in st.session_state:
    st.session_state.active_source = None

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

# --- Dialog to display the source ---
@st.dialog("Source Content")
def show_source_details(content, title):
    st.write(f"### {title}")
    st.write("---")
    st.write(content)
    if st.button("Close"):
        st.rerun()

# --- Check for active source ---
if st.session_state.active_source:
    source_data = st.session_state.active_source
    st.session_state.active_source = None 
    show_source_details(source_data["content"], source_data["title"])

# --- Helper to show source content
def handle_source_click(content, title):
    st.session_state.active_source = {"content": content, "title": title}

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
    for i, m in enumerate(st.session_state.messages):
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

            if m["role"] == "assistant" and "sources" in m and m["sources"]:
                srcs = m["sources"]
                cols = st.columns(len(srcs))
                for j, doc in enumerate(srcs):
                    source_name = doc.metadata.get("source", "Doc")
                    page = doc.metadata.get("page", "N/A")
                    title = f"{source_name} (P. {page})"
                    
                    with cols[j]:
                        st.button(title, key=f"btn_{i}_{j}", on_click=handle_source_click, args=(doc.page_content, title),use_container_width=True)

    if prompt := st.chat_input("Ask a question..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        try:
            llm = get_llm(provider, selected_model, api_key=api_key)

            if st.session_state.report is None:
                llm_name = getattr(llm, "model_name", llm.__class__.__name__)
                st.session_state.report = Report(llm_name)

            chain = create_rag_chain(st.session_state.vector_store, llm)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    ans, sources = answer_question(chain, prompt, id_document=st.session_state.get("id_document"), id_uploaded=st.session_state.get("id_uploaded", False), report=st.session_state.report)
                    st.markdown(ans)

                    if sources:
                        cols = st.columns(len(sources))
                        for k, doc in enumerate(sources):
                            title = f"{doc.metadata.get('source', 'Doc')} (P. {doc.metadata.get('page', 'N/A')})"
                            with cols[k]:
                                st.button(title, key=f"btn_new_{k}", on_click=handle_source_click, args=(doc.page_content, title), use_container_width=True)

            st.session_state.messages.append({
                "role": "assistant", 
                "content": ans, 
                "sources": sources
            })
        except Exception as e:
            st.error(f"An error occurred: {e}")
else:
    st.info("Please build the index to start chatting.")
