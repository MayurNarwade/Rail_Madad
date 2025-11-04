# backend/routers/trends.py - UPDATED for new field name
import logging
import io
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any
import pandas as pd

from database import get_db, get_trends, get_metrics

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/trends", tags=["trends"])

# Pydantic models
class TrendItem(BaseModel):
    category: str
    count: int
    percentage: float

class TrendsResponse(BaseModel):
    trends: List[TrendItem]
    metrics: Dict[str, float]
    total_complaints: int

@router.get("/", response_model=TrendsResponse)
async def get_analytics(db: Session = Depends(get_db)):
    """Get comprehensive analytics and trends"""
    try:
        # Get basic trends
        trends_data = get_trends(db)
        total = sum(count for _, count in trends_data) if trends_data else 0
        
        # Format trends with percentages
        trends = []
        for category, count in trends_data:
            percentage = (count / total * 100) if total > 0 else 0
            trends.append(TrendItem(
                category=category,
                count=count,
                percentage=round(percentage, 2)
            ))
        
        # Get performance metrics
        metrics = get_metrics(db)
        
        return TrendsResponse(
            trends=trends,
            metrics=metrics,
            total_complaints=total
        )
        
    except Exception as e:
        logger.error(f"Error generating analytics: {e}")
        raise HTTPException(500, "Internal server error generating analytics")

@router.get("/export/csv")
async def export_trends_csv(db: Session = Depends(get_db)):
    """Export trends data as CSV"""
    try:
        trends_data = get_trends(db)
        
        # Create DataFrame
        df = pd.DataFrame(trends_data, columns=['Category', 'Count'])
        if not df.empty:
            df['Percentage'] = (df['Count'] / df['Count'].sum() * 100).round(2)
        
        # Create CSV in memory
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        
        return StreamingResponse(
            iter([csv_buffer.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=rail_madad_trends.csv"}
        )
        
    except Exception as e:
        logger.error(f"CSV export error: {e}")
        raise HTTPException(500, "Internal server error exporting data")

@router.get("/department/stats")
async def get_department_stats(db: Session = Depends(get_db)):
    """Get statistics by department"""
    try:
        from database import Complaint
        from sqlalchemy import func
        
        stats = db.query(
            Complaint.department,
            func.count(Complaint.id).label('total'),
            func.avg(func.case((Complaint.urgency == 'high', 1), else_=0)).label('high_urgency_rate'),
            func.avg(func.case((Complaint.sentiment == 'negative', 1), else_=0)).label('negative_sentiment_rate')
        ).group_by(Complaint.department).all()
        
        return {
            "department_stats": [
                {
                    "department": dept,
                    "total_complaints": total,
                    "high_urgency_percentage": round(high_urgency_rate * 100, 2) if high_urgency_rate else 0,
                    "negative_sentiment_percentage": round(negative_sentiment_rate * 100, 2) if negative_sentiment_rate else 0
                }
                for dept, total, high_urgency_rate, negative_sentiment_rate in stats
            ]
        }
        
    except Exception as e:
        logger.error(f"Department stats error: {e}")
        raise HTTPException(500, "Internal server error")

@router.get("/urgency/distribution")
async def get_urgency_distribution(db: Session = Depends(get_db)):
    """Get urgency level distribution"""
    try:
        from database import Complaint
        from sqlalchemy import func
        
        distribution = db.query(
            Complaint.urgency,
            func.count(Complaint.id).label('count')
        ).group_by(Complaint.urgency).all()
        
        total = sum(count for _, count in distribution)
        
        return {
            "urgency_distribution": [
                {
                    "urgency_level": urgency,
                    "count": count,
                    "percentage": round((count / total * 100), 2) if total > 0 else 0
                }
                for urgency, count in distribution
            ],
            "total_complaints": total
        }
        
    except Exception as e:
        logger.error(f"Urgency distribution error: {e}")
        raise HTTPException(500, "Internal server error")