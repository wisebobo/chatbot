"""
Database Test Script

Tests database operations with both SQLite and PostgreSQL configurations.

Usage:
    python scripts/test_database.py
"""
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import get_db_manager, reset_db_manager
from app.db.repositories import WikiRepository, APIKeyRepository
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def print_section(title: str):
    """Print test section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_wiki_operations():
    """Test wiki entry CRUD operations."""
    print_section("Test 1: Wiki Entry Operations")
    
    db_manager = get_db_manager()
    
    with db_manager.get_session() as session:
        repo = WikiRepository(session)
        
        # Create
        logger.info("Creating wiki entry...")
        entry_data = {
            "entry_id": "test_entry_001",
            "version": 1,
            "type": "concept",
            "title": "Test Concept",
            "summary": "This is a test entry",
            "content": "# Test Content\n\nThis is test content for validation.",
            "aliases": ["test", "example"],
            "tags": ["test", "validation"],
            "related_ids": [],
            "sources": ["test_script"],
            "confidence": 0.85,
            "status": "active",
        }
        
        entry = repo.create(entry_data)
        logger.info(f"✅ Created entry: {entry.entry_id} (ID: {entry.id})")
        
        # Read
        logger.info("Reading wiki entry...")
        retrieved = repo.get_by_id("test_entry_001")
        assert retrieved is not None, "Failed to retrieve entry"
        assert retrieved.title == "Test Concept"
        logger.info(f"✅ Retrieved entry: {retrieved.title}")
        
        # Update
        logger.info("Updating wiki entry...")
        updated = repo.update("test_entry_001", {
            "content": "# Updated Content\n\nThis content has been updated.",
            "confidence": 0.90,
        })
        assert updated is not None
        assert updated.version == 2
        logger.info(f"✅ Updated entry to version {updated.version}")
        
        # Search
        logger.info("Searching wiki entries...")
        results = repo.search("test", limit=5)
        assert len(results) > 0
        logger.info(f"✅ Found {len(results)} matching entries")
        
        # List all
        logger.info("Listing all entries...")
        all_entries = repo.list_all(limit=10)
        logger.info(f"✅ Total entries: {len(all_entries)}")
        
        # Count
        count = repo.count()
        logger.info(f"✅ Entry count: {count}")
        
        # Add feedback
        logger.info("Adding user feedback...")
        feedback = repo.add_feedback(
            entry_id="test_entry_001",
            user_id="test_user",
            feedback_type="positive",
            comment="Great entry!"
        )
        assert feedback is not None
        logger.info(f"✅ Feedback added: {feedback.feedback_type}")
        
        # Verify confidence update
        updated_entry = repo.get_by_id("test_entry_001")
        logger.info(f"✅ New confidence: {updated_entry.confidence:.2f}")
        logger.info(f"✅ Positive feedback: {updated_entry.positive_feedback}")
        
        # Delete
        logger.info("Deleting wiki entry...")
        deleted = repo.delete("test_entry_001")
        assert deleted is True
        logger.info("✅ Entry deleted")
        
        # Verify deletion (expire session to clear cache)
        session.expire_all()
        verify = repo.get_by_id("test_entry_001")
        assert verify is None
        logger.info("✅ Deletion verified")


def test_api_key_operations():
    """Test API key operations."""
    print_section("Test 2: API Key Operations")
    
    db_manager = get_db_manager()
    
    with db_manager.get_session() as session:
        repo = APIKeyRepository(session)
        
        # Create
        logger.info("Creating API key...")
        api_key = repo.create(
            key_hash="test_hash_12345",
            name="Test API Key",
            owner="test_user",
            rate_limit=100
        )
        logger.info(f"✅ Created API key: {api_key.name}")
        
        # Get by hash
        logger.info("Retrieving API key...")
        retrieved = repo.get_by_hash("test_hash_12345")
        assert retrieved is not None
        logger.info(f"✅ Retrieved key: {retrieved.name}")
        
        # Increment usage
        logger.info("Incrementing usage counter...")
        repo.increment_usage("test_hash_12345")
        updated = repo.get_by_hash("test_hash_12345")
        logger.info(f"✅ Total requests: {updated.total_requests}")
        
        # Deactivate
        logger.info("Deactivating API key...")
        deactivated = repo.deactivate("test_hash_12345")
        assert deactivated is True
        
        # Verify deactivation
        inactive = repo.get_by_hash("test_hash_12345")
        assert inactive is None  # Should not return inactive keys
        logger.info("✅ Key deactivated successfully")


def test_health_check():
    """Test database health check."""
    print_section("Test 3: Health Check")
    
    db_manager = get_db_manager()
    health = db_manager.health_check()
    
    logger.info(f"Status: {health['status']}")
    logger.info(f"Database: {health['database']}")
    
    if health['status'] == 'healthy':
        logger.info("✅ Database is healthy")
    else:
        logger.error(f"❌ Database unhealthy: {health.get('error')}")
        raise Exception("Health check failed")


def main():
    """Run all database tests."""
    print("\n" + "=" * 70)
    print("  Database Test Suite")
    print("=" * 70)
    
    # Get environment info
    db_manager = get_db_manager()
    env = os.getenv("APP_ENV", "development")
    db_type = "PostgreSQL" if not db_manager.database_url.startswith("sqlite") else "SQLite"
    
    print(f"\nEnvironment: {env}")
    print(f"Database Type: {db_type}")
    print(f"Connection: {db_manager._mask_url(db_manager.database_url)}")
    
    try:
        # Run tests
        test_health_check()
        test_wiki_operations()
        test_api_key_operations()
        
        # Summary
        print("\n" + "=" * 70)
        print("  ✅ All Tests Passed!")
        print("=" * 70)
        
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"  ❌ Test Failed: {e}")
        print("=" * 70)
        logger.exception("Stack trace:")
        sys.exit(1)
    finally:
        # Cleanup
        reset_db_manager()


if __name__ == "__main__":
    main()
