from __future__ import annotations

from copy import deepcopy


DEFAULT_SESSION_STATE = {
    "provider": "Local (Ollama)",
    "selected_model": "llama3.2",
    "embedding_model_name": "llama3.2",
    "vector_store": None,
    "messages": [],
    "id_uploaded": False,
    "id_document": None,
    "report": None,
    "active_source": None,
    "urls": [],
    "url_input": "",
}


def initialize_app_session(streamlit_module) -> None:
    """Populate shared Streamlit session defaults for all pages."""
    for key, default_value in DEFAULT_SESSION_STATE.items():
        if key not in streamlit_module.session_state:
            # Copy mutable defaults so each browser session gets isolated state.
            streamlit_module.session_state[key] = deepcopy(default_value)


def reset_chat_context(streamlit_module) -> None:
    """Clear the current chat conversation while keeping the loaded index."""
    streamlit_module.session_state["messages"] = []
    streamlit_module.session_state["report"] = None
    streamlit_module.session_state["active_source"] = None

    # Remove pending suggestion state so the new chat starts empty.
    streamlit_module.session_state.pop("prefill", None)
    streamlit_module.session_state.pop("auto_send", None)
