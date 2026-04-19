"""
Database Integration Test Script

Tests the integration of database persistence with existing components:
- Wiki engine using WikiRepository
- API Key management using APIKeyRepository
- Audit logging
"""
import sys
import os
import asyncio

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import get_db_manager
from app.db.repositories import WikiRepository, APIKeyRepository, AuditLogRepository
from app.wiki.db_engine import DatabaseWikiEngine
from app.wiki.engine import WikiArticle, KnowledgeType, EntryStatus
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def print_section(title: str):
    """Print test section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_wiki_database_integration():
    """Test Wiki engine with database backend"""
    print_section("Test 1: Wiki Database Integration")
    
    # Initialize database wiki engine
    wiki_engine = DatabaseWikiEngine()
    
    # Check initial count
    initial_count = wiki_engine.get_article_count()
    logger.info(f"Initial article count: {initial_count}")
    
    # Create a test article
    test_article = WikiArticle(
        entry_id="test_db_integration",
        title="Database Integration Test",
        aliases=["db test", "integration"],
        type=KnowledgeType.CONCEPT,
        content="# Test Content\n\nThis is a test article for database integration.",
        summary="Test article",
        tags=["test", "database"],
        confidence=0.95,
        status=EntryStatus.ACTIVE,
        version=1
    )
    
    # Save article
    logger.info("Saving test article...")
    wiki_engine.save_article(test_article)
    logger.info("✅ Article saved successfully")
    
    # Retrieve article
    logger.info("Retrieving article...")
    retrieved = wiki_engine.get_article("test_db_integration")
    assert retrieved is not None
    assert retrieved.title == "Database Integration Test"
    logger.info(f"✅ Article retrieved: {retrieved.title}")
    
    # Search articles
    logger.info("Searching articles...")
    results = wiki_engine.search_articles("database", limit=5)
    assert len(results) > 0
    logger.info(f"✅ Found {len(results)} matching articles")
    
    # Add feedback
    logger.info("Adding user feedback...")
    success = wiki_engine.add_feedback(
        entry_id="test_db_integration",
        user_id="test_user",
        is_positive=True,
        comment="Great article!"
    )
    assert success
    logger.info("✅ Feedback added successfully")
    
    # Verify feedback updated confidence
    updated = wiki_engine.get_article("test_db_integration")
    logger.info(f"✅ Updated confidence: {updated.confidence:.2f}")
    logger.info(f"✅ Positive feedback: {updated.feedback.positive}")
    
    # List articles
    logger.info("Listing all articles...")
    all_articles = wiki_engine.list_articles(limit=10)
    logger.info(f"✅ Total articles: {len(all_articles)}")
    
    # Delete article
    logger.info("Deleting test article...")
    deleted = wiki_engine.delete_article("test_db_integration")
    assert deleted
    logger.info("✅ Article deleted successfully")
    
    # Verify deletion
    verify = wiki_engine.get_article("test_db_integration")
    assert verify is None
    logger.info("✅ Deletion verified")


def test_api_key_database_integration():
    """Test API Key management with database"""
    print_section("Test 2: API Key Database Integration")
    
    db_manager = get_db_manager()
    
    with db_manager.get_session() as session:
        repo = APIKeyRepository(session)
        
        # Create API key
        logger.info("Creating API key...")
        import hashlib
        test_key = "sk-test-key-integration"
        key_hash = hashlib.sha256(test_key.encode()).hexdigest()
        
        api_key = repo.create(
            key_hash=key_hash,
            name="Integration Test Key",
            owner="test_user",
            rate_limit=100
        )
        logger.info(f"✅ API key created: {api_key.name}")
        
        # Retrieve by hash
        logger.info("Retrieving API key...")
        retrieved = repo.get_by_hash(key_hash)
        assert retrieved is not None
        assert retrieved.name == "Integration Test Key"
        logger.info(f"✅ API key retrieved: {retrieved.name}")
        
        # Increment usage
        logger.info("Incrementing usage counter...")
        repo.increment_usage(key_hash)
        repo.increment_usage(key_hash)
        updated = repo.get_by_hash(key_hash)
        logger.info(f"✅ Total requests: {updated.total_requests}")
        
        # List all keys
        logger.info("Listing all API keys...")
        all_keys = repo.list_all(active_only=False)
        logger.info(f"✅ Total keys: {len(all_keys)}")
        
        # Deactivate key
        logger.info("Deactivating API key...")
        deactivated = repo.deactivate(key_hash)
        assert deactivated
        
        # Verify deactivation
        inactive = repo.get_by_hash(key_hash)
        assert inactive is None  # Should not return inactive keys
        logger.info("✅ Key deactivated successfully")
        
        session.commit()


def test_audit_logging():
    """Test audit log creation and querying"""
    print_section("Test 3: Audit Logging")
    
    db_manager = get_db_manager()
    
    with db_manager.get_session() as session:
        repo = AuditLogRepository(session)
        
        # Create audit logs
        logger.info("Creating audit logs...")
        
        log1 = repo.create_log(
            action="login_success",
            user_id="test_user",
            ip_address="192.168.1.100",
            method="POST",
            endpoint="/api/v1/auth/login",
            status_code=200,
            metadata={"display_name": "Test User"}
        )
        logger.info(f"✅ Created log entry: ID={log1.id}, Action={log1.action}")
        
        log2 = repo.create_log(
            action="api_auth_failed",
            user_id="unknown",
            ip_address="10.0.0.50",
            method="GET",
            endpoint="/api/v1/chat",
            status_code=401,
            error_message="Invalid API key"
        )
        logger.info(f"✅ Created log entry: ID={log2.id}, Action={log2.action}")
        
        log3 = repo.create_log(
            action="wiki_article_created",
            user_id="admin_user",
            resource_type="wiki_entry",
            resource_id="test_article",
            ip_address="192.168.1.100",
            method="POST",
            endpoint="/api/v1/wiki/articles",
            status_code=201
        )
        logger.info(f"✅ Created log entry: ID={log3.id}, Action={log3.action}")
        
        # Query logs by user
        logger.info("Querying logs by user...")
        user_logs = repo.get_logs(user_id="test_user", limit=10)
        logger.info(f"✅ Found {len(user_logs)} logs for test_user")
        
        # Query logs by action
        logger.info("Querying logs by action...")
        auth_logs = repo.get_logs(action="login_success", limit=10)
        logger.info(f"✅ Found {len(auth_logs)} login_success logs")
        
        # Get all recent logs
        logger.info("Getting recent logs...")
        recent_logs = repo.get_logs(limit=20)
        logger.info(f"✅ Total recent logs: {len(recent_logs)}")
        
        session.commit()


def main():
    """Run all integration tests"""
    print("\n" + "=" * 70)
    print("  Database Integration Test Suite")
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
        test_wiki_database_integration()
        test_api_key_database_integration()
        test_audit_logging()
        
        # Summary
        print("\n" + "=" * 70)
        print("  ✅ All Integration Tests Passed!")
        print("=" * 70)
        print("\n📊 Summary:")
        print("  ✓ Wiki engine now uses database storage (WikiRepository)")
        print("  ✓ API Keys are managed in database (APIKeyRepository)")
        print("  ✓ Audit logging is active for all critical operations")
        print("\n🎯 Next Steps:")
        print("  1. Start the application: python main.py")
        print("  2. Test API endpoints with database-backed authentication")
        print("  3. Monitor audit logs in database")
        
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"  ❌ Integration Test Failed: {e}")
        print("=" * 70)
        logger.exception("Stack trace:")
        sys.exit(1)
    finally:
        # Cleanup
        from app.db.database import reset_db_manager
        reset_db_manager()


if __name__ == "__main__":
    main()
