import os
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from psycopg_pool import ConnectionPool  # type: ignore
import pyodbc


class Config:
    def __init__(self):
        # Load environment variables from .env file if needed
        from dotenv import load_dotenv
        load_dotenv()

        # Construct connection string using environment variables
        self.mosefak_app_conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            f"SERVER={os.getenv('MOSEFAK_APP_DATABASE_SERVER')};"
            f"DATABASE={os.getenv('MOSEFAK_APP_DATABASE_NAME')};"
            f"UID={os.getenv('MOSEFAK_APP_DATABASE_USER')};"
            f"PWD={os.getenv('MOSEFAK_APP_DATABASE_PASSWORD')};"
            f"Encrypt={os.getenv('MOSEFAK_APP_ENCRYPT')};"
            f"TrustServerCertificate={os.getenv('MOSEFAK_APP_TRUST_SERVER_CERTIFICATE')};"
        )

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
        self.NUMBER_OF_LAST_MESSAGES = int(os.getenv("NUMBER_OF_LAST_MESSAGES", -5))

        # Initialize PostgreSQL connection pool
        self.pool = ConnectionPool(
            conninfo=str(self.POSTGRES_DB_URI),
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
        chat_model = ChatGoogleGenerativeAI(
            model=f"{self.MODEL_NAME}",
            google_api_key=self.get_google_api_key(),
            temperature=self.TEMPERATURE
        )
        return chat_model

    @property
    def embeddings(self):
        return GoogleGenerativeAIEmbeddings(
            model=str(self.EMBEDDING_MODEL_NAME),
            google_api_key=self.get_google_api_key()
        )

    @property
    def mosefak_app_db(self):
        return pyodbc.connect(self.mosefak_app_conn_str)

    @property
    def postgres_pool(self):
        return self.pool
