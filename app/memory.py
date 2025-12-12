from typing import Dict, List, Optional
from datetime import datetime
import uuid


class ConversationMemory:
    """
    Manages conversation history for multiple sessions.
    Each session maintains its own memory of messages.
    """
    
    def __init__(self):
        # Structure: {session_id: {"model": str, "messages": List[dict], "created_at": str}}
        self._sessions: Dict[str, dict] = {}
    
    def create_session(self, model: str, session_id: Optional[str] = None, system_prompt: Optional[str] = None) -> str:
        """Create a new conversation session."""
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        self._sessions[session_id] = {
            "model": model,
            "system_prompt": system_prompt,
            "messages": [],
            "documents": [], # List of text chunks or full text
            "created_at": datetime.now().isoformat()
        }
        return session_id
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """Get session data by ID."""
        return self._sessions.get(session_id)
    
    def add_document_text(self, session_id: str, text: str):
        """Add document text to session context."""
        if session_id in self._sessions:
            self._sessions[session_id]["documents"].append(text)

    def get_context(self, session_id: str, query: str) -> str:
        """
        Retrieve relevant context from documents based on query.
        For now, we'll do a simple implementation: return all text if small, 
        or simple keyword matching if large.
        """
        if session_id not in self._sessions:
            return ""
        
        docs = self._sessions[session_id]["documents"]
        if not docs:
            return ""
            
        # Simple strategy: Join all text. 
        # In a real RAG, you'd use embeddings here.
        full_text = "\n\n".join(docs)
        
        # If text is huge, we might want to truncate or filter.
        # For this demo, we'll limit to ~4000 chars to fit in context
        return full_text[:4000]

    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        return session_id in self._sessions
    
    def add_message(self, session_id: str, role: str, content: str) -> bool:
        """Add a message to a session's history."""
        if session_id not in self._sessions:
            return False
        
        self._sessions[session_id]["messages"].append({
            "role": role,
            "content": content
        })
        return True
    
    def get_messages(self, session_id: str) -> List[dict]:
        """Get all messages for a session."""
        if session_id not in self._sessions:
            return []
        return self._sessions[session_id]["messages"]
    
    def get_model(self, session_id: str) -> Optional[str]:
        """Get the model associated with a session."""
        if session_id not in self._sessions:
            return None
        return self._sessions[session_id]["model"]
    
    def clear_session(self, session_id: str) -> bool:
        """Clear all messages in a session but keep the session."""
        if session_id not in self._sessions:
            return False
        self._sessions[session_id]["messages"] = []
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session entirely."""
        if session_id not in self._sessions:
            return False
        del self._sessions[session_id]
        return True
    
    def list_sessions(self) -> List[dict]:
        """List all active sessions."""
        sessions = []
        for session_id, data in self._sessions.items():
            sessions.append({
                "session_id": session_id,
                "model": data["model"],
                "message_count": len(data["messages"]),
                "created_at": data["created_at"]
            })
        return sessions


# Global memory instance
memory = ConversationMemory()
