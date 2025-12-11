from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router

app = FastAPI(
    title="Ollama Backend API",
    description="""
    A backend API for interacting with Ollama LLM models.
    
    Features:
    - List available Ollama models
    - Create chat sessions with specific models
    - Maintain conversation memory per session
    - Send messages with full conversation context
    - Manage multiple concurrent sessions
    """,
    version="1.0.0"
)

# Add CORS middleware for frontend compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api", tags=["Ollama API"])


@app.get("/")
async def root():
    """
    Root endpoint - API information.
    """
    return {
        "name": "Ollama Backend API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "models": "/api/models",
            "sessions": "/api/sessions",
            "chat": "/api/chat"
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
