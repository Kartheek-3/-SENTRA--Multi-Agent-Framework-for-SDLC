import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.events import event_bus

router = APIRouter(prefix="/api/projects", tags=["websocket"])

@router.websocket("/{project_id}/events")
async def project_events_ws(websocket: WebSocket, project_id: str):
    await websocket.accept()
    queue = event_bus.subscribe()
    try:
        while True:
            event = await queue.get()
            # Filter events by project_id
            if event.get("project_id") == project_id:
                await websocket.send_json(event)
    except WebSocketDisconnect:
        pass
    finally:
        event_bus.unsubscribe(queue)
