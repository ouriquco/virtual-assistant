import nest_asyncio
from llama_parse import LlamaParse
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import os

nest_asyncio.apply()

def get_files():
    relative_path = "web_data"
    current_working_directory = os.getcwd()
    directory = os.path.join(current_working_directory, relative_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    files = [os.path.join(directory, file) for file in os.listdir(directory)]
    return files

def load_parser():
    parser = LlamaParse(
    api_key=os.environ.get('LLAMA_PARSE_API_KEY'),
    result_type = "text",
    verbose=True,
    language = "en"
    )
    return parser

def get_chunks(files, parser):
    documents = [parser.load_data(file_path=file) for file in files]
    partitions = []

    for doc in documents:
        for i, data in enumerate(doc):
            d = Document(page_content=data.text, metadata={"source": f"data_{i}"})
            partitions.append(d)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=100,  
        separators=["\n\n", "\n", " ", ""], 
    )

    chunks = text_splitter.split_documents(partitions)
    return chunks

def get_vectorstore():
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    persist_directory = "./vectorstore"

    try:
        vectorstore = Chroma(
            persist_directory=persist_directory,
            collection_name="document_chunks",
            embedding_function=embedding_model
        )
    except ValueError:
        vectorstore.reset() 

    return vectorstore

def add_documents_to_vectorstore(vectorstore, chunks):
    vectorstore.add_documents(chunks, ids=[f"chunk_{i}" for i in range(len(chunks))])

def get_retriever():
    try:
        vectorstore = Chroma(
            persist_directory="./vectorstore",
            collection_name="document_chunks"
        )
    except ValueError:
        print("Vector store not found. Please create it first.")
        return None
    
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    return retriever

def run_vectorstore():
    files = get_files()
    parser = load_parser()
    chunks = get_chunks(files, parser)
    vectorstore = get_vectorstore()
    add_documents_to_vectorstore(vectorstore, chunks)


