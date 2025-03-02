import ast
import re
import textwrap
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv
load_dotenv()

from langchain_core.runnables import RunnablePassthrough
from langchain_text_splitters import RecursiveCharacterTextSplitter


from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import RetrievalQA
from langchain.schema import Document
from langchain_community.vectorstores import FAISS

    

def to_markdown(text):
    text = text.replace('•', '  *')
    return "> " + textwrap.indent(text, '> ', predicate=lambda _: True).replace('\n', '\n> ')


def remove_sql_block(input_string: str) -> str:
    """
    Removes the ```sql``` block from the input string.
    
    Args:
        input_string (str): The input string containing the SQL query with ```sql``` block.
    
    Returns:
        str: The SQL query without the ```sql``` block.
    """
    # Remove the leading and trailing ```sql```
    if input_string.startswith("```sql") and input_string.endswith("```"):
        # Strip the ```sql``` and trailing ```
        return input_string[6:-3].strip()
    return input_string



def extract_messages(input_string):
    """
    Extracts human and AI messages from the input string.

    Args:
        input_string (str): The input string containing HumanMessage and AIMessage objects.

    Returns:
            - human_messages: List of human messages.
            - ai_messages: List of AI messages.
    """
    # Regex pattern to match HumanMessage and AIMessage content
    pattern = r"(HumanMessage|AIMessage)\(content='(.*?)'[^)]*\)"

    # Find all matches
    matches = re.findall(pattern, input_string)

    # Separate variables for human and AI messages
    human_messages = []
    ai_messages = []

    # Organize results
    for match in matches:
        message_type, content = match
        if message_type == "HumanMessage":
            human_messages.append(content)
        elif message_type == "AIMessage":
            ai_messages.append(content)

    structured_conversation = "\n".join(
    [f"Human: {human_msg}\nAI: {ai_msg}\n--------------------" 
    for human_msg, ai_msg in zip(human_messages, ai_messages)]
    )

    return structured_conversation


def query_as_list(db, query):
    # Execute the query
    res = db.run(query)
    
    # Parse the result as a list of lists (rows)
    try:
        rows = ast.literal_eval(res)
    except (ValueError, SyntaxError) as e:
        raise ValueError(f"Failed to parse query result: {e}")
    
    # Ensure the result is a list of lists (or tuples)
    if not isinstance(rows, list) or not all(isinstance(row, (list, tuple)) for row in rows):
        raise ValueError("Query result is not in the expected format (list of lists/tuples).")
    
    # Remove any empty or null values within rows
    cleaned_rows = [
        [str(el).strip() for el in row if el is not None and str(el).strip()]
        for row in rows
    ]
    
    # Return the cleaned rows as a list of tuples
    return [tuple(row) for row in cleaned_rows]


def query_doctors_from_db(db) -> List[Tuple]:
    """
    Query the database for doctor information.

    Parameters:
    - db: Database connection or query executor.

    Returns:
    - List[Tuple]: Doctor information as tuples.
    """
    query_result = query_as_list(db, """
        SELECT 
            'Dr. ' + u.FirstName + ' ' + u.LastName AS DoctorName,
            COALESCE(STRING_AGG(wt.DayOfWeek, ', '), 'Not available') AS WorkingDays,
            COALESCE(ca.Street, 'Unknown Street') AS Street,
            COALESCE(ca.City, 'Unknown City') AS City,
            COALESCE(ca.Country, 'Unknown Country') AS Country,
            COALESCE(STRING_AGG(sp.Name, ', '), 'No specialization') AS Specializations
        FROM dbo.Doctors d
        JOIN Security.Users u ON d.AppUserId = u.Id
        LEFT JOIN dbo.WorkingTimes wt ON d.Id = wt.DoctorId
        LEFT JOIN dbo.ClinicAddresses ca ON d.Id = ca.DoctorId
        LEFT JOIN dbo.Specializations sp ON d.Id = sp.DoctorId
        GROUP BY u.FirstName, u.LastName, ca.Street, ca.City, ca.Country;
    """)
    return query_result


def format_doctors(doctors: List[Tuple]) -> str:
    """
    Format doctor information into a human-readable string.

    Parameters:
    - doctors (List[Tuple]): Doctor information as tuples.

    Returns:
    - str: Formatted doctor information.
    """
    if not doctors:
        return ""

    return "\n".join([
        f"{doctor[0]} is working on {doctor[1]} at {doctor[2]}, {doctor[3]}, {doctor[4]}, and specializes in {doctor[5]}."
        for doctor in doctors
    ])


def process_documents(text: str) -> List[Document]:
    """
    Process raw text into Document objects and split them into chunks.

    Parameters:
    - text (str): Raw text to process.

    Returns:
    - List[Document]: Processed documents.
    """
    documents = [Document(page_content=text)]
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    return text_splitter.split_documents(documents)


def create_faiss_index(documents: List[Document], embeddings) -> FAISS:
    """
    Create a FAISS vector store from the given documents.

    Parameters:
    - documents (List[Document]): Processed documents.
    - embeddings: Embedding model for FAISS index creation.

    Returns:
    - FAISS: The created FAISS index.
    """
    return FAISS.from_documents(documents, embeddings)


def retrieve_context(faiss_index: FAISS, query: str, llm) -> Dict[str, str]:
    """
    Retrieve relevant context from the FAISS index.

    Parameters:
    - faiss_index (FAISS): The FAISS index.
    - query (str): The query to search for.
    - llm: Language model for generating responses.

    Returns:
    - Dict[str, str]: Retrieved context.
    """
    retriever = faiss_index.as_retriever()
    retrieval_qa = RetrievalQA.from_llm(llm=llm, retriever=retriever)
    return retrieval_qa.invoke(query)


def generate_response(
    system_message: ChatPromptTemplate,
    messages: List[Any],
    llm: Any,
    user_id: Optional[str] = None,
    tables_info: Optional[str] = None,
    context: Dict[str, str] = None,
) -> str:
    """
    Generate a response using the chain.

    Parameters:
    - system_message (ChatPromptTemplate): The system message template.
    - messages (List[Any]): Conversation history.
    - llm: Language model for generating responses.
    - user_id (Optional[str]): The ID of the user. Defaults to None.
    - tables_info (Optional[str]): Information about tables. Defaults to None.
    - context (Dict[str, str]): Retrieved context. Defaults to None.

    Returns:
    - str: Generated response.
    """
    # Prepare input data for the chain
    input_data = {
        "messages": messages,
        "context": context['result'] if context else None,
    }

    # Add user_id and tables_info only if they are provided
    if user_id is not None:
        input_data["user_id"] = user_id
    if tables_info is not None:
        input_data["tables_info"] = tables_info

    # Define the chain
    chain = (
        RunnablePassthrough()
        | system_message
        | llm
    )

    # Invoke the chain with the prepared input data
    return chain.invoke(input_data)