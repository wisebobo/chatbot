# Database Configuration Guide

This guide explains how to configure and use the database layer in the LangGraph Enterprise Agent Platform.

## 📋 Overview

The platform supports **dual database backends**:

- **Development**: SQLite (zero configuration, file-based)
- **Production**: PostgreSQL (enterprise-grade, high-performance)

Both use the same SQLAlchemy ORM interface, so your application code remains identical regardless of the backend.

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│     Application Layer (FastAPI)     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   Repository Pattern (Data Access)  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│    SQLAlchemy ORM (Abstraction)     │
└──────────────┬──────────────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
  ┌─────────┐    ┌──────────┐
  │ SQLite  │    │PostgreSQL│
  │  (Dev)  │    │ (Prod)   │
  └─────────┘    └──────────┘
```

## ⚙️ Configuration

### Development (SQLite - Default)

No configuration needed! SQLite is used automatically in development mode.

```bash
# Just run the app
python main.py

# Or with explicit settings
export APP_ENV=development
export SQLITE_PATH=./data/chatbot_dev.db
python main.py
```

**Advantages:**
- ✅ Zero setup
- ✅ Single file database
- ✅ Easy to backup/reset
- ✅ Perfect for unit tests

**Limitations:**
- ❌ No concurrent writes
- ❌ Limited scalability
- ❌ Not suitable for production

### Production (PostgreSQL)

#### Option 1: Environment Variable

```bash
export APP_ENV=production
export POSTGRES_DSN=postgresql://user:password@localhost:5432/chatbot_db
python main.py
```

#### Option 2: .env File

```ini
APP_ENV=production
POSTGRES_DSN=postgresql://chatbot_user:secure_password@db-server:5432/chatbot_db

# Connection pool settings
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800
```

#### Option 3: Docker Compose

```yaml
services:
  chatbot:
    environment:
      - POSTGRES_DSN=postgresql://chatbot_user:chatbot_password@postgres:5432/chatbot_db
    depends_on:
      - postgres
  
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: chatbot_db
      POSTGRES_USER: chatbot_user
      POSTGRES_PASSWORD: chatbot_password
    volumes:
      - postgres-data:/var/lib/postgresql/data
```

## 🚀 Quick Start

### 1. Initialize Database

```bash
# Development (SQLite)
python scripts/init_db.py

# With sample data
python scripts/init_db.py --seed

# Production (PostgreSQL)
export POSTGRES_DSN=postgresql://user:pass@host/dbname
python scripts/init_db.py
```

### 2. Test Database Operations

```bash
python scripts/test_database.py
```

Expected output:
```
======================================================================
  Database Test Suite
======================================================================

Environment: development
Database Type: SQLite
Connection: sqlite:///./data/chatbot_dev.db

======================================================================
  Test 1: Wiki Entry Operations
======================================================================
✅ Created entry: test_entry_001 (ID: 1)
✅ Retrieved entry: Test Concept
✅ Updated entry to version 2
...

======================================================================
  ✅ All Tests Passed!
======================================================================
```

### 3. Run with Docker Compose

```bash
# Start with PostgreSQL
docker-compose up -d

# Access pgAdmin (database management UI)
# URL: http://localhost:5050
# Email: admin@company.com
# Password: admin

# View logs
docker-compose logs -f postgres
docker-compose logs -f chatbot
```

## 📊 Database Schema

### Core Tables

#### `wiki_entries`
Structured knowledge base entries.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key (auto-increment) |
| entry_id | VARCHAR(100) | Unique identifier (indexed) |
| version | INTEGER | Version number |
| type | VARCHAR(50) | Entry type (concept/rule/process) |
| title | VARCHAR(200) | Entry title |
| content | TEXT | Markdown content |
| confidence | FLOAT | Confidence score (0.0-1.0) |
| status | VARCHAR(20) | active/archived/draft |
| created_at | TIMESTAMP | Creation time |
| updated_at | TIMESTAMP | Last update time |

#### `wiki_feedback`
User feedback tracking.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| entry_id | VARCHAR(100) | Foreign key to wiki_entries |
| user_id | VARCHAR(100) | User identifier |
| feedback_type | VARCHAR(20) | positive/negative/neutral |
| comment | TEXT | Optional comment |
| created_at | TIMESTAMP | Feedback time |

#### `api_keys`
API authentication keys.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| key_hash | VARCHAR(64) | Hashed API key |
| name | VARCHAR(100) | Key name |
| is_active | BOOLEAN | Active status |
| rate_limit | INTEGER | Requests per minute |
| total_requests | INTEGER | Usage counter |

#### `audit_logs`
Action audit trail.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| action | VARCHAR(50) | Action type |
| user_id | VARCHAR(100) | User identifier |
| endpoint | VARCHAR(200) | API endpoint |
| status_code | INTEGER | HTTP status code |
| created_at | TIMESTAMP | Log time |

## 🔧 Database Operations

### Using Repositories

Repositories provide a clean API for database operations:

```python
from app.db.database import get_db_manager
from app.db.repositories import WikiRepository

# Get database session
db_manager = get_db_manager()

with db_manager.get_session() as session:
    repo = WikiRepository(session)
    
    # Create
    entry = repo.create({
        "entry_id": "my_entry",
        "type": "concept",
        "title": "My Title",
        "content": "# Content",
        # ... other fields
    })
    
    # Read
    entry = repo.get_by_id("my_entry")
    
    # Update
    updated = repo.update("my_entry", {
        "content": "# Updated content"
    })
    
    # Delete
    repo.delete("my_entry")
    
    # Search
    results = repo.search("keyword", limit=10)
    
    # List all
    all_entries = repo.list_all(status_filter="active")
```

### Direct SQL Queries

For complex queries, you can use raw SQL:

```python
from sqlalchemy import text

with db_manager.get_session() as session:
    result = session.execute(
        text("SELECT COUNT(*) FROM wiki_entries WHERE status = :status"),
        {"status": "active"}
    )
    count = result.scalar()
```

## 🔄 Database Migrations

Use Alembic for schema migrations:

```bash
# Generate migration
alembic revision --autogenerate -m "Add new column"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# View history
alembic history
```

**Configuration:**
- Config file: `app/db/migrations/alembic.ini`
- Migration scripts: `app/db/migrations/versions/`

## 📈 Performance Tuning

### PostgreSQL Optimization

#### 1. Connection Pooling

Adjust pool settings in `.env`:

```ini
DB_POOL_SIZE=20          # Base pool size
DB_MAX_OVERFLOW=30       # Extra connections under load
DB_POOL_TIMEOUT=30       # Wait time for connection
DB_POOL_RECYCLE=1800     # Recycle connections every 30 min
```

#### 2. Indexes

Key indexes are already defined in models:

```python
__table_args__ = (
    Index('idx_wiki_title_type', 'title', 'type'),
    Index('idx_wiki_status_confidence', 'status', 'confidence'),
)
```

#### 3. Query Optimization

Use eager loading for relationships:

```python
from sqlalchemy.orm import joinedload

session.query(WikiEntry).options(
    joinedload(WikiEntry.feedbacks)
).filter(...)
```

### SQLite Optimization

SQLite uses WAL (Write-Ahead Logging) mode automatically for better concurrency:

```python
# Enabled by default in database.py
PRAGMA journal_mode=WAL
PRAGMA foreign_keys=ON
```

## 🆘 Troubleshooting

### Common Issues

#### 1. "Database not found" (PostgreSQL)

**Cause:** PostgreSQL server not running or connection string incorrect

**Solution:**
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Test connection
psql postgresql://user:pass@localhost:5432/dbname

# Check logs
docker logs chatbot-postgres
```

#### 2. "Table does not exist"

**Cause:** Database schema not initialized

**Solution:**
```bash
python scripts/init_db.py
```

#### 3. "Too many connections" (PostgreSQL)

**Cause:** Connection pool exhausted

**Solution:**
```ini
# Increase pool size in .env
DB_POOL_SIZE=30
DB_MAX_OVERFLOW=50
```

Or increase PostgreSQL max_connections:
```sql
ALTER SYSTEM SET max_connections = 200;
-- Restart PostgreSQL
```

#### 4. "Database is locked" (SQLite)

**Cause:** Concurrent write operations

**Solution:**
- SQLite only supports one writer at a time
- For production, switch to PostgreSQL
- For development, ensure proper session management:

```python
# Always use context manager
with db_manager.get_session() as session:
    # operations here
    pass  # Session automatically closed
```

#### 5. Migration conflicts

**Cause:** Manual schema changes without migration

**Solution:**
```bash
# Reset migrations (development only!)
rm -rf app/db/migrations/versions/*
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

## 🔐 Security Best Practices

### 1. Never Store Plain Text Passwords

Always hash sensitive data:

```python
from passlib.hash import bcrypt

hashed = bcrypt.hash("plain_password")
```

### 2. Use Environment Variables for Credentials

```bash
# ✅ Good
POSTGRES_DSN=postgresql://user:${DB_PASSWORD}@host/db

# ❌ Bad - Hardcoded in code
POSTGRES_DSN=postgresql://user:password123@host/db
```

### 3. Enable SSL for Production PostgreSQL

```ini
POSTGRES_DSN=postgresql://user:pass@host/db?sslmode=require
```

### 4. Restrict Database Access

In Kubernetes, use NetworkPolicy:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
spec:
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: chatbot
      ports:
        - port: 5432
```

## 📚 Additional Resources

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Migrations](https://alembic.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)

---

**Last Updated:** 2026-04-19  
**Status:** ✅ Production Ready
