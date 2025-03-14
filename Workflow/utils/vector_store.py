import os
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pandas as pd

from Workflow.utils.config import Config



config = Config()
embeddings = config.embeddings


def create_and_save_faiss(file_path: str, save_path: str = "faiss_index/") -> None:
    """
    Create a FAISS database from a local CSV file and save it locally.

    Args:
        file_path (str): Path to the CSV file.
        save_path (str): Directory where the FAISS index will be saved.
    """

    # Load the CSV file
    df = pd.read_csv(file_path)

    # Ensure required columns exist
    required_columns = {"q_type", "question", "answer"}
    if not required_columns.issubset(df.columns):
        missing_cols = required_columns - set(df.columns)
        raise ValueError(f"Missing columns in CSV file: {missing_cols}")

    # Drop rows with missing question or answer
    df = df.dropna(subset=["question", "answer"])

    # Convert each row to a formatted string
    df["combined_text"] = df.apply(lambda row: f"{str(row['q_type'])}: {str(row['question'])} - {str(row['answer'])}", axis=1)

    # Create LangChain Documents
    documents = [Document(page_content=text, metadata={"source": file_path}) for text in df["combined_text"].tolist()]

    # Split documents into smaller chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=100)
    docs = text_splitter.split_documents(documents)

    # Create FAISS vector store
    db = FAISS.from_documents(docs, embeddings)

    # Ensure save directory exists
    os.makedirs(save_path, exist_ok=True)

    # Save FAISS locally
    db.save_local(save_path)
    print(f"FAISS database saved to: {save_path}")



# file_path = os.path.join("Data Prepration", "data_preprocessed.csv")

# if os.path.exists(file_path):
#     create_and_save_faiss(file_path)
#     print("FAISS database created and saved successfully.")
# else:
#     print("❌ File NOT found! Check folder names and path.")



def load_faiss_index(directory: str):
    """
    Load a FAISS index from the specified directory and filename.

    Parameters:
    - directory (str): The directory where the FAISS index is stored.
    - filename (str): The FAISS index filename.

    Returns:
    - faiss.Index: The loaded FAISS index.
    - None: If the file does not exist.
    """

    # Load FAISS retriever using LangChain's method
    try:
        faiss_index = FAISS.load_local(directory, embeddings, allow_dangerous_deserialization=True)
        print("✅ FAISS index loaded successfully.")
        return faiss_index
    except Exception as e:
        print(f"❌ Failed to load FAISS index. Error: {e}")
        return None


# from langchain.chains import RetrievalQA

# retriever = load_faiss_index()

# MODEL_NAME = "gemini-2.0-flash-001"
# llm = ChatGoogleGenerativeAI(model=f"models/{MODEL_NAME}", google_api_key=google_api_key)
# retrievalQA = RetrievalQA.from_llm(llm=llm, retriever=retriever)

# response = retrievalQA.run("How to diagnose Parasites - Cysticercosis ?")
# print(response)



def create_db_from_local_pdf(file_path: str) -> FAISS:
    """
    Create a FAISS database from a locally stored PDF file.

    Args:
        file_path (str): Path to the local PDF file.

    Returns:
        FAISS: A FAISS vector store database built from the PDF's content.
    """
    # Load the document from the local file
    loader = PyPDFLoader(file_path)
    documents = loader.load()

    # Split the documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = text_splitter.split_documents(documents)

    # Create the FAISS vector store
    db = FAISS.from_documents(docs, embeddings)

    db.save_local("system_flow")

# create_db_from_local_pdf("Data Prepration\Mobile Application Design Documentation.pdf")