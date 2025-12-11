from fastapi import APIRouter, HTTPException
from typing import List

from .models import (
    ChatRequest,
    ChatResponse,
    ModelsListResponse,
    ModelInfo,
    SessionInfo,
    CreateSessionRequest,
    CreateSessionResponse,
    Message
)
from .memory import memory
from .ollama_client import ollama_client

router = APIRouter()


@router.get("/models", response_model=ModelsListResponse)
async def list_models():
    """
    Get list of all available Ollama models.
    """
    try:
        models = ollama_client.list_models()
        model_list = [ModelInfo(**m) for m in models]
        return ModelsListResponse(models=model_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(request: CreateSessionRequest):
    """
    Create a new chat session with a specific model.
    This session will maintain conversation memory.
    """
    # Verify model exists
    if not ollama_client.check_model_exists(request.model):
        raise HTTPException(
            status_code=404,
            detail=f"Model '{request.model}' not found. Use /models to see available models."
        )
    
    session_id = memory.create_session(
        model=request.model,
        session_id=request.session_id
    )
    
    return CreateSessionResponse(
        session_id=session_id,
        model=request.model,
        message=f"Session created successfully with model '{request.model}'"
    )


@router.get("/sessions", response_model=List[SessionInfo])
async def list_sessions():
    """
    List all active chat sessions.
    """
    sessions = memory.list_sessions()
    return [SessionInfo(**s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str):
    """
    Get information about a specific session.
    """
    session = memory.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionInfo(
        session_id=session_id,
        model=session["model"],
        message_count=len(session["messages"]),
        created_at=session["created_at"]
    )


@router.get("/sessions/{session_id}/history", response_model=List[Message])
async def get_session_history(session_id: str):
    """
    Get the full conversation history for a session.
    """
    if not memory.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = memory.get_messages(session_id)
    return [Message(**m) for m in messages]


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a chat session and its memory.
    """
    if not memory.delete_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": f"Session '{session_id}' deleted successfully"}


@router.post("/sessions/{session_id}/clear")
async def clear_session_history(session_id: str):
    """
    Clear the conversation history for a session but keep the session active.
    """
    if not memory.clear_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": f"Session '{session_id}' history cleared successfully"}


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to the model within a session.
    The session maintains conversation memory for context.
    """
    # Check if session exists
    if not memory.session_exists(request.session_id):
        raise HTTPException(
            status_code=404,
            detail=f"Session '{request.session_id}' not found. Create a session first using POST /sessions"
        )
    
    # Verify the model matches the session's model
    session_model = memory.get_model(request.session_id)
    if session_model != request.model:
        raise HTTPException(
            status_code=400,
            detail=f"Model mismatch. Session uses '{session_model}', but '{request.model}' was requested."
        )
    
    # Add user message to memory
    memory.add_message(request.session_id, "user", request.message)
    
    # Get full conversation history for context
    messages = memory.get_messages(request.session_id)
    
    try:
        # Send to Ollama with full conversation history
        response_content = ollama_client.chat(
            model=request.model,
            messages=messages
        )
        
        # Add assistant response to memory
        memory.add_message(request.session_id, "assistant", response_content)
        
        # Get updated conversation history
        updated_messages = memory.get_messages(request.session_id)
        
        return ChatResponse(
            session_id=request.session_id,
            model=request.model,
            response=response_content,
            conversation_history=[Message(**m) for m in updated_messages]
        )
    
    except Exception as e:
        # Remove the user message if the request failed
        messages = memory.get_messages(request.session_id)
        if messages and messages[-1]["role"] == "user":
            messages.pop()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/quick")
async def quick_chat(model: str, message: str):
    """
    Send a quick one-off message without session management.
    No memory is maintained between calls.
    """
    if not ollama_client.check_model_exists(model):
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model}' not found. Use /models to see available models."
        )
    
    try:
        response = ollama_client.chat(
            model=model,
            messages=[{"role": "user", "content": message}]
        )
        return {
            "model": model,
            "message": message,
            "response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
