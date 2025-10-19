
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
import uvicorn

from app.models.schemas import ChatRequest, ChatResponse
from app.graph.graph import create_graph
from app.graph.state import AgentState
from app.utils.session import generate_session_id, generate_user_id
from app.database.postgres import PostgresManager
from app.database.redis_client import RedisClient
from app.config import get_settings

settings = get_settings()
app = FastAPI(title="Personal Care Chatbot API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
graph = create_graph()
db = PostgresManager()
redis_client = RedisClient()

@app.on_event("startup")
async def startup_event():
    print("🚀 Starting Personal Care Chatbot API...")
    print(f"📊 PostgreSQL: {settings.postgres_host}:{settings.postgres_port}")
    print(f"🔴 Redis: {settings.redis_host}:{settings.redis_port}")

@app.get("/")
def read_root():
    return {
        "message": "Personal Care Chatbot API",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/chat",
            "health": "/health",
            "history": "/history/{session_id}"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
# app/main.py - Update the chat endpoint

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """Main chat endpoint"""
    try:
        # Generate IDs if not provided
        session_id = request.session_id or generate_session_id()
        user_id = request.user_id or generate_user_id()
        
        # Save user message to database
        db.save_message(session_id, user_id, "user", request.message)
        
        # Get checkpoint if exists
        checkpoint = db.get_checkpoint(session_id)
        csv_file = checkpoint.get("csv_file") if checkpoint else None
        
        # Load conversation history from database
        history = db.get_conversation_history(session_id, limit=50)
        
        # Convert history to LangChain messages
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
        messages = []
        for msg in history:
            if msg['role'] == 'user':
                messages.append(HumanMessage(content=msg['content']))
            elif msg['role'] == 'assistant':
                messages.append(AIMessage(content=msg['content']))
        
        # Add current message if not already in history
        if not messages or messages[-1].content != request.message:
            messages.append(HumanMessage(content=request.message))
        
        # Initialize state with conversation history
        initial_state: AgentState = {
            "messages": messages,  # Pass full conversation history
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
        last_message = result["messages"][-1].content
        requires_human = result.get("requires_human_escalation", False)
        
        # Save checkpoint
        db.save_checkpoint(
            session_id,
            user_id,
            result,
            result.get("csv_file")
        )
        
        # Publish to Redis (background)
        background_tasks.add_task(
            redis_client.publish,
            f"chat:{session_id}",
            {
                "user_id": user_id,
                "message": request.message,
                "response": last_message,
                "timestamp": str(datetime.utcnow())
            }
        )
        
        return ChatResponse(
            response=last_message,
            session_id=session_id,
            user_id=user_id,
            requires_human=requires_human,
            contact_info=settings.support_contact_number if requires_human else None
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/{session_id}")
async def get_history(session_id: str, limit: int = 50):
    """Get conversation history"""
    try:
        history = db.get_conversation_history(session_id, limit)
        return {"session_id": session_id, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True
    )
