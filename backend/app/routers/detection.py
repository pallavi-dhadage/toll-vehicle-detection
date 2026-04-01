from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from ..services.detector import detector
from ..models.database import SessionLocal, DetectionRecord

router = APIRouter(prefix="/detect", tags=["detection"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
async def detect_vehicle(file: UploadFile = File(...), db: Session = Depends(get_db)):
    image_bytes = await file.read()
    detections = detector.detect(image_bytes)
    for det in detections:
        db_record = DetectionRecord(
            vehicle_type=det["type"],
            confidence=det["confidence"],
        )
        db.add(db_record)
    db.commit()
    return {"detections": detections}

@router.get("/records")
def get_records(limit: int = 10, db: Session = Depends(get_db)):
    records = db.query(DetectionRecord).order_by(DetectionRecord.timestamp.desc()).limit(limit).all()
    return records
