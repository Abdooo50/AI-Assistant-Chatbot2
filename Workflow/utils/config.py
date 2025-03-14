import os
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.utilities import SQLDatabase
from psycopg_pool import ConnectionPool  # type: ignore


class Config:
    def __init__(self):
        # Load environment variables from .env file if needed
        from dotenv import load_dotenv
        load_dotenv()

        # Database configuration for MSSQL
        self.MSSQL_DATABASE_URI = os.getenv("MSSQL_DATABASE_URI")

        # Database configuration for PostgreSQL
        self.POSTGRES_DB_URI = os.getenv("POSTGRES_DB_URI")
        self.POSTGRES_CONNECTION_KWARGS = {
            "autocommit": os.getenv("POSTGRES_AUTOCOMMIT", "True").lower() == "true",
            "prepare_threshold": int(os.getenv("POSTGRES_PREPARE_THRESHOLD", 0)),
        }

        # Google Generative AI configuration
        self.MODEL_NAME = os.getenv("MODEL_NAME")
        self.EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME")
        self.TEMPERATURE = float(os.getenv("TEMPERATURE", 0))

        # Application settings
        self.NUMBER_OF_LAST_MESSAGES = int(os.getenv("NUMBER_OF_LAST_MESSAGES", -10))

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