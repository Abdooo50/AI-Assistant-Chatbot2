import os
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from jose import JWTError, jwt # type: ignore
from Workflow.utils.config import Config
from Workflow.workflow import Workflow
import logging
import uuid

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
config = Config()
workflow = Workflow(config)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

postgres_pool = config.postgres_pool

def validate_token(authorization: str = Header(...)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid or missing token", headers={"WWW-Authenticate": "Bearer"})
    token = authorization.split("Bearer ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token", headers={"WWW-Authenticate": "Bearer"})

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
    print(thread_id, " ", user_id)
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