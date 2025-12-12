from pydantic import BaseModel
from typing import Optional, List


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    session_id: str
    model: str
    message: str
    use_web_search: Optional[bool] = False


class ChatResponse(BaseModel):
    session_id: str
    model: str
    response: str
    conversation_history: List[Message]


class ModelInfo(BaseModel):
    name: str
    modified_at: Optional[str] = None
    size: Optional[int] = None
    digest: Optional[str] = None


class ModelsListResponse(BaseModel):
    models: List[ModelInfo]


class SessionInfo(BaseModel):
    session_id: str
    model: str
    message_count: int
    created_at: str


class CreateSessionRequest(BaseModel):
    model: str
    session_id: Optional[str] = None
    system_prompt: Optional[str] = None


class CreateSessionResponse(BaseModel):
    session_id: str
    model: str
    system_prompt: Optional[str] = None
    message: str
