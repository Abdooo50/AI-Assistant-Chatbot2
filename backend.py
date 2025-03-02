from fastapi import FastAPI, HTTPException, Depends, status, Header
from pydantic import BaseModel
from jose import JWTError, jwt # type: ignore
from Workflow.utils.config import Config
from Workflow.workflow import Workflow

# Define a Pydantic model for the request body
class UserQuestion(BaseModel):
    question: str

# Initialize the FastAPI app
app = FastAPI()

config = Config()

# Initialize the workflow
workflow = Workflow(config)

# JWT Configuration
SECRET_KEY = "secret-key-123"  # Replace with a secure secret key
ALGORITHM = "HS256"  # Algorithm used for encoding/decoding

# Dependency to decode and validate the token
def validate_token(authorization: str = Header(...)):
    """
    Decode and validate the token from the Authorization header.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split("Bearer ")[1]
    try:
        # Decode the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Optionally, you can validate the payload here (e.g., check expiration, roles, etc.)
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Protected endpoint to ask a question
@app.post("/ask")
async def ask_question(user_question: UserQuestion, payload: dict = Depends(validate_token)):
    """
    Endpoint to ask a question and get a response from the workflow.
    """
    try:
        response = workflow.get_response(user_question.question, payload)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


# Protected endpoint to visualize the workflow graph
@app.get("/visualize")
async def visualize_graph(payload: dict = Depends(validate_token)):
    """
    Endpoint to visualize the workflow graph.
    """
    try:
        graph_image = workflow.visualize_graph()
        return {"graph_image": graph_image}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))