"""
Terminal-based chat interface for Personal Care Chatbot
Run with: python -m app.cli
"""

import os
import sys
from datetime import datetime
from langchain_core.messages import HumanMessage

from app.graph.graph import create_graph
from app.graph.state import AgentState
from app.utils.session import generate_session_id, generate_user_id
from app.database.postgres import PostgresManager
from app.database.redis_client import RedisClient
from app.config import get_settings

# Initialize
settings = get_settings()
graph = create_graph()
db = PostgresManager()
redis_client = RedisClient()

# ANSI color codes for terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_banner():
    """Print welcome banner"""
    banner = f"""
{Colors.OKCYAN}{Colors.BOLD}
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║        Personal Care Product Chatbot - Terminal            ║
║                                                            ║
║                                                            ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
{Colors.ENDC}
    """
    print(banner)

def print_help():
    """Print help information"""
    help_text = f"""
{Colors.OKGREEN}Available Commands:{Colors.ENDC}
  {Colors.BOLD}/help{Colors.ENDC}     - Show this help message
  {Colors.BOLD}/history{Colors.ENDC}  - Show conversation history
  {Colors.BOLD}/clear{Colors.ENDC}    - Clear the screen
  {Colors.BOLD}/new{Colors.ENDC}      - Start a new conversation
  {Colors.BOLD}/load{Colors.ENDC}     - Load a previous session
  {Colors.BOLD}/sessions{Colors.ENDC} - List all available sessions
  {Colors.BOLD}/status{Colors.ENDC}   - Show session information
  {Colors.BOLD}/exit{Colors.ENDC}     - Exit the chatbot
  {Colors.BOLD}/quit{Colors.ENDC}     - Exit the chatbot

{Colors.OKGREEN}Usage:{Colors.ENDC}
  - Simply type your message and press Enter
  - To scrape a website, provide a URL in your message
  - For offers/returns/refunds, you'll be redirected to support
    """
    print(help_text)

def print_session_info(session_id: str, user_id: str, csv_file: str = None):
    """Print session information"""
    print(f"\n{Colors.OKCYAN}Session Information:{Colors.ENDC}")
    print(f"  Session ID: {Colors.BOLD}{session_id}{Colors.ENDC}")
    print(f"  User ID: {Colors.BOLD}{user_id}{Colors.ENDC}")
    if csv_file and os.path.exists(csv_file):
        print(f"  Knowledge Base: {Colors.OKGREEN}{os.path.basename(csv_file)}{Colors.ENDC}")
    else:
        print(f"  Knowledge Base: {Colors.WARNING}Not loaded{Colors.ENDC}")
    print()

def print_history(session_id: str):
    """Print conversation history"""
    history = db.get_conversation_history(session_id)
    
    if not history:
        print(f"\n{Colors.WARNING}No conversation history found.{Colors.ENDC}\n")
        return
    
    print(f"\n{Colors.OKCYAN}Conversation History:{Colors.ENDC}\n")
    for msg in history:
        timestamp = datetime.fromisoformat(msg['timestamp']).strftime("%H:%M:%S")
        if msg['role'] == 'user':
            print(f"{Colors.BOLD}[{timestamp}] You:{Colors.ENDC}")
            print(f"  {msg['content']}\n")
        elif msg['role'] == 'assistant':
            print(f"{Colors.OKGREEN}[{timestamp}] Bot:{Colors.ENDC}")
            print(f"  {msg['content']}\n")

def list_sessions():
    """List all available sessions"""
    sessions = db.get_all_sessions(limit=20)
    
    if not sessions:
        print(f"\n{Colors.WARNING}No previous sessions found.{Colors.ENDC}\n")
        return None
    
    print(f"\n{Colors.OKCYAN}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}Available Sessions:{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{'='*70}{Colors.ENDC}\n")
    
    for i, session in enumerate(sessions, 1):
        last_updated = datetime.fromisoformat(session['last_updated']).strftime("%Y-%m-%d %H:%M:%S")
        kb_status = f"{Colors.OKGREEN}✓ Has KB{Colors.ENDC}" if session['has_knowledge_base'] else f"{Colors.WARNING}✗ No KB{Colors.ENDC}"
        
        print(f"{Colors.BOLD}{i}.{Colors.ENDC} Session ID: {session['session_id'][:30]}...")
        print(f"   Last updated: {last_updated}")
        print(f"   Knowledge Base: {kb_status}")
        if session['csv_file']:
            print(f"   CSV: {os.path.basename(session['csv_file'])}")
        print()
    
    return sessions

def load_session():
    """Load a previous session"""
    sessions = list_sessions()
    
    if not sessions:
        return None, None, None
    
    while True:
        choice = input(f"\n{Colors.BOLD}Enter session number to load (or 'c' to cancel):{Colors.ENDC} ").strip()
        
        if choice.lower() == 'c':
            return None, None, None
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(sessions):
                selected = sessions[idx]
                
                # Get full session details
                summary = db.get_session_summary(selected['session_id'])
                
                if summary:
                    print(f"\n{Colors.OKGREEN}Loading session...{Colors.ENDC}")
                    print(f"  Session ID: {summary['session_id']}")
                    print(f"  Messages: {summary['message_count']}")
                    print(f"  Preview: {summary['preview']}")
                    
                    return summary['session_id'], summary['user_id'], summary['csv_file']
                else:
                    print(f"{Colors.FAIL}Error loading session.{Colors.ENDC}")
                    return None, None, None
            else:
                print(f"{Colors.FAIL}Invalid choice. Please try again.{Colors.ENDC}")
        except ValueError:
            print(f"{Colors.FAIL}Invalid input. Please enter a number.{Colors.ENDC}")

def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')
# app/cli.py - Update the chat_loop function

# app/cli.py - Update chat_loop function to load history from database

def chat_loop():
    """Main chat loop"""
    # Ask user if they want to load a previous session or start new
    clear_screen()
    print_banner()
    
    print(f"{Colors.OKGREEN}Welcome! Would you like to:{Colors.ENDC}")
    print(f"  1. Start a new conversation")
    print(f"  2. Load a previous session\n")
    
    choice = input(f"{Colors.BOLD}Enter your choice (1 or 2):{Colors.ENDC} ").strip()
    
    if choice == '2':
        session_id, user_id, csv_file = load_session()
        if session_id:
            print(f"\n{Colors.OKGREEN}Session loaded successfully!{Colors.ENDC}")
            input(f"{Colors.BOLD}Press Enter to continue...{Colors.ENDC}")
        else:
            # Start new if loading failed
            session_id = generate_session_id()
            user_id = generate_user_id()
            csv_file = None
    else:
        # Generate new session and user IDs
        session_id = generate_session_id()
        user_id = generate_user_id()
        csv_file = None
    
    # Print session info
    clear_screen()
    print_banner()
    print_session_info(session_id, user_id, csv_file)
    print(f"{Colors.OKGREEN}Type your message or '/help' for commands.{Colors.ENDC}\n")
    
    # Don't maintain in-memory conversation history
    # Always load from database to keep it lightweight
    
    while True:
        try:
            # Get user input
            user_input = input(f"{Colors.BOLD}You:{Colors.ENDC} ").strip()
            
            # Handle empty input
            if not user_input:
                continue
            
            # Handle commands
            if user_input.startswith('/'):
                command = user_input.lower()
                
                if command in ['/exit', '/quit']:
                    print(f"\n{Colors.OKCYAN}Thank you for using Personal Care Chatbot! Goodbye!{Colors.ENDC}\n")
                    sys.exit(0)
                
                elif command == '/help':
                    print_help()
                    continue
                
                elif command == '/history':
                    print_history(session_id)
                    continue
                
                elif command == '/sessions':
                    list_sessions()
                    continue
                
                elif command == '/load':
                    loaded_session_id, loaded_user_id, loaded_csv_file = load_session()
                    if loaded_session_id:
                        session_id = loaded_session_id
                        user_id = loaded_user_id
                        csv_file = loaded_csv_file
                        clear_screen()
                        print_banner()
                        print_session_info(session_id, user_id, csv_file)
                        
                        # Get message count
                        msg_count = len(db.get_conversation_history(session_id))
                        print(f"{Colors.OKGREEN}Session loaded successfully! ({msg_count} messages){Colors.ENDC}\n")
                    continue
                
                elif command == '/clear':
                    clear_screen()
                    print_banner()
                    print_session_info(session_id, user_id, csv_file)
                    continue
                
                elif command == '/new':
                    session_id = generate_session_id()
                    user_id = generate_user_id()
                    csv_file = None
                    clear_screen()
                    print_banner()
                    print_session_info(session_id, user_id)
                    print(f"{Colors.OKGREEN}New conversation started!{Colors.ENDC}\n")
                    continue
                
                elif command == '/status':
                    print_session_info(session_id, user_id, csv_file)
                    continue
                
                else:
                    print(f"{Colors.FAIL}Unknown command. Type '/help' for available commands.{Colors.ENDC}\n")
                    continue
            
            # Save user message
            db.save_message(session_id, user_id, "user", user_input, csv_file)
            
            # Show processing indicator
            print(f"{Colors.OKCYAN}Bot is thinking...{Colors.ENDC}")
            
            # Load conversation history from database (last 20 messages for context)
            conversation_messages = db.get_conversation_messages(session_id, limit=20)
            
            # If current message not in history, add it
            if not conversation_messages or conversation_messages[-1].content != user_input:
                conversation_messages.append(HumanMessage(content=user_input))
            
            # Initialize state with conversation history from database
            initial_state: AgentState = {
                "messages": conversation_messages,  # Loaded from DB
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
            
            # Extract response (last message)
            last_message = result["messages"][-1].content
            csv_file = result.get("csv_file") or csv_file
            
            # Save checkpoint (only stores last 10 messages internally)
            db.save_checkpoint(session_id, user_id, result, csv_file)
            
            # Publish to Redis
            redis_client.publish(f"chat:{session_id}", {
                "user_id": user_id,
                "message": user_input,
                "response": last_message,
                "timestamp": str(datetime.utcnow())
            })
            
            # Print bot response
            print(f"\r{Colors.OKGREEN}{Colors.BOLD}Bot:{Colors.ENDC}")
            print(f"{last_message}\n")
            
        except KeyboardInterrupt:
            print(f"\n\n{Colors.WARNING}Interrupted. Type '/exit' to quit or continue chatting.{Colors.ENDC}\n")
            continue
        
        except Exception as e:
            print(f"\n{Colors.FAIL}Error: {str(e)}{Colors.ENDC}\n")
            import traceback
            traceback.print_exc()
            continue


def load_conversation_history(session_id: str) -> list:
    """Load conversation history from database and convert to LangChain messages"""
    return db.get_conversation_messages(session_id, limit=50)


def main():
    """Entry point"""
    try:
        # Ensure data directory exists
        os.makedirs(settings.data_dir, exist_ok=True)
        
        # Start chat loop
        chat_loop()
    
    except Exception as e:
        print(f"\n{Colors.FAIL}Fatal error: {str(e)}{Colors.ENDC}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
