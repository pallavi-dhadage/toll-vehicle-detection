from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DetectionRecordBase(BaseModel):
    vehicle_type: str
    confidence: float
    image_path: Optional[str] = None
    lane: Optional[str] = None

class DetectionRecordCreate(DetectionRecordBase):
    pass

class DetectionRecord(DetectionRecordBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True

class DetectionResponse(BaseModel):
    detections: list[dict]
