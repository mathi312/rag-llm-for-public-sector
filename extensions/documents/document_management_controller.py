from __future__ import annotations


class DocumentManagementController:
    """Orchestrates document management actions for the Streamlit page."""

    def __init__(
        self,
        streamlit_module,
        generate_questions_fn,
        show_questions_dialog_fn,
        view_pdf_dialog_fn,
        update_document_fn,
        confirm_delete_document_fn,
    ) -> None:
        self._st = streamlit_module
        self._generate_questions = generate_questions_fn
        self._show_questions_dialog = show_questions_dialog_fn
        self._view_pdf_dialog = view_pdf_dialog_fn
        self._update_document = update_document_fn
        self._confirm_delete_document = confirm_delete_document_fn

    @staticmethod
    def get_next_version(raw_version) -> str:
        try:
            return str(int(raw_version) + 1)
        except (TypeError, ValueError):
            return str(raw_version or "1")

    def handle_generate_questions(self, doc: dict) -> None:
        questions = self._generate_questions(
            document_name=doc.get("original_name"),
            provider=self._st.session_state.provider,
            model_name=self._st.session_state.selected_model,
        )

        print(questions)

        if questions:
            self._show_questions_dialog(questions)
            return
        self._st.error(
            f"Could not generate questions for **{doc.get('original_name')}**. Please try again later."
        )

    def handle_view(self, doc: dict) -> None:
        self._view_pdf_dialog(
            document_name=doc.get("document"),
            original_name=doc.get("original_name"),
        )

    def handle_edit(self, doc: dict) -> None:
        self._update_document(
            record_id=doc["id"],
            title=doc.get("title"),
            version=self.get_next_version(doc.get("version")),
            needed_id=doc.get("needed_id"),
            original_name=doc.get("original_name"),
            document_name=doc.get("document"),
            current_version=doc.get("version"),
        )

    def handle_delete(self, doc: dict) -> None:
        if self._confirm_delete_document(
            record_id=doc["id"],
            document_name=doc.get("document"),
            original_name=doc.get("original_name"),
        ):
            self._st.success("Dokument gelöscht.")
            self._st.rerun()
