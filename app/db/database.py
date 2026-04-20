"""
Database Configuration and Connection Management

Supports both SQLite (development) and PostgreSQL (production) with automatic detection.
"""
import os
from typing import Optional
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

# SQLAlchemy Base class for models
Base = declarative_base()


class DatabaseManager:
    """
    Manages database connections for both SQLite (dev) and PostgreSQL (prod).
    
    Automatically detects environment and configures appropriate connection.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database manager.
        
        Args:
            database_url: Database connection URL. If None, auto-detect from env.
        """
        self.database_url = database_url or self._get_database_url()
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        logger.info(f"Database initialized: {self._mask_url(self.database_url)}")
    
    def _get_database_url(self) -> str:
        """
        Get database URL from environment or use defaults.
        
        Returns:
            Database connection URL string
        """
        # Check for explicit configuration
        if os.getenv("POSTGRES_DSN"):
            return os.getenv("POSTGRES_DSN")
        
        # Auto-detect environment
        app_env = os.getenv("APP_ENV", "development").lower()
        
        if app_env == "production":
            # Production: Require PostgreSQL
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                raise ValueError(
                    "Production environment requires DATABASE_URL or POSTGRES_DSN to be set. "
                    "Example: postgresql://user:password@localhost:5432/chatbot_db"
                )
            return db_url
        else:
            # Development: Use SQLite by default
            sqlite_path = os.getenv("SQLITE_PATH", "./data/chatbot_dev.db")
            return f"sqlite:///{sqlite_path}"
    
    def _create_engine(self):
        """
        Create SQLAlchemy engine with appropriate configuration.
        
        Returns:
            SQLAlchemy Engine instance
        """
        is_sqlite = self.database_url.startswith("sqlite")
        
        if is_sqlite:
            # SQLite configuration
            engine = create_engine(
                self.database_url,
                connect_args={"check_same_thread": False},  # Required for FastAPI
                poolclass=StaticPool,  # Single connection for SQLite
                echo=os.getenv("DB_ECHO", "false").lower() == "true",
            )
            
            # Enable WAL mode for better concurrency
            @event.listens_for(engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
            
            logger.info("Using SQLite (development mode)")
        
        else:
            # PostgreSQL configuration
            engine = create_engine(
                self.database_url,
                pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
                max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
                pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
                pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "1800")),
                echo=os.getenv("DB_ECHO", "false").lower() == "true",
            )
            
            logger.info("Using PostgreSQL (production mode)")
        
        return engine
    
    def _mask_url(self, url: str) -> str:
        """Mask password in database URL for logging."""
        if "@" in url:
            parts = url.split("@")
            creds = parts[0].split("://")
            if ":" in creds[1]:
                user_pass = creds[1].split(":")
                masked = f"{creds[0]}://{user_pass[0]}:***@{parts[1]}"
                return masked
        return url
    
    def create_tables(self):
        """Create all database tables."""
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")
    
    def drop_tables(self):
        """Drop all database tables (use with caution!)."""
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("All database tables dropped")
    
    @contextmanager
    def get_session(self):
        """
        Provide a transactional scope around a series of operations.
        
        Usage:
            with db_manager.get_session() as session:
                # do something with session
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
    
    def get_session_dependency(self):
        """
        FastAPI dependency for getting database session.
        
        Usage:
            @app.get("/items/")
            def read_items(db: Session = Depends(db_manager.get_session_dependency)):
                ...
        """
        def _get_db():
            db = self.SessionLocal()
            try:
                yield db
            finally:
                db.close()
        
        return _get_db
    
    def health_check(self) -> dict:
        """
        Check database connectivity.
        
        Returns:
            Dictionary with health status
        """
        try:
            with self.get_session() as session:
                # Use SQLAlchemy text for raw SQL
                from sqlalchemy import text
                session.execute(text("SELECT 1"))
            
            db_type = "postgresql" if not self.database_url.startswith("sqlite") else "sqlite"
            
            return {
                "status": "healthy",
                "database": db_type,
                "url": self._mask_url(self.database_url),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "database": "unknown",
            }
    
    def close(self):
        """Close database connections."""
        self.engine.dispose()
        logger.info("Database connections closed")


# Global database manager instance (lazy initialization)
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """
    Get or create global database manager instance.
    
    Returns:
        DatabaseManager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def reset_db_manager():
    """Reset database manager (useful for testing)."""
    global _db_manager
    if _db_manager:
        _db_manager.close()
        _db_manager = None


# Convenience function for FastAPI dependency
def get_db():
    """FastAPI dependency to get database session."""
    db_manager = get_db_manager()
    # Call the returned generator function
    yield from db_manager.get_session_dependency()()
