from Workflow.utils.config import Config
from Workflow.utils.helper_functions import contains_arabic, create_faiss_index, execute_query, extract_messages, generate_response, query_doctors_from_db, remove_sql_block, retrieve_context, translate_question
from Workflow.utils.tables_info import load_tables_info
from Workflow.utils.vector_store import load_faiss_index
from Workflow.utils.state import State

from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from langsmith import traceable


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
    Uses the LLM to classify the user question into one of four categories:
    - "query_related" for database queries and medical advice.
    - "medical_related" for medical advice or information

    Args:
        state: The current state of the workflow.

    Returns:
        One of the three category strings.
    """

    messages = str(state["messages"][NUMBER_OF_LAST_MESSAGES:])
    structured_conversation = extract_messages(messages)

    question = state["messages"][-1].content

    prompt_template = ChatPromptTemplate([
        (
            "system",
            """
            - **Previous Human AI Messages:**\n {messages}\n

            Based on Previous Human AI Messages Determine the category of the latest user question. The question can belong to one of these four categories:

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

            Respond with one of the following: 'query_related', 'medical_related', 'doctor_recommendation_related', or 'system_flow_related'.
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
def question_answer(state: State):

    print("state['messages']", state["messages"])

    messages = str(state["messages"][NUMBER_OF_LAST_MESSAGES:])
    structured_conversation = extract_messages(messages)

    question = state["messages"][-1].content

    response_langauge = "English"

    is_arabic = contains_arabic(question)

    if is_arabic:
        response_langauge = "Arabic"
        question = translate_question(question=question, llm=llm)

    prompt_template = ChatPromptTemplate([
        (
            "system",
            """
            You are a virtual medical assistant designed to provide general health advices.\n

            - **Previous Human AI Messages:**\n {messages}\n
            {context_text}

            Respond based on the **The guidelines are as follows:**\n

            Scope of Advice:
            - Answering general health inquiries.
            - Offering guidance based on common symptoms.

            Responding to Out-of-Scope Questions:
            If you receive a question outside the scope of your role, respond politely as follows:
            "Sorry, I am designed to provide general health advices. For accurate medical consultation, please reach out to a licensed medical professional."

            Compliance and Privacy:
            - Ensure that advice is general, based on reliable information, and complies with medical regulations.

            Response Style:
            - Respond with kindness and professionalism, maintaining a supportive tone.
            - Respond in {response_langauge}.
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
def write_and_execute_query(state: State):
    """Generate an optimized SQL query, ensuring the database can provide the requested data."""

    payload = state["payload"]
    print("payload in state: ", payload)

    user_role = payload.get("role")
    user_id = payload.get("user_id")

    tables_info = load_tables_info(role=user_role)

    messages = str(state["messages"][NUMBER_OF_LAST_MESSAGES:])
    structured_conversation = extract_messages(messages)


    question = state["messages"][-1].content

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
                - Only allow queries for patients that the doctor is responsible for (e.g., patients with appointments linked to the doctor).
                - Do not allow queries that retrieve personal or sensitive information about patients not associated with the doctor.

                **Context:**
                - **Previous Human AI Messages Context:**\n {messages}\n
                - **Database Schema:**\n {tables_info}\n
                - **Use this user id if needed:**\n {user_id}\n
                - **The Unique Values** context to correct user spelling or use for filters:\n {context}\n\n

                **Expected Output:**
                ```sql
                -- Optimized SQL Query (or "Not Available" if the data is not retrievable)
                ```
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
                - Validate if the requested information can be retrieved using the available databases schema.
                - If the required data is available, generate an optimized SQL Server query.
                - If the databases do not contain relevant tables or fields, return **"Not Available"** as the SQL query.
                - Follow strict SQL Server syntax and best practices.
                - Do **not** provide explanations—return only the SQL query or "Not Available".

                **Context:**
                - **Previous Human AI Messages Context:**\n {messages}\n
                - **Databases Schema:**\n {tables_info}\n
                - **Use this user id if needed:**\n {user_id}\n
                - **The Unique Values** context to correct user spelling or use for filters:\n {context}\n\n

                **Expected Output:**
                **mosefak-app**
                ```sql
                -- Optimized SQL Query (or "Not Available" if the data is not retrievable)
                ```

                **mosefak-management**
                ```sql
                -- Optimized SQL Query (or "Not Available" if the data is not retrievable)
                ```
                """
            ),
            ("user", question)
        ])


    # Query database for doctor information
    proper_nouns = query_doctors_from_db(mosefak_app_db)

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
        "tables_info": tables_info
    }

    print("Messages: ", messages)
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
        state = {"SQLResult": "No data available for this request.", "SQLQuery": "Not Available"}
    else:
        query_result = execute_query(mosefak_app_db, cleaned_query)
        logger.info(f"Mosefak App SQL Result: {query_result}")
        state = {"SQLResult": query_result, "SQLQuery": cleaned_query}

    print("SQL Result:", state["SQLResult"])
    return state



@traceable(metadata={"llm": MODEL_NAME})
def generate_answer(state: State):
    """Generate a professional and structured response, ensuring consistency between the question, query, and result."""
    
    prompt = f"""
    You are a professional AI assistant responding to a client. Your role is to provide clear, accurate, and well-structured answers.

    **Key Responsibilities:**
    - **Answer Generation:**
        - If the SQL result correctly answers the question, provide a **precise and well-structured response**.

    **Client’s Input:**
    - **User Question:** {state["messages"][-1].content}
    - **SQL Result:** {state["SQLResult"]}

    **Response Guidelines:**
    - If the data is correct: Provide a **concise and professional answer**.
    - If the query or result is incorrect: Politely aswer that we didn't find the info you are looking for.
    - Maintain a **professional and reassuring tone**.
    - Respond in the same language as the client's question.
    """

    response = llm.invoke(prompt)
    print("LLM Generated Response:", response)
    return {"messages": [response]}



def system_flow_qa(state: State):

    messages = str(state["messages"][NUMBER_OF_LAST_MESSAGES:])
    structured_conversation = extract_messages(messages)

    question = state["messages"][-1].content

    response_langauge = "English"

    is_arabic = contains_arabic(question)

    if is_arabic:
        response_langauge = "Arabic"
        question = translate_question(question=question, llm=llm)

    faiss_index = load_faiss_index("system_flow")
    context = retrieve_context(faiss_index, question, llm)


    print("retrieval Context:", context)

    prompt = PromptTemplate(
        template="""Answer the question:\n\n {question}\n

        - **The context**: {context}\n
        - **Previous Human AI Messages Context:**\n {messages}\n
        

        - Your answers should be concise and accurate.
        - Respond in {response_langauge}.
        """,
    )

    rag_chain = (
        RunnablePassthrough()
        | prompt
        | llm
    )

    response = rag_chain.invoke({"question": question,"context": context["result"], "messages": structured_conversation, "response_langauge": response_langauge})
    return {"messages": [response]}



@traceable(metadata={"llm": MODEL_NAME})
def recommend_doctor(state: State):
    """
    Analyze user symptoms and recommend a doctor based on specialization and user location.

    Parameters:
    - state (Dict[str, any]): The current state containing user payload and messages.

    Returns:
    - Dict[str, any]: Updated state with the generated response.
    """

    payload = state["payload"]
    messages = str(state["messages"][NUMBER_OF_LAST_MESSAGES:])

    print("Payload in state:", payload)

    user_role = payload.get("role")
    user_id = payload.get("user_id")

    if not user_role or not user_id:
        return {"messages": ["Error: Missing user role or ID."]}


    # tables_info = load_tables_info(role=user_role)
    structured_conversation = extract_messages(messages)

    question = state["messages"][-1].content

    system_message = ChatPromptTemplate.from_messages([
        (
            "system",
            """
            You are a smart medical assistant that helps users find the right doctor based on their symptoms and location.

            **Key Responsibilities:**
            - Analyze the user's symptoms and determine the most relevant medical specializations.
            - Recommend doctors based on their specialization and relevance to the given symptoms.
            - Prioritize doctors near the user, but if no nearby doctor is found, suggest the closest alternative.
            - Provide clear and professional responses, ensuring the user understands why a certain specialization is recommended.
            - If symptoms match multiple specializations, suggest all relevant ones.
            - If the symptoms are vague, ask clarifying questions before making a recommendation.

            **Response Guidelines:**
            - Use a professional but friendly tone.
            - Keep recommendations concise and actionable.
            - Prioritize common medical specializations such as General Practitioner, Dermatologist, Cardiologist, Neurologist, etc.
            - If symptoms suggest a severe condition, advise the user to seek urgent medical care.
            - If no nearby doctor is available, suggest the closest alternative.
            - Respond in the same language as the client's question.

            **Context:**
            - **Previous Human AI Messages Context:**\n {messages}\n
            - **The Unique Values** context to correct user spelling or use for filters:\n {context}\n\n

            **Expected Output:**
            - A structured response recommending the best doctor(s) for the symptoms and their location.
            """
        ),
        ("user", question)
    ])

    # Query database for doctor information
    proper_nouns = query_doctors_from_db(mosefak_app_db)
    faiss_index = create_faiss_index(proper_nouns, embeddings)

    context = retrieve_context(faiss_index, question, llm)

    response = generate_response(system_message=system_message, context=context, messages=structured_conversation, llm=llm)

    print("response:", response)
    return {"messages": [response]}