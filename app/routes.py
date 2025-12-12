from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import List
import io
from pypdf import PdfReader
import asyncio

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
from .tools import search_web
from .rag import rag_engine

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
        session_id=request.session_id,
        system_prompt=request.system_prompt
    )
    
    return CreateSessionResponse(
        session_id=session_id,
        model=request.model,
        system_prompt=request.system_prompt,
        message=f"Session created successfully with model '{request.model}'"
    )


@router.post("/sessions/{session_id}/upload")
async def upload_document(session_id: str, file: UploadFile = File(...)):
    """
    Upload a PDF or Text file to add to the session context (RAG).
    """
    if not memory.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    content = ""
    filename = file.filename.lower()
    
    try:
        if filename.endswith(".pdf"):
            # Read PDF
            pdf_content = await file.read()
            pdf_file = io.BytesIO(pdf_content)
            reader = PdfReader(pdf_file)
            for page in reader.pages:
                content += page.extract_text() + "\n"
        else:
            # Assume text
            content_bytes = await file.read()
            content = content_bytes.decode("utf-8", errors="ignore")
            
        if not content.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from file")
            
        # Get session model to use for embeddings
        session_data = memory.get_session(session_id)
        model_name = session_data.get("model", "llama3")
        
        # Add to Vector Store (ChromaDB)
        rag_engine.add_document(session_id, content, filename, model_name)
        
        return {
            "message": f"File '{file.filename}' processed and indexed successfully",
            "chars_extracted": len(content)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


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
    
    # Clear RAG context
    rag_engine.clear_session(session_id)
    
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
    history_messages = memory.get_messages(request.session_id)
    
    # Construct the actual messages list sent to Ollama
    # 1. Start with System Prompt (if any)
    # 2. Add RAG Context (if any)
    # 3. Add Conversation History
    
    final_messages = []
    
    session_data = memory.get_session(request.session_id)
    system_prompt = session_data.get("system_prompt")
    
    # Get RAG context from Vector Store
    rag_context = rag_engine.query(request.session_id, request.message, request.model)
    
    # Web Search Logic
    web_context = ""
    if request.use_web_search:
        try:
            # Run search in a separate thread to avoid blocking
            search_results = await asyncio.to_thread(search_web, request.message)
            web_context = f"CONTEXT FROM WEB TOOLS (Weather/Wiki/Search):\n{search_results}\n\n"
        except Exception as e:
            print(f"Web search failed: {e}")
            web_context = f"Web search failed: {str(e)}\n\n"
    
    if system_prompt or rag_context or web_context:
        sys_content = ""
        if system_prompt:
            sys_content += f"{system_prompt}\n\n"
        if web_context:
            sys_content += web_context
            sys_content += "IMPORTANT: If the user asked for a specific person, use the provided LinkedIn or social links to answer. Do not hallucinate URLs. Only use the links provided in the context.\n"
        if rag_context:
            sys_content += f"CONTEXT FROM UPLOADED DOCUMENTS:\n{rag_context}\n\n"
            
        if web_context or rag_context:
            sys_content += "Answer the user's question based on the context above if relevant."
            
        final_messages.append({"role": "system", "content": sys_content})
        
    final_messages.extend(history_messages)
    
    try:
        # Send to Ollama with full conversation history
        response_content = ollama_client.chat(
            model=request.model,
            messages=final_messages
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


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream a message response from the model within a session.
    """
    # Check if session exists
    if not memory.session_exists(request.session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Verify the model matches the session's model
    session_model = memory.get_model(request.session_id)
    if session_model != request.model:
        raise HTTPException(status_code=400, detail="Model mismatch")
    
    # Add user message to memory
    memory.add_message(request.session_id, "user", request.message)
    
    # Construct messages (same logic as regular chat)
    history_messages = memory.get_messages(request.session_id)
    final_messages = []
    
    session_data = memory.get_session(request.session_id)
    system_prompt = session_data.get("system_prompt")
    rag_context = rag_engine.query(request.session_id, request.message, request.model)
    
    # Web Search Logic
    web_context = ""
    if request.use_web_search:
        try:
            # Run search in a separate thread to avoid blocking
            search_results = await asyncio.to_thread(search_web, request.message)
            web_context = f"CONTEXT FROM WEB TOOLS (Weather/Wiki/Search):\n{search_results}\n\n"
        except Exception as e:
            print(f"Web search failed: {e}")
            web_context = f"Web search failed: {str(e)}\n\n"
    
    if system_prompt or rag_context or web_context:
        sys_content = ""
        if system_prompt:
            sys_content += f"{system_prompt}\n\n"
        if web_context:
            sys_content += web_context
            sys_content += "IMPORTANT: If the user asked for a specific person, use the provided LinkedIn or social links to answer. Do not hallucinate URLs. Only use the links provided in the context.\n"
        if rag_context:
            sys_content += f"CONTEXT FROM UPLOADED DOCUMENTS:\n{rag_context}\n\n"
            
        if web_context or rag_context:
            sys_content += "Answer the user's question based on the context above if relevant."
            
        final_messages.append({"role": "system", "content": sys_content})
        
    final_messages.extend(history_messages)

    async def generate():
        full_response = ""
        try:
            for chunk in ollama_client.chat_stream(model=request.model, messages=final_messages):
                full_response += chunk
                yield chunk
            
            # Save to memory after completion
            memory.add_message(request.session_id, "assistant", full_response)
        except Exception as e:
            yield f"Error: {str(e)}"

    return StreamingResponse(generate(), media_type="text/plain")


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
