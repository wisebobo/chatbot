"""
Pytest configuration for the test suite

Provides fixtures, markers, and settings for comprehensive testing.
"""
import pytest
import sys
import os
import shutil
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ===== Handle .env Unicode issues on Windows =====
# Temporarily rename .env file before any imports to avoid UnicodeDecodeError
_env_path = Path(".env")
_env_backup = Path(".env.pytest_backup")

if _env_path.exists() and not _env_backup.exists():
    shutil.copy(_env_path, _env_backup)
    _env_path.unlink()
elif _env_backup.exists() and not _env_path.exists():
    # Restore from backup if needed
    shutil.copy(_env_backup, _env_path)


def pytest_configure(config):
    """Configure pytest"""
    # Register custom markers
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "load: marks tests as load/performance tests"
    )


def pytest_unconfigure(config):
    """Cleanup after all tests"""
    # Restore .env file
    if _env_backup.exists():
        if _env_path.exists():
            _env_path.unlink()
        shutil.copy(_env_backup, _env_path)
        _env_backup.unlink()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables"""
    os.environ["APP_ENV"] = "testing"
    os.environ["DB_ECHO"] = "false"
    
    # Use in-memory SQLite for tests
    if not os.getenv("POSTGRES_DSN"):
        os.environ["SQLITE_PATH"] = ":memory:"
    
    # Use in-memory rate limiter for tests
    os.environ["RATE_LIMIT_STORAGE"] = "memory://"
    
    # Clear skill registry to avoid duplicate registration warnings
    from app.skills.base import skill_registry
    skill_registry.clear()
    
    yield
    
    # Cleanup
    if "SQLITE_PATH" in os.environ:
        del os.environ["SQLITE_PATH"]
    if "RATE_LIMIT_STORAGE" in os.environ:
        del os.environ["RATE_LIMIT_STORAGE"]


@pytest.fixture
def test_db_manager():
    """Get database manager for testing"""
    from app.db.database import get_db_manager, reset_db_manager
    
    # Reset to ensure clean state
    reset_db_manager()
    db_manager = get_db_manager()
    
    # Create tables
    db_manager.create_tables()
    
    yield db_manager
    
    # Cleanup
    reset_db_manager()


@pytest.fixture(autouse=True)
def setup_wiki_database(test_db_manager):
    """Setup wiki database tables for all tests"""
    # Tables are already created by test_db_manager fixture
    yield
