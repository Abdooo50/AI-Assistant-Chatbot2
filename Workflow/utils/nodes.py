import os
import sys
from dotenv import load_dotenv
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langsmith import traceable

load_dotenv()

from Workflow.utils.config import Config
from Workflow.utils.helper_functions import (
    contains_arabic, create_faiss_index, execute_query, extract_messages, 
    format_doctors, query_doctors_from_db, remove_sql_block, retrieve_context, 
    translate_question, process_query_results, validate_query_security,
    get_cache_key, get_cached_result, cache_result, classify_query_intent,
    get_example_queries, handle_query_error
)
from Workflow.utils.tables_info import load_tables_info
from Workflow.utils.vector_store import load_faiss_index
from Workflow.utils.state import State

import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = Config()

mosefak_app_db = config.mosefak_app_db
llm = config.llm
embeddings = config.embeddings
MODEL_NAME = config.MODEL_NAME

NUMBER_OF_LAST_MESSAGES = config.NUMBER_OF_LAST_MESSAGES

@traceable(metadata={"llm": MODEL_NAME})
def classify_user_intent(state: State) -> str:
    """
    Uses the LLM to classify the user question into one of five categories:
    - "query_related" for database queries and medical advice.
    - "medical_related" for medical advice or information
    - "doctor_recommendation_related" for doctor recommendations
    - "system_flow_related" for UI navigation or system features
    - "out_of_scope" for non-medical questions outside the chatbot's domain

    Args:
        state: The current state of the workflow.

    Returns:
        One of the five category strings.
    """

    messages = str(state["messages"][NUMBER_OF_LAST_MESSAGES:])
    structured_conversation = extract_messages(messages)

    question = state["messages"][-1].content

    prompt_template = ChatPromptTemplate([
        (
            "system",
            """
            - **Previous Human AI Messages:**\n {messages}\n

            Based on Previous Human AI Messages Determine the category of the latest user question. The question can belong to one of these five categories:

            1. **query_related**: The user wants to retrieve or analyze data from the database.
                - Examples:
                    - How many patients visited the clinic last month?
                    - Show me the appointment schedule for Dr. Smith.
                    - List all available doctors next Monday.
                    - I need to know information about my profile

            2. **medical_related**: The user is asking for general medical advice or information.
                - Examples:
                    - What are the symptoms of diabetes?
                    - How can I lower my blood pressure?
                    - What is the treatment for migraines?
                    - Hi, How are you?
                    - Hello!

            3. **doctor_recommendation_related**: The user is describing symptoms and needs a doctor recommendation.
                - Examples:
                    - I have chest pain and feel dizzy. Which doctor should I see?
                    - My child has a rash. Can you recommend a doctor?
                    - I need an eye specialist for blurry vision.
                    - Which doctor should I visit for stomach pain?

            4. **system_flow_related**: The user is asking about UI navigation or system features.
                - Examples:
                    - How do I book an appointment on this app?
                    - Where can I find my medical history in the system?
                    - How do I change my profile settings?
                    - What does the "Notifications" tab do?
                    - How do I log out of the app?
                    
            5. **out_of_scope**: The user is asking about topics unrelated to healthcare, medicine, or the medical system.
                - Examples:
                    - How do I learn programming?
                    - What's the weather like today?
                    - Can you help me with my homework?
                    - Tell me about the history of Egypt.
                    - How do I cook pasta?

            Respond with one of the following: 'query_related', 'medical_related', 'doctor_recommendation_related', 'system_flow_related', or 'out_of_scope'.
            """
        ), 
        ("human", question)
    ])

    chain = (
        {"messages": RunnablePassthrough()}
        | prompt_template
        | llm
        | StrOutputParser()
    )

    response = chain.invoke(structured_conversation)
    state["category"] = response

    print("Query Category: ", state["category"])
    return state["category"]

@traceable(metadata={"llm": MODEL_NAME, "embedding": "FAISS"})
def write_and_execute_query(state: State):
    """
    Enhanced SQL Database Chain with improved performance, security, and user experience.
    
    Enhancements:
    - Query caching
    - Parameterized queries
    - Advanced error handling
    - Result processing and formatting
    - Query intent classification
    """
    # Extract state information
    payload = state["payload"]
    user_role = payload.get("role")
    user_id = payload.get("user_id")
    
    if not user_role or not user_id:
        return {"error": "Missing user role or ID."}
    

    print("user_id: ", user_id)
    print("payload: ", payload)
    print("user_role: ", user_role)
    print("type(user_role): ", type(user_role))
    
    # Load appropriate tables info based on role
    tables_info = load_tables_info(role=user_role)
    
    # Extract conversation history and question
    messages = str(state["messages"][NUMBER_OF_LAST_MESSAGES:])
    structured_conversation = extract_messages(messages)
    question = state["messages"][-1].content
    
    # Check cache for similar questions
    cache_key = f"{user_id}:{user_role}:{question}"
    cached_result = get_cached_result(cache_key)
    
    if cached_result:
        print("Cache hit: Using cached result")
        return cached_result
    
    
    try:
        # Classify query intent for better SQL generation
        query_intent = classify_query_intent(question, llm)
        print(f"Query intent classified as: {query_intent}")
        
        # Get example queries for this intent and role
        examples = get_example_queries(query_intent, user_role)
        
        # Select appropriate prompt template based on user role and query intent
        if user_role == "Patient":
            system_message = ChatPromptTemplate.from_messages([
                (
                    "system",
                    """
                    You are an SQL expert specializing in SQL Server. Your role is to generate only a valid and optimized SQL query based on the user's request.

                    **Key Responsibilities:**
                    - Validate if the requested information can be retrieved using the available database schema.
                    - If the required data is available, generate an optimized SQL Server query.
                    - If the database does not contain relevant tables or fields, return **"Not Available"** as the SQL query.
                    - Follow strict SQL Server syntax and best practices.
                    - Do **not** provide explanations—return only the SQL query or "Not Available".

                    **Restrictions:**
                    - Only allow access to private columns/tables (e.g., [ProblemDescription], [CancellationReason], [IsPaid], [Security].[Users]) if the query includes a filter matching the user's `AppUserId` with their own ID.

                    **Query Intent:** {query_intent}
                    
                    **Context:**
                    - **Previous Human AI Messages Context:**\n {messages}\n
                    - **Database Schema:**\n {tables_info}\n
                    - **Use this user id if needed:**\n {user_id}\n
                    {context_text}

                    **Expected Output:**
                    ```sql
                    ```
                    (or "Not Available" if the data is not retrievable)
                    """
                ),
                ("user", question)
            ])

        elif user_role == "Doctor":
            system_message = ChatPromptTemplate.from_messages([
                (
                    "system",
                    """
                    You are an SQL expert specializing in SQL Server. Your role is to generate only a valid and optimized SQL query based on the user's request.

                    **Key Responsibilities:**
                    - Validate if the requested information can be retrieved using the available database schema.
                    - If the required data is available, generate an optimized SQL Server query.
                    - If the database does not contain relevant tables or fields, return **"Not Available"** as the SQL query.
                    - Follow strict SQL Server syntax and best practices.
                    - Do **not** provide explanations—return only the SQL query or "Not Available".

                    **Restrictions:**
                    - Only allow access to private columns/tables (e.g., [ProblemDescription], [CancellationReason], [IsPaid], [Security].[Users]) if the query includes a filter matching the user's `AppUserId` with their own ID.

                    **Query Intent:** {query_intent}
                    
                    **Context:**
                    - **Previous Human AI Messages Context:**\n {messages}\n
                    - **Database Schema:**\n {tables_info}\n
                    - **Use this user id if needed:**\n {user_id}\n
                    {context_text}

                    **Expected Output:**
                    ```sql
                    ```
                    (or "Not Available" if the data is not retrievable)
                    """
                ),
                ("user", question)
            ])

        elif user_role == "Admin":

            system_message = ChatPromptTemplate.from_messages([
                (
                    "system",
                    """
                    You are an SQL expert specializing in SQL Server. Your role is to generate only a valid and optimized SQL query based on the user's request.

                    **Key Responsibilities:**
                    - Validate if the requested information can be retrieved using the available database schema.
                    - If the required data is available, generate an optimized SQL Server query.
                    - If the database does not contain relevant tables or fields, return **"Not Available"** as the SQL query.
                    - Follow strict SQL Server syntax and best practices.
                    - Do **not** provide explanations—return only the SQL query or "Not Available".

                    **Restrictions:**
                    - Only allow access to private columns/tables (e.g., [ProblemDescription], [CancellationReason], [IsPaid], [Security].[Users]) if the query includes a filter matching the user's `AppUserId` with their own ID.

                    **Query Intent:** {query_intent}
                    
                    **Context:**
                    - **Previous Human AI Messages Context:**\n {messages}\n
                    - **Database Schema:**\n {tables_info}\n
                    - **Use this user id if needed:**\n {user_id}\n
                    {context_text}

                    **Expected Output:**
                    ```sql
                    ```
                    (or "Not Available" if the data is not retrievable)
                    """
                ),
                ("user", question)
            ])

        # Query database for doctor information
        proper_nouns = query_doctors_from_db(mosefak_app_db, user_id, user_role)

        faiss_index = create_faiss_index(proper_nouns, embeddings)

        # Retrieve relevant context using the latest message
        context = retrieve_context(faiss_index, question, llm)

        context_text = (
            f"- **The Unique Values to correct user spelling or use for filters**:\n {context}"
        ) if not any(word in context["result"].lower() for word in ["sorry", "عذرًا", "آسف", "نأسف", "متأسف"]) \
        else ""

        input_data = {
            "messages": structured_conversation,
            "context_text": context_text,
            "user_id": user_id,
            "tables_info": tables_info,
            "context": context,
            "query_intent": query_intent,
            "examples": examples
        }

        print("Messages: ", messages)
        print("________________________________________________________________________")
        print("context_text: ", context_text)

        # Generate response using the chain
        chain = (
            RunnablePassthrough()
            | system_message
            | llm
            | StrOutputParser()
        )

        # Invoke the chain to get the AI-generated response
        response = chain.invoke(input_data)
        logger.info("Successfully retrieved response from chain")

        cleaned_query = remove_sql_block(response)
        logger.info(f"MosefakApp_SQLQuery: {cleaned_query}")

        # If the generated SQL query is "Not Available", return an empty result
        if cleaned_query.strip().lower() == "not available":
            result = {"SQLResult": "No data available for this request.", "SQLQuery": "Not Available"}
            cache_result(cache_key, result)
            return result
        
        # Validate query security
        is_safe, message = validate_query_security(cleaned_query)
        print("validate_query_security: ", message)
        if not is_safe:
            error_result = {
                "SQLResult": f"Query blocked: {message}",
                "SQLQuery": cleaned_query,
                "error": "Security violation"
            }
            return error_result
            
        # Execute the query with enhanced security and caching
        query_result = execute_query(mosefak_app_db, cleaned_query, user_id, user_role)
        
        # Process and format the results
        processed_result = process_query_results(
            query_result, 
            page=1, 
            format_type="default",
            original_question=question
        )
        
        logger.info(f"Mosefak App SQL Result: {processed_result}")
        
        # Prepare the final result
        result = {
            "SQLResult": processed_result,
            "SQLQuery": cleaned_query
        }
        
        # Cache the result
        cache_result(cache_key, result)
        
        return result
        
    except Exception as e:
        # Use enhanced error handling
        error_result = handle_query_error(e, "Unknown query")
        return {"SQLResult": error_result, "SQLQuery": "Error", "error": str(e)}

@traceable(metadata={"llm": MODEL_NAME})
def generate_answer(state: State):
    """
    Generate a professional and structured response with enhanced formatting and explanations.
    
    Enhancements:
    - Context-aware response generation
    - Data visualization suggestions
    - Rich formatting of results
    - Error explanation in user-friendly terms
    """
    # Check if there was an error in the SQL chain
    if "error" in state:
        error_info = state["error"]
        
        # Generate user-friendly error response
        prompt = f"""
        You are a helpful AI assistant. The user asked a question that resulted in an error
        when trying to query the database. Please explain the issue in a friendly and helpful way.
        
        User question: {state["messages"][-1].content}
        
        Error information: {error_info}
        
        Provide a helpful response that:
        1. Acknowledges the issue
        2. Explains what might have gone wrong in simple terms
        3. Suggests alternative approaches or questions
        4. Maintains a professional and friendly tone
        """
        
        response = llm.invoke(prompt)
        return {"messages": [response]}
    
    # Process successful results
    sql_result = state.get("SQLResult", "No results available.")
    sql_query = state.get("SQLQuery", "")
    
    # Determine if results might benefit from visualization
    visualization_suggestion = ""
    if isinstance(sql_result, dict) and "data" in sql_result:
        # Logic to determine if visualization would be helpful
        if isinstance(sql_result["data"], list) and len(sql_result["data"]) > 5:
            visualization_suggestion = "These results might be easier to understand as a chart or graph."
    
    # Check if the original question is in Arabic
    question = state["messages"][-1].content
    is_arabic = contains_arabic(question)
    language_instruction = "Respond in Arabic." if is_arabic else "Respond in English."
    
    prompt = f"""
    You are a professional AI assistant responding to a client. Your role is to provide clear, accurate, 
    and well-structured answers based on database query results.

    **User Question:** {state["messages"][-1].content}
    
    **SQL Query Used:** {sql_query}
    
    **Query Results:** {sql_result}
    
    **Response Guidelines:**
    - Provide a concise and professional answer that directly addresses the user's question
    - Format the information in an easy-to-read manner
    - Highlight the most important insights from the data
    - Maintain a professional and helpful tone
    - {language_instruction}
    {visualization_suggestion}
    """

    response = llm.invoke(prompt)
    print("LLM Generated Response:", response)
    return {"messages": [response]}

@traceable(metadata={"llm": MODEL_NAME})
def question_answer(state: State):
    """
    Provides empathetic and informative medical advice responses to user questions.
    
    Args:
        state: The current state of the workflow.
        
    Returns:
        Updated state with the generated response.
    """
    print("state['messages']", state["messages"])

    messages = str(state["messages"][NUMBER_OF_LAST_MESSAGES:])
    structured_conversation = extract_messages(messages)

    question = state["messages"][-1].content

    response_langauge = "English"

    is_arabic = contains_arabic(question)

    if is_arabic:
        response_langauge = "Arabic"
        question = translate_question(question=question, llm=llm)

    # Enhanced medical advice template with more empathetic and informative guidance
    prompt_template = ChatPromptTemplate([
        (
            "system",
            """
            You are an empathetic virtual medical assistant designed to provide helpful general health information and guidance.

            - **Previous Human AI Messages:**\n {messages}\n
            {context_text}

            **Approach to Medical Questions:**
            - Begin by acknowledging the user's concern with empathy and understanding
            - Provide clear, accurate, and evidence-based general health information
            - Structure your responses in easy-to-read paragraphs with a logical flow
            - Use a conversational, warm tone while maintaining professionalism
            - When appropriate, explain both what to do and why it helps
            - For common conditions like headaches, provide comprehensive information about possible causes, self-care strategies, and when to seek professional help

            **Scope of Advice:**
            - Provide general health information and educational content
            - Offer evidence-based self-care suggestions for common conditions
            - Explain general concepts about symptoms, treatments, and prevention
            - Discuss lifestyle factors that may impact health conditions
            - Suggest when professional medical care should be sought

            **Medical Disclaimers:**
            - Include appropriate disclaimers without making them sound robotic
            - Integrate disclaimers naturally into your helpful response
            - Make it clear that your information is general and not a substitute for professional medical advice

            **Out-of-Scope Questions:**
            If you receive a question outside your scope, respond with empathy first, then explain:
            "I understand your concern about [specific concern]. While I can provide general information about health topics, I'm not able to provide personalized medical advice, diagnosis, or treatment recommendations. For your specific situation, it would be best to consult with a healthcare professional who can evaluate your individual circumstances."

            **Response Style:**
            - Be conversational and natural, as if having a helpful discussion
            - Show empathy for the user's concerns or symptoms
            - Use clear, non-technical language when possible
            - Explain medical terms when you need to use them
            - Balance being informative with being concise
            - Respond in {response_langauge}
            """
        ), 
        ("user", question)
    ])

    faiss_index = load_faiss_index("faiss_index")
    context = retrieve_context(faiss_index, question, llm)
    
    sorry_words = ["sorry", "عذرًا", "آسف", "نأسف", "متأسف"]  
    context_text = (  
        f"- The Result from our data:\n {context['result']}" 
    ) if not any(word in context["result"].lower() for word in sorry_words) else " "

    print("Retrieved Context: ", context["result"])

    chain = (
        RunnablePassthrough()
        | prompt_template
        | llm
    )

    response = chain.invoke({"context_text": context_text, "messages": structured_conversation, "response_langauge": response_langauge})

    return {"messages": [response]}

@traceable(metadata={"llm": MODEL_NAME})
def recommend_doctor(state: State):
    """
    Recommends appropriate doctors based on user symptoms with enhanced error handling.
    
    Args:
        state: The current state of the workflow.
        
    Returns:
        Updated state with the generated response.
    """
    messages = str(state["messages"][NUMBER_OF_LAST_MESSAGES:])
    structured_conversation = extract_messages(messages)

    question = state["messages"][-1].content

    response_langauge = "English"

    is_arabic = contains_arabic(question)

    if is_arabic:
        response_langauge = "Arabic"
        question = translate_question(question=question, llm=llm)

    try:
        # Get database name from environment variable with fallback
        db_name = os.getenv("MOSEFAK_APP_DATABASE_NAME", "mosefak-management")
        
        # Query doctors from database with enhanced error handling
        doctors_info = query_doctors_from_db(mosefak_app_db)
        
        # Check if we got an error message back
        if isinstance(doctors_info, str) and ("error" in doctors_info.lower() or "unable to access" in doctors_info.lower()):
            # Handle database error with appropriate language response
            if is_arabic:
                return {"messages": [f"""
                عذراً، لا يمكنني الوصول إلى قاعدة البيانات في الوقت الحالي للحصول على المعلومات المطلوبة.

                إذا كنت تبحث عن توصية طبيب لصداع، فبشكل عام، يمكن أن يساعدك طبيب الأعصاب أو طبيب الأسرة.

                للصداع، قد تساعد بعض النصائح العامة مثل:
                - شرب الكثير من الماء
                - أخذ قسط من الراحة في غرفة هادئة ومظلمة
                - تجنب مسببات الصداع مثل الضوضاء الصاخبة أو الإضاءة الساطعة

                إذا كان الصداع شديداً أو مستمراً، يرجى استشارة طبيب في أقرب وقت ممكن.
                """]}
            else:
                return {"messages": [f"""
                I'm sorry, I cannot access the database at the moment to retrieve the requested information.

                If you're looking for a doctor recommendation for a headache, generally, a neurologist or family physician can help you.

                For headaches, some general advice that might help includes:
                - Drinking plenty of water
                - Taking rest in a quiet, dark room
                - Avoiding headache triggers like loud noise or bright lights

                If the headache is severe or persistent, please consult a doctor as soon as possible.
                """]}
    
        # Enhanced doctor recommendation template with more empathetic and informative guidance
        prompt_template = ChatPromptTemplate([
            (
                "system",
                f"""
                You are an empathetic medical assistant specializing in doctor recommendations.

                - **Previous Human AI Messages:**\n {{messages}}\n
                - **Available Doctors Information:**\n {doctors_info}\n

                **Approach to Doctor Recommendations:**
                - Begin by acknowledging the user's health concern with empathy
                - Based on their symptoms, identify the most appropriate medical specialty
                - Recommend specific doctors from the available list who match their needs
                - If no perfect match exists, suggest the closest appropriate specialist
                - Provide a brief explanation of why this type of doctor is appropriate for their condition
                - Include practical information about the recommended doctors (location, working days)

                **When No Doctors Are Available:**
                - Acknowledge the user's concern with empathy
                - Explain what type of specialist would typically help with their symptoms
                - Provide general self-care advice for their condition
                - Suggest when they should seek urgent medical care
                - Offer guidance on finding appropriate specialists elsewhere

                **Response Style:**
                - Be conversational and warm while maintaining professionalism
                - Structure your response in clear, easy-to-read paragraphs
                - Use simple, non-technical language when possible
                - Show genuine concern for the user's wellbeing
                - Respond in {response_langauge}
                """
            ), 
            ("user", question)
        ])

        chain = (
            RunnablePassthrough()
            | prompt_template
            | llm
        )

        response = chain.invoke({"messages": structured_conversation})

        return {"messages": [response]}
        
    except Exception as e:
        # Fallback response in case of errors
        error_message = str(e)
        print(f"Error in recommend_doctor: {error_message}")
        
        if is_arabic:
            return {"messages": ["""
            عذراً، حدث خطأ أثناء محاولة الوصول إلى معلومات الأطباء. 

            للحصول على توصية طبية مناسبة، يرجى استشارة طبيب الرعاية الأولية الذي يمكنه توجيهك إلى الأخصائي المناسب.

            نأسف على هذا الانقطاع في الخدمة.
            """]}
        else:
            return {"messages": ["""
            I apologize, but there was an error while trying to access doctor information.

            For an appropriate medical recommendation, please consult with a primary care physician who can direct you to the right specialist.

            We apologize for this service interruption.
            """]}

@traceable(metadata={"llm": MODEL_NAME})
def system_flow_qa(state: State):
    """
    Handles system-related questions with enhanced error handling and multilingual support.
    
    Args:
        state: The current state of the workflow.
        
    Returns:
        Updated state with the generated response.
    """
    messages = str(state["messages"][NUMBER_OF_LAST_MESSAGES:])
    structured_conversation = extract_messages(messages)

    question = state["messages"][-1].content

    response_langauge = "English"

    is_arabic = contains_arabic(question)

    if is_arabic:
        response_langauge = "Arabic"
        question = translate_question(question=question, llm=llm)

    try:
        faiss_index = load_faiss_index("system_flow")
        context = retrieve_context(faiss_index, question, llm)

        print("retrieval Context:", context)

        prompt_template = ChatPromptTemplate([
            (
                "system",
                """
                You are a helpful assistant specializing in explaining how to use the medical system.

                - **Previous Human AI Messages:**\n {messages}\n
                - **System Information:**\n {context}\n

                **Approach to System Questions:**
                - Provide clear, step-by-step instructions for using system features
                - Include specific UI navigation details when relevant
                - Use a friendly, patient tone as if guiding a new user
                - Structure your response in a logical sequence
                - For complex processes, break down into numbered steps

                **Response Style:**
                - Be concise but thorough
                - Use simple, non-technical language
                - Include practical examples when helpful
                - Respond in {response_langauge}
                """
            ), 
            ("user", question)
        ])

        chain = (
            RunnablePassthrough()
            | prompt_template
            | llm
        )

        response = chain.invoke({"messages": structured_conversation, "context": context["result"], "response_langauge": response_langauge})

        return {"messages": [response]}
        
    except Exception as e:
        # Fallback response in case of errors
        error_message = str(e)
        print(f"Error in system_flow_qa: {error_message}")
        
        if is_arabic:
            return {"messages": ["""
            عذراً، حدث خطأ أثناء محاولة الوصول إلى معلومات النظام.

            للحصول على مساعدة في استخدام النظام، يرجى الاتصال بفريق الدعم الفني أو مراجعة دليل المستخدم.

            نأسف على هذا الانقطاع في الخدمة.
            """]}
        else:
            return {"messages": ["""
            I apologize, but there was an error while trying to access system information.

            For help using the system, please contact technical support or refer to the user manual.

            We apologize for this service interruption.
            """]}

@traceable(metadata={"llm": MODEL_NAME})
def handle_out_of_scope(state: State):
    """
    Handles questions that are outside the medical domain of the chatbot.
    Provides a friendly response explaining the chatbot's purpose and limitations.
    
    Args:
        state: The current state of the workflow.
        
    Returns:
        Updated state with the generated response.
    """
    print("Handling out-of-scope question")
    
    question = state["messages"][-1].content
    
    # Determine language
    is_arabic = contains_arabic(question)
    response_language = "Arabic" if is_arabic else "English"
    
    # Template for out-of-scope responses
    prompt_template = ChatPromptTemplate([
        (
            "system",
            """
            You are a medical assistant chatbot that specializes in health-related topics.
            The user has asked a question that is outside your medical domain.
            
            Respond with a polite, friendly message explaining that you're a medical assistant
            and can only help with health-related questions. Suggest that they ask you about
            medical topics instead.
            
            Use these guidelines:
            1. Be polite and respectful
            2. Clearly explain your purpose as a medical assistant
            3. Suggest some medical topics you can help with
            4. Do not attempt to answer the non-medical question
            5. Respond in the same language as the user's question
            
            For Arabic questions, use this template:
            "أنا مساعد طبي مصمم لمساعدتك في المسائل المتعلقة بالصحة. للأسف، لا يمكنني تقديم معلومات حول [موضوع السؤال]. 
            يمكنني مساعدتك في أمور مثل النصائح الصحية العامة، ومعلومات عن الأعراض، والتوصية بالأطباء المناسبين. 
            هل يمكنني مساعدتك في أي استفسار طبي؟"
            
            For English questions, use this template:
            "I'm a medical assistant designed to help you with health-related matters. Unfortunately, I can't provide information about [question topic]. 
            I can assist you with things like general health advice, information about symptoms, and recommending appropriate doctors. 
            Can I help you with any medical questions?"
            
            Replace [question topic] or [موضوع السؤال] with the specific topic of the user's question.
            """
        ),
        ("user", question)
    ])
    
    chain = (
        RunnablePassthrough()
        | prompt_template
        | llm
    )
    
    response = chain.invoke({})
    
    return {"messages": [response]}

@traceable(metadata={"llm": MODEL_NAME})
def handle_api_quota_exceeded(state: State):
    """
    Handles cases where the API quota has been exceeded.
    Provides a friendly response explaining the issue and suggesting to try again later.
    
    Args:
        state: The current state of the workflow.
        
    Returns:
        Updated state with the generated response.
    """
    question = state["messages"][-1].content
    
    # Determine language
    is_arabic = contains_arabic(question)
    
    if is_arabic:
        response = """
        عذراً، لا يمكنني معالجة طلبك في الوقت الحالي بسبب الوصول إلى الحد الأقصى لاستخدام واجهة برمجة التطبيقات.
        
        يرجى المحاولة مرة أخرى بعد بضع دقائق. نحن نعمل على توسيع قدراتنا لخدمتك بشكل أفضل.
        
        شكراً لتفهمك.
        """
    else:
        response = """
        I'm sorry, I cannot process your request at the moment due to reaching the API usage limit.
        
        Please try again in a few minutes. We're working on expanding our capacity to serve you better.
        
        Thank you for your understanding.
        """
    
    return {"messages": [response]}

@traceable(metadata={"llm": MODEL_NAME})
def handle_database_error(state: State):
    """
    Handles cases where there is an error accessing the database.
    Provides a friendly response explaining the issue and offering alternative help.
    
    Args:
        state: The current state of the workflow.
        
    Returns:
        Updated state with the generated response.
    """
    question = state["messages"][-1].content
    
    # Determine language
    is_arabic = contains_arabic(question)
    
    if is_arabic:
        response = """
        عذراً، لا يمكنني الوصول إلى قاعدة البيانات في الوقت الحالي للحصول على المعلومات المطلوبة.
        
        يرجى المحاولة مرة أخرى لاحقاً. إذا كنت بحاجة إلى مساعدة عاجلة، يرجى الاتصال بفريق الدعم الفني.
        
        شكراً لتفهمك.
        """
    else:
        response = """
        I'm sorry, I cannot access the database at the moment to retrieve the requested information.
        
        Please try again later. If you need urgent assistance, please contact technical support.
        
        Thank you for your understanding.
        """
    
    return {"messages": [response]}

@traceable(metadata={"llm": MODEL_NAME})
def handle_error(state: State):
    """
    Handles general errors that may occur during processing.
    Provides a friendly response explaining that an error occurred.
    
    Args:
        state: The current state of the workflow.
        
    Returns:
        Updated state with the generated response.
    """
    question = state["messages"][-1].content
    
    # Determine language
    is_arabic = contains_arabic(question)
    
    if is_arabic:
        response = """
        عذراً، حدث خطأ أثناء معالجة طلبك. يرجى المحاولة مرة أخرى لاحقاً.
        
        إذا استمرت المشكلة، يرجى الاتصال بفريق الدعم الفني.
        
        شكراً لتفهمك.
        """
    else:
        response = """
        I'm sorry, an error occurred while processing your request. Please try again later.
        
        If the problem persists, please contact technical support.
        
        Thank you for your understanding.
        """
    
    return {"messages": [response]}
