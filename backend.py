# fastapi_backend.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from Workflow.workflow import Workflow

# Define a Pydantic model for the request body
class UserQuestion(BaseModel):
    question: str

# Initialize the FastAPI app
app = FastAPI()

# Initialize the Workflow instance
workflow = Workflow()

@app.post("/ask")
async def ask_question(user_question: UserQuestion):
    """
    Endpoint to ask a question and get a response from the workflow.
    """
    try:
        response = workflow.get_response(user_question.question)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/visualize")
async def visualize_graph():
    """
    Endpoint to visualize the workflow graph.
    """
    try:
        graph_image = workflow.visualize_graph()
        return {"graph_image": graph_image}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))