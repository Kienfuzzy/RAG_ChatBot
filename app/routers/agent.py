from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.services.query_agent import QueryAgent
from app.services.qdrant_service import QdrantService
from app.services.elasticsearch_service import ElasticsearchService
from app.services.openai_service import OpenAIService
from app.services.conversation_memory import ConversationMemory
from app.services.mysql_service import MySQLService

router = APIRouter(prefix="/agent", tags=["agent"])

# Global conversation memory
memory = ConversationMemory(max_messages=10)

# Initialize MySQL database service
db_service = MySQLService()


class AgentQuery(BaseModel):
    query: str
    session_id: str


class AgentResponse(BaseModel):
    answer: str
    tool_calls: list
    iterations: int


@router.post("/query", response_model=AgentResponse)
async def agent_query(
    request: AgentQuery,
    qdrant_service: QdrantService = Depends(),
    es_service: ElasticsearchService = Depends(),
    openai_service: OpenAIService = Depends()
):
    """
    Conversational agent with memory and tool calling.
    
    The agent:
    - Remembers previous conversation context
    - Uses search_products tool when needed
    - Has friendly sales personality
    """
    # Get conversation history
    conversation_history = memory.get_history(request.session_id)
    
    # Create agent and run
    agent = QueryAgent(
        openai_client=openai_service.client,
        qdrant_service=qdrant_service,
        es_service=es_service,
        db_service=db_service
    )
    
    result = agent.run(
        user_query=request.query,
        conversation_history=conversation_history
    )
    
    # Save conversation to memory
    memory.add_message(request.session_id, "user", request.query)
    memory.add_message(request.session_id, "assistant", result["answer"])
    
    return AgentResponse(
        answer=result["answer"],
        tool_calls=result.get("tool_calls", []),
        iterations=result["iterations"]
    )


@router.post("/clear-session")
async def clear_session(session_id: str):
    """Clear conversation history for a session."""
    memory.clear_session(session_id)
    return {"message": "Session cleared"}
