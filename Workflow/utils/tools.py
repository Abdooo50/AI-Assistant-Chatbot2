from langchain_core.vectorstores import InMemoryVectorStore
from langchain.agents.agent_toolkits import create_retriever_tool
from Workflow.utils.helper_functions import query_as_list



def create_proper_noun_retriever_tool(db, embeddings):
    """
    A clean function to retrieve unique values from the database, create a vector store,
    and generate a retriever tool for proper nouns.

    Args:
        db: Database connection object.
        embeddings: Embeddings model for the vector store.

    Returns:
        A retriever tool for searching proper nouns.
    """
    # Retrieve unique values from the database
    unique_values = [
        *query_as_list(db, "SELECT Name FROM Specializations"),
        *query_as_list(db, "SELECT Street + ', ' + City + ', ' + Country FROM ClinicAddresses"),
        *query_as_list(db, "SELECT FirstName + ' ' + LastName FROM Security.Users WHERE Id IN (SELECT AppUserId FROM Doctors)"),
        *query_as_list(db, "SELECT City FROM ClinicAddresses"),
        *query_as_list(db, "SELECT AppointmentStatus FROM Appointments"),
        *query_as_list(db, "SELECT DayOfWeek FROM WorkingTimes"),
        *query_as_list(db, "SELECT Country FROM ClinicAddresses")
    ]

    # Create and populate the vector store
    vector_store = InMemoryVectorStore(embeddings)
    vector_store.add_texts(unique_values)

    # Create the retriever tool
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
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