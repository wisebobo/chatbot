"""
Integration tests for database transactions and repositories

Tests CRUD operations, transactions, and data integrity.
"""
import pytest
from app.db.database import get_db_manager
from app.db.repositories import WikiRepository, APIKeyRepository, AuditLogRepository
from app.db.models import WikiEntry, APIKey, AuditLog


@pytest.fixture
def db_manager():
    """Get database manager"""
    return get_db_manager()


@pytest.fixture
def session(db_manager):
    """Get database session"""
    with db_manager.get_session() as session:
        yield session
        session.rollback()  # Clean up after test


@pytest.fixture
def wiki_repo(session):
    """Create Wiki repository"""
    return WikiRepository(session)


@pytest.fixture
def api_key_repo(session):
    """Create API Key repository"""
    return APIKeyRepository(session)


@pytest.fixture
def audit_repo(session):
    """Create Audit Log repository"""
    return AuditLogRepository(session)


class TestWikiRepository:
    """Tests for WikiRepository"""
    
    def test_create_wiki_entry(self, wiki_repo, session):
        """Test creating a new wiki entry"""
        entry_data = {
            "entry_id": "test_concept_001",
            "version": 1,
            "type": "concept",
            "title": "Test Concept",
            "content": "# Test Content\nThis is a test.",
            "confidence": 0.9,
            "status": "active"
        }
        
        entry = wiki_repo.create(entry_data)
        session.commit()
        
        assert entry.id is not None
        assert entry.entry_id == "test_concept_001"
        assert entry.title == "Test Concept"
    
    def test_get_wiki_entry_by_id(self, wiki_repo, session):
        """Test retrieving wiki entry by ID"""
        # Create entry first
        entry_data = {
            "entry_id": "test_get_001",
            "version": 1,
            "type": "concept",
            "title": "Get Test",
            "content": "Content",
            "confidence": 0.8,
            "status": "active"
        }
        created = wiki_repo.create(entry_data)
        session.commit()
        
        # Retrieve
        retrieved = wiki_repo.get_by_id("test_get_001")
        
        assert retrieved is not None
        assert retrieved.entry_id == "test_get_001"
        assert retrieved.title == "Get Test"
    
    def test_update_wiki_entry(self, wiki_repo, session):
        """Test updating wiki entry"""
        # Create entry
        entry_data = {
            "entry_id": "test_update_001",
            "version": 1,
            "type": "concept",
            "title": "Original Title",
            "content": "Original content",
            "confidence": 0.7,
            "status": "active"
        }
        wiki_repo.create(entry_data)
        session.commit()
        
        # Update
        updated = wiki_repo.update("test_update_001", {
            "title": "Updated Title",
            "content": "Updated content",
            "version": 2
        })
        session.commit()
        
        assert updated.title == "Updated Title"
        assert updated.content == "Updated content"
        assert updated.version == 2
    
    def test_delete_wiki_entry(self, wiki_repo, session):
        """Test deleting wiki entry"""
        # Create entry
        entry_data = {
            "entry_id": "test_delete_001",
            "version": 1,
            "type": "concept",
            "title": "To Delete",
            "content": "Content",
            "confidence": 0.8,
            "status": "active"
        }
        wiki_repo.create(entry_data)
        session.commit()
        
        # Delete
        deleted = wiki_repo.delete("test_delete_001")
        session.commit()
        
        assert deleted is True
        
        # Verify deletion
        retrieved = wiki_repo.get_by_id("test_delete_001")
        assert retrieved is None
    
    def test_search_wiki_entries(self, wiki_repo, session):
        """Test searching wiki entries"""
        # Create multiple entries
        entries = [
            {
                "entry_id": f"search_test_{i}",
                "version": 1,
                "type": "concept",
                "title": f"Test Article {i}",
                "content": f"Content about topic {i}",
                "confidence": 0.8,
                "status": "active"
            }
            for i in range(5)
        ]
        
        for entry_data in entries:
            wiki_repo.create(entry_data)
        session.commit()
        
        # Search
        results = wiki_repo.search("topic", status_filter="active", limit=10)
        
        assert len(results) > 0
    
    def test_list_wiki_entries_with_filters(self, wiki_repo, session):
        """Test listing entries with filters"""
        # Create entries of different types
        for entry_type in ["concept", "rule", "process"]:
            entry_data = {
                "entry_id": f"filter_test_{entry_type}",
                "version": 1,
                "type": entry_type,
                "title": f"{entry_type.title()} Article",
                "content": "Content",
                "confidence": 0.8,
                "status": "active"
            }
            wiki_repo.create(entry_data)
        session.commit()
        
        # Filter by type
        results = wiki_repo.list_all(type_filter="concept", limit=10)
        
        assert len(results) >= 1
        assert all(e.type == "concept" for e in results)
    
    def test_add_feedback(self, wiki_repo, session):
        """Test adding feedback to wiki entry"""
        # Create entry
        entry_data = {
            "entry_id": "feedback_test_001",
            "version": 1,
            "type": "concept",
            "title": "Feedback Test",
            "content": "Content",
            "confidence": 0.8,
            "status": "active"
        }
        wiki_repo.create(entry_data)
        session.commit()
        
        # Add positive feedback
        feedback = wiki_repo.add_feedback(
            entry_id="feedback_test_001",
            user_id="user123",
            feedback_type="positive",
            comment="Great article!"
        )
        session.commit()
        
        assert feedback is not None
        assert feedback.feedback_type == "positive"
        
        # Verify confidence increased
        entry = wiki_repo.get_by_id("feedback_test_001")
        assert entry.confidence > 0.8
    
    def test_wiki_entry_count(self, wiki_repo, session):
        """Test counting wiki entries"""
        count_before = wiki_repo.count(status_filter="active")
        
        # Add entry
        entry_data = {
            "entry_id": "count_test_001",
            "version": 1,
            "type": "concept",
            "title": "Count Test",
            "content": "Content",
            "confidence": 0.8,
            "status": "active"
        }
        wiki_repo.create(entry_data)
        session.commit()
        
        count_after = wiki_repo.count(status_filter="active")
        
        assert count_after == count_before + 1


class TestAPIKeyRepository:
    """Tests for APIKeyRepository"""
    
    def test_create_api_key(self, api_key_repo, session):
        """Test creating API key"""
        import hashlib
        
        key_hash = hashlib.sha256(b"test-key-123").hexdigest()
        
        api_key = api_key_repo.create(
            key_hash=key_hash,
            name="Test Key",
            owner="test_user",
            rate_limit=100
        )
        session.commit()
        
        assert api_key.id is not None
        assert api_key.name == "Test Key"
        assert api_key.is_active is True
    
    def test_get_api_key_by_hash(self, api_key_repo, session):
        """Test retrieving API key by hash"""
        import hashlib
        
        key_hash = hashlib.sha256(b"get-test-key").hexdigest()
        
        api_key_repo.create(
            key_hash=key_hash,
            name="Get Test Key",
            owner="user",
            rate_limit=50
        )
        session.commit()
        
        retrieved = api_key_repo.get_by_hash(key_hash)
        
        assert retrieved is not None
        assert retrieved.name == "Get Test Key"
    
    def test_increment_usage(self, api_key_repo, session):
        """Test incrementing API key usage counter"""
        import hashlib
        
        key_hash = hashlib.sha256(b"usage-test-key").hexdigest()
        
        api_key_repo.create(
            key_hash=key_hash,
            name="Usage Test Key",
            owner="user",
            rate_limit=100
        )
        session.commit()
        
        # Increment usage
        api_key_repo.increment_usage(key_hash)
        api_key_repo.increment_usage(key_hash)
        api_key_repo.increment_usage(key_hash)
        session.commit()
        
        retrieved = api_key_repo.get_by_hash(key_hash)
        assert retrieved.total_requests == 3
    
    def test_deactivate_api_key(self, api_key_repo, session):
        """Test deactivating API key"""
        import hashlib
        
        key_hash = hashlib.sha256(b"deactivate-test").hexdigest()
        
        api_key_repo.create(
            key_hash=key_hash,
            name="Deactivate Test",
            owner="user",
            rate_limit=100
        )
        session.commit()
        
        # Deactivate
        deactivated = api_key_repo.deactivate(key_hash)
        session.commit()
        
        assert deactivated is True
        
        # Should not retrieve inactive keys
        retrieved = api_key_repo.get_by_hash(key_hash)
        assert retrieved is None
    
    def test_list_api_keys(self, api_key_repo, session):
        """Test listing API keys"""
        import hashlib
        
        # Create multiple keys
        for i in range(3):
            key_hash = hashlib.sha256(f"list-test-{i}".encode()).hexdigest()
            api_key_repo.create(
                key_hash=key_hash,
                name=f"List Test Key {i}",
                owner="user",
                rate_limit=100
            )
        session.commit()
        
        # List all
        keys = api_key_repo.list_all(active_only=False)
        
        assert len(keys) >= 3


class TestAuditLogRepository:
    """Tests for AuditLogRepository"""
    
    def test_create_audit_log(self, audit_repo, session):
        """Test creating audit log entry"""
        log = audit_repo.create_log(
            action="test_action",
            user_id="test_user",
            ip_address="192.168.1.1",
            method="POST",
            endpoint="/api/v1/test",
            status_code=200
        )
        session.commit()
        
        assert log.id is not None
        assert log.action == "test_action"
        assert log.user_id == "test_user"
    
    def test_get_logs_by_user(self, audit_repo, session):
        """Test querying logs by user"""
        # Create logs
        for i in range(5):
            audit_repo.create_log(
                action="login",
                user_id="specific_user",
                ip_address="192.168.1.1",
                method="POST",
                endpoint="/auth/login",
                status_code=200
            )
        
        audit_repo.create_log(
            action="login",
            user_id="other_user",
            ip_address="192.168.1.2",
            method="POST",
            endpoint="/auth/login",
            status_code=200
        )
        session.commit()
        
        # Query by user
        logs = audit_repo.get_logs(user_id="specific_user", limit=10)
        
        assert len(logs) == 5
        assert all(log.user_id == "specific_user" for log in logs)
    
    def test_get_logs_by_action(self, audit_repo, session):
        """Test querying logs by action type"""
        # Create different action types
        for action in ["login", "logout", "api_call"]:
            audit_repo.create_log(
                action=action,
                user_id="test_user",
                ip_address="192.168.1.1",
                method="POST",
                endpoint="/test",
                status_code=200
            )
        session.commit()
        
        # Query by action
        login_logs = audit_repo.get_logs(action="login", limit=10)
        
        assert len(login_logs) >= 1
        assert all(log.action == "login" for log in login_logs)
    
    def test_get_recent_logs(self, audit_repo, session):
        """Test getting recent logs"""
        # Create logs
        for i in range(10):
            audit_repo.create_log(
                action="test",
                user_id="test_user",
                ip_address="192.168.1.1",
                method="GET",
                endpoint="/test",
                status_code=200
            )
        session.commit()
        
        # Get recent (should be limited)
        recent = audit_repo.get_logs(limit=5)
        
        assert len(recent) <= 5
    
    def test_audit_log_with_metadata(self, audit_repo, session):
        """Test creating audit log with metadata"""
        log = audit_repo.create_log(
            action="api_key_created",
            user_id="admin",
            ip_address="192.168.1.1",
            method="POST",
            endpoint="/api-keys",
            status_code=201,
            metadata={"key_name": "Production Key", "owner": "service-account"}
        )
        session.commit()
        
        assert log.metadata is not None
        assert "key_name" in log.metadata


class TestDatabaseTransactions:
    """Tests for database transaction handling"""
    
    def test_transaction_rollback_on_error(self, db_manager):
        """Test that transactions rollback on error"""
        with db_manager.get_session() as session:
            repo = WikiRepository(session)
            
            try:
                # Create entry
                entry_data = {
                    "entry_id": "rollback_test",
                    "version": 1,
                    "type": "concept",
                    "title": "Rollback Test",
                    "content": "Content",
                    "confidence": 0.8,
                    "status": "active"
                }
                repo.create(entry_data)
                
                # Don't commit - should rollback
                raise Exception("Simulated error")
            except Exception:
                session.rollback()
        
        # Verify entry was rolled back
        with db_manager.get_session() as session:
            repo = WikiRepository(session)
            entry = repo.get_by_id("rollback_test")
            assert entry is None
    
    def test_transaction_commit_success(self, db_manager):
        """Test successful transaction commit"""
        with db_manager.get_session() as session:
            repo = WikiRepository(session)
            
            entry_data = {
                "entry_id": "commit_test",
                "version": 1,
                "type": "concept",
                "title": "Commit Test",
                "content": "Content",
                "confidence": 0.8,
                "status": "active"
            }
            repo.create(entry_data)
            session.commit()
        
        # Verify entry exists
        with db_manager.get_session() as session:
            repo = WikiRepository(session)
            entry = repo.get_by_id("commit_test")
            assert entry is not None
            assert entry.title == "Commit Test"
