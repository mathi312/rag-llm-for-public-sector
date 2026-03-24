import pytest
from unittest.mock import MagicMock, patch
from chat import needs_id_prompt, create_rag_chain, answer_question, sources_require_id


@patch("chat.create_stuff_documents_chain")
def test_create_rag_chain(mock_create_stuff_documents_chain):
    """Test creation of the rag chain"""
    mock_vector_store = MagicMock()
    mock_llm = MagicMock()
    mock_retriever = MagicMock()
    mock_chain = MagicMock()
    
    mock_vector_store.as_retriever.return_value = mock_retriever
    mock_create_stuff_documents_chain.return_value = mock_chain
    
    retriever, chain = create_rag_chain(mock_vector_store, mock_llm)
    
    mock_vector_store.as_retriever.assert_called_once_with(
        search_type="mmr",
        search_kwargs={"k": 6, "fetch_k": 24, "lambda_mult": 0.25}
    )
    mock_create_stuff_documents_chain.assert_called_once()

    assert retriever is mock_retriever
    assert chain is mock_chain

class TestAnswerQuestion:
    """Test for answering questions"""
    
    @pytest.fixture
    def mock_rag_chain(self):
        """This method creates a mock for the rag chain"""
        retriever = MagicMock()
        retriever.invoke.return_value = ["Source 1", "Source 2"]
        chain = MagicMock()
        chain.invoke.return_value = {
            "answer": "Dies ist die Antwort.",
            "context": ["Source 1", "Source 2"]
        }
        return retriever, chain

    @pytest.fixture
    def mock_report(self):
        """This method creates a mock for the report"""
        return MagicMock()

    def test_basic_answer_flow(self, mock_rag_chain):
        """Test basic question and answer functionality"""
        answer, sources = answer_question(mock_rag_chain, "Was ist das?")
        
        assert answer == "Dies ist die Antwort."
        assert len(sources) == 2

        _, chain = mock_rag_chain

        chain.invoke.assert_called_with({"input": "Was ist das?", "context": sources})

    def test_with_id_uploaded(self, mock_rag_chain):
        """Test addition of a passport to the question"""
        passport = {"type": "Passport", "data": "Max Mustermann"}
        answer_question(mock_rag_chain, "Wer bin ich?", id_document=passport, id_uploaded=True)

        _, chain = mock_rag_chain
        
        called_args = chain.invoke.call_args[0][0]
        assert "[Citizen ID provided]" in called_args["input"]
        assert "Passport" in called_args["input"]

    def test_trigger_id_prompt_concatenation(self, mock_rag_chain):
        """Test addition of the id prompt to the answer"""
        answer, _ = answer_question(mock_rag_chain, "Was ist eine Bescheinigung", id_uploaded=False)
        
        assert "Zur weiteren Bearbeitung benötige ich eine Ausweisbestätigung" in answer
        assert "(Derzeit kein Ausweis hochgeladen)" in answer

    def test_report_logging(self, mock_rag_chain, mock_report):
        """Test that question is added to the report"""
        question = "Testfrage"
        answer_question(mock_rag_chain, question, report=mock_report)
        
        mock_report.add_entry.assert_called_once_with(question, "Dies ist die Antwort.")


class TestSourcesRequireId:
    """Tests for the method sources_require_id"""

    def make_doc(self, needed_id=None):
        doc = MagicMock()
        doc.metadata = {"needed_id": needed_id} if needed_id is not None else {}
        return doc

    def test_empty_sources_returns_false_and_empty_list(self):
        assert sources_require_id([]) == (False, [])

    def test_none_sources_returns_false_and_empty_list(self):
        assert sources_require_id(None) == (False, [])

    def test_single_doc_with_one_id_type(self):
        doc = self.make_doc(needed_id=["passport"])
        result = sources_require_id([doc])
        assert result == (True, ["passport"])

    def test_single_doc_with_multiple_id_types(self):
        doc = self.make_doc(needed_id=["passport", "driver_license"])
        result = sources_require_id([doc])
        assert result == (True, ["driver_license", "passport"])

    def test_multiple_docs_with_overlapping_ids_deduplicates(self):
        doc1 = self.make_doc(needed_id=["passport"])
        doc2 = self.make_doc(needed_id=["passport", "id_card"])
        result = sources_require_id([doc1, doc2])
        assert result == (True, ["id_card", "passport"])

    def test_doc_with_no_needed_id_key(self):
        doc = self.make_doc()  # metadata exists but no 'needed_id' key
        assert sources_require_id([doc]) == (False, [])

    def test_doc_with_none_needed_id(self):
        doc = self.make_doc(needed_id=None)
        assert sources_require_id([doc]) == (False, [])

    def test_doc_with_empty_needed_id_list(self):
        doc = self.make_doc(needed_id=[])
        assert sources_require_id([doc]) == (False, [])

    def test_doc_without_metadata_attribute(self):
        doc = object()
        assert sources_require_id([doc]) == (False, [])

    def test_bool_flag_is_true_when_ids_present(self):
        doc = self.make_doc(needed_id=["passport"])
        required, _ = sources_require_id([doc])
        assert required is True

    def test_bool_flag_is_false_when_no_ids(self):
        doc = self.make_doc(needed_id=[])
        required, _ = sources_require_id([doc])
        assert required is False


class TestNeedsIdPrompt:

    def make_doc(self, needed_id=None):
        doc = MagicMock()
        doc.metadata = {"needed_id": needed_id} if needed_id is not None else {}
        return doc

    @pytest.mark.parametrize("question, id_uploaded, expected", [
        ("Was ist ein Führungszeugnis?", False, True),
        ("Ich brauche eine Bescheinigung.", False, True),
        ("Text ohne Keywords.", False, False),
        ("Was ist ein Führungszeugnis?", True, False),
    ])
    def test_needs_id_prompt_keywords(self, question, id_uploaded, expected):
        """Test keyword-based detection without sources."""
        assert needs_id_prompt(question, id_uploaded) == expected

    def test_needs_id_prompt_id_already_uploaded_return_false(self):
        doc = self.make_doc(needed_id=["passport"])
        assert needs_id_prompt("Führungszeugnis", id_uploaded=True, sources=[doc]) is False

    def test_needs_id_prompt_sources_require_id_returns_true(self):
        doc = self.make_doc(needed_id=["passport"])
        assert needs_id_prompt("Text ohne Keywords.", id_uploaded=False, sources=[doc]) is True

    def test_needs_id_prompt_sources_require_id_overrides_no_keyword_match(self):
        doc = self.make_doc(needed_id=["id_card"])
        assert needs_id_prompt("Wie ist das Wetter?", id_uploaded=False, sources=[doc]) is True

    def test_needs_id_prompt_sources_no_id_required_falls_back_to_keyword_true(self):
        doc = self.make_doc(needed_id=[])
        assert needs_id_prompt("Führungszeugnis", id_uploaded=False, sources=[doc]) is True

    def test_needs_id_prompt_sources_no_id_required_falls_back_to_keyword_false(self):
        doc = self.make_doc(needed_id=[])
        assert needs_id_prompt("Text ohne Keywords.", id_uploaded=False, sources=[doc]) is False
