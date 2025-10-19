from typing import TypedDict, List, Optional, Annotated
from langgraph.graph import MessagesState
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    """State for the chatbot agent"""
    messages: Annotated[List[BaseMessage], operator.add]
    session_id: str
    user_id: str
    csv_file: Optional[str]
    url_to_scrape: Optional[str]
    scraping_complete: bool
    requires_human_escalation: bool
    knowledge_base_ready: bool
