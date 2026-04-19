# Documentation Index

This directory contains detailed technical guides for the LangGraph Enterprise Agent Platform.

## 📚 Available Documentation

### Core Guides

| Document | Description | Size |
|----------|-------------|------|
| [API Authentication & Rate Limiting](API_AUTH_AND_RATE_LIMITING_GUIDE.md) | Phase 1 implementation: API key auth, rate limiting with slowapi | 12 KB |
| [LDAP Integration Guide](LDAP_INTEGRATION_GUIDE.md) | **NEW**: Active Directory authentication via LDAP protocol | 8 KB |
| [JWT Authentication Guide](JWT_AUTHENTICATION_GUIDE.md) | JWT token management and validation (updated for LDAP) | 15 KB |
| [Monitoring & Observability Guide](PHASE3_MONITORING_GUIDE.md) | Phase 3 implementation: Prometheus metrics, Grafana dashboard, alert rules | 23 KB |

### Database & Persistence

| Document | Description | Size |
|----------|-------------|------|
| [Database Configuration Guide](DATABASE_CONFIGURATION_GUIDE.md) | **NEW**: PostgreSQL/SQLite dual architecture setup and usage | 10 KB |
| [Database Integration Summary](DATABASE_INTEGRATION_SUMMARY.md) | **NEW**: Migration from memory/file storage to database repositories | 9 KB |

### Knowledge Management

| Document | Description | Size |
|----------|-------------|------|
| [RAG Integration Guide](RAG_INTEGRATION_GUIDE.md) | Complete guide for integrating company Group AI Platform RAG API | 10 KB |
| [LLM Wiki Compiler Guide](LLM_WIKI_COMPILER_GUIDE.md) | LLM-powered wiki compilation with one-shot JSON generation | 17 KB |
| [Enhanced Wiki Compiler v2.0](ENHANCED_WIKI_COMPILER_V2.md) | Advanced wiki compiler with deduplication and version history | 19 KB |
| [Enhanced Wiki Knowledge Graph](ENHANCED_WIKI_KNOWLEDGE_GRAPH.md) | Knowledge graph construction with relationship resolution | 14 KB |
| [Local Wiki Engine Guide](LOCAL_WIKI_ENGINE_GUIDE.md) | File-based local wiki engine for offline capability | 10 KB |
| [Wiki Feedback API Guide](WIKI_FEEDBACK_API_GUIDE.md) | User feedback system for wiki articles with confidence scoring | 14 KB |
| [Wiki Integration Guide](WIKI_INTEGRATION_GUIDE.md) | Complete wiki integration guide with examples | 10 KB |

## 🎯 Quick Reference

For most users, the **[README.md](../README.md)** file in the project root contains all essential information including:
- Quick start guide
- Architecture overview
- Core features summary
- API documentation
- Configuration guide
- Deployment instructions

Use the detailed guides in this directory when you need:
- In-depth technical explanations
- Implementation details
- Advanced configuration options
- Troubleshooting specific components

## 📖 Reading Recommendations

### For New Users
1. Start with [README.md](../README.md)
2. Read [LDAP Integration Guide](LDAP_INTEGRATION_GUIDE.md) for authentication setup
3. Read [Database Configuration Guide](DATABASE_CONFIGURATION_GUIDE.md) for persistence setup
4. Read [RAG Integration Guide](RAG_INTEGRATION_GUIDE.md) if using knowledge base

### For Developers
1. [LLM Wiki Compiler Guide](LLM_WIKI_COMPILER_GUIDE.md) - Understanding wiki architecture
2. [Enhanced Wiki Compiler v2.0](ENHANCED_WIKI_COMPILER_V2.md) - Advanced features
3. [Monitoring Guide](PHASE3_MONITORING_GUIDE.md) - Setting up observability

### For DevOps/Admins
1. [LDAP Integration Guide](LDAP_INTEGRATION_GUIDE.md) - AD authentication setup
2. [API Auth & Rate Limiting](API_AUTH_AND_RATE_LIMITING_GUIDE.md) - Security setup
3. [Monitoring Guide](PHASE3_MONITORING_GUIDE.md) - Prometheus/Grafana deployment
4. [Local Wiki Engine](LOCAL_WIKI_ENGINE_GUIDE.md) - Backup and recovery

## 🔗 Related Resources

- **API Documentation**: http://localhost:8000/api/v1/docs (Swagger UI)
- **Prometheus Metrics**: http://localhost:8000/metrics
- **Grafana Dashboard**: http://localhost:3000 (after setup)
- **Project Repository**: See project root for source code

---

**Last Updated:** 2026-04-19  
**Total Documents:** 11 guides  
**Purpose:** Detailed technical reference documentation
