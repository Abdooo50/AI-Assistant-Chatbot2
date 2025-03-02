from langchain_core.vectorstores import InMemoryVectorStore
from langchain.agents.agent_toolkits import create_retriever_tool
from Workflow.utils.helper_functions import query_as_list



def create_proper_noun_retriever_tool(db, embeddings):
    """
    Creates a retriever tool to search for proper nouns (e.g., doctor names, locations, specializations)
    from the SQL Server database using vector embeddings.

    This function:
    1. **Extracts unique values** from relevant tables in the database with human-readable formatting.
    2. **Stores these values in a vector database** for efficient searching.
    3. **Creates a retriever tool** that finds the closest match to a given input.

    Args:
        db: Database connection object.
        embeddings: Embeddings model for the vector store.

    Returns:
        A retriever tool for finding valid proper nouns.
    """

    # Extract unique proper nouns with human-readable formatting
    proper_nouns = [
        # Medical specializations (e.g., "Specialization: Cardiology")
        *query_as_list(db, "SELECT 'Specialization: ' + Name FROM Specializations"),

        # Clinic addresses formatted naturally (SQL Server uses CONCAT for safer string operations)
        *query_as_list(db, """
            SELECT CONCAT('The location of available clinic is in ', ', Street: ' , Street, ', City: ', City, ', Country: ', Country)
            FROM ClinicAddresses
        """),

        # Doctor names with 'Dr.' prefix (ensuring NULL-safe concatenation)
        *query_as_list(db, """
            SELECT CONCAT('Dr. ', FirstName, ' ', LastName) 
            FROM Security.Users 
            WHERE Id IN (SELECT AppUserId FROM Doctors)
        """),

        # Appointment statuses formatted naturally
        *query_as_list(db, "SELECT CONCAT('Appointment Status: ', AppointmentStatus) FROM Appointments"),

        # Days of the week formatted for schedules
        *query_as_list(db, "SELECT CONCAT('Available on: ', DayOfWeek) FROM WorkingTimes"),
    ]

    # Initialize the in-memory vector store and add extracted proper nouns
    vector_store = InMemoryVectorStore(embeddings)
    vector_store.add_texts(proper_nouns)

    # Create a retriever tool for searching valid proper nouns
    retriever = vector_store.as_retriever(search_kwargs={"k": 10})

    # Description for the retriever tool (guiding the model on how to use it)
    description = (
        "Use to look up values to filter on. Input is an approximate spelling "
        "of the proper noun, output is valid proper nouns. Use the noun most "
        "similar to the search."
    )

    return create_retriever_tool(
        retriever,
        name="search_proper_nouns",
        description=description,
    )
