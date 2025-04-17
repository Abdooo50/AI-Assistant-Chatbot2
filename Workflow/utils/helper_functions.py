import ast
import hashlib
import math
import pydoc
import re
import time
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

# Initialize global cache manager
query_cache = {}
CACHE_TTL = 300  # 5 minutes in seconds

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
    elif input_string.startswith("```") and input_string.endswith("```"):
        # Handle case where just ``` is used without sql
        return input_string[3:-3].strip()
    return input_string


def get_cache_key(query: str, params: dict = None, user_id: str = None, user_role: str = None) -> str:
    """
    Generate a unique cache key for a query and its parameters.
    
    Args:
        query: SQL query string
        params: Query parameters
        user_id: User ID for role-specific caching
        user_role: User role for role-specific caching
        
    Returns:
        str: Cache key as MD5 hash
    """
    # Normalize query by removing extra whitespace
    normalized_query = re.sub(r'\s+', ' ', query.strip())
    
    # Create a hash of the query and parameters
    key_parts = [normalized_query]
    if params:
        key_parts.append(str(sorted(params.items())))
    if user_id:
        key_parts.append(str(user_id))
    if user_role:
        key_parts.append(str(user_role))
        
    return hashlib.md5(''.join(key_parts).encode()).hexdigest()


def get_cached_result(query: str, params: dict = None, user_id: str = None, user_role: str = None) -> Optional[Any]:
    """
    Get cached result for a query if available and not expired.
    
    Args:
        query: SQL query string
        params: Query parameters
        user_id: User ID for role-specific caching
        user_role: User role for role-specific caching
        
    Returns:
        Optional[Any]: Cached result or None if not found or expired
    """
    global query_cache
    
    cache_key = get_cache_key(query, params, user_id, user_role)
    
    if cache_key in query_cache:
        entry = query_cache[cache_key]
        # Check if entry is still valid
        if time.time() - entry['timestamp'] < CACHE_TTL:
            print(f"Cache hit for key: {cache_key}")
            return entry['result']
        else:
            # Remove expired entry
            del query_cache[cache_key]
            
    print(f"Cache miss for key: {cache_key}")
    return None


def cache_result(query: str, result: Any, params: dict = None, user_id: str = None, user_role: str = None) -> Any:
    """
    Cache the result of a query.
    
    Args:
        query: SQL query string
        result: Query result to cache
        params: Query parameters
        user_id: User ID for role-specific caching
        user_role: User role for role-specific caching
        
    Returns:
        Any: The result (unchanged)
    """
    global query_cache
    
    cache_key = get_cache_key(query, params, user_id, user_role)
    
    query_cache[cache_key] = {
        'result': result,
        'timestamp': time.time()
    }
    
    # Perform cache maintenance if needed
    if len(query_cache) > 1000:  # Arbitrary limit
        maintain_cache()
        
    return result


def maintain_cache():
    """
    Perform cache maintenance by removing expired entries.
    """
    global query_cache
    
    current_time = time.time()
    expired_keys = [
        k for k, v in query_cache.items() 
        if current_time - v['timestamp'] >= CACHE_TTL
    ]
    
    for key in expired_keys:
        del query_cache[key]


def validate_query_security(query: str) -> Tuple[bool, str]:
    """
    Comprehensive validation of SQL query for security issues.
    
    Args:
        query: SQL query string
        
    Returns:
        Tuple of (is_safe, message)
    """
    # Convert to lowercase for case-insensitive checks
    query_lower = query.strip().lower()
    
    # Check for SQL injection patterns
    sql_injection_patterns = [
        r";\s*select", r";\s*insert", r";\s*update", r";\s*delete",
        r"--", r"/\*", r"\*/", r"xp_", r"sp_", r"exec\s+", r"execute\s+"
    ]
    
    for pattern in sql_injection_patterns:
        if re.search(pattern, query_lower):
            return False, f"Potential SQL injection detected: {pattern}"
    
    # Check for forbidden operations
    forbidden_operations = {
        "delete": "DELETE operations are not allowed",
        "drop": "DROP operations are not allowed",
        "alter": "ALTER operations are not allowed",
        "truncate": "TRUNCATE operations are not allowed",
        "update": "UPDATE operations are not allowed",
        "insert": "INSERT operations are not allowed",
        "create": "CREATE operations are not allowed",
        "exec": "EXEC operations are not allowed"
    }
    
    for operation, message in forbidden_operations.items():
        # Use word boundary to avoid false positives
        if re.search(r'\b' + operation + r'\b', query_lower):
            return False, message
    
    # Validate basic SQL syntax
    try:
        # Simple syntax validation logic
        if not query_lower.startswith("select"):
            return False, "Only SELECT queries are allowed"
            
        # Check for balanced parentheses
        if query.count('(') != query.count(')'):
            return False, "Unbalanced parentheses in query"
    except Exception as e:
        return False, f"Syntax validation error: {str(e)}"
    
    return True, "Query is safe to execute"


def execute_parameterized_query(conn, query: str, params: dict = None, user_id: str = None, user_role: str = None):
    """
    Execute a SQL query using parameterization to prevent SQL injection.
    
    Args:
        conn: Database connection
        query: SQL query with parameter placeholders
        params: Dictionary of parameter values
        user_id: User ID for role-specific caching
        user_role: User role for role-specific caching
        
    Returns:
        Query results or error information
    """
    if query.lower() == "not available":
        return "No data available."
    
    # Check cache first
    cached_result = get_cached_result(query, params, user_id, user_role)
    if cached_result is not None:
        return cached_result
        
    # Validate query before execution
    is_safe, message = validate_query_security(query)
    if not is_safe:
        return f"Blocked due to security policy: {message}"
    
    try:
        with conn.cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            result = cursor.fetchall()
            processed_result = [tuple(row) for row in result]
            
            # Cache the result
            cache_result(query, processed_result, params, user_id, user_role)
            
            return processed_result
    except Exception as e:
        error_result = handle_query_error(e, query)
        return error_result


def handle_query_error(error, query, max_retries=3):
    """
    Enhanced error handling for SQL queries with retry logic and detailed error classification.
    
    Args:
        error: The exception that occurred
        query: The SQL query that caused the error
        max_retries: Maximum number of retry attempts for transient errors
        
    Returns:
        Error message or retry result
    """
    error_str = str(error)
    error_code = getattr(error, 'code', None) or extract_error_code(error_str)
    
    # Classify the error
    error_type = classify_sql_error(error_code, error_str)
    
    # Handle based on error type
    if error_type == "TRANSIENT" and max_retries > 0:
        # Implement exponential backoff
        backoff_time = 2 ** (3 - max_retries)  # 1, 2, 4 seconds
        time.sleep(backoff_time)
        
        # Retry logic would go here in a real implementation
        # For now, just return an error message
        return f"Transient error occurred. Would retry {max_retries} more times in production."
    
    # Format user-friendly error message based on error type
    if error_type == "PERMISSION":
        return {
            "error": "Permission denied",
            "details": "You don't have sufficient permissions to access this data.",
            "suggestions": ["Check your user role", "Request access from administrator"]
        }
    elif error_type == "SYNTAX":
        return {
            "error": "Invalid query syntax",
            "details": f"The query contains syntax errors: {error_str}",
            "suggestions": ["Check column and table names", "Verify SQL syntax"]
        }
    elif error_type == "CONNECTION":
        return {
            "error": "Database connection issue",
            "details": "Unable to connect to the database at this time.",
            "suggestions": ["Try again later", "Contact support if the issue persists"]
        }
    elif error_type == "DATABASE_OBJECT":
        return {
            "error": "Database object not found",
            "details": f"The requested table or view does not exist: {error_str}",
            "suggestions": ["Check table names", "Verify database schema"]
        }
    else:
        # Generic error handling
        return {
            "error": "Query execution failed",
            "details": error_str,
            "suggestions": ["Try simplifying your request", "Contact support for assistance"]
        }


def classify_sql_error(error_code, error_message):
    """
    Classify SQL errors into categories for appropriate handling.
    
    Args:
        error_code: SQL error code if available
        error_message: Error message string
        
    Returns:
        Error type: TRANSIENT, PERMISSION, SYNTAX, CONNECTION, DATABASE_OBJECT, or UNKNOWN
    """
    error_message_lower = error_message.lower()
    
    # SQL Server error codes
    transient_errors = [4060, 40197, 40501, 40613, 49918, 49919, 49920]
    permission_errors = [229, 230, 262, 300, 301, 378]
    syntax_errors = [102, 103, 104, 105, 156, 170]
    connection_errors = [53, 67, 10054, 10060, 40613]
    object_errors = [208, 1, 207, 4902]
    
    if error_code in transient_errors or "timeout" in error_message_lower:
        return "TRANSIENT"
    elif error_code in permission_errors or "permission" in error_message_lower or "access" in error_message_lower:
        return "PERMISSION"
    elif error_code in syntax_errors or "syntax" in error_message_lower:
        return "SYNTAX"
    elif error_code in connection_errors or "connection" in error_message_lower:
        return "CONNECTION"
    elif error_code in object_errors or "invalid object" in error_message_lower or "not found" in error_message_lower:
        return "DATABASE_OBJECT"
    else:
        return "UNKNOWN"


def extract_error_code(error_message):
    """
    Extract error code from error message string.
    
    Args:
        error_message: Error message string
        
    Returns:
        int: Error code if found, None otherwise
    """
    # Look for patterns like (42S02) or [42S02] in error messages
    match = re.search(r'[\(\[](\d+)[\)\]]', error_message)
    if match:
        return int(match.group(1))
    return None


def process_query_results(results, page=1, format_type="default", original_question=None, max_rows_per_page=50):
    """
    Process and format SQL query results for optimal presentation.
    
    Args:
        results: Raw query results
        page: Page number for pagination
        format_type: Formatting style (default, table, json, etc.)
        original_question: The original natural language question
        max_rows_per_page: Maximum rows per page
        
    Returns:
        Processed and formatted results
    """
    # Handle error messages or special cases
    if isinstance(results, str) or isinstance(results, dict):
        return results
        
    # Apply pagination
    start_idx = (page - 1) * max_rows_per_page
    end_idx = start_idx + max_rows_per_page
    paginated_results = results[start_idx:end_idx]
    
    # Apply formatting based on format_type
    if format_type == "table":
        formatted_results = format_as_table(paginated_results)
    elif format_type == "json":
        formatted_results = format_as_json(paginated_results)
    else:
        formatted_results = format_default(paginated_results)
        
    # Add metadata
    result_metadata = {
        "total_rows": len(results),
        "page": page,
        "total_pages": math.ceil(len(results) / max_rows_per_page),
        "rows_per_page": max_rows_per_page,
        "format_type": format_type
    }
    
    # Generate explanation if original question is provided
    explanation = None
    if original_question:
        explanation = generate_result_explanation(paginated_results, original_question)
        
    return {
        "data": formatted_results,
        "metadata": result_metadata,
        "explanation": explanation
    }


def format_as_table(results):
    """
    Format results as a markdown table.
    
    Args:
        results: Query results
        
    Returns:
        str: Markdown table
    """
    if not results:
        return "No results found."
        
    # Assume first row has the same structure as all rows
    # Create header based on column positions
    headers = [f"Column {i+1}" for i in range(len(results[0]))]
    
    # Build markdown table
    table = "| " + " | ".join(headers) + " |\n"
    table += "| " + " | ".join(["---"] * len(headers)) + " |\n"
    
    for row in results:
        table += "| " + " | ".join(str(cell) for cell in row) + " |\n"
        
    return table


def format_as_json(results):
    """
    Format results as JSON.
    
    Args:
        results: Query results
        
    Returns:
        list: List of dictionaries representing rows
    """
    if not results:
        return []
        
    # Convert to list of dictionaries
    json_results = []
    for row in results:
        json_row = {f"column_{i+1}": value for i, value in enumerate(row)}
        json_results.append(json_row)
        
    return json_results


def format_default(results):
    """
    Default formatting for results.
    
    Args:
        results: Query results
        
    Returns:
        str: Formatted results
    """
    if not results:
        return "No results found."
        
    formatted = []
    for row in results:
        formatted.append(", ".join(str(cell) for cell in row))
        
    return "\n".join(formatted)


def generate_result_explanation(results, original_question):
    """
    Generate a natural language explanation of the results.
    
    Args:
        results: Query results
        original_question: Original natural language question
        
    Returns:
        str: Explanation of results
    """
    # This would use the LLM to generate an explanation in a real implementation
    # Simplified implementation for now
    if not results:
        return "No data was found that matches your query."
        
    num_results = len(results)
    return f"Found {num_results} results that answer your question about '{original_question}'."


def execute_query(conn, query, user_id=None, user_role=None):
    """
    Executes an SQL query safely with enhanced security and caching.

    Args:
        conn: The active database connection.
        query (str): The SQL query to execute.
        user_id: User ID for role-specific caching
        user_role: User role for role-specific caching

    Returns:
        list: The query results as a list of tuples or error information.
    """
    return execute_parameterized_query(conn, query, None, user_id, user_role)


def query_as_list(db, query, user_id=None, user_role=None):
    """
    Execute a query and return results as a list with enhanced error handling.
    
    Args:
        db: Database connection
        query: SQL query
        user_id: User ID for role-specific caching
        user_role: User role for role-specific caching
        
    Returns:
        list: Query results or error information
    """
    try:
        cursor = db.cursor()
        cursor.execute(query)
        res = cursor.fetchall() or []  # Ensure it's always a list
        cursor.close()

        print(f"Raw query result: {res}")  # Debugging line

        # Convert rows to a list of tuples (ensuring it's JSON serializable)
        cleaned_rows = [tuple(row) for row in res]
        
        # Cache the result
        cache_result(query, cleaned_rows, None, user_id, user_role)
        
        return cleaned_rows
    except Exception as e:
        return handle_query_error(e, query)


def query_doctors_from_db(db, user_id=None, user_role=None) -> List[Tuple]:
    """
    Query the database for doctor information with dynamic database name.
    
    Args:
        db: Database connection
        user_id: User ID for role-specific caching
        user_role: User role for role-specific caching
        
    Returns:
        List[Tuple]: Doctor information as tuples or error message
    """
    import os
    
    # Get database name from environment variable with fallback
    db_name = os.getenv("MOSEFAK_APP_DATABASE_NAME", "mosefak-management")
    
    # Check if the Doctors table exists before running the complex query
    try:
        test_query = f"""
        SELECT TOP 1 1 
        FROM [{db_name}].[dbo].[Doctors]
        """
        test_result = query_as_list(db, test_query, user_id, user_role)
        
        # If test query returns an error, return it
        if isinstance(test_result, dict) and "error" in test_result:
            return f"Unable to access doctor information: {test_result['details']}"
    except Exception as e:
        return f"Unable to access doctor information: {str(e)}"
    
    # If test query succeeds, run the full query
    try:
        query = f"""
            SELECT 
                'Dr. ' + u.FirstName + ' ' + u.LastName AS DoctorName,
                COALESCE(STRING_AGG(wt.Day, ', '), 'Not available') AS WorkingDays,
                COALESCE(ca.Street, 'Unknown Street') AS Street,
                COALESCE(ca.City, 'Unknown City') AS City,
                COALESCE(ca.Country, 'Unknown Country') AS Country,
                COALESCE(STRING_AGG(CAST(sp.Name AS NVARCHAR(MAX)), ', '), 'No specialization') AS Specializations
            FROM [{db_name}].[dbo].[Doctors] d
            JOIN [{db_name}].[Security].[Users] u ON d.AppUserId = u.Id
            LEFT JOIN [{db_name}].[dbo].[Clinics] ca ON d.Id = ca.DoctorId
            LEFT JOIN [{db_name}].[dbo].[WorkingTimes] wt ON ca.Id = wt.ClinicId
            LEFT JOIN [{db_name}].[dbo].[Specializations] sp ON d.Id = sp.DoctorId
            GROUP BY u.FirstName, u.LastName, ca.Street, ca.City, ca.Country;
        """
        
        query_result = query_as_list(db, query, user_id, user_role)
        
        # Format doctor information into a readable string
        formatted_output = format_doctors(query_result)
        
        return formatted_output
    except Exception as e:
        error_info = handle_query_error(e, query if 'query' in locals() else "Unknown query")
        return f"Error retrieving doctor information: {error_info}"


def format_doctors(doctors) -> str:
    """
    Format doctor information into a human-readable string.
    
    Args:
        doctors: Doctor information as tuples or error message
        
    Returns:
        str: Formatted doctor information
    """
    # Handle case where doctors is an error message or dictionary
    if isinstance(doctors, str):
        return doctors
    if isinstance(doctors, dict) and "error" in doctors:
        return f"Error: {doctors['error']} - {doctors['details']}"
    
    # Handle empty results
    if not doctors:
        return "No doctors available."

    try:
        return "\n".join([
            f"{doctor[0]} is working on {doctor[1]} at {doctor[2]}, {doctor[3]}, {doctor[4]}, specializes in {doctor[5]}"
            for doctor in doctors
        ])
    except Exception as e:
        return f"Error formatting doctor information: {str(e)}"


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
    """
    Translate a question to English.
    
    Args:
        question: Question in any language
        llm: Language model
        
    Returns:
        str: Translated question in English
    """
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
    """
    Check if the given text contains Arabic characters.
    
    Args:
        text: Input text
        
    Returns:
        bool: True if text contains Arabic characters
    """
    arabic_pattern = re.compile("[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+")
    return bool(arabic_pattern.search(text))


def is_safe_sql_query(query):
    """
    Validates if the given SQL query is safe by preventing DELETE, UPDATE, TRUNCATE, DROP, and ALTER operations.
    
    Args:
        query: SQL query as a string
        
    Returns:
        Tuple (is_safe, message), where is_safe is a boolean indicating safety
    """
    return validate_query_security(query)


def classify_query_intent(question: str, llm: Any) -> str:
    """
    Classify the intent of a user's question for better SQL generation.
    
    Args:
        question: User's question
        llm: Language model
        
    Returns:
        str: Query intent classification
    """
    prompt = PromptTemplate(
        input_variables=["question"],
        template=
        """Classify the intent of this database query question into one of these categories:
        - AGGREGATION: Questions asking for counts, sums, averages, etc.
        - FILTERING: Questions asking for specific records matching criteria
        - JOINING: Questions requiring data from multiple tables
        - SORTING: Questions asking for ordered results
        - GROUPING: Questions asking for grouped or categorized data
        - SIMPLE: Simple lookup questions
        
        Question: {question}
        
        Intent:""",
    )

    chain = (
        RunnablePassthrough()
        | prompt
        | llm
        | StrOutputParser()
    )

    response = chain.invoke({"question": question})
    
    # Clean up and normalize the response
    intent = response.strip().upper()
    
    # Map to standard intents
    standard_intents = ["AGGREGATION", "FILTERING", "JOINING", "SORTING", "GROUPING", "SIMPLE"]
    
    for std_intent in standard_intents:
        if std_intent in intent:
            return std_intent
    
    # Default to SIMPLE if no match
    return "SIMPLE"


def get_example_queries(intent: str, user_role: str) -> str:
    """
    Get example queries for a specific intent and user role.
    
    Args:
        intent: Query intent
        user_role: User role
        
    Returns:
        str: Example queries
    """
    examples = {
        "AGGREGATION": {
            "Patient": "How many appointments do I have scheduled?",
            "Doctor": "How many patients did I see last month?",
            "Admin": "What is the average consultation fee across all doctors?"
        },
        "FILTERING": {
            "Patient": "Show me my appointments with Dr. Smith",
            "Doctor": "Show me patients with appointments on Monday",
            "Admin": "List all doctors with more than 5 years of experience"
        },
        "JOINING": {
            "Patient": "What specializations do my doctors have?",
            "Doctor": "Which clinics have my patients visited?",
            "Admin": "Show me doctors and their clinic locations"
        },
        "SORTING": {
            "Patient": "Show my appointments in order of date",
            "Doctor": "List my patients sorted by appointment date",
            "Admin": "Show doctors ordered by years of experience"
        },
        "GROUPING": {
            "Patient": "How many appointments do I have with each doctor?",
            "Doctor": "How many patients do I have in each city?",
            "Admin": "How many doctors do we have in each specialization?"
        },
        "SIMPLE": {
            "Patient": "When is my next appointment?",
            "Doctor": "What is my schedule for today?",
            "Admin": "How many doctors are in the system?"
        }
    }
    
    # Get examples for the intent and role
    role_examples = examples.get(intent, {}).get(user_role, "No examples available")
    
    # Get SQL examples for the intent
    sql_examples = {
        "AGGREGATION": "SELECT COUNT(*) FROM Appointments WHERE AppUserId = @userId",
        "FILTERING": "SELECT * FROM Appointments WHERE DoctorId = 5 AND AppUserId = @userId",
        "JOINING": "SELECT d.Name FROM Doctors d JOIN Appointments a ON d.Id = a.DoctorId WHERE a.AppUserId = @userId",
        "SORTING": "SELECT * FROM Appointments WHERE AppUserId = @userId ORDER BY StartDate",
        "GROUPING": "SELECT DoctorId, COUNT(*) FROM Appointments WHERE AppUserId = @userId GROUP BY DoctorId",
        "SIMPLE": "SELECT TOP 1 * FROM Appointments WHERE AppUserId = @userId ORDER BY StartDate"
    }
    
    sql_example = sql_examples.get(intent, "SELECT * FROM Table")
    
    return f"Example question: '{role_examples}'\nExample SQL: {sql_example}"
