
"""
Simple terminal chat interface
Run with: python -m app.cli_simple
"""

import os
from langchain_core.messages import HumanMessage

from app.graph.graph import create_graph
from app.graph.state import AgentState
from app.utils.session import generate_session_id, generate_user_id
from app.database.postgres import PostgresManager
from app.config import get_settings

# Initialize
settings = get_settings()
graph = create_graph()
db = PostgresManager()

def main():
    """Simple chat loop"""
    print("\n" + "="*60)
    print("Personal Care Product Chatbot - Terminal Chat")
    print("="*60)
    print("Type 'quit' or 'exit' to stop\n")
    
    # Generate session
    session_id = generate_session_id()
    user_id = generate_user_id()
    csv_file = None
    
    print(f"Session ID: {session_id}")
    print(f"User ID: {user_id}\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit']:
                print("\nGoodbye!\n")
                break
            
            # Save user message
            db.save_message(session_id, user_id, "user", user_input, csv_file)
            
            # Initialize state
            initial_state: AgentState = {
                "messages": [HumanMessage(content=user_input)],
                "session_id": session_id,
                "user_id": user_id,
                "csv_file": csv_file,
                "url_to_scrape": None,
                "scraping_complete": False,
                "requires_human_escalation": False,
                "knowledge_base_ready": bool(csv_file)
            }
            
            # Run graph
            config = {"configurable": {"thread_id": session_id}}
            result = graph.invoke(initial_state, config)
            
            # Extract response
            response = result["messages"][-1].content
            csv_file = result.get("csv_file") or csv_file
            
            # Save checkpoint
            db.save_checkpoint(session_id, user_id, result, csv_file)
            
            # Print response
            print(f"\nBot: {response}\n")
            
        except KeyboardInterrupt:
            print("\n\nInterrupted. Type 'quit' to exit.\n")
            continue
        except Exception as e:
            print(f"\nError: {str(e)}\n")
            continue

if __name__ == "__main__":
    main()
