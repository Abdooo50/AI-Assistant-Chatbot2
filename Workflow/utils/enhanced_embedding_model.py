"""
Enhanced Embedding Model Implementation for Medical Assistant

This module provides an improved embedding model implementation using the latest
Gemini embedding models for better semantic search and retrieval in medical contexts.
"""

import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

class EnhancedEmbeddings:
    """
    Enhanced embeddings class that provides access to the latest Google AI embedding models
    with optimized configurations for medical domain applications.
    """
    
    def __init__(self, model_name=None):
        """
        Initialize the enhanced embeddings with the specified model.
        
        Args:
            model_name (str, optional): The embedding model to use. 
                Defaults to the latest Gemini embedding model if not specified.
        """
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        
        if not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY is not set in environment variables")
        
        # Use the latest Gemini embedding model if not specified
        self.model_name = model_name or "models/gemini-embedding-exp-03-07"
        
        # Initialize the embedding model
        self.embeddings = self._initialize_embeddings()
    
    def _initialize_embeddings(self):
        """
        Initialize the embedding model with optimized parameters.
        
        Returns:
            GoogleGenerativeAIEmbeddings: Configured embedding model instance
        """
        return GoogleGenerativeAIEmbeddings(
            model=self.model_name,
            google_api_key=self.google_api_key,
            task_type="RETRIEVAL_DOCUMENT",  # Optimize for document retrieval
            title="Medical Information Retrieval",  # Provide context about the domain
            dimensions=1024  # Use higher dimensions for better representation
        )
    
    def get_embeddings(self):
        """
        Get the configured embedding model.
        
        Returns:
            GoogleGenerativeAIEmbeddings: The embedding model instance
        """
        return self.embeddings
    
    def embed_query(self, text):
        """
        Generate embeddings for a query text.
        
        Args:
            text (str): The query text to embed
            
        Returns:
            list: The embedding vector
        """
        return self.embeddings.embed_query(text)
    
    def embed_documents(self, documents):
        """
        Generate embeddings for a list of documents.
        
        Args:
            documents (list): List of document texts to embed
            
        Returns:
            list: List of embedding vectors
        """
        return self.embeddings.embed_documents(documents)


def get_enhanced_embeddings(model_name=None):
    """
    Factory function to get enhanced embeddings instance.
    
    Args:
        model_name (str, optional): The embedding model to use.
            Defaults to the latest Gemini embedding model if not specified.
            
    Returns:
        GoogleGenerativeAIEmbeddings: Configured embedding model instance
    """
    embeddings_instance = EnhancedEmbeddings(model_name)
    return embeddings_instance.get_embeddings()


# Available embedding models with descriptions
AVAILABLE_MODELS = {
    "models/gemini-embedding-exp-03-07": {
        "description": "Latest Gemini embedding model with superior performance",
        "dimensions": 1024,
        "recommended_for": ["medical_retrieval", "system_flow_qa", "general_purpose"]
    },
    "models/text-embedding-large-exp-03-07": {
        "description": "Large embedding model designed for highest quality embeddings",
        "dimensions": 1536,
        "recommended_for": ["complex_medical_queries", "detailed_system_documentation"]
    },
    "models/text-embedding-004": {
        "description": "Previous generation embedding model (current implementation)",
        "dimensions": 768,
        "recommended_for": ["basic_retrieval", "compatibility"]
    }
}
