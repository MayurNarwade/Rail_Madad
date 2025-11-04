# backend/app.py - UPDATED to use SQLAlchemy database
import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Load environment variables
load_dotenv()

# Import routers
try:
    from routers.complaints import router as complaints_router
    from routers.chat import router as chat_router
    from routers.trends import router as trends_router
    print("✅ All routers imported successfully")
except ImportError as e:
    print(f"❌ Router import error: {e}")
    raise

# Import SQLAlchemy database
try:
    from database import get_db, Complaint, SessionLocal
    print("✅ Database imported successfully")
except ImportError as e:
    print(f"❌ Database import error: {e}")
    raise

# Pydantic model for status update
class StatusUpdate(BaseModel):
    status: str

# FastAPI app setup
app = FastAPI(
    title="Rail Madad AI Backend", 
    description="Scalable API for AI-powered complaint management",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(complaints_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(trends_router, prefix="/api/v1")

# Status update endpoint using SQLAlchemy database
@app.put("/api/v1/complaints/status/{complaint_id}")
async def update_complaint_status(complaint_id: int, status_update: StatusUpdate):
    """Update complaint status in SQLAlchemy database"""
    try:
        # Validate status
        valid_statuses = ['pending', 'in_progress', 'resolved', 'closed']
        if status_update.status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        
        # Get database session
        db = SessionLocal()
        try:
            # Check if complaint exists
            complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
            
            if not complaint:
                raise HTTPException(status_code=404, detail=f"Complaint with ID {complaint_id} not found")
            
            # Update status
            complaint.status = status_update.status
            db.commit()
            
            return {
                "success": True,
                "message": f"Complaint {complaint_id} status updated to {status_update.status}",
                "complaint_id": complaint_id,
                "new_status": status_update.status,
                "complaint": {
                    "id": complaint.id,
                    "category": complaint.category,
                    "urgency": complaint.urgency,
                    "department": complaint.department,
                    "status": complaint.status,
                    "timestamp": complaint.timestamp.isoformat() if complaint.timestamp else None
                }
            }
            
        finally:
            db.close()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating status: {str(e)}")

# Additional endpoints using SQLAlchemy database
@app.get("/api/v1/complaints/list")
async def get_complaints_list(limit: int = 100, status: Optional[str] = None):
    """Get list of complaints from SQLAlchemy database"""
    try:
        db = SessionLocal()
        try:
            query = db.query(Complaint)
            
            if status:
                query = query.filter(Complaint.status == status)
            
            complaints = query.order_by(Complaint.timestamp.desc()).limit(limit).all()
            
            complaints_list = []
            for complaint in complaints:
                complaints_list.append({
                    "id": complaint.id,
                    "category": complaint.category,
                    "urgency": complaint.urgency,
                    "department": complaint.department,
                    "status": complaint.status,
                    "timestamp": complaint.timestamp.isoformat() if complaint.timestamp else None,
                    "description": complaint.description or "",
                    "sentiment": complaint.sentiment or "neutral"
                })
            
            return {
                "complaints": complaints_list,
                "total": len(complaints_list)
            }
            
        finally:
            db.close()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching complaints: {str(e)}")

@app.get("/api/v1/complaints/status/{complaint_id}")
async def get_complaint_status(complaint_id: int):
    """Get specific complaint status from SQLAlchemy database"""
    try:
        db = SessionLocal()
        try:
            complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
            
            if not complaint:
                raise HTTPException(status_code=404, detail="Complaint not found")
            
            return {
                "id": complaint.id,
                "category": complaint.category,
                "urgency": complaint.urgency,
                "department": complaint.department,
                "status": complaint.status,
                "timestamp": complaint.timestamp.isoformat() if complaint.timestamp else None,
                "description": complaint.description or "",
                "sentiment": complaint.sentiment or "neutral"
            }
            
        finally:
            db.close()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching complaint status: {str(e)}")

@app.get("/api/v1/complaints/stats")
async def get_complaint_stats():
    """Get complaint statistics from SQLAlchemy database"""
    try:
        db = SessionLocal()
        try:
            from sqlalchemy import func
            
            # Total complaints
            total = db.query(func.count(Complaint.id)).scalar()
            
            # Complaints by status
            status_stats = db.query(Complaint.status, func.count(Complaint.id)).group_by(Complaint.status).all()
            status_dict = {status: count for status, count in status_stats}
            
            # Complaints by category
            category_stats = db.query(Complaint.category, func.count(Complaint.id)).group_by(Complaint.category).all()
            category_dict = {category: count for category, count in category_stats}
            
            # Complaints by urgency
            urgency_stats = db.query(Complaint.urgency, func.count(Complaint.id)).group_by(Complaint.urgency).all()
            urgency_dict = {urgency: count for urgency, count in urgency_stats}
            
            return {
                "total_complaints": total,
                "by_status": status_dict,
                "by_category": category_dict,
                "by_urgency": urgency_dict,
                "timestamp": datetime.now().isoformat()
            }
            
        finally:
            db.close()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")

@app.get("/api/v1/trends/")
async def get_trends():
    """Get trends data from SQLAlchemy database"""
    try:
        db = SessionLocal()
        try:
            from sqlalchemy import func
            
            # Get category trends
            trends_data = db.query(Complaint.category, func.count(Complaint.id)).group_by(Complaint.category).all()
            trends_list = [{"category": category, "count": count} for category, count in trends_data]
            
            # Get total complaints
            total_complaints = db.query(func.count(Complaint.id)).scalar()
            
            return {
                "total_complaints": total_complaints,
                "trends": trends_list,
                "metrics": {
                    "avg_accuracy": 0.95,  # Placeholder
                    "avg_processing_time": 2.5,  # Placeholder
                    "total_processed": total_complaints
                }
            }
            
        finally:
            db.close()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching trends: {str(e)}")

# FIXED: Add the correct root endpoint for API status check
@app.get("/api/v1/")
async def api_root():
    return {
        "message": "Rail Madad AI API is running!",
        "version": "1.0.0",
        "endpoints": {
            "complaints": "/api/v1/complaints",
            "chat": "/api/v1/chat", 
            "trends": "/api/v1/trends",
            "status_update": "/api/v1/complaints/status/{id}",
            "complaints_list": "/api/v1/complaints/list",
            "docs": "/docs"
        }
    }

@app.get("/")
async def root():
    return {
        "message": "Rail Madad AI Backend is running!",
        "version": "1.0.0",
        "api_base": "/api/v1/",
        "documentation": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/api/v1/health")
async def api_health():
    return {"status": "healthy", "version": "1.0.0"}

# Run server
if __name__ == "__main__":
    print("🚀 Starting Rail Madad AI Backend...")
    print("📊 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("🌐 API Base: http://localhost:8000/api/v1/")
    print("🗄️ Database: SQLAlchemy (railmadad.db)")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )