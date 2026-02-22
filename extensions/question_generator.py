from pathlib import Path
from documentupload import extract_text_from_file
from langchain.prompts import PromptTemplate

def generate_example_questions(document_name: str | None = None):
    data_dir = Path(__file__).resolve().parent.parent / "data"
    file_path = data_dir / document_name

    text = extract_text_from_file(file_path)

    prompt_template = PromptTemplate(
        input_variables=["text"],
        template=(
            "You are a helpful assistant.  "
            "Given the following document content, come up with five concise, "
            "varied example questions a user might ask about it.  "
            "Return each question on its own line.\n\n"
            "Document:\n{text}"
        ),
    )

    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.5)
    chain = LLMChain(llm=llm, prompt=prompt_template)
    output = chain.run(text=text)

    # optionally split into a list of questions
    return [q.strip() for q in output.strip().splitlines() if q.strip()]
