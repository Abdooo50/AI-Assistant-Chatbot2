import os
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.utilities import SQLDatabase

from psycopg_pool import ConnectionPool # type: ignore


class Config:
    # Database configuration for MSSQL
    MSSQL_DATABASE_URI = "mssql+pyodbc://@ASUS/MosefakDB?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes"

    # Database configuration for PostgreSQL
    POSTGRES_DB_URI = "postgresql://postgres:12345@localhost:5432/postgres?sslmode=prefer"
    POSTGRES_CONNECTION_KWARGS = {
        "autocommit": True,
        "prepare_threshold": 0,
    }

    # Google Generative AI configuration
    MODEL_NAME = "gemini-2.0-flash-001"
    EMBEDDING_MODEL_NAME = "models/text-embedding-004"
    TEMPERATURE = 0

    def __init__(self):
        # Initialize PostgreSQL connection pool
        self.pool = ConnectionPool(
            conninfo=self.POSTGRES_DB_URI,
            max_size=20,
            kwargs=self.POSTGRES_CONNECTION_KWARGS
        )

    @staticmethod
    def get_google_api_key():
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is not set. Please set it as an environment variable.")
        
        return GOOGLE_API_KEY

    @property
    def llm(self):
        return ChatGoogleGenerativeAI(
            model=f"models/{self.MODEL_NAME}",
            google_api_key=self.get_google_api_key(),
            temperature=self.TEMPERATURE
        )

    @property
    def embeddings(self):
        return GoogleGenerativeAIEmbeddings(
            model=self.EMBEDDING_MODEL_NAME,
            google_api_key=self.get_google_api_key()
        )

    @property
    def mssql_db(self):
        return SQLDatabase.from_uri(self.MSSQL_DATABASE_URI)

    @property
    def postgres_pool(self):
        return self.pool