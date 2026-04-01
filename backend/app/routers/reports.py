from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from ..services.report import generate_daily_report
from ..models.database import SessionLocal

router = APIRouter(prefix="/reports", tags=["reports"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/daily")
def daily_report(date: str, db: Session = Depends(get_db)):
    excel_file = generate_daily_report(db, date)
    if excel_file is None:
        raise HTTPException(status_code=404, detail="No data for this date")
    return StreamingResponse(excel_file, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename=report_{date}.xlsx"})
