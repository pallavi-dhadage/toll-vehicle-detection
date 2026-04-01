from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from ..services.streaming import camera_manager

router = APIRouter(prefix="/stream", tags=["streaming"])

class CameraConfig(BaseModel):
    camera_id: str
    url: str
    fps: int = 2

@router.post("/add")
def add_camera(config: CameraConfig):
    if camera_manager.add_camera(config.camera_id, config.url, config.fps):
        return {"status": "ok", "message": f"Camera {config.camera_id} added"}
    raise HTTPException(status_code=400, detail="Camera ID already exists")

@router.delete("/remove/{camera_id}")
def remove_camera(camera_id: str):
    if camera_manager.remove_camera(camera_id):
        return {"status": "ok", "message": f"Camera {camera_id} removed"}
    raise HTTPException(status_code=404, detail="Camera not found")

@router.get("/list")
def list_cameras():
    return {"cameras": camera_manager.list_cameras()}

@router.websocket("/ws/{camera_id}")
async def websocket_endpoint(websocket: WebSocket, camera_id: str):
    await websocket.accept()
    camera = camera_manager.get_camera(camera_id)
    if not camera:
        await websocket.close(code=1000, reason="Camera not found")
        return

    async def send_detection(detection_data):
        await websocket.send_json(detection_data)

    camera.subscribe(send_detection)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        camera.unsubscribe(send_detection)
