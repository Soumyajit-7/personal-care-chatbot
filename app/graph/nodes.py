from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.graph.state import AgentState
from app.graph.prompts import CHATBOT_SYSTEM_PROMPT, ESCALATION_CHECK_PROMPT, PRODUCT_QUERY_PROMPT
from app.utils.csv_handler import CSVKnowledgeBase
from app.tools.scraper_tool import scrape_website_tool
from app.config import get_settings
from app.database.postgres import PostgresManager
from app.database.redis_client import RedisClient
import os
import re

settings = get_settings()

#Llama 4 Scout model
llm = ChatGroq(
    api_key=settings.groq_api_key, 
    model="meta-llama/llama-4-scout-17b-16e-instruct"
)

db = PostgresManager()
redis_client = RedisClient()

def check_escalation_node(state: AgentState) -> AgentState:
    """Check if query requires human escalation"""
    last_message = state["messages"][-1].content
    
    escalation_keywords = [
        "offer", "discount", "return", "refund", "shipping", 
        "delivery", "order", "complaint", "cancel", "exchange", "policy"
    ]
    
    requires_escalation = any(keyword in last_message.lower() for keyword in escalation_keywords)
    
    state["requires_human_escalation"] = requires_escalation
    return state

def url_extraction_node(state: AgentState) -> AgentState:
    """Extract URL from user message"""
    last_message = state["messages"][-1].content
    
    # Simple URL regex
    url_pattern = r'https?://[^\s]+'
    urls = re.findall(url_pattern, last_message)
    
    if urls:
        state["url_to_scrape"] = urls[0]
    
    return state

def scraping_node(state: AgentState) -> AgentState:
    """Execute scraping if URL is provided"""
    if state.get("url_to_scrape") and not state.get("scraping_complete"):
        from app.utils.session import get_csv_filename
        
        csv_filename = get_csv_filename(state["session_id"], state["user_id"])
        csv_path = os.path.join(settings.data_dir, csv_filename)
        
        try:
            print(f"\n🔍 Scraping node activated")
            print(f"URL: {state['url_to_scrape']}")
            print(f"CSV filename: {csv_filename}")
            
            # Run scraper - FIX: Call the function directly with correct parameters
            result = scrape_website_tool.invoke({
                "url": state["url_to_scrape"],
                "output_filename": csv_filename  # Pass just the filename
            })
            
            state["csv_file"] = csv_path
            state["scraping_complete"] = True
            state["knowledge_base_ready"] = True
            
            # Save checkpoint
            db.save_checkpoint(
                state["session_id"],
                state["user_id"],
                {"csv_file": csv_path, "scraping_complete": True},
                csv_path
            )
            
            # Publish to Redis
            redis_client.publish("scraping_events", {
                "session_id": state["session_id"],
                "status": "completed",
                "csv_file": csv_path
            })
            
            state["messages"].append(AIMessage(content=result))
            
        except Exception as e:
            error_msg = f"❌ Scraping failed: {str(e)}"
            print(error_msg)
            state["messages"].append(AIMessage(content=error_msg))
    
    return state

def query_answering_node(state: AgentState) -> AgentState:
    """Answer user queries using knowledge base"""
    # Get the last user message (not assistant messages)
    last_user_message = None
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_user_message = msg.content
            break
    
    if not last_user_message:
        return state
    
    # Skip if last message was from scraping
    if state.get("scraping_complete") and isinstance(state["messages"][-1], AIMessage):
        return state
    
    # Check if we have a CSV file
    csv_file = state.get("csv_file") or db.get_csv_file_for_session(state["session_id"])
    
    # Build conversation context for the LLM (only last 6 messages to keep it manageable)
    conversation_context = ""
    if len(state["messages"]) > 1:
        # Include last 6 messages for context (3 exchanges)
        recent_messages = state["messages"][-7:-1] if len(state["messages"]) > 7 else state["messages"][:-1]
        conversation_context = "\n\nRecent conversation:\n"
        for msg in recent_messages:
            if isinstance(msg, HumanMessage):
                conversation_context += f"User: {msg.content[:200]}\n"  # Limit message length
            elif isinstance(msg, AIMessage):
                conversation_context += f"Assistant: {msg.content[:200]}\n"  # Limit message length
    
    if csv_file and os.path.exists(csv_file):
        try:
            # Load knowledge base
            kb = CSVKnowledgeBase(csv_file)
            
            # Check for specific queries
            query_lower = last_user_message.lower()
            
            # Handle different query types
            if any(word in query_lower for word in ['best value', 'cheap', 'affordable', 'budget', 'value for money', 'cheapest']):
                products = kb.get_best_value_products(top_n=5)
                query_type = "best value products (sorted by price)"
            
            elif any(word in query_lower for word in ['top rated', 'best rated', 'highest rated', 'best review']):
                products = kb.get_top_rated_products(top_n=5)
                query_type = "top-rated products"
            
            elif any(word in query_lower for word in ['review', 'reviews', 'customer feedback', 'what people say']):
                products = kb.get_products_with_reviews()[:5]
                query_type = "products with customer reviews"
            
            else:
                # Search for relevant products
                products = kb.search_products(last_user_message)
                query_type = "matching products"
            
            if products:
                # Format product data - include new fields
                product_data = "\n\n".join([
                    f"Product {i+1}:\n"
                    f"Name: {p.get('name', 'N/A')}\n"
                    f"Brand: {p.get('brand', 'N/A')}\n"
                    f"Price: {p.get('price', 'N/A')}\n"
                    f"Rating: {p.get('rating', 'N/A')} ({p.get('review_count', 'N/A')} reviews)\n"
                    f"Description: {p.get('description', 'N/A')[:150]}...\n"
                    f"Breadcrumbs: {p.get('breadcrumbs', 'N/A')}\n"
                    f"Link: {p.get('link', 'N/A')}\n"
                    f"Customer Reviews: {p.get('reviews', 'No reviews')[:200]}..."
                    for i, p in enumerate(products[:5])  # Limit to top 5
                ])
                
                prompt = (
                    f"{CHATBOT_SYSTEM_PROMPT.format(knowledge_base_status=f'{len(products)} products available')}"
                    f"{conversation_context}\n\n"
                    f"Here are the {query_type}:\n\n{product_data}\n\n"
                    f"Current User Question: {last_user_message}\n\n"
                    f"Provide a helpful, concise answer considering the conversation history and product data. "
                    f"Include ratings and review information when relevant."
                )
            else:
                summary = kb.get_product_summary()
                prompt = (
                    f"{CHATBOT_SYSTEM_PROMPT.format(knowledge_base_status=summary)}"
                    f"{conversation_context}\n\n"
                    f"Current User Question: {last_user_message}"
                )
        
        except Exception as e:
            print(f"Error in query_answering_node: {e}")
            import traceback
            traceback.print_exc()
            
            prompt = (
                f"{CHATBOT_SYSTEM_PROMPT.format(knowledge_base_status='Error loading product data.')}"
                f"{conversation_context}\n\n"
                f"Current User Question: {last_user_message}"
            )
    else:
        prompt = (
            f"{CHATBOT_SYSTEM_PROMPT.format(knowledge_base_status='No products loaded. Ask user for a website URL.')}"
            f"{conversation_context}\n\n"
            f"Current User Question: {last_user_message}"
        )
    
    try:
        response = llm.invoke([SystemMessage(content=prompt)])
        state["messages"].append(AIMessage(content=response.content))
        
        # Save to database
        db.save_message(
            state["session_id"],
            state["user_id"],
            "assistant",
            response.content,
            csv_file
        )
    except Exception as e:
        error_msg = f"Error generating response: {str(e)}"
        print(error_msg)
        state["messages"].append(AIMessage(content=error_msg))
    
    return state


def escalation_node(state: AgentState) -> AgentState:
    """Handle escalation to human support"""
    escalation_message = (
        f"I understand you need assistance with this matter. "
        f"For queries related to offers, returns, refunds, or other policies, "
        f"please contact our support team at: {settings.support_contact_number}\n\n"
        f"They will be happy to help you with your specific request."
    )
    
    state["messages"].append(AIMessage(content=escalation_message))
    
    # Save to database
    db.save_message(
        state["session_id"],
        state["user_id"],
        "assistant",
        escalation_message,
        state.get("csv_file")
    )
    
    return state
