from PyPDF2 import PdfReader
from io import BytesIO
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI
from typing_extensions import Concatenate

def process_pdf_and_answer_questions(pdf_file_content, user_prompt, openai_api_key):
    # Wrap the bytes content in a BytesIO object
    pdf_stream = BytesIO(pdf_file_content)

    # Read text from PDF
    raw_text = ''
    pdfreader = PdfReader(pdf_stream)
    for i, page in enumerate(pdfreader.pages):
        content = page.extract_text()
        if content:
            raw_text += content

    # Split the text using Character Text Splitter
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=800,
        chunk_overlap=200,
        length_function=len,
    )
    texts = text_splitter.split_text(raw_text)

    # Download embeddings from OpenAI
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

    document_search = FAISS.from_texts(texts, embeddings)

    # Load the QA chain
    chain = load_qa_chain(OpenAI(openai_api_key=openai_api_key), chain_type="stuff")

    # Execute the QA chain
    docs = document_search.similarity_search(user_prompt)
    result = chain.run(input_documents=docs, question=user_prompt)

    return result
