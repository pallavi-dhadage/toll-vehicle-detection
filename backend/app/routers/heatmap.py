from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..utils.heatmap import get_heatmap_data
from ..models.database import SessionLocal

router = APIRouter(prefix="/heatmap", tags=["heatmap"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def heatmap(start: str, end: str, db: Session = Depends(get_db)):
    return get_heatmap_data(db, start, end)
