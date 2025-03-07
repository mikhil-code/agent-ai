from docx import Document
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter

def process_docx(file):
    doc = Document(file)
    text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    return split_text(text)

def process_pdf(file):
    pdf_reader = PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return split_text(text)

def split_text(text):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    return text_splitter.split_text(text)

def process_document(file):
    file_name = file.name.lower()
    if file_name.endswith('.pdf'):
        return process_pdf(file)
    elif file_name.endswith('.docx'):
        return process_docx(file)
    else:
        raise ValueError("Unsupported file format. Please upload PDF or DOCX files only.")
