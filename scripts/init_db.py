#!/usr/bin/env python3
"""
Database initialization script to create tables.
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from sqlalchemy import create_engine
from src.database.models import Base
from src.database.connection import get_database_url

def init_database():
    """Create all database tables."""
    print("Initializing database...")
    
    # Get database URL
    db_url = get_database_url()
    print(f"Connecting to database: {db_url}")
    
    # Create engine
    engine = create_engine(db_url)
    
    try:
        # Create all tables
        Base.metadata.create_all(engine)
        print("✅ Database tables created successfully!")
        
        # List created tables
        tables = list(Base.metadata.tables.keys())
        print(f"Created tables: {', '.join(tables)}")
        
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_database()
