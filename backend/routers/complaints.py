# backend/routers/complaints.py - UPDATED for new field name
import os
import io
import time
import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
import cv2
import numpy as np
from PIL import Image
import pytesseract

# Import database functions
from database import get_db, save_complaint, log_performance

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/complaints", tags=["complaints"])

# Pydantic models
class ComplaintResponse(BaseModel):
    id: int
    category: str
    urgency: str
    department: str
    complaint_data: dict  # CHANGED: from metadata to complaint_data
    acknowledgment: str
    sentiment: str
    processing_time: float

class ComplaintStatus(BaseModel):
    id: int
    status: str
    category: str
    urgency: str
    department: str

# Configuration
SUPPORTED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/jpg"]
SUPPORTED_VIDEO_TYPES = ["video/mp4", "video/avi"]
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Category mappings
CATEGORY_KEYWORDS = {
    "cleanliness": ["dirty", "trash", "unclean", "garbage", "filthy", "messy"],
    "damage": ["broken", "damaged", "cracked", "torn", "ripped", "not working"],
    "staff_behavior": ["rude", "unhelpful", "impolite", "arrogant", "staff"],
    "safety": ["unsafe", "danger", "hazard", "emergency", "risk"],
    "electrical": ["light", "fan", "ac", "electric", "power"]
}

URGENCY_KEYWORDS = ["urgent", "emergency", "critical", "immediate", "asap", "now"]

DEPARTMENT_MAP = {
    "cleanliness": "Housekeeping",
    "damage": "Maintenance", 
    "staff_behavior": "Human Resources",
    "safety": "Safety Department",
    "electrical": "Electrical Department",
    "other": "General Administration"
}

def preprocess_image(image_array):
    """Preprocess image for analysis"""
    try:
        if len(image_array.shape) == 3:
            gray = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
        else:
            gray = image_array
            
        resized = cv2.resize(gray, (640, 480))
        return resized
    except Exception as e:
        logger.error(f"Error preprocessing image: {e}")
        return image_array

def extract_text_from_image(image_array):
    """Extract text using OCR"""
    try:
        text = pytesseract.image_to_string(image_array)
        return text.lower().strip()
    except Exception as e:
        logger.error(f"OCR error: {e}")
        return ""

def analyze_sentiment_text(text):
    """Analyze sentiment of text"""
    try:
        negative_words = ["bad", "poor", "terrible", "awful", "horrible", "broken", "dirty", "not working"]
        positive_words = ["good", "great", "excellent", "clean", "working", "nice", "thank"]
        
        text_lower = text.lower()
        negative_count = sum(1 for word in negative_words if word in text_lower)
        positive_count = sum(1 for word in positive_words if word in text_lower)
        
        if negative_count > positive_count:
            return "negative"
        elif positive_count > negative_count:
            return "positive"
        else:
            return "neutral"
    except Exception as e:
        logger.error(f"Sentiment analysis error: {e}")
        return "neutral"

def categorize_complaint(image_text, description_text):
    """Categorize complaint based on text analysis"""
    combined_text = f"{image_text} {description_text}".lower()
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in combined_text for keyword in keywords):
            return category
            
    return "other"

def determine_urgency(text, sentiment):
    """Determine urgency level"""
    text_lower = text.lower()
    
    if any(keyword in text_lower for keyword in URGENCY_KEYWORDS):
        return "high"
    elif sentiment == "negative":
        return "medium"
    else:
        return "low"

@router.post("/submit", response_model=ComplaintResponse)
async def submit_complaint(
    request: Request,
    file: UploadFile = File(...),
    description: str = Form(""),
    db: Session = Depends(get_db)
):
    """Submit a complaint with media attachment"""
    start_time = time.time()
    
    try:
        # Validate file
        if file.size and file.size > MAX_FILE_SIZE:
            raise HTTPException(400, f"File too large. Max size: {MAX_FILE_SIZE//1024//1024}MB")
        
        # Read file content
        contents = await file.read()
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Process based on file type
        if file.content_type and file.content_type.startswith('image/'):
            # Process image
            image = Image.open(io.BytesIO(contents))
            image_array = np.array(image)
            processed_image = preprocess_image(image_array)
            extracted_text = extract_text_from_image(processed_image)
            
        elif file.content_type and file.content_type.startswith('video/'):
            # Process video (extract first frame)
            video_bytes = io.BytesIO(contents)
            cap = cv2.VideoCapture(video_bytes)
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                raise HTTPException(400, "Could not read video file")
                
            processed_image = preprocess_image(frame)
            extracted_text = extract_text_from_image(processed_image)
        else:
            raise HTTPException(400, "Unsupported file type")
        
        # Analyze complaint
        combined_text = f"{extracted_text} {description}".strip()
        sentiment = analyze_sentiment_text(combined_text)
        category = categorize_complaint(extracted_text, description)
        urgency = determine_urgency(combined_text, sentiment)
        department = DEPARTMENT_MAP.get(category, "General Administration")
        
        # Prepare complaint_data (CHANGED from metadata)
        complaint_data_dict = {
            "file_type": file.content_type,
            "file_size": len(contents),
            "text_extracted": extracted_text[:200],
            "processing_steps": "ocr_text_extraction, sentiment_analysis, keyword_categorization",
            "client_ip": client_ip
        }
        
        # Save to database
        complaint_dict = {
            "category": category,
            "urgency": urgency,
            "department": department,
            "complaint_data": complaint_data_dict,  # CHANGED
            "sentiment": sentiment,
            "description": description,
            "file_name": file.filename,
            "user_ip": client_ip
        }
        
        complaint_id = save_complaint(db, complaint_dict)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Log performance
        log_performance(db, complaint_id, 0.9, processing_time)
        
        # Prepare response
        acknowledgment = (
            f"Complaint ID: {complaint_id} received successfully. "
            f"Category: {category}, Urgency: {urgency}. "
            f"Forwarded to: {department}. Processing time: {processing_time:.2f}s"
        )
        
        logger.info(f"Complaint {complaint_id} processed in {processing_time:.2f}s")
        
        return ComplaintResponse(
            id=complaint_id,
            category=category,
            urgency=urgency,
            department=department,
            complaint_data=complaint_data_dict,  # CHANGED
            acknowledgment=acknowledgment,
            sentiment=sentiment,
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing complaint: {e}")
        raise HTTPException(500, "Internal server error processing complaint")

@router.get("/status/{complaint_id}", response_model=ComplaintStatus)
async def get_complaint_status(complaint_id: int, db: Session = Depends(get_db)):
    """Get status of a specific complaint"""
    try:
        from database import Complaint
        
        complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if not complaint:
            raise HTTPException(404, "Complaint not found")
        
        return ComplaintStatus(
            id=complaint.id,
            status=complaint.status,
            category=complaint.category,
            urgency=complaint.urgency,
            department=complaint.department
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching complaint status: {e}")
        raise HTTPException(500, "Internal server error")

@router.get("/list")
async def list_complaints(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """List complaints with pagination"""
    try:
        from database import Complaint
        
        complaints = db.query(Complaint).offset(skip).limit(limit).all()
        
        return {
            "complaints": [
                {
                    "id": c.id,
                    "category": c.category,
                    "urgency": c.urgency,
                    "department": c.department,
                    "status": c.status,
                    "timestamp": c.timestamp.isoformat() if c.timestamp else None,
                    "sentiment": c.sentiment
                }
                for c in complaints
            ],
            "total": db.query(Complaint).count()
        }
    except Exception as e:
        logger.error(f"Error listing complaints: {e}")
        raise HTTPException(500, "Internal server error")

@router.get("/stats")
async def get_complaint_stats(db: Session = Depends(get_db)):
    """Get complaint statistics"""
    try:
        from database import Complaint
        from sqlalchemy import func
        
        stats = db.query(
            func.count(Complaint.id).label('total'),
            func.count(func.distinct(Complaint.category)).label('categories'),
            func.avg(func.case((Complaint.urgency == 'high', 1), else_=0)).label('high_urgency_percent')
        ).first()
        
        return {
            "total_complaints": stats.total or 0,
            "unique_categories": stats.categories or 0,
            "high_urgency_percentage": round((stats.high_urgency_percent or 0) * 100, 2)
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(500, "Internal server error")