import ast
import pydoc
import re
import textwrap
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv
load_dotenv()

from langchain_core.runnables import RunnablePassthrough
from langchain_text_splitters import RecursiveCharacterTextSplitter


from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser

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



def execute_query(conn, query):
    """
    Executes an SQL query safely.

    Args:
        conn: The active database connection.
        query (str): The SQL query to execute.

    Returns:
        list: The query results as a list of tuples.
    """
    if query.lower() == "not available":
        return "No data available."

    is_safe, message = is_safe_sql_query(query)
    if not is_safe:
        return f"Blocked due to security policy: {message}"

    try:
        with conn.cursor() as cursor:  # Use context manager for cursor
            cursor.execute(query)
            result = cursor.fetchall()
            return [tuple(row) for row in result]
    except Exception as e:
        return f"Query execution error: {str(e)}"



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
    cursor = db.cursor()
    cursor.execute(query)
    res = cursor.fetchall() or []  # Ensure it's always a list
    cursor.close()

    print(f"Raw query result: {res}")  # Debugging line

    # Convert rows to a list of tuples (ensuring it's JSON serializable)
    cleaned_rows = [tuple(row) for row in res]

    return cleaned_rows


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
            COALESCE(STRING_AGG(wt.Day, ', '), 'Not available') AS WorkingDays,
            COALESCE(ca.Street, 'Unknown Street') AS Street,
            COALESCE(ca.City, 'Unknown City') AS City,
            COALESCE(ca.Country, 'Unknown Country') AS Country,
            COALESCE(STRING_AGG(CAST(sp.Name AS NVARCHAR(MAX)), ', '), 'No specialization') AS Specializations
        FROM [mosefak-app].[dbo].[Doctors] d
        JOIN [mosefak-management].[Security].[Users] u ON d.AppUserId = u.Id
        LEFT JOIN [mosefak-app].[dbo].[Clinics] ca ON d.Id = ca.DoctorId
        LEFT JOIN [mosefak-app].[dbo].[WorkingTimes] wt ON ca.Id = wt.ClinicId
        LEFT JOIN [mosefak-app].[dbo].[Specializations] sp ON d.Id = sp.DoctorId
        GROUP BY u.FirstName, u.LastName, ca.Street, ca.City, ca.Country;
    """)

    # Format doctor information into a readable string
    formatted_output = format_doctors(query_result)

    return formatted_output


def format_doctors(doctors: List[Tuple]) -> str:
    """
    Format doctor information into a human-readable string.

    Parameters:
    - doctors (List[Tuple]): Doctor information as tuples.

    Returns:
    - str: Formatted doctor information.
    """
    if not doctors:
        return "No doctors available."

    return "\n".join([
        f"{doctor[0]} is working on {doctor[1]} at {doctor[2]}, {doctor[3]}, {doctor[4]}, specializes in {doctor[5]}, "
        # f"has {doctor[6]} years of experience, and charges {doctor[7]:.2f} for a consultation."
        for doctor in doctors
    ])



def create_faiss_index(text: str, embeddings: Any) -> FAISS:
    """
    Process raw text into Document objects and split them into chunks.

    Parameters:
    - text (str): Raw text to process.

    Returns:
    - List[Document]: Processed documents.
    """
    documents = [Document(page_content=text)]
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = text_splitter.split_documents(documents)
    faiss_index = FAISS.from_documents(docs, embeddings)
    return faiss_index



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



def translate_question(question: str, llm: Any):

    prompt = PromptTemplate(
        input_variables=["question"],
        template=
        """Translate this question to English:\n {question}\n\n

        Important: Only return the Translated Question to English
        """,
    )

    rag_chain = (
        RunnablePassthrough()
        | prompt
        | llm
        | StrOutputParser()
    )

    response = rag_chain.invoke({"question": question})

    print("Translated Q: ", response)
    return response


def contains_arabic(text: str) -> bool:
    """Check if the given text contains Arabic characters."""
    arabic_pattern = re.compile("[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+")
    return bool(arabic_pattern.search(text))


def is_safe_sql_query(query):
    """
    Validates if the given SQL query is safe by preventing DELETE, UPDATE, TRUNCATE, DROP, and ALTER operations.

    :param query: SQL query as a string
    :return: Tuple (is_safe, message), where is_safe is a boolean indicating safety
    """
    # Define forbidden SQL keywords
    forbidden_keywords = {"delete", "update", "truncate", "drop", "alter"}
    query_lower = query.strip().lower()

    # Check if query contains any forbidden keywords
    if any(keyword in query_lower for keyword in forbidden_keywords):
        return False, "Error: Unsafe SQL operation detected."

    # Query is safe
    return True, "Query is safe to execute."
