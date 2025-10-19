from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import List, Dict, Optional, Any
import json
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from app.config import get_settings

settings = get_settings()
Base = declarative_base()

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), index=True, nullable=False)
    user_id = Column(String(100), index=True, nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    csv_file = Column(String(255), nullable=True)
    meta_data = Column(JSON, nullable=True)

class Checkpoint(Base):
    __tablename__ = "checkpoints"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(String(100), index=True, nullable=False)
    state = Column(JSON, nullable=False)
    csv_file = Column(String(255), nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PostgresManager:
    def __init__(self):
        self.engine = create_engine(settings.database_url, pool_pre_ping=True)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def _serialize_message(self, msg: BaseMessage) -> Dict:
        """Convert LangChain message to JSON-serializable dict"""
        return {
            "type": msg.__class__.__name__,
            "content": msg.content,
            "additional_kwargs": msg.additional_kwargs if hasattr(msg, 'additional_kwargs') else {},
            "response_metadata": msg.response_metadata if hasattr(msg, 'response_metadata') else {}
        }
    
    def _deserialize_message(self, msg_dict: Dict) -> BaseMessage:
        """Convert dict back to LangChain message"""
        msg_type = msg_dict.get("type", "HumanMessage")
        content = msg_dict.get("content", "")
        
        if msg_type == "HumanMessage":
            return HumanMessage(content=content)
        elif msg_type == "AIMessage":
            return AIMessage(content=content)
        elif msg_type == "SystemMessage":
            return SystemMessage(content=content)
        else:
            return HumanMessage(content=content)
    
    def _serialize_state(self, state: Dict, max_messages: int = 10) -> Dict:
        """
        Serialize state for JSON storage with message limit.
        We don't store all messages in checkpoint - only recent ones.
        Full history is stored in conversations table.
        """
        serialized = {}
        for key, value in state.items():
            if key == "messages" and isinstance(value, list):
                # Only keep last N messages in checkpoint
                recent_messages = value[-max_messages:] if len(value) > max_messages else value
                serialized[key] = [self._serialize_message(msg) for msg in recent_messages]
            elif isinstance(value, BaseMessage):
                serialized[key] = self._serialize_message(value)
            else:
                serialized[key] = value
        return serialized
    
    def _deserialize_state(self, state: Dict) -> Dict:
        """Deserialize state from JSON storage"""
        deserialized = {}
        for key, value in state.items():
            if key == "messages" and isinstance(value, list):
                # Deserialize messages
                deserialized[key] = [self._deserialize_message(msg) for msg in value]
            elif isinstance(value, dict) and "type" in value and value["type"].endswith("Message"):
                deserialized[key] = self._deserialize_message(value)
            else:
                deserialized[key] = value
        return deserialized
    
    def save_checkpoint(self, session_id: str, user_id: str, state: Dict, csv_file: Optional[str] = None):
        """
        Save graph checkpoint with lightweight state.
        Only stores last 10 messages to avoid memory issues.
        Full conversation history is in conversations table.
        """
        session = self.SessionLocal()
        try:
            # Serialize with message limit (last 10 messages only)
            serialized_state = self._serialize_state(state, max_messages=10)
            
            checkpoint = session.query(Checkpoint).filter(Checkpoint.session_id == session_id).first()
            if checkpoint:
                checkpoint.state = serialized_state
                checkpoint.csv_file = csv_file
                checkpoint.last_updated = datetime.utcnow()
            else:
                checkpoint = Checkpoint(
                    session_id=session_id,
                    user_id=user_id,
                    state=serialized_state,
                    csv_file=csv_file
                )
                session.add(checkpoint)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error saving checkpoint: {e}")
        finally:
            session.close()
    
    def get_conversation_messages(self, session_id: str, limit: int = 50) -> List[BaseMessage]:
        """
        Get conversation messages as LangChain message objects.
        This is the proper way to load conversation history.
        """
        history = self.get_conversation_history(session_id, limit)
        messages = []
        
        for msg in history:
            if msg['role'] == 'user':
                messages.append(HumanMessage(content=msg['content']))
            elif msg['role'] == 'assistant':
                messages.append(AIMessage(content=msg['content']))
            elif msg['role'] == 'system':
                messages.append(SystemMessage(content=msg['content']))
        
        return messages
    
    def save_message(self, session_id: str, user_id: str, role: str, content: str, csv_file: Optional[str] = None):
        """Save a conversation message"""
        session = self.SessionLocal()
        try:
            message = Conversation(
                session_id=session_id,
                user_id=user_id,
                role=role,
                content=content,
                csv_file=csv_file
            )
            session.add(message)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error saving message: {e}")
        finally:
            session.close()
    
    def get_conversation_history(self, session_id: str, limit: int = 50) -> List[Dict]:
        """Retrieve conversation history"""
        session = self.SessionLocal()
        try:
            messages = session.query(Conversation)\
                .filter(Conversation.session_id == session_id)\
                .order_by(Conversation.timestamp.desc())\
                .limit(limit)\
                .all()
            return [{
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "csv_file": msg.csv_file
            } for msg in reversed(messages)]
        except Exception as e:
            print(f"Error retrieving history: {e}")
            return []
        finally:
            session.close()
    
    # def save_checkpoint(self, session_id: str, user_id: str, state: Dict, csv_file: Optional[str] = None):
    #     """Save graph checkpoint"""
    #     session = self.SessionLocal()
    #     try:
    #         # Serialize the state before saving
    #         serialized_state = self._serialize_state(state)
            
    #         checkpoint = session.query(Checkpoint).filter(Checkpoint.session_id == session_id).first()
    #         if checkpoint:
    #             checkpoint.state = serialized_state
    #             checkpoint.csv_file = csv_file
    #             checkpoint.last_updated = datetime.utcnow()
    #         else:
    #             checkpoint = Checkpoint(
    #                 session_id=session_id,
    #                 user_id=user_id,
    #                 state=serialized_state,
    #                 csv_file=csv_file
    #             )
    #             session.add(checkpoint)
    #         session.commit()
    #     except Exception as e:
    #         session.rollback()
    #         print(f"Error saving checkpoint: {e}")
    #     finally:
    #         session.close()
    
    def get_checkpoint(self, session_id: str) -> Optional[Dict]:
        """Retrieve graph checkpoint"""
        session = self.SessionLocal()
        try:
            checkpoint = session.query(Checkpoint).filter(Checkpoint.session_id == session_id).first()
            if checkpoint:
                # Deserialize the state when retrieving
                deserialized_state = self._deserialize_state(checkpoint.state)
                return {
                    "state": deserialized_state,
                    "csv_file": checkpoint.csv_file,
                    "last_updated": checkpoint.last_updated.isoformat()
                }
            return None
        except Exception as e:
            print(f"Error retrieving checkpoint: {e}")
            return None
        finally:
            session.close()
    
    def get_csv_file_for_session(self, session_id: str) -> Optional[str]:
        """Get the CSV file associated with a session"""
        session = self.SessionLocal()
        try:
            checkpoint = session.query(Checkpoint).filter(Checkpoint.session_id == session_id).first()
            return checkpoint.csv_file if checkpoint else None
        except Exception as e:
            print(f"Error getting CSV file: {e}")
            return None
        finally:
            session.close()

    def get_all_sessions(self, limit: int = 20) -> List[Dict]:
        """Get all recent sessions with their details"""
        session = self.SessionLocal()
        try:
            checkpoints = session.query(Checkpoint)\
                .order_by(Checkpoint.last_updated.desc())\
                .limit(limit)\
                .all()
            
            return [{
                "session_id": cp.session_id,
                "user_id": cp.user_id,
                "csv_file": cp.csv_file,
                "last_updated": cp.last_updated.isoformat(),
                "has_knowledge_base": bool(cp.csv_file and os.path.exists(cp.csv_file))
            } for cp in checkpoints]
        except Exception as e:
            print(f"Error getting sessions: {e}")
            return []
        finally:
            session.close()
    
    def get_sessions_by_user(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get sessions for a specific user"""
        session = self.SessionLocal()
        try:
            checkpoints = session.query(Checkpoint)\
                .filter(Checkpoint.user_id == user_id)\
                .order_by(Checkpoint.last_updated.desc())\
                .limit(limit)\
                .all()
            
            return [{
                "session_id": cp.session_id,
                "csv_file": cp.csv_file,
                "last_updated": cp.last_updated.isoformat(),
                "has_knowledge_base": bool(cp.csv_file and os.path.exists(cp.csv_file))
            } for cp in checkpoints]
        except Exception as e:
            print(f"Error getting user sessions: {e}")
            return []
        finally:
            session.close()
    
    def get_session_summary(self, session_id: str) -> Optional[Dict]:
        """Get a summary of a session"""
        session = self.SessionLocal()
        try:
            checkpoint = session.query(Checkpoint).filter(Checkpoint.session_id == session_id).first()
            if not checkpoint:
                return None
            
            # Get message count
            msg_count = session.query(Conversation)\
                .filter(Conversation.session_id == session_id)\
                .count()
            
            # Get first message
            first_msg = session.query(Conversation)\
                .filter(Conversation.session_id == session_id)\
                .order_by(Conversation.timestamp.asc())\
                .first()
            
            return {
                "session_id": session_id,
                "user_id": checkpoint.user_id,
                "csv_file": checkpoint.csv_file,
                "last_updated": checkpoint.last_updated.isoformat(),
                "message_count": msg_count,
                "preview": first_msg.content[:100] if first_msg else "No messages",
                "has_knowledge_base": bool(checkpoint.csv_file and os.path.exists(checkpoint.csv_file))
            }
        except Exception as e:
            print(f"Error getting session summary: {e}")
            return None
        finally:
            session.close()