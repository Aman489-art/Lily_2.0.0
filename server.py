import os
import sys
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure all relative paths in modules resolve relative to this file's directory
BASE_DIR = Path(__file__).parent.resolve()
os.chdir(BASE_DIR)
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from modules.ai_agent import (
    is_system_task_request,
    handle_general_chat,
    load_chat_history,
    load_command_history,
    log_execution_attempt,
)
from modules.lily_memory import load_memory, save_important_point, show_memory


app = FastAPI(title="Lily Server", version="2.0")

# Allow mobile and desktop clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    mood: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    mode: str  # CHAT or SYSTEM


class MemoryRequest(BaseModel):
    text: str
    source: Optional[str] = "user"


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    message = (req.message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    # Route using existing logic but avoid running system commands on server
    try:
        if is_system_task_request(message):
            # For safety, do not execute OS commands on the server.
            # Log intent for unified command history so context remains shared
            analysis = {"status": "FAILED", "summary": "System tasks are disabled on server."}
            log_execution_attempt(
                user_query=message,
                attempt_num=1,
                explanation="Server mode: skip system commands",
                command="N/A",
                analysis=analysis,
                output="",
            )
            return ChatResponse(
                response=(
                    "System-related tasks are disabled on the server. "
                    "Please run them on your desktop client."
                ),
                mode="SYSTEM",
            )
        else:
            # Use the existing chat path which logs chat history and speaks (speaking is a no-op for API)
            text = handle_general_chat(message)
            return ChatResponse(response=text or "", mode="CHAT")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory")
def get_memory() -> List[dict]:
    try:
        return load_memory()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory")
def add_memory(req: MemoryRequest) -> dict:
    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")
    try:
        save_important_point(text, source=req.source or "user")
        return {"status": "saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/pretty")
def show_memory_pretty() -> dict:
    try:
        return {"content": show_memory()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history/chat")
def history_chat(limit: int = 20) -> List[dict]:
    try:
        # load_chat_history returns last N already; pass limit
        return load_chat_history(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history/commands")
def history_commands() -> List[dict]:
    try:
        return load_command_history() or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=1,
    )


