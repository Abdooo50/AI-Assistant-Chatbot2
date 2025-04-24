"""
PDF Embeddings Generator for Medical Assistant

This script specifically processes PDF files and generates embeddings using the enhanced Gemini embedding model.
It's designed to save embeddings directly to the system_flow directory in the project root.
"""

import os
import sys
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Add the parent directory to sys.path to allow imports from Workflow
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from Workflow.utils.config import Config

# Load environment variables
load_dotenv()

# Initialize config with enhanced embedding model
config = Config()

def generate_pdf_embeddings(pdf_path=None):
    """
    Generate embeddings for a specific PDF file or all PDFs in the data directory.
    
    Args:
        pdf_path: Optional path to a specific PDF file. If None, will look for PDFs in the data directory.
    """
    print("Starting PDF embeddings generation process...")
    
    # Define paths relative to the project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Define the system_flow directory in the project root for saving the index
    system_flow_dir = os.path.join(project_root, "system_flow")
    if not os.path.exists(system_flow_dir):
        print(f"Creating system_flow directory at {system_flow_dir}")
        os.makedirs(system_flow_dir, exist_ok=True)
    
    # Check for Data Preparation directory (with both possible spellings)
    data_dir = os.path.join(project_root, "Data Prepration")
    if not os.path.exists(data_dir):
        data_dir = os.path.join(project_root, "Data Preparation")  # Alternative spelling
    
    if not os.path.exists(data_dir):
        print(f"Warning: Data directory not found at either 'Data Prepration' or 'Data Preparation'")
        print(f"Will look for PDF files in the project root directory")
        data_dir = project_root
    
    # If specific PDF path is provided, use it; otherwise look for Mobile Application Design Documentation.pdf
    if pdf_path is None:
        pdf_path = os.path.join(data_dir, "Mobile Application Design Documentation.pdf")
        if not os.path.exists(pdf_path):
            # Look for any PDF files in the data directory
            pdf_files = [f for f in os.listdir(data_dir) if f.lower().endswith('.pdf')]
            if pdf_files:
                pdf_path = os.path.join(data_dir, pdf_files[0])
                print(f"Using PDF file: {pdf_path}")
            else:
                print(f"Error: No PDF files found in {data_dir}")
                return
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return
    
    try:
        print(f"Loading PDF document: {pdf_path}")
        # Use PyPDFLoader to load the PDF file
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        
        if not documents:
            print("Error: No content extracted from the PDF file.")
            return
            
        print(f"Loaded {len(documents)} pages from the PDF.")
        
        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = text_splitter.split_documents(documents)
        
        print(f"Processing {len(chunks)} document chunks...")
        
        # Generate embeddings and create FAISS index
        print("Generating embeddings with enhanced Gemini model...")
        print(f"Using model: {config.EMBEDDING_MODEL_NAME}")
        print(f"Dimensions: {config.EMBEDDING_DIMENSIONS}")
        print(f"Task type: {config.EMBEDDING_TASK_TYPE}")
        
        vectorstore = FAISS.from_documents(
            documents=chunks,
            embedding=config.embeddings
        )
        
        # Save the new index to system_flow directory in the project root
        index_path = os.path.join(system_flow_dir, "index")
        vectorstore.save_local(index_path)
        
        print(f"PDF embeddings generation complete. New index saved to {index_path}")
        print(f"Full path: {os.path.abspath(index_path)}")
        print("You can now restart your application to use the enhanced embeddings.")
        
    except Exception as e:
        print(f"Error during PDF embeddings generation: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Check if a specific PDF path is provided as a command-line argument
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        generate_pdf_embeddings(pdf_path)
    else:
        # Use default path (will look for Mobile Application Design Documentation.pdf)
        generate_pdf_embeddings()
