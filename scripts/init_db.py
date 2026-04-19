"""
Database Initialization Script

Initializes the database schema and optionally seeds with sample data.
Supports both SQLite (development) and PostgreSQL (production).

Usage:
    python scripts/init_db.py              # Initialize with default settings
    python scripts/init_db.py --reset      # Drop and recreate all tables
    python scripts/init_db.py --seed       # Initialize and add sample data
"""
import argparse
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import get_db_manager
from app.db.models import WikiEntry
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database(reset: bool = False):
    """
    Initialize database schema.
    
    Args:
        reset: If True, drop all tables before creating
    """
    logger.info("=" * 70)
    logger.info("Database Initialization")
    logger.info("=" * 70)
    
    db_manager = get_db_manager()
    
    if reset:
        logger.warning("⚠️  Dropping all existing tables...")
        db_manager.drop_tables()
    
    logger.info("Creating database tables...")
    db_manager.create_tables()
    logger.info("✅ Database tables created successfully")
    
    # Show database info
    health = db_manager.health_check()
    logger.info(f"Database Type: {health.get('database', 'unknown')}")
    logger.info(f"Status: {health.get('status', 'unknown')}")
    
    return db_manager


def seed_sample_data(db_manager):
    """
    Seed database with sample wiki entries for testing.
    
    Args:
        db_manager: DatabaseManager instance
    """
    logger.info("\nSeeding sample data...")
    
    sample_entries = [
        {
            "entry_id": "concept_chatbot",
            "version": 1,
            "type": "concept",
            "title": "Chatbot Platform Overview",
            "summary": "Enterprise-level Agent platform based on LangGraph",
            "content": """# Chatbot Platform

An enterprise-level Agent platform supporting:
- Stateful workflow orchestration
- Control-M job management
- Playwright web automation
- RAG knowledge base search
- LLM Wiki structured knowledge
- JWT authentication
- Rate limiting
- Comprehensive monitoring

## Architecture

The platform uses a plugin-based skill architecture where each skill is a self-contained module.
""",
            "aliases": ["agent platform", "langgraph bot"],
            "tags": ["overview", "architecture", "platform"],
            "related_ids": [],
            "sources": ["README.md"],
            "confidence": 0.95,
            "status": "active",
            "compiled_at": datetime.utcnow(),
        },
        {
            "entry_id": "process_deploy",
            "version": 1,
            "type": "process",
            "title": "Kubernetes Deployment Process",
            "summary": "Steps to deploy chatbot to Kubernetes cluster",
            "content": """# Kubernetes Deployment

## Prerequisites
- Kubernetes cluster (v1.24+)
- kubectl configured
- Docker installed

## Deployment Steps

1. Build Docker image:
   ```bash
   docker build -t chatbot:latest .
   ```

2. Apply K8s manifests:
   ```bash
   kubectl apply -k k8s/
   ```

3. Verify deployment:
   ```bash
   kubectl get all -n chatbot
   ```
""",
            "aliases": ["k8s deploy", "kubernetes setup"],
            "tags": ["deployment", "kubernetes", "devops"],
            "related_ids": [{"entry_id": "concept_chatbot", "relation": "implements"}],
            "sources": ["k8s/README.md"],
            "confidence": 0.90,
            "status": "active",
            "compiled_at": datetime.utcnow(),
        },
        {
            "entry_id": "rule_security",
            "version": 1,
            "type": "rule",
            "title": "Security Best Practices",
            "summary": "Essential security guidelines for production deployment",
            "content": """# Security Guidelines

## Authentication
- Use LDAP/Active Directory for user authentication
- Implement JWT tokens with short expiration (30 min)
- Rotate JWT_SECRET regularly

## API Security
- Enable rate limiting on all endpoints
- Use API keys for service-to-service communication
- Implement CORS policies

## Data Protection
- Never commit .env files to version control
- Use external secret management (Vault, AWS Secrets Manager)
- Encrypt sensitive data at rest

## Network Security
- Use LDAPS for LDAP connections
- Enable TLS for all external endpoints
- Configure NetworkPolicy in Kubernetes
""",
            "aliases": ["security rules", "best practices"],
            "tags": ["security", "compliance", "production"],
            "related_ids": [],
            "sources": ["docs/LDAP_INTEGRATION_GUIDE.md"],
            "confidence": 0.98,
            "status": "active",
            "compiled_at": datetime.utcnow(),
        },
    ]
    
    with db_manager.get_session() as session:
        for entry_data in sample_entries:
            # Check if entry already exists
            existing = session.query(WikiEntry).filter(
                WikiEntry.entry_id == entry_data["entry_id"]
            ).first()
            
            if existing:
                logger.info(f"  ⏭️  Skipping existing entry: {entry_data['entry_id']}")
                continue
            
            entry = WikiEntry(**entry_data)
            session.add(entry)
            logger.info(f"  ✅ Created: {entry_data['entry_id']}")
        
        session.commit()
    
    logger.info("✅ Sample data seeded successfully")


def main():
    parser = argparse.ArgumentParser(description="Initialize chatbot database")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop all tables before creating (WARNING: destroys all data)"
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Seed database with sample data"
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize database
        db_manager = init_database(reset=args.reset)
        
        # Seed sample data if requested
        if args.seed:
            seed_sample_data(db_manager)
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ Database initialization complete!")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"\n❌ Database initialization failed: {e}")
        logger.exception("Stack trace:")
        sys.exit(1)


if __name__ == "__main__":
    main()
