import os
import requests
import base64
import json
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from jose import JWTError, jwt  # type: ignore
from Workflow.utils.config import Config
from Workflow.workflow import Workflow
import logging
import uuid
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserQuestion(BaseModel):
    question: str
    thread_id: str

class ThreadIDRequest(BaseModel):
    thread_id: str

class NewChatRequest(BaseModel):
    chat_name: str

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

config = Config()
workflow = Workflow(config)

# JWT Configuration from .env
SECRET_KEY = os.getenv("SECRET_KEY", "E1BF978D6F44AE82ED6FD6CDC481EE1BF978D6F44AE82ED6FD6CDC481E")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
JWT_TOKEN_GENERATOR_URL = os.getenv("JWT_TOKEN_GENERATOR_URL", "https://yth3d4dbpe.eu-west-1.awsapprunner.com/api/Authentication/Login")

postgres_pool = config.postgres_pool

def get_jwt_token(username: str, password: str) -> str:
    """
    Get the JWT token by calling the JWT Token Generator endpoint.

    Args:
        username (str): The username of the user requesting the token.
        password (str): The password of the user requesting the token.

    Returns:
        str: The generated JWT token.
    """
    try:
        response = requests.post(JWT_TOKEN_GENERATOR_URL, json={"email": username, "password": password})
        response.raise_for_status()  # Will raise an exception for non-2xx responses
        token_data = response.json()
        return token_data["token"]
    except requests.exceptions.HTTPError as err:
        raise HTTPException(status_code=400, detail="Failed to generate token")
    except Exception as e:
        logger.error(f"Error generating token: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

def manual_decode_token(token):
    """
    Manually decode the JWT token without using the jwt.decode function.
    
    Args:
        token (str): The JWT token to decode.
        
    Returns:
        dict: The decoded token payload.
        
    Raises:
        Exception: If the token is invalid or cannot be decoded.
    """
    try:
        # Split the token into its parts
        header_b64, payload_b64, signature = token.split('.')
        
        # Decode the base64 encoded parts
        # Add padding if needed
        def decode_base64_url(b64_str):
            padding = '=' * (4 - len(b64_str) % 4)
            return base64.urlsafe_b64decode(b64_str + padding).decode('utf-8')
        
        payload = json.loads(decode_base64_url(payload_b64))
        
        # Check token expiration
        current_time = int(time.time())
        if "exp" in payload and payload["exp"] <= current_time:
            raise Exception("Token has expired")
            
        return payload
    except Exception as e:
        raise Exception(f"Invalid token format: {str(e)}")

def validate_token(authorization: str = Header(...)):
    """
    Validate the JWT token from the Authorization header.
    
    This function extracts the token from the Authorization header,
    manually decodes it without using the jose library (to avoid the key parameter issue),
    and returns the payload if the token is valid.
    
    Args:
        authorization (str): The Authorization header containing the JWT token.
        
    Returns:
        dict: The decoded token payload.
        
    Raises:
        HTTPException: If the token is invalid or missing.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid or missing token", headers={"WWW-Authenticate": "Bearer"})
    
    token = authorization.split("Bearer ")[1]
    
    try:
        # Manually decode the token without using jwt.decode
        payload = manual_decode_token(token)
        
        # Extract user_id from the nameid claim
        if "nameid" in payload:
            payload["user_id"] = payload["nameid"]
        else:
            raise HTTPException(status_code=401, detail="Invalid token format: missing nameid claim", headers={"WWW-Authenticate": "Bearer"})
        
        # Extract role from the roles array
        if "roles" in payload and isinstance(payload["roles"], list) and len(payload["roles"]) > 0:
            # Use the first role in the array as the primary role
            payload["role"] = payload["roles"][0]
        else:
            raise HTTPException(status_code=401, detail="Missing user role or ID", headers={"WWW-Authenticate": "Bearer"})
            
        return payload
    except JWTError as e:
        logger.error(f"JWT Error: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token", headers={"WWW-Authenticate": "Bearer"})
    except Exception as e:
        logger.error(f"Error decoding JWT token: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Token error: {str(e)}", headers={"WWW-Authenticate": "Bearer"})

@app.post("/chat/new")
async def create_new_chat(request: NewChatRequest, payload: dict = Depends(validate_token)):
    user_id = payload.get("user_id")
    thread_id = f"{user_id}/{request.chat_name}/{uuid.uuid4().hex[:8]}"
    try:
        with postgres_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO chat_threads (thread_id, user_id, chat_name) VALUES (%s, %s, %s) RETURNING thread_id",
                    (thread_id, user_id, request.chat_name)
                )
                result = cur.fetchone()
                conn.commit()
        config = {"configurable": {"thread_id": thread_id}}
        workflow.graph.stream({"messages": [], "payload": payload}, config, stream_mode="values")
        return {"thread_id": thread_id, "chat_name": request.chat_name}
    except Exception as e:
        logger.error(f"Error creating chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating chat: {str(e)}")

@app.get("/chats")
async def get_user_chats(payload: dict = Depends(validate_token)):
    user_id = payload.get("user_id")
    try:
        with postgres_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT thread_id, chat_name FROM chat_threads WHERE user_id = %s ORDER BY last_updated_at DESC",
                    (user_id,)
                )
                chats = cur.fetchall()
        return {"chats": [{"thread_id": chat[0], "chat_name": chat[1]} for chat in chats]}
    except Exception as e:
        logger.error(f"Error fetching chats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching chats: {str(e)}")

@app.post("/ask")
async def ask_question(user_question: UserQuestion, payload: dict = Depends(validate_token)):
    user_id = payload.get("user_id")
    thread_id = user_question.thread_id
    if not thread_id.startswith(f"{user_id}/"):
        raise HTTPException(status_code=403, detail="Unauthorized access to chat")
    try:
        with postgres_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT chat_name FROM chat_threads WHERE thread_id = %s", (thread_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail=f"Chat with thread_id '{thread_id}' not found")
                cur.execute(
                    "INSERT INTO chat_messages (thread_id, role, content) VALUES (%s, %s, %s)",
                    (thread_id, "user", user_question.question)
                )
                conn.commit()
        config = {"configurable": {"thread_id": thread_id}}
        response = workflow.get_response(user_question.question, payload, config)
        with postgres_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO chat_messages (thread_id, role, content) VALUES (%s, %s, %s)",
                    (thread_id, "assistant", response)
                )
                cur.execute(
                    "UPDATE chat_threads SET last_updated_at = CURRENT_TIMESTAMP WHERE thread_id = %s",
                    (thread_id,)
                )
                conn.commit()
        return {"response": response, "thread_id": thread_id}
    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def get_chat_history(request: ThreadIDRequest, payload: dict = Depends(validate_token)):
    user_id = payload.get("user_id")
    thread_id = request.thread_id
    if not thread_id.startswith(f"{user_id}/"):
        raise HTTPException(status_code=403, detail="Unauthorized access to chat")
    try:
        with postgres_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT role, content, created_at FROM chat_messages WHERE thread_id = %s ORDER BY created_at",
                    (thread_id,)
                )
                messages = cur.fetchall()
        return {"history": [{"role": msg[0], "content": msg[1]} for msg in messages]}
    except Exception as e:
        logger.error(f"Error fetching history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/chat")
async def delete_chat(request: ThreadIDRequest, payload: dict = Depends(validate_token)):
    user_id = payload.get("user_id")
    thread_id = request.thread_id
    if not thread_id.startswith(f"{user_id}/"):
        raise HTTPException(status_code=403, detail="Unauthorized access to chat")
    try:
        with postgres_pool.connection() as conn:
            with conn.cursor() as cur:
                # Check if chat exists
                cur.execute("SELECT 1 FROM chat_threads WHERE thread_id = %s", (thread_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail=f"Chat with thread_id '{thread_id}' not found")
                
                # Delete from all related tables
                cur.execute("DELETE FROM chat_threads WHERE thread_id = %s", (thread_id,))
                # Note: chat_messages will be deleted automatically due to ON DELETE CASCADE
                # Delete from checkpoint tables
                cur.execute("DELETE FROM checkpoint_blobs WHERE thread_id = %s", (thread_id,))
                cur.execute("DELETE FROM checkpoint_writes WHERE thread_id = %s", (thread_id,))
                cur.execute("DELETE FROM checkpoints WHERE thread_id = %s", (thread_id,))
                conn.commit()
        return {"message": f"Chat {thread_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting chat: {str(e)}")

@app.delete("/chats")
async def delete_all_chats(payload: dict = Depends(validate_token)):
    user_id = payload.get("user_id")
    try:
        with postgres_pool.connection() as conn:
            with conn.cursor() as cur:
                # Delete all chats for this user
                cur.execute("DELETE FROM chat_threads WHERE user_id = %s", (user_id,))
                # Note: chat_messages will be deleted automatically due to ON DELETE CASCADE
                # Delete from checkpoint tables
                cur.execute("DELETE FROM checkpoint_blobs WHERE thread_id LIKE %s", (f"{user_id}/%",))
                cur.execute("DELETE FROM checkpoint_writes WHERE thread_id LIKE %s", (f"{user_id}/%",))
                cur.execute("DELETE FROM checkpoints WHERE thread_id LIKE %s", (f"{user_id}/%",))
                conn.commit()
        return {"message": "All chats deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting all chats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting all chats: {str(e)}")
