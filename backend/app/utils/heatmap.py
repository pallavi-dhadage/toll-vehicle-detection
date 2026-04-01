from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models.database import DetectionRecord
from datetime import datetime

def get_heatmap_data(db: Session, start_date: str, end_date: str):
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    results = db.query(
        func.extract('hour', DetectionRecord.timestamp).label('hour'),
        DetectionRecord.vehicle_type,
        func.count().label('count')
    ).filter(
        DetectionRecord.timestamp.between(start, end)
    ).group_by('hour', 'vehicle_type').all()
    return [{"hour": int(r.hour), "vehicle_type": r.vehicle_type, "count": r.count} for r in results]
