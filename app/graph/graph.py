from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver
from app.graph.state import AgentState
from app.graph import nodes
from app.config import get_settings

settings = get_settings()

def create_graph():
    """Create the LangGraph workflow"""
    
    # Define the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("check_escalation", nodes.check_escalation_node)
    workflow.add_node("url_extraction", nodes.url_extraction_node)
    workflow.add_node("scraping", nodes.scraping_node)
    workflow.add_node("query_answering", nodes.query_answering_node)
    workflow.add_node("escalation", nodes.escalation_node)
    
    # Define routing logic
    def route_after_escalation_check(state: AgentState):
        if state.get("requires_human_escalation"):
            return "escalation"
        return "url_extraction"
    
    def route_after_url_extraction(state: AgentState):
        if state.get("url_to_scrape") and not state.get("scraping_complete"):
            return "scraping"
        return "query_answering"
    
    # Set entry point
    workflow.set_entry_point("check_escalation")
    
    # Add edges
    workflow.add_conditional_edges(
        "check_escalation",
        route_after_escalation_check,
        {
            "escalation": "escalation",
            "url_extraction": "url_extraction"
        }
    )
    
    workflow.add_conditional_edges(
        "url_extraction",
        route_after_url_extraction,
        {
            "scraping": "scraping",
            "query_answering": "query_answering"
        }
    )
    
    workflow.add_edge("scraping", "query_answering")
    workflow.add_edge("query_answering", END)
    workflow.add_edge("escalation", END)
    
    # Compile with checkpointer
    # Note: PostgresSaver requires additional setup
    graph = workflow.compile()
    
    return graph
