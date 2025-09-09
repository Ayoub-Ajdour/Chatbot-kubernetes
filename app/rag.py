from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from spellchecker import SpellChecker
import logging
import os

# Configure logging to track application events
logging.basicConfig(
    filename="logs/chatbot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Initialize the embeddings model for semantic search
#embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
# Initialize spell checker to correct user typos
spell = SpellChecker()

# Declare vector store and set directory paths
vector_store = None
DOCS_DIR = "docs/"
PERSIST_DIR = "chroma_db"

# Function to correct spelling mistakes in the input query
def correct_typos(query):
    words = query.split()
    corrected = [spell.correction(word) if spell.correction(word) else word for word in words]
    corrected_query = " ".join(corrected)
    return corrected_query

# Function to load documents, split them, and create the vector store
def initialize_vector_store():
    global vector_store
    try:
        if not os.path.exists(DOCS_DIR):
            os.makedirs(DOCS_DIR)
            vector_store = Chroma.from_texts(["placeholder"], embeddings, persist_directory=PERSIST_DIR)
            return

        loader = DirectoryLoader(DOCS_DIR, glob="*.txt", loader_cls=TextLoader, show_progress=True)
        documents = loader.load()

        if not documents:
            vector_store = Chroma.from_texts(["placeholder"], embeddings, persist_directory=PERSIST_DIR)
            return

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(documents)

        vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=PERSIST_DIR
        )
    except Exception as e:
        logging.error(f"Failed to initialize vector store: {str(e)}")
        vector_store = None

# Function to retrieve the most relevant context based on a user query
def retrieve_context(query, k=3):
    if vector_store is None:
        return "Error: Vector store not initialized."

    try:
        corrected_query = correct_typos(query)
        docs = vector_store.similarity_search(corrected_query, k=k)
        context = "\n".join([doc.page_content for doc in docs])
        return context
    except Exception as e:
        logging.error(f"Retrieval error: {str(e)}")
        return "Error: Could not retrieve context."

# Function to retrieve specific command examples related to the query
def retrieve_command_context(query, k=2):
    if vector_store is None:
        return ""

    try:
        corrected_query = correct_typos(query)
        docs = vector_store.similarity_search(corrected_query, k=k)
        command_docs = [doc for doc in docs if doc.metadata.get("source", "").endswith("k8s_commands.txt")]
        context = "\n".join([doc.page_content for doc in command_docs])
        return context
    except Exception as e:
        logging.error(f"Command retrieval error: {str(e)}")
        return ""

# Initialize the vector store when the module is loaded
initialize_vector_store()
