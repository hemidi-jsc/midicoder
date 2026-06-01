"""
WebSocket Router - stream real-time progress từ CLI commands
Cho phép frontend nhận update về pipeline progress theo thời gian thực
"""

import asyncio
import json
import re
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["WebSocket"])

# Active WebSocket connections ( keyed by session_id )
active_connections: dict[str, WebSocket] = {}


@router.websocket("/ws/pipeline")
async def websocket_pipeline(websocket: WebSocket):
    """
    WebSocket endpoint cho pipeline progress streaming.
    
    Client gửi:
    {
        "type": "subscribe",
        "session_id": "unique-session-id"
    }
    
    Server trả về:
    {
        "type": "progress" | "stdout" | "stderr" | "complete" | "error",
        "data": { ... },
        "timestamp": "ISO string"
    }
    """
    await websocket.accept()
    session_id = None

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "Invalid JSON"},
                    "timestamp": datetime.utcnow().isoformat(),
                })
                continue

            msg_type = message.get("type")

            if msg_type == "subscribe":
                session_id = message.get("session_id", "default")
                active_connections[session_id] = websocket
                await websocket.send_json({
                    "type": "subscribed",
                    "data": {"session_id": session_id},
                    "timestamp": datetime.utcnow().isoformat(),
                })

            elif msg_type == "unsubscribe":
                sid = message.get("session_id", session_id)
                if sid and sid in active_connections:
                    del active_connections[sid]
                await websocket.send_json({
                    "type": "unsubscribed",
                    "data": {},
                    "timestamp": datetime.utcnow().isoformat(),
                })

            elif msg_type == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "data": {},
                    "timestamp": datetime.utcnow().isoformat(),
                })

    except WebSocketDisconnect:
        if session_id and session_id in active_connections:
            del active_connections[session_id]
    except Exception as e:
        print(f"WebSocket error: {e}")
        if session_id and session_id in active_connections:
            del active_connections[session_id]


async def broadcast(message: dict, exclude_session: str | None = None):
    """
    Broadcast message đến tất cả active WebSocket connections.
    
    Args:
        message: Message dict để send
        exclude_session: Session ID để exclude (optional)
    """
    disconnected = []
    for sid, ws in active_connections.items():
        if exclude_session and sid == exclude_session:
            continue
        try:
            await ws.send_json(message)
        except Exception:
            disconnected.append(sid)

    # Clean up disconnected sessions
    for sid in disconnected:
        del active_connections[sid]


async def send_to_session(session_id: str, message: dict):
    """
    Send message đến specific session.
    
    Args:
        session_id: Session ID để send đến
        message: Message dict
    """
    ws = active_connections.get(session_id)
    if ws:
        try:
            await ws.send_json(message)
        except Exception:
            del active_connections[session_id]


def parse_pipeline_stage(output: str) -> dict | None:
    """
    Parse CLI output để detect pipeline stage progress.
    
    Looks for patterns like:
    - "[contract/gen]" 
    - "Running brief analyze"
    - "Building IR"
    - "Generating code"
    
    Args:
        output: CLI stdout/stderr text
        
    Returns:
        Dict với stage info nếu detect được, None nếu không
    """
    output_lower = output.lower()
    
    stage_patterns = {
        "brief_analyze": r"brief[\s_]*analyz",
        "brief_rewrite": r"brief[\s_]*rewrit",
        "contract_gen": r"contract[\s_]*gen",
        "contract_check": r"contract[\s_]*check",
        "ir_build": r"ir[\s_]*build|building[\s_]*ir",
        "code_build": r"code[\s_]*(build|plan)",
        "code_gen": r"code[\s_]*gen|generating[\s_]*code",
        "code_apply": r"code[\s_]*apply|applying[\s_]*code",
        "runtime_test": r"runtime[\s_]*test|testing[\s_]*runtime",
        "runtime_fix": r"runtime[\s_]*fix",
    }

    for stage, pattern in stage_patterns.items():
        if re.search(pattern, output_lower):
            return {"stage": stage, "output": output[-200:]}
    
    return None
