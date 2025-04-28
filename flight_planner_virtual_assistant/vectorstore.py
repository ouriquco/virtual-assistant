import nest_asyncio
from llama_parse import LlamaParse
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import os

def get_files(relative_path):
    rp = relative_path
    current_working_directory = os.getcwd()
    directory = os.path.join(current_working_directory, rp)
    if not os.path.exists(directory):
        raise ValueError(f"Directory {directory} does not exist.")
    
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
        chunk_overlap=200,  
        separators=["\n\n", "\n", " ", ""], 
    )

    chunks = text_splitter.split_documents(partitions)
    return chunks

def get_vectorstore(collection_name=None):
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    persist_directory = "./vectorstore"

    try:
        vectorstore = Chroma(
            persist_directory=persist_directory,
            collection_name=collection_name,
            embedding_function=embedding_model
        )
    except ValueError:
        vectorstore.reset() 

    return vectorstore

def add_flights_to_vectorstore(vectorstore, offers):
    documents = [Document(page_content=offer) for offer in offers]
    ids = [f"flight_{i}" for i in range(len(offers))]
    vectorstore.add_documents(documents, ids=ids)

def add_web_search_to_vectorstore(vectorstore, documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""]
    )

    langchain_docs = [Document(page_content=doc['content'], metadata={"source": doc['url'], "title": doc['title']}) for doc in documents]
    splits = text_splitter.split_documents(langchain_docs)
    
    vectorstore.add_documents(splits)

def run_vectorstore(relative_path=None, collection_name=None):
    files = get_files(relative_path)
    parser = load_parser()
    chunks = get_chunks(files, parser)
    vectorstore = get_vectorstore(collection_name)
    add_web_search_to_vectorstore(vectorstore, chunks)


