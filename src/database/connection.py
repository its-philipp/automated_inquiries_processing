"""
Database connection and session management.
"""
import os
from typing import Generator
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from src.database.models import Base


class DatabaseManager:
    """Manage database connections and sessions."""
    
    def __init__(self, database_url: str = None):
        """
        Initialize database manager.
        
        Args:
            database_url: Database connection URL
        """
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/inquiry_automation"
        )
        
        # Create engine with connection pooling
        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,  # Verify connections before using
            echo=os.getenv("SQL_ECHO", "false").lower() == "true",
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )
    
    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """Drop all database tables."""
        Base.metadata.drop_all(bind=self.engine)
    
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get database session (for use with FastAPI Depends).
        
        Yields:
            Database session
        """
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    @contextmanager
    def session_scope(self):
        """
        Provide a transactional scope for a series of operations.
        
        Yields:
            Database session
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# Global database manager instance
_db_manager = None


def get_db_manager(database_url: str = None) -> DatabaseManager:
    """Get or create global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(database_url)
    return _db_manager


def get_database_url() -> str:
    """Get database URL from environment variables."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/inquiry_automation"
    )


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI to get database session.
    
    Yields:
        Database session
    """
    db_manager = get_db_manager()
    yield from db_manager.get_session()

