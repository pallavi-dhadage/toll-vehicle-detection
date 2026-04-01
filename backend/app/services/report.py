import pandas as pd
from io import BytesIO
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models.database import DetectionRecord
from datetime import datetime

def generate_daily_report(db: Session, date_str: str):
    date = datetime.strptime(date_str, "%Y-%m-%d").date()
    records = db.query(DetectionRecord).filter(func.date(DetectionRecord.timestamp) == date).all()
    if not records:
        return None
    data = [{"vehicle_type": r.vehicle_type, "confidence": r.confidence, "timestamp": r.timestamp} for r in records]
    df = pd.DataFrame(data)
    df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
    pivot = df.pivot_table(index='vehicle_type', columns='hour', aggfunc='size', fill_value=0)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pivot.to_excel(writer, sheet_name='Hourly Breakdown')
        df.to_excel(writer, sheet_name='Raw Records', index=False)
    output.seek(0)
    return output
