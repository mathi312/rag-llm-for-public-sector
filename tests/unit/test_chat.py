import pytest
from unittest.mock import MagicMock, patch
from chat import needs_id_prompt, create_rag_chain, answer_question

@pytest.mark.parametrize("question, id_uploaded, expected", [
    ("Was ist ein Führungszeugnis?", False, True),
    ("Ich brauche eine Bescheinigung.", False, True),
    ("Text ohne Keywords.", False, False),
    ("Was ist ein Führungszeugnis?", True, False),
])
def test_needs_id_prompt(question, id_uploaded, expected):
    """Test if the id prompt should be displayed"""
    assert needs_id_prompt(question, id_uploaded) == expected

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
        search_type="similarity_score_threshold",
        search_kwargs={"k": 6, "score_threshold": 0.3}
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
