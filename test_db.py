# test_db.py
import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://railmadad_user:123456@localhost:5432/railmadad"

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as connection:
        print("✅ Database connection successful!")
        
        # Test version
        result = connection.execute(text("SELECT version();"))
        print("PostgreSQL:", result.fetchone()[0])
        
        # Test current database
        result = connection.execute(text("SELECT current_database();"))
        print("Database:", result.fetchone()[0])
        
        # Test current user
        result = connection.execute(text("SELECT current_user;"))
        print("User:", result.fetchone()[0])
        
    print("✅ All connection tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")