from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver # type: ignore
from psycopg_pool import ConnectionPool # type: ignore

from Workflow.utils.nodes import (
    classify_user_intent,
    generate_answer,
    question_answer,
    recommend_doctor,
    system_flow_qa,
    write_and_execute_query,
    handle_out_of_scope,
)
from Workflow.utils.state import State



class Workflow:
    def __init__(self, config):
        self.graph_builder = StateGraph(State)
        self.graph_builder.add_node("question_answer", question_answer)
        self.graph_builder.add_sequence([write_and_execute_query, generate_answer])
        self.graph_builder.add_node("system_flow_qa", system_flow_qa)
        self.graph_builder.add_node("recommend_doctor", recommend_doctor)
        self.graph_builder.add_node("handle_out_of_scope", handle_out_of_scope)

        self.graph_builder.add_conditional_edges(
            START,
            classify_user_intent,
            {
                "query_related": "write_and_execute_query",
                "medical_related": "question_answer",
                "system_flow_related": "system_flow_qa",
                "doctor_recommendation_related": "recommend_doctor",
                "out_of_scope": "handle_out_of_scope"
            }
        )

        self.graph_builder.add_edge("write_and_execute_query", "generate_answer")
        self.graph_builder.add_edge("question_answer", END)
        self.graph_builder.add_edge("generate_answer", END)
        self.graph_builder.add_edge("system_flow_qa", END)
        self.graph_builder.add_edge("recommend_doctor", END)
        self.graph_builder.add_edge("handle_out_of_scope", END)

        self.checkpointer = PostgresSaver(config.postgres_pool)
        self.graph = self.graph_builder.compile(checkpointer=self.checkpointer)

    def get_response(self, question: str, payload: dict, config: dict) -> str:
        # Extract user_id from 'nameid' field instead of 'user_id'
        user_id = payload.get("nameid")
        
        # Extract user_role from 'roles' array
        user_role = payload.get("roles")[0] if payload.get("roles") else None
        
        try:
            # Include both user_id and user_role in the input state
            events = self.graph.stream(
                {
                    "messages": [{"role": "user", "content": question}], 
                    "payload": payload,
                    "user_id": user_id,
                    "user_role": user_role
                },
                config,
                stream_mode="values",
            )
  
            last_message = None
            for event in events:
                last_message = event["messages"][-1].content
            
            return last_message if last_message else "No results found."
        except Exception as e:
            print(f"An error occurred during workflow execution: {e}")
            
            # Check if it's an out-of-scope question
            from Workflow.utils.helper_functions import contains_arabic
            
            # Determine language
            is_arabic = contains_arabic(question)
            
            if is_arabic:
                return """
                أنا مساعد طبي مصمم لمساعدتك في المسائل المتعلقة بالصحة. للأسف، لا يمكنني تقديم معلومات حول الأسئلة خارج النطاق الطبي. 
                يمكنني مساعدتك في أمور مثل النصائح الصحية العامة، ومعلومات عن الأعراض، والتوصية بالأطباء المناسبين. 
                هل يمكنني مساعدتك في أي استفسار طبي؟
                """
            else:
                return """
                I'm a medical assistant designed to help you with health-related matters. Unfortunately, I can't provide information about topics outside the medical domain. 
                I can assist you with things like general health advice, information about symptoms, and recommending appropriate doctors. 
                Can I help you with any medical questions?
                """
