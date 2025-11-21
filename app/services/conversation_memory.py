from typing import List, Dict

class ConversationMemory:
    """Simple session-based conversation memory with buffer limit."""
    
    def __init__(self, max_messages: int = 10):
        self.sessions = {}  # {session_id: [messages]}
        self.max_messages = max_messages
    
    def add_message(self, session_id: str, role: str, content: str):
        """Add a message to session history.
        
        Args:
            session_id: Unique identifier for the conversation session
            role: 'user' or 'assistant'
            content: The message content
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        self.sessions[session_id].append({
            "role": role,
            "content": content
        })
        
        # Keep only last N messages (buffer memory)
        if len(self.sessions[session_id]) > self.max_messages:
            self.sessions[session_id] = self.sessions[session_id][-self.max_messages:]
    
    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get conversation history for a session.
        
        Returns:
            List of messages in format: [{"role": "user", "content": "..."}]
        """
        return self.sessions.get(session_id, [])
    
    def clear_session(self, session_id: str):
        """Clear history for a specific session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def get_recent_context(self, session_id: str, num_messages: int = 5) -> str:
        """Get recent messages as a formatted string for context.
        
        Args:
            session_id: Session to get context from
            num_messages: Number of recent messages to include
            
        Returns:
            Formatted string of recent conversation
        """
        history = self.get_history(session_id)
        recent = history[-num_messages:] if history else []
        
        if not recent:
            return ""
        
        context_parts = []
        for msg in recent:
            prefix = "User:" if msg["role"] == "user" else "Assistant:"
            context_parts.append(f"{prefix} {msg['content']}")
        
        return "\n".join(context_parts)