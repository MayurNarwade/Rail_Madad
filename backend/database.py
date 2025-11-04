# backend/database.py - FIXED version
import os
import logging
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from contextlib import contextmanager
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./railmadad.db")

try:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    raise

# Database Models
class Complaint(Base):
    __tablename__ = "complaints"
    
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), index=True)
    urgency = Column(String(50))
    department = Column(String(100))
    complaint_data = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    sentiment = Column(String(50))
    status = Column(String(50), default="pending")
    description = Column(Text, default="")
    file_name = Column(String(255))

class PerformanceLog(Base):
    __tablename__ = "performance_logs"
    
    id = Column(Integer, primary_key=True)
    complaint_id = Column(Integer)
    accuracy = Column(Float)
    processing_time = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Create tables
def create_tables():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise

# FIXED: Simple database session function
def get_db():
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        db.close()
        raise

# Utility functions
def save_complaint(db, complaint_data_dict):
    try:
        complaint_data_json = json.dumps(complaint_data_dict.get("complaint_data", {}))
        
        complaint = Complaint(
            category=complaint_data_dict.get("category", "other"),
            urgency=complaint_data_dict.get("urgency", "low"),
            department=complaint_data_dict.get("department", "General"),
            complaint_data=complaint_data_json,
            sentiment=complaint_data_dict.get("sentiment", "neutral"),
            description=complaint_data_dict.get("description", ""),
            file_name=complaint_data_dict.get("file_name", ""),
            timestamp=datetime.utcnow()
        )
        
        db.add(complaint)
        db.commit()
        db.refresh(complaint)
        
        logger.info(f"Complaint saved with ID: {complaint.id}")
        return complaint.id
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving complaint: {e}")
        raise

def log_performance(db, complaint_id, accuracy, processing_time):
    try:
        log = PerformanceLog(
            complaint_id=complaint_id,
            accuracy=accuracy,
            processing_time=processing_time,
            timestamp=datetime.utcnow()
        )
        db.add(log)
        db.commit()
        logger.info(f"Performance logged for complaint {complaint_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error logging performance: {e}")

def get_trends(db):
    try:
        from sqlalchemy import func
        trends = db.query(Complaint.category, func.count(Complaint.id)).group_by(Complaint.category).all()
        return trends
    except Exception as e:
        logger.error(f"Error fetching trends: {e}")
        return []

def get_metrics(db):
    try:
        from sqlalchemy import func
        result = db.query(
            func.avg(PerformanceLog.accuracy).label("avg_accuracy"),
            func.avg(PerformanceLog.processing_time).label("avg_processing_time"),
            func.count(PerformanceLog.id).label("total_processed")
        ).first()
        
        return {
            "avg_accuracy": float(result.avg_accuracy or 0),
            "avg_processing_time": float(result.avg_processing_time or 0),
            "total_processed": result.total_processed or 0
        }
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
        return {"avg_accuracy": 0, "avg_processing_time": 0, "total_processed": 0}

# Initialize database
create_tables()