from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
import json
from datetime import datetime
import uvicorn

# Import Lily's core modules (modified for API use)
from modules.ai_engine import ask_lily
from modules.history_manager import (
    save_to_history, recall_context, get_history_summary
)
from modules.emotion_analyser import get_sentiment
from modules.ai_agent import (
    load_chat_history, save_chat_history, log_chat,
    get_recent_chat_context, is_system_task_request,
    load_persona
)

app = FastAPI(
    title="Lily AI Assistant API",
    description="AI Assistant API with memory and personality",
    version="2.0.0"
)

# CORS middleware - allows your mobile app to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify your app's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data directory setup
os.makedirs("data", exist_ok=True)

# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "default_user"
    include_context: Optional[bool] = True

class ChatResponse(BaseModel):
    response: str
    sentiment: str
    timestamp: str
    context_used: bool

class HistoryResponse(BaseModel):
    total_chats: int
    recent_chats: List[Dict]
    summary: str

class SystemCommandRequest(BaseModel):
    command: str
    user_id: Optional[str] = "default_user"

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime: str

# Track server start time
SERVER_START_TIME = datetime.now()

# ==================== ENDPOINTS ====================

@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    uptime = str(datetime.now() - SERVER_START_TIME)
    return {
        "status": "online",
        "version": "2.0.0",
        "uptime": uptime
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint - handles AI conversations
    """
    try:
        user_message = request.message.strip()
        
        if not user_message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Get user sentiment
        sentiment = get_sentiment(user_message)
        
        # Get conversation context if requested
        context = ""
        if request.include_context:
            context = get_recent_chat_context(last_n=5)
            recall = recall_context(5)
            if recall:
                context = f"{context}\n\nImportant memories:\n{recall}"
        
        # Load persona
        persona = load_persona()
        
        # Build chat prompt
        chat_prompt = f"""
{json.dumps(persona, indent=2) if persona else "You are Lily, a friendly AI assistant."}

RECENT CONVERSATION HISTORY:
{context if context else "This is the start of the conversation."}

User just said: "{user_message}"

Respond naturally as Lily, taking into account the conversation history and your persona.
Keep your response conversational and human-like.
"""
        
        # Get AI response
        ai_response = ask_lily(chat_prompt)
        
        # Log the conversation
        log_chat(user_message, ai_response)
        
        return {
            "response": ai_response,
            "sentiment": sentiment,
            "timestamp": datetime.now().isoformat(),
            "context_used": request.include_context
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@app.get("/history", response_model=HistoryResponse)
async def get_history(limit: int = 10):
    """
    Get chat history
    """
    try:
        chat_history = load_chat_history()
        
        recent_chats = chat_history[-limit:] if chat_history else []
        
        # Get summary
        summary = get_history_summary() if chat_history else "No conversation history yet"
        
        return {
            "total_chats": len(chat_history),
            "recent_chats": recent_chats,
            "summary": summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")

@app.delete("/history")
async def clear_history():
    """
    Clear chat history (creates backup)
    """
    try:
        import shutil
        from datetime import datetime
        
        # Create backup
        backup_file = f"data/chat_history_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        if os.path.exists("data/chat_history.json"):
            shutil.copy("data/chat_history.json", backup_file)
        
        # Clear history
        save_chat_history([])
        
        return {
            "status": "success",
            "message": "Chat history cleared",
            "backup_created": backup_file
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing history: {str(e)}")

@app.post("/memory/save")
async def save_memory(message: str):
    """
    Save an important memory
    """
    try:
        from modules.lily_memory import save_important_point
        
        save_important_point(message, source="api")
        
        return {
            "status": "success",
            "message": "Memory saved successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving memory: {str(e)}")

@app.get("/memory/recall")
async def recall_memory(limit: int = 5):
    """
    Recall important memories
    """
    try:
        memories = recall_context(limit)
        
        return {
            "memories": memories,
            "count": len(memories) if memories else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recalling memory: {str(e)}")

@app.post("/command/execute")
async def execute_command(request: SystemCommandRequest):
    """
    Execute system commands (for Android system control)
    Note: This is limited on Render - mainly for chat-based commands
    """
    try:
        command = request.command.strip().lower()
        
        # Handle safe commands only
        if "weather" in command:
            from modules.weather import get_weather_report
            result = get_weather_report()
            return {"status": "success", "result": result}
        
        elif "news" in command:
            from modules.system_tasks import news
            result = news()
            return {"status": "success", "result": result}
        
        elif "wikipedia" in command:
            query = command.replace("wikipedia", "").strip()
            from modules.system_tasks import wiki_search
            result = wiki_search(query)
            return {"status": "success", "result": result}
        
        else:
            return {
                "status": "unsupported",
                "message": "This command cannot be executed remotely. Use chat instead."
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing command: {str(e)}")

@app.get("/stats")
async def get_stats():
    """
    Get usage statistics
    """
    try:
        chat_history = load_chat_history()
        from modules.ai_agent import load_command_history
        command_history = load_command_history()
        
        return {
            "total_conversations": len(chat_history),
            "total_commands": len(command_history),
            "server_uptime": str(datetime.now() - SERVER_START_TIME),
            "last_interaction": chat_history[-1]["timestamp"] if chat_history else "None"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")

# ==================== SERVER STARTUP ====================

if __name__ == "__main__":
    # Get port from environment (Render will set this)
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
