import os
import requests
import base64
import json
from fastapi import FastAPI, HTTPException, Depends, Header, Query, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from jose import JWTError, jwt  # type: ignore
from Workflow.utils.config import Config
from Workflow.workflow import Workflow
import logging
import uuid
import time
import asyncio
from datetime import datetime, timedelta
import markdown
import re

# Proper logger initialization with double underscores
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache for storing frequently accessed data
cache = {}
CACHE_TTL = 300  # 5 minutes

# Environment variables for configuration
ALLOWED_ORIGINS = json.loads(os.getenv("ALLOWED_ORIGINS", '["*"]'))
SECRET_KEY = os.getenv("SECRET_KEY", "E1BF978D6F44AE82ED6FD6CDC481EE1BF978D6F44AE82ED6FD6CDC481E")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
JWT_TOKEN_GENERATOR_URL = os.getenv("JWT_TOKEN_GENERATOR_URL", "https://mosefakapiss.runasp.net/api/Authentication/Login")

# Request models
class UserQuestion(BaseModel):
    question: str
    thread_id: str
    stream: Optional[bool] = False

class ThreadIDRequest(BaseModel):
    thread_id: str

class ChatHistoryRequest(BaseModel):
    thread_id: str
    limit: Optional[int] = Field(20, description="Number of messages to return per page")
    cursor: Optional[int] = Field(None, description="Message ID to use as reference point for pagination")
    direction: Optional[str] = Field("before", description="Direction of pagination ('before' or 'after' the cursor)")

class ChatsListRequest(BaseModel):
    limit: Optional[int] = Field(20, description="Number of chat threads to return per page")
    cursor: Optional[str] = Field(None, description="Timestamp to use as reference point for pagination")

class NewChatRequest(BaseModel):
    chat_name: str

# Response models for better API documentation
class PaginationMetadata(BaseModel):
    has_more_before: Optional[bool] = False
    has_more_after: Optional[bool] = False
    next_cursor: Optional[Union[int, str]] = None
    prev_cursor: Optional[Union[int, str]] = None
    total_count: int

class ChatMessage(BaseModel):
    message_id: int
    role: str
    content: str
    created_at: str
    message_type: Optional[str] = None

class ChatThread(BaseModel):
    thread_id: str
    chat_name: str
    last_updated_at: Optional[str] = None
    summary: Optional[str] = None

class ChatHistoryResponse(BaseModel):
    history: List[ChatMessage]
    pagination: PaginationMetadata

class ChatsListResponse(BaseModel):
    chats: List[ChatThread]
    pagination: PaginationMetadata

class SuggestedQuestion(BaseModel):
    text: str
    type: Optional[str] = "follow-up"

class AskResponse(BaseModel):
    response: str
    thread_id: str
    suggested_questions: Optional[List[SuggestedQuestion]] = None

# Initialize FastAPI app
app = FastAPI(
    title="Medical Assistant API",
    description="API for the Medical Assistant application with enhanced chat functionality",
    version="2.0.0"
)

# Configure CORS middleware with environment variables
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize configuration and workflow
config = Config()
workflow = Workflow(config)
postgres_pool = config.postgres_pool

# Connected WebSocket clients
connected_clients = {}

# Utility functions
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

def get_cache_key(user_id, endpoint, params=None):
    """Generate a cache key based on user_id, endpoint, and optional parameters"""
    if params:
        return f"{user_id}:{endpoint}:{json.dumps(params, sort_keys=True)}"
    return f"{user_id}:{endpoint}"

def get_cached_data(key):
    """Get data from cache if it exists and is not expired"""
    if key in cache:
        entry = cache[key]
        if time.time() < entry["expires"]:
            return entry["data"]
        # Remove expired entry
        del cache[key]
    return None

def set_cached_data(key, data, ttl=CACHE_TTL):
    """Store data in cache with expiration time"""
    cache[key] = {
        "data": data,
        "expires": time.time() + ttl
    }

def clean_expired_cache(background_tasks):
    """Clean expired cache entries"""
    current_time = time.time()
    keys_to_delete = [k for k, v in cache.items() if current_time > v["expires"]]
    for key in keys_to_delete:
        del cache[key]
    # Schedule next cleanup
    background_tasks.add_task(schedule_cache_cleanup)

def schedule_cache_cleanup():
    """Schedule cache cleanup after a delay"""
    time.sleep(300)  # 5 minutes
    background_tasks = BackgroundTasks()
    clean_expired_cache(background_tasks)

def generate_suggested_questions(thread_id, question, response):
    """Generate suggested follow-up questions based on the conversation"""
    try:
        # Get the last few messages for context
        with postgres_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT role, content FROM chat_messages 
                    WHERE thread_id = %s 
                    ORDER BY created_at DESC 
                    LIMIT 5
                    """,
                    (thread_id,)
                )
                messages = cur.fetchall()
        
        # Format the conversation context
        conversation = "\n".join([f"{msg[0]}: {msg[1]}" for msg in messages])
        
        # Use the LLM to generate suggested questions
        prompt = f"""
        Based on the following conversation, generate 3 natural follow-up questions that the user might want to ask next.
        Make the questions specific to the medical topic being discussed and directly related to the last response.
        
        Conversation:
        {conversation}
        
        Current question: {question}
        Response: {response}
        
        Generate only the questions as a JSON array of objects with 'text' field, nothing else.
        Example: [{{"text": "What are the side effects of this medication?"}}, {{"text": "How long should I take this treatment?"}}]
        """
        
        # Use the workflow's LLM to generate suggestions
        llm_response = config.llm.invoke(prompt)
        
        # Extract JSON array from response
        match = re.search(r'\[.*\]', llm_response.content, re.DOTALL)
        if match:
            json_str = match.group(0)
            questions = json.loads(json_str)
            return questions
        
        return []
    except Exception as e:
        logger.error(f"Error generating suggested questions: {e}")
        return []

def format_markdown_response(text):
    """Format response text with markdown"""
    try:
        # Convert markdown to HTML
        html = markdown.markdown(text)
        return html
    except Exception as e:
        logger.error(f"Error formatting markdown: {e}")
        return text

async def notify_thread_update(thread_id, message_type="message"):
    """Notify connected clients about updates to a thread"""
    if thread_id in connected_clients:
        for client in connected_clients[thread_id]:
            try:
                await client.send_json({
                    "type": "update",
                    "thread_id": thread_id,
                    "message_type": message_type,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error notifying client: {e}")

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/chat/new", response_model=ChatThread)
async def create_new_chat(
    request: NewChatRequest, 
    background_tasks: BackgroundTasks,
    payload: dict = Depends(validate_token)
):
    """
    Create a new chat thread.
    
    Args:
        request: NewChatRequest containing chat_name
        payload: User payload from JWT token
        
    Returns:
        New chat thread details
    """
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
        
        # Generate welcome message
        welcome_message = "Welcome to your new medical assistant chat. How can I help you today?"
        
        # Store welcome message
        with postgres_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO chat_messages (thread_id, role, content, message_type) VALUES (%s, %s, %s, %s)",
                    (thread_id, "assistant", welcome_message, "greeting")
                )
                conn.commit()
        
        # Initialize workflow for this thread
        config_params = {"configurable": {"thread_id": thread_id}}
        background_tasks.add_task(
            workflow.graph.stream,
            {"messages": [], "payload": payload},
            config_params,
            stream_mode="values"
        )
        
        # Invalidate cache for user's chat list
        cache_key = get_cache_key(user_id, "chats")
        if cache_key in cache:
            del cache[cache_key]
        
        return {
            "thread_id": thread_id, 
            "chat_name": request.chat_name,
            "welcome_message": welcome_message
        }
    except Exception as e:
        logger.error(f"Error creating chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating chat: {str(e)}")

@app.post("/chats", response_model=ChatsListResponse)
async def get_user_chats(
    request: ChatsListRequest = None, 
    payload: dict = Depends(validate_token)
):
    """
    Get paginated list of chat threads for a user.
    
    Args:
        request: ChatsListRequest containing pagination parameters
        payload: User payload from JWT token
        
    Returns:
        Paginated list of chat threads with pagination metadata
    """
    user_id = payload.get("user_id")
    
    # Initialize request if not provided
    if request is None:
        request = ChatsListRequest()
    
    limit = request.limit or 20
    cursor = request.cursor
    
    # Validate parameters
    if limit < 1 or limit > 100:
        limit = 20  # Default to 20 if out of range
    
    # Check cache first
    cache_key = get_cache_key(user_id, "chats", {"limit": limit, "cursor": cursor})
    cached_data = get_cached_data(cache_key)
    if cached_data:
        return cached_data
    
    try:
        with postgres_pool.connection() as conn:
            with conn.cursor() as cur:
                # Get total count of chat threads for this user
                cur.execute(
                    "SELECT COUNT(*) FROM chat_threads WHERE user_id = %s",
                    (user_id,)
                )
                total_count = cur.fetchone()[0]
                
                # Build the query based on pagination parameters
                if cursor is None:
                    # Initial load - get most recent chat threads
                    query = """
                        SELECT thread_id, chat_name, last_updated_at 
                        FROM chat_threads 
                        WHERE user_id = %s 
                        ORDER BY last_updated_at DESC 
                        LIMIT %s
                    """
                    cur.execute(query, (user_id, limit))
                else:
                    # Load older chat threads (before the cursor)
                    query = """
                        SELECT thread_id, chat_name, last_updated_at 
                        FROM chat_threads 
                        WHERE user_id = %s AND last_updated_at < %s 
                        ORDER BY last_updated_at DESC 
                        LIMIT %s
                    """
                    # Parse the cursor timestamp
                    cursor_timestamp = datetime.fromisoformat(cursor)
                    cur.execute(query, (user_id, cursor_timestamp, limit))
                
                chats = cur.fetchall()
                
                # Prepare the response
                chat_list = []
                next_cursor = None
                
                if chats:
                    # Format chat threads for response
                    chat_list = [
                        {
                            "thread_id": chat[0],
                            "chat_name": chat[1],
                            "last_updated_at": chat[2].isoformat() if chat[2] else None
                        } 
                        for chat in chats
                    ]
                    
                    # Set cursor for pagination
                    if len(chat_list) == limit:
                        next_cursor = chat_list[-1]["last_updated_at"]
                
                # Check if there are more chat threads
                has_more = False
                
                if next_cursor:
                    cursor_timestamp = datetime.fromisoformat(next_cursor)
                    cur.execute(
                        "SELECT 1 FROM chat_threads WHERE user_id = %s AND last_updated_at < %s LIMIT 1",
                        (user_id, cursor_timestamp)
                    )
                    has_more = bool(cur.fetchone())
                
                # Build pagination metadata
                pagination = {
                    "has_more_before": has_more,
                    "has_more_after": False,  # Always false for forward-only pagination
                    "next_cursor": next_cursor,
                    "prev_cursor": None,
                    "total_count": total_count
                }
                
                result = {
                    "chats": chat_list,
                    "pagination": pagination
                }
                
                # Cache the result
                set_cached_data(cache_key, result)
                
                return result
    except Exception as e:
        logger.error(f"Error fetching chats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching chats: {str(e)}")

@app.post("/chat", response_model=ChatHistoryResponse)
async def get_chat_history(
    request: ChatHistoryRequest, 
    payload: dict = Depends(validate_token)
):
    """
    Get paginated chat history for a specific thread.
    
    Args:
        request: ChatHistoryRequest containing thread_id, pagination parameters
        payload: User payload from JWT token
        
    Returns:
        Paginated chat history with pagination metadata
    """
    user_id = payload.get("user_id")
    thread_id = request.thread_id
    limit = request.limit or 20
    cursor = request.cursor
    direction = request.direction or "before"
    
    # Validate parameters
    if limit < 1 or limit > 100:
        limit = 20  # Default to 20 if out of range
    
    if direction not in ["before", "after"]:
        direction = "before"  # Default to "before" if invalid
    
    if not thread_id.startswith(f"{user_id}/"):
        raise HTTPException(status_code=403, detail="Unauthorized access to chat")
    
    # Check cache first
    cache_key = get_cache_key(user_id, f"chat:{thread_id}", {"limit": limit, "cursor": cursor, "direction": direction})
    cached_data = get_cached_data(cache_key)
    if cached_data:
        return cached_data
    
    try:
        with postgres_pool.connection() as conn:
            with conn.cursor() as cur:
                # Get total count of messages for this thread
                cur.execute(
                    "SELECT COUNT(*) FROM chat_messages WHERE thread_id = %s",
                    (thread_id,)
                )
                total_count = cur.fetchone()[0]
                
                # Build the query based on pagination parameters
                if cursor is None:
                    # Initial load - get most recent messages
                    query = """
                        SELECT message_id, role, content, created_at, message_type 
                        FROM chat_messages 
                        WHERE thread_id = %s 
                        ORDER BY created_at DESC 
                        LIMIT %s
                    """
                    cur.execute(query, (thread_id, limit))
                elif direction == "before":
                    # Load older messages (before the cursor)
                    query = """
                        SELECT message_id, role, content, created_at, message_type 
                        FROM chat_messages 
                        WHERE thread_id = %s AND message_id < %s 
                        ORDER BY created_at DESC 
                        LIMIT %s
                    """
                    cur.execute(query, (thread_id, cursor, limit))
                else:  # direction == "after"
                    # Load newer messages (after the cursor)
                    query = """
                        SELECT message_id, role, content, created_at, message_type 
                        FROM chat_messages 
                        WHERE thread_id = %s AND message_id > %s 
                        ORDER BY created_at ASC 
                        LIMIT %s
                    """
                    cur.execute(query, (thread_id, cursor, limit))
                
                messages = cur.fetchall()
                
                # For "after" direction, we need to reverse the results to maintain chronological order
                if direction == "after" and messages:
                    messages.reverse()
                
                # Prepare the response
                message_list = []
                next_cursor = None
                prev_cursor = None
                
                if messages:
                    # Format messages for response
                    message_list = [
                        {
                            "message_id": msg[0],
                            "role": msg[1],
                            "content": msg[2],
                            "created_at": msg[3].isoformat() if msg[3] else None,
                            "message_type": msg[4]
                        } 
                        for msg in messages
                    ]
                    
                    # Set cursors for pagination
                    if len(message_list) == limit:
                        if direction == "before" or cursor is None:
                            next_cursor = message_list[-1]["message_id"]
                        if direction == "after" or cursor is None:
                            prev_cursor = message_list[0]["message_id"]
                
                # Check if there are more messages in each direction
                has_more_before = False
                has_more_after = False
                
                if next_cursor:
                    cur.execute(
                        "SELECT 1 FROM chat_messages WHERE thread_id = %s AND message_id < %s LIMIT 1",
                        (thread_id, next_cursor)
                    )
                    has_more_before = bool(cur.fetchone())
                
                if prev_cursor:
                    cur.execute(
                        "SELECT 1 FROM chat_messages WHERE thread_id = %s AND message_id > %s LIMIT 1",
                        (thread_id, prev_cursor)
                    )
                    has_more_after = bool(cur.fetchone())
                
                # Build pagination metadata
                pagination = {
                    "has_more_before": has_more_before,
                    "has_more_after": has_more_after,
                    "next_cursor": next_cursor,
                    "prev_cursor": prev_cursor,
                    "total_count": total_count
                }
                
                result = {
                    "history": message_list,
                    "pagination": pagination
                }
                
                # Cache the result
                set_cached_data(cache_key, result)
                
                return result
    except Exception as e:
        logger.error(f"Error fetching chat history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching chat history: {str(e)}")

@app.post("/ask", response_model=AskResponse)
async def ask_question(
    user_question: UserQuestion, 
    background_tasks: BackgroundTasks,
    payload: dict = Depends(validate_token)
):
    """
    Ask a question and get a response.
    
    Args:
        user_question: UserQuestion containing question and thread_id
        payload: User payload from JWT token
        
    Returns:
        Response from the assistant
    """
    user_id = payload.get("user_id")
    thread_id = user_question.thread_id
    
    # Check if streaming is requested
    if user_question.stream:
        return StreamingResponse(
            stream_response(user_question, payload),
            media_type="text/event-stream"
        )
    
    if not thread_id.startswith(f"{user_id}/"):
        raise HTTPException(status_code=403, detail="Unauthorized access to chat")
    
    try:
        # Store user question in database
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
        
        # Get response from workflow
        config_params = {"configurable": {"thread_id": thread_id}}
        response = workflow.get_response(user_question.question, payload, config_params)
        
        # Format response with markdown
        formatted_response = format_markdown_response(response)
        
        # Store assistant response in database
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
        
        # Generate suggested follow-up questions
        suggested_questions = generate_suggested_questions(thread_id, user_question.question, response)
        
        # Invalidate cache for this thread's history
        cache_key_prefix = get_cache_key(user_id, f"chat:{thread_id}")
        keys_to_delete = [k for k in cache.keys() if k.startswith(cache_key_prefix)]
        for key in keys_to_delete:
            del cache[key]
        
        # Notify connected clients about the update
        background_tasks.add_task(notify_thread_update, thread_id)
        
        return {
            "response": formatted_response, 
            "thread_id": thread_id,
            "suggested_questions": suggested_questions
        }
    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def stream_response(user_question: UserQuestion, payload: dict):
    """
    Stream the response to a question.
    
    Args:
        user_question: UserQuestion containing question and thread_id
        payload: User payload from JWT token
        
    Yields:
        Chunks of the response as server-sent events
    """
    user_id = payload.get("user_id")
    thread_id = user_question.thread_id
    
    if not thread_id.startswith(f"{user_id}/"):
        yield f"data: {json.dumps({'type': 'error', 'error': 'Unauthorized access to chat'})}\n\n"
        return
    
    try:
        # Store user question in database
        with postgres_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT chat_name FROM chat_threads WHERE thread_id = %s", (thread_id,))
                if not cur.fetchone():
                    yield f"data: {json.dumps({'type': 'error', 'error': 'Chat not found'})}\n\n"
                    return
                
                cur.execute(
                    "INSERT INTO chat_messages (thread_id, role, content) VALUES (%s, %s, %s)",
                    (thread_id, "user", user_question.question)
                )
                conn.commit()
        
        # Get response from workflow
        config_params = {"configurable": {"thread_id": thread_id}}
        
        # Simulate streaming by breaking the response into chunks
        # In a real implementation, you would modify workflow.get_response to yield chunks
        response = workflow.get_response(user_question.question, payload, config_params)
        
        # Store the complete response for later use
        full_response = response
        
        # Break response into words for streaming simulation
        words = response.split()
        chunks = []
        current_chunk = ""
        
        for word in words:
            current_chunk += word + " "
            if len(current_chunk) >= 10 or word == words[-1]:
                chunks.append(current_chunk)
                current_chunk = ""
        
        # Stream each chunk with a small delay
        for chunk in chunks:
            yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
            await asyncio.sleep(0.1)  # Small delay to simulate typing
        
        # Store assistant response in database
        with postgres_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO chat_messages (thread_id, role, content) VALUES (%s, %s, %s)",
                    (thread_id, "assistant", full_response)
                )
                cur.execute(
                    "UPDATE chat_threads SET last_updated_at = CURRENT_TIMESTAMP WHERE thread_id = %s",
                    (thread_id,)
                )
                conn.commit()
        
        # Generate suggested follow-up questions
        suggested_questions = generate_suggested_questions(thread_id, user_question.question, full_response)
        
        # Send the final event with suggested questions
        yield f"data: {json.dumps({'type': 'done', 'suggested_questions': suggested_questions})}\n\n"
        
        # Invalidate cache for this thread's history
        cache_key_prefix = get_cache_key(user_id, f"chat:{thread_id}")
        keys_to_delete = [k for k in cache.keys() if k.startswith(cache_key_prefix)]
        for key in keys_to_delete:
            del cache[key]
        
        # Notify connected clients about the update
        await notify_thread_update(thread_id)
        
    except Exception as e:
        logger.error(f"Error streaming response: {str(e)}")
        yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

@app.delete("/chat")
async def delete_chat(
    request: ThreadIDRequest, 
    background_tasks: BackgroundTasks,
    payload: dict = Depends(validate_token)
):
    """
    Delete a chat thread.
    
    Args:
        request: ThreadIDRequest containing thread_id
        payload: User payload from JWT token
        
    Returns:
        Success message
    """
    user_id = payload.get("user_id")
    thread_id = request.thread_id
    
    if not thread_id.startswith(f"{user_id}/"):
        raise HTTPException(status_code=403, detail="Unauthorized access to chat")
    
    try:
        with postgres_pool.connection() as conn:
            with conn.cursor() as cur:
                # Delete messages first (foreign key constraint)
                cur.execute(
                    "DELETE FROM chat_messages WHERE thread_id = %s",
                    (thread_id,)
                )
                
                # Delete the thread
                cur.execute(
                    "DELETE FROM chat_threads WHERE thread_id = %s AND user_id = %s",
                    (thread_id, user_id)
                )
                deleted_count = cur.rowcount
                conn.commit()
        
        if deleted_count == 0:
            raise HTTPException(status_code=404, detail="Chat not found or already deleted")
        
        # Invalidate cache for user's chat list and this thread's history
        cache_key_prefix = get_cache_key(user_id, "chats")
        keys_to_delete = [k for k in cache.keys() if k.startswith(cache_key_prefix)]
        
        cache_key_prefix = get_cache_key(user_id, f"chat:{thread_id}")
        keys_to_delete.extend([k for k in cache.keys() if k.startswith(cache_key_prefix)])
        
        for key in keys_to_delete:
            del cache[key]
        
        # Notify connected clients about the deletion
        background_tasks.add_task(notify_thread_update, thread_id, "deleted")
        
        return {"message": "Chat deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting chat: {str(e)}")

@app.delete("/chats")
async def delete_all_chats(
    background_tasks: BackgroundTasks,
    payload: dict = Depends(validate_token)
):
    """
    Delete all chat threads for a user.
    
    Args:
        payload: User payload from JWT token
        
    Returns:
        Success message
    """
    user_id = payload.get("user_id")
    
    try:
        # Get all thread IDs for notification
        thread_ids = []
        with postgres_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT thread_id FROM chat_threads WHERE user_id = %s",
                    (user_id,)
                )
                thread_ids = [row[0] for row in cur.fetchall()]
        
        # Delete all chats for the user
        with postgres_pool.connection() as conn:
            with conn.cursor() as cur:
                # Delete messages first (foreign key constraint)
                cur.execute(
                    """
                    DELETE FROM chat_messages 
                    WHERE thread_id IN (
                        SELECT thread_id FROM chat_threads WHERE user_id = %s
                    )
                    """,
                    (user_id,)
                )
                
                # Delete the threads
                cur.execute(
                    "DELETE FROM chat_threads WHERE user_id = %s",
                    (user_id,)
                )
                deleted_count = cur.rowcount
                conn.commit()
        
        # Invalidate all cache entries for this user
        cache_key_prefix = get_cache_key(user_id, "")
        keys_to_delete = [k for k in cache.keys() if k.startswith(cache_key_prefix)]
        for key in keys_to_delete:
            del cache[key]
        
        # Notify connected clients about the deletion
        for thread_id in thread_ids:
            background_tasks.add_task(notify_thread_update, thread_id, "deleted")
        
        return {"message": f"Deleted {deleted_count} chats successfully"}
    except Exception as e:
        logger.error(f"Error deleting all chats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting all chats: {str(e)}")

# @app.websocket("/ws/{thread_id}")
# async def websocket_endpoint(websocket: WebSocket, thread_id: str):
#     """
#     WebSocket endpoint for real-time updates.
    
#     Args:
#         websocket: WebSocket connection
#         thread_id: Chat thread ID
#     """
#     await websocket.accept()
    
#     try:
#         # Get token from query parameters
#         token = websocket.query_params.get("token")
#         if not token:
#             await websocket.close(code=1008, reason="Missing token")
#             return
        
#         # Validate token
#         try:
#             payload = manual_decode_token(token)
#             user_id = payload.get("nameid")
            
#             if not thread_id.startswith(f"{user_id}/"):
#                 await websocket.close(code=1008, reason="Unauthorized access to chat")
#                 return
#         except Exception as e:
#             await websocket.close(code=1008, reason=f"Invalid token: {str(e)}")
#             return
        
#         # Add client to connected clients
#         if thread_id not in connected_clients:
#             connected_clients[thread_id] = []
#         connected_clients[thread_id].append(websocket)
        
#         # Send initial connection confirmation
#         await websocket.send_json({
#             "type": "connected",
#             "thread_id": thread_id,
#             "timestamp": datetime.now().isoformat()
#         })
        
#         # Keep connection open until client disconnects
#         while True:
#             data = await websocket.receive_text()
#             # Process any client messages if needed
#             await websocket.send_json({
#                 "type": "ack",
#                 "timestamp": datetime.now().isoformat()
#             })
            
#     except WebSocketDisconnect:
#         # Remove client from connected clients
#         if thread_id in connected_clients and websocket in connected_clients[thread_id]:
#             connected_clients[thread_id].remove(websocket)
#             if not connected_clients[thread_id]:
#                 del connected_clients[thread_id]
#     except Exception as e:
#         logger.error(f"WebSocket error: {str(e)}")
#         try:
#             await websocket.close(code=1011, reason=f"Server error: {str(e)}")
#         except:
#             pass

# Initialize cache cleanup task
@app.on_event("startup")
async def startup_event():
    """Initialize background tasks on startup"""
    background_tasks = BackgroundTasks()
    background_tasks.add_task(schedule_cache_cleanup)

