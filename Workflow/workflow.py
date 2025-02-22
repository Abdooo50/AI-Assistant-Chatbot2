from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver # type: ignore
from psycopg_pool import ConnectionPool # type: ignore


from Workflow.utils.nodes import classify_user_intent, generate_answer, question_answer, write_and_execute_query
from Workflow.utils.state import State



class Workflow:
    def __init__(self):
        self.graph_builder = StateGraph(State)
        self.graph_builder.add_node("question_answer", question_answer)
        self.graph_builder.add_node("write_and_execute_query", write_and_execute_query)
        self.graph_builder.add_node("generate_answer", generate_answer)

        self.graph_builder.add_conditional_edges(
            START,
            classify_user_intent,
            {
                "query_related": "write_and_execute_query",
                "medical_related": "question_answer"
            }
        )

        self.graph_builder.add_edge("write_and_execute_query", "generate_answer")
        self.graph_builder.add_edge("question_answer", END)
        self.graph_builder.add_edge("generate_answer", END)

        DB_URI = "postgresql://postgres:12345@localhost:5432/postgres?sslmode=prefer"
        connection_kwargs = {
            "autocommit": True,
            "prepare_threshold": 0,
        }

        self.pool = ConnectionPool(conninfo=DB_URI, max_size=20, kwargs=connection_kwargs)
        self.checkpointer = PostgresSaver(self.pool)
        self.checkpointer.setup()
        self.graph = self.graph_builder.compile(checkpointer=self.checkpointer)
        self.viz_graph = self.graph.get_graph().draw_mermaid_png()

    def get_response(self, question: str) -> str:
        config = {"configurable": {"thread_id": "2"}}
        try:
            events = self.graph.stream(
                {"messages": [{"role": "user", "content": question}]},
                config,
                stream_mode="values",
            )
            
            last_message = None
            for event in events:
                last_message = event["messages"][-1].content
            
            return last_message if last_message else "No results found."
        except Exception as e:
            print(f"An error occurred during workflow execution: {e}")
            return "An error occurred while processing the request."
        

    def visualize_graph(self):
        """
        Visualizes the workflow's StateGraph using Mermaid and displays it as an image.

        This function attempts to use Mermaid's graph rendering capabilities to 
        produce a PNG image of the graph.
        """
        try:
            # Render the graph as a PNG image and display it
            return self.viz_graph
        except Exception as e:
            print(f"Graph visualization failed: {e}")