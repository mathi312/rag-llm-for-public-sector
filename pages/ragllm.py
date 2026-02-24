"""Streamlit-based user interface for the RAG document assistant.

This module provides the web interface for uploading documents, building
or loading vector indexes, and interacting with the document corpus via
natural language queries.
"""

import streamlit as st
from pathlib import Path

from loaders import load_files_to_documents, load_directory_documents, load_urls_as_documents, split_documents
from models import get_embeddings, get_llm
from indexing import load_index, build_index_from_documents
from chat import create_rag_chain, answer_question

import time

from extensions.report_generator import *
from extensions.report import Report
from extensions.idprovider import *
from extensions.pocketbase import *
from extensions.user import User
from extensions.documentupload import upload_document

#Questions suggestions für Bubbles
SUGGESTED_QUESTIONS = [
    "Welche Dateien sind bereits indexiert?",
    "Erkläre mir die Beziehung zwischen Blutdruck und Blutfluss",
    "Wie wechsle ich von Ollama zu OpenAI?",
    "Baue den Index neu auf.",
    "Welche Modelle sind verfügbar?"
]

if "hide_suggestions" not in st.session_state:
    st.session_state.hide_suggestions = False

def render_suggestions():
    if st.session_state.hide_suggestions:
        return
    st.markdown("#### How can I help you today?")
    cols = st.columns(3)
    for i, q in enumerate(SUGGESTED_QUESTIONS):
        with cols[i % 3]:
            if st.button(q, key=f"suggest-{i}"):
                st.session_state["prefill"] = q
                st.session_state["auto_send"] = True
                st.session_state.hide_suggestions = True  # sofort ausblenden


# Define the static data directory (mounted via Docker)
DATA_DIR = Path(__file__).parent.parent / "data"

st.set_page_config(page_title="Digital Assistant - RAG-LLM", layout="wide")
st.title("🤖 Digital Assistant - RAG-LLM (Hybrid)")

# -- DEFAULT VALUES --
provider = "Local (Ollama)"
api_key = None
selected_model = "llama3.2"
embedding_model_name = selected_model
include_static = False
uploaded_files = None
static_files = []
build_mode = "Use existing index"
process_btn = False

# --- SESSION STATE ---
if "provider" not in st.session_state:
    st.session_state.provider = provider
if "selected_model" not in st.session_state:
    st.session_state.selected_model = selected_model
if "embedding_model_name" not in st.session_state:
    st.session_state.embedding_model_name = embedding_model_name
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
if "user" not in st.session_state:
    st.session_state.user = get_user_from_auth_store()
if "urls" not in st.session_state:
    st.session_state.urls = []
if "url_input" not in st.session_state:
    st.session_state.url_input = ""

# callback to add url to the urls in the sidebar
def add_url():
    url = st.session_state.url_input.strip()
    if url and url not in st.session_state.urls:
        st.session_state.urls.append(url)
    st.session_state.url_input = ""

# helper to handle the upload of an id
def handle_id_upload(id_image, id_type: IdType | None = None):
    # rewind to start of file, needed when trying to process the image a second time
    id_image.seek(0)

    extracted_data = process_id_document(
        id_image.read(),
        id_type=id_type
    )
    st.session_state["id_uploaded"] = True

    st.session_state["id_document"] = {
        "type": extracted_data.get("id_type").value,
        "data": extracted_data,
    }

# Dialog for manually selecting id type after ocr failed to get the id type from the uploaded id
@st.dialog("Manually select your id type")
def select_id_type_dialog(id_image, exception: str):
    st.error(exception)
    st.write("Please manually select the ID type you provided.")

    selected_id_type = st.selectbox(
        "Select Citizen ID",
        options=list(IdType),
        index=0,
        format_func=lambda x: x.value
    )

    if st.button("Process ID Document Again"):
        try:
            handle_id_upload(id_image, selected_id_type)

            st.success("ID Document successfully processed!")
        except Exception as exc:
            st.error(f"OCR processing failed: {exc}")

# --- SIDEBAR UI ---
with st.sidebar:
    st.header("Current User")
    show_logged_in_status()

    st.divider()

    tab_labels = ["General"]
    is_admin = is_authenticated() and user_is_admin()
    if is_admin:
        tab_labels.append("Administration")

    tabs = st.tabs(tab_labels)

    if is_admin:
        admin_tab = tabs[1]
        with admin_tab:
            st.header("1. AI Provider Configuration")

            provider = st.radio(
                "Select Provider",
                ["Local (Ollama)", "OpenAI"],
                index=0 if st.session_state.provider == "Local (Ollama)" else 1
            )

            api_key = None
            selected_model = ""

            if provider == "OpenAI":
                api_key = st.text_input("OpenAI API Key", type="password")
                openai_models = ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]
                selected_model = st.selectbox(
                    "Select OpenAI Model",
                    openai_models,
                    index=openai_models.index(st.session_state.selected_model)
                    if st.session_state.selected_model in openai_models else 1,
                )
                # We hardcode the embedding model for OpenAI to be consistent
                embedding_model_name = "text-embedding-3-small"
            else:
                local_models = ["llama3.2", "llama3", "mistral"]
                selected_model = st.selectbox(
                    "Select Local Model",
                    local_models,
                    index=local_models.index(st.session_state.selected_model)
                    if st.session_state.selected_model in local_models else 0,
                )
                embedding_model_name = selected_model

            st.session_state.provider = provider
            st.session_state.selected_model = selected_model
            st.session_state.embedding_model_name = embedding_model_name

            st.divider()

            st.header("2. Data Sources")

            # Static Files Check
            static_files = []
            if DATA_DIR.exists():
                static_files = [
                    f
                    for f in DATA_DIR.iterdir()
                    if f.suffix.lower() in [".pdf", ".docx"]
                ]

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
                accept_multiple_files=True,
            )

            # Enter a URL from which to load the html content
            st.text_input(
                "Enter URL from which to load content:",
                key="url_input",
                on_change=add_url,
            )

            # Display all entered URLs
            if st.session_state.urls:
                st.markdown("Added URLs")
                for u in st.session_state.urls:
                    st.write(u)

            st.divider()

            build_mode = st.radio(
                "Index mode", ["Use existing index", "Rebuild index"], index=0
            )

            process_btn = st.button("Build / Update Index")


    user_tab = tabs[0]
    with user_tab:
        # Citizen ID Upload Section
        st.header("Citizen ID Upload")

        id_image = st.file_uploader("Upload ID image", type=["png", "jpg", "jpeg"]) # Upload ID image

        upload_citizen_file = st.button("Upload Citizen ID Document")

        if upload_citizen_file:
            if not id_image:
                st.warning("Please upload an image of your ID before proceeding.")
            else:
                try:
                    handle_id_upload(id_image)

                    msg = st.empty()
                    msg.success(f"{st.session_state.get("id_document").get("type")} document uploaded successfully!")
                    time.sleep(2)
                    msg.empty()

                    st.success("ID Document successfully processed!")
                except ValueError as exc:
                    select_id_type_dialog(id_image, exc)
                except Exception as exc:
                    st.error(f"OCR processing failed: {exc}")

        st.divider()

        print_report_btn = st.button("Print Report")


# Dialog for entering a email address
@st.dialog("Enter your email address")
def email_dialog(exception: str):
    st.error(exception)
    st.write("Please provide your email to receive the report.")
    email = st.text_input("Email")

    if st.button("Send email"):
        try:
            send_report_via_email(st.session_state.report, email, st.session_state.user)
            st.success("Email sent successfully.")
        except (EmptyReportError, EmptyEmailAddressError) as e:
            st.warning(str(e))
        except Exception as e:
            st.exception(e)

if print_report_btn:
    try:
        print_report(st.session_state.report, st.session_state.user)

        st.success("Report printed successfully.")
    except EmptyReportError as e:
        st.sidebar.warning(str(e))
    except PrinterBrokenError as e:
        email_dialog(str(e))
    except Exception as e:
        st.sidebar.exception(e)

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
        
        # Load Html content from urls
        if st.session_state.urls:
            status_msg.info("Loading content form URLs...")
            url_docs = load_urls_as_documents(st.session_state.urls)
            all_docs.extend(url_docs)

        if not all_docs:
            st.sidebar.warning("No documents found.")
        else:
            status_msg.info(f"Processing {len(all_docs)} documents...")
            splits = split_documents(all_docs)

            status_msg.info("Building vector index...")
            # Batch size 5 is safe for local; OpenAI can handle larger but 5 is fine for both
            st.session_state.vector_store = build_index_from_documents(
                splits, embeddings, batch_size=5
            )

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
                        st.button(
                            title,
                            key=f"btn_{i}_{j}",
                            on_click=handle_source_click,
                            args=(doc.page_content, title),
                            use_container_width=True,
                        )

    render_suggestions()
    auto_send = st.session_state.pop("auto_send", False)
    prefill = st.session_state.pop("prefill", "")
    user_input = st.chat_input("Frage stellen …")  # bleibt immer sichtbar
    user_msg = prefill if auto_send else user_input

    if auto_send or user_msg:
        st.session_state.hide_suggestions = True

        prompt = user_msg
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
                    ans, sources = answer_question(
                        chain,
                        prompt,
                        id_document=st.session_state.get("id_document"),
                        id_uploaded=st.session_state.get("id_uploaded", False),
                        report=st.session_state.report,
                    )
                    st.markdown(ans)

                    if sources:
                        cols = st.columns(len(sources))
                        for k, doc in enumerate(sources):
                            title = f"{doc.metadata.get('source', 'Doc')} (P. {doc.metadata.get('page', 'N/A')})"
                            with cols[k]:
                                st.button(
                                    title,
                                    key=f"btn_new_{k}",
                                    on_click=handle_source_click,
                                    args=(doc.page_content, title),
                                    use_container_width=True,
                                )

            st.session_state.messages.append(
                {"role": "assistant", "content": ans, "sources": sources}
            )

        except Exception as e:
            st.error(f"An error occurred: {e}")
else:
    st.info("Please build the index to start chatting.")
