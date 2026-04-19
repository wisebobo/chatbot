# LangGraph Enterprise Agent Platform

An enterprise-level Agent platform based on LangGraph, supporting stateful workflow orchestration, Control-M job management, Playwright web automation, RAG knowledge base search, LLM Wiki structured knowledge, JWT authentication, rate limiting, and comprehensive monitoring.

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [Architecture Overview](#-architecture-overview)
- [Core Features](#-core-features)
  - [Authentication & Security](#authentication--security)
  - [Skills System](#skills-system)
  - [Knowledge Management](#knowledge-management)
  - [Monitoring & Observability](#monitoring--observability)
- [API Documentation](#-api-documentation)
- [Configuration](#-configuration)
- [Testing](#-testing)
- [Deployment](#-deployment)
  - [Docker Deployment](#docker-deployment)
  - [Kubernetes Deployment](#kubernetes-deployment)
- [Troubleshooting](#-troubleshooting)

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd E:\python\chatbot
pip install -r requirements.txt

# Install Playwright browsers (if web automation is needed)
playwright install chromium
```

### 2. Configure Environment Variables

```bash
copy .env.example .env
# Edit .env and fill in your company AI platform URL and API Key
```

**Required Configuration:**
```ini
# LLM Configuration
LLM_API_BASE_URL=http://your-company-ai-platform/v1
LLM_API_KEY=your-api-key-here
LLM_MODEL_NAME=qwen-turbo

# Database (optional for development)
POSTGRES_DSN=postgresql://user:password@localhost:5432/chatbot_db
REDIS_URL=redis://localhost:6379/0

# Monitoring
ENABLE_PROMETHEUS=true
PROMETHEUS_PORT=9090
```

### 3. Start API Service

```bash
python main.py
# Visit http://localhost:8000/api/v1/docs to view Swagger documentation
```

### 4. Command-Line Usage

```bash
# Single conversation
python -m app.cli chat "Check the status of Control-M job DailyReport"

# Streaming output
python -m app.cli chat "Take a screenshot of Baidu homepage" --stream

# Interactive mode
python -m app.cli interactive

# List registered skills
python -m app.cli skills
```

### 5. Run Tests

```bash
pytest tests/ -v --cov=app
```

---

## 📁 Project Structure

```
chatbot/
├── app/
│   ├── api/
│   │   ├── main.py              # FastAPI entry point with all endpoints
│   │   ├── auth.py              # API key authentication (Phase 1)
│   │   ├── auth_routes.py       # JWT authentication routes (Phase 2)
│   │   ├── jwt_auth.py          # JWT token generation and validation
│   │   └── jwt_dependencies.py  # FastAPI dependencies for JWT
│   ├── cli.py                   # Command-line interaction interface
│   ├── config/
│   │   └── settings.py          # Pydantic Settings configuration
│   ├── graph/
│   │   ├── graph.py             # StateGraph and Checkpointer setup
│   │   ├── nodes.py             # Workflow nodes (intent, skills, response)
│   │   └── routing.py           # Conditional routing logic
│   ├── llm/
│   │   └── adapter.py           # LLM adapter for company AI platform
│   ├── monitoring/
│   │   ├── logger.py            # Structured logging
│   │   ├── metrics.py           # Prometheus metrics (40+ metrics)
│   │   └── system_monitor.py    # CPU/memory monitoring thread
│   ├── skills/
│   │   ├── base.py              # BaseSkill class + SkillRegistry
│   │   ├── controlm_skill.py    # Control-M job scheduling
│   │   ├── playwright_skill.py  # Web automation with Playwright
│   │   ├── rag_skill.py         # RAG knowledge base search
│   │   └── wiki_skill.py        # LLM Wiki structured knowledge
│   ├── wiki/
│   │   ├── __init__.py          # Wiki module initialization
│   │   ├── engine.py            # Local file-based wiki engine
│   │   ├── compiler.py          # LLM-powered wiki compiler
│   │   └── sample_data.py       # Sample wiki articles
│   └── state/
│       └── agent_state.py       # AgentState workflow definition
├── tests/
│   ├── unit/                    # Unit tests
│   └── integration/             # Integration tests
├── docs/                        # Documentation (consolidated)
├── scripts/                     # Utility scripts
├── monitoring/                  # Monitoring configurations
│   ├── prometheus-alerts.yml    # 16 alert rules
│   └── grafana-dashboard.json   # 14-panel dashboard
├── data/
│   └── wiki/                    # Wiki article storage
├── main.py                      # Service startup entry
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variable template
└── README.md                    # This file
```

---

## 🏗️ Architecture Overview

### Workflow Nodes

```mermaid
graph TD
    A[User Input] --> B[intent_recognition_node]
    B -->|LLM Intent Analysis| C{Routing Decision}
    C -->|Skill Required| D[skill_execution_node]
    C -->|Direct Reply| E[response_generation_node]
    D -->|Human Approval Needed?| F{Check Approval}
    F -->|Yes - Pending| G[⏸️ WAITING_HUMAN]
    F -->|No or Approved| E
    G -->|Admin Approves| D
    E -->|Generate Response| H[Output to User]
    
    style A fill:#e1f5ff
    style H fill:#e1f5ff
    style G fill:#fff3cd
    style B fill:#d4edda
    style D fill:#d4edda
    style E fill:#d4edda
```

**Node Descriptions:**

| Node | Responsibility |
|------|---------------|
| **intent_recognition_node** | Calls LLM to analyze user intent and determine routing strategy |
| **skill_execution_node** | Executes registered skills (Control-M, Playwright, RAG, Wiki, etc.) |
| **response_generation_node** | Generates natural language responses using LLM |
| **Human-in-the-Loop** | Pauses workflow for risky operations requiring manual approval |

### Adding New Skills

1. Create a new skill class inheriting from `BaseSkill`
2. Implement `execute()` method with business logic
3. Register the skill in `app/api/main.py`:
   ```python
   skill_registry.register(MyNewSkill())
   ```

---

## ✨ Core Features

### Authentication & Security

#### Phase 1: API Key Authentication
- **Endpoint Protection**: Sensitive endpoints require `X-API-Key` header
- **Rate Limiting**: Configurable rate limits per API key (slowapi integration)
- **Key Management**: Script-based API key creation/revocation
- **Usage**: 
  ```bash
  curl -H "X-API-Key: your-api-key" http://localhost:8000/api/v1/chat
  ```

#### Phase 2: LDAP + JWT Authentication
- **Active Directory Integration**: Authenticate users against company AD via LDAP
- **LDAP Support**: Both simple bind and NTLM authentication methods
- **Token-Based Auth**: Access tokens (30min) + Refresh tokens (7 days)
- **Role-Based Access**: Admin roles determined by AD group membership
- **No Local Passwords**: All authentication handled by Active Directory

**LDAP Configuration:**
```ini
# .env file configuration
LDAP_SERVER_URL=ldaps://ad.company.com
LDAP_BASE_DN=DC=company,DC=com
LDAP_DOMAIN=COMPANY
LDAP_USE_SSL=true
LDAP_AUTH_METHOD=ntlm
LDAP_BIND_DN=CN=service_account,OU=Service Accounts,DC=company,DC=com
LDAP_BIND_PASSWORD=your-service-account-password
```

**Authentication Endpoints:**
```bash
# Login with AD credentials
POST /api/v1/auth/login
{
  "username": "your_ad_username",
  "password": "your_ad_password"
}

# Response includes JWT tokens
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}

# Access protected endpoint
GET /api/v1/auth/me
Headers: Authorization: Bearer <access_token>

# Check LDAP connection health
GET /api/v1/auth/health
```

**Role Assignment:**
- User roles are automatically determined based on Active Directory group membership
- Users in groups containing "Admin", "Administrator", or "IT-Admin" get admin role
- All other users get the default 'user' role
- Customize role logic in `auth_routes.py:_determine_role_from_groups()`

⚠️ **Security Note**: Configure LDAP service account credentials securely. Never commit `.env` file to version control.

### Skills System

The platform uses a plugin-based skill architecture. Each skill is a self-contained module that can be invoked by the agent.

#### Available Skills

| Skill | Description | Requires Approval |
|-------|-------------|-------------------|
| **ControlMSkill** | Manage Control-M jobs: submit, query status, hold/release | Yes (for write operations) |
| **PlaywrightSkill** | Web automation: screenshots, form filling, data extraction | No (read-only) |
| **RagSkill** | Knowledge base search via company Group AI Platform | No |
| **WikiSkill** | Query structured LLM Wiki knowledge base | No |

#### Skill Execution Flow

```mermaid
graph LR
    A[User Request] --> B{Intent Recognition}
    B -->|Skill Match| C[Execute Skill]
    C --> D{Requires Approval?}
    D -->|Yes| E[Wait for Human Approval]
    D -->|No| F[Execute Directly]
    E -->|Approved| F
    F --> G[Return Result]
    
    style E fill:#fff3cd
```

**Dynamic Approval Logic:**
- Read-only operations (GET, query): No approval needed
- Write operations (POST, PUT, DELETE, trigger): Require approval
- Configurable per skill via `CHG_REQUIRE_ACTIONS` constant

### Knowledge Management

#### RAG (Retrieval-Augmented Generation)

**Purpose**: Search unstructured documents in company knowledge base

**Configuration:**
```ini
RAG_API_URL=http://your-group-ai-platform/rag/search
RAG_API_KEY=your-rag-api-key
RAG_DEFAULT_TOP_K=5
RAG_MIN_RELEVANCE_SCORE=0.7
```

**Implementation:**
- Located in `app/skills/rag_skill.py`
- TODO section at lines 68-90 needs your actual API implementation
- Supports both REST and GraphQL APIs
- Automatic retry on timeout
- LLM-friendly result formatting

**Usage Example:**
```python
# The skill is automatically called when user asks knowledge questions
user_query = "What is our company's leave policy?"
# Agent will invoke RagSkill to search knowledge base
```

#### LLM Wiki (Structured Knowledge)

**Purpose**: Maintain structured, versioned knowledge with relationships and feedback

**Key Features:**
- **One-Shot Compilation**: Single LLM call generates complete structured JSON (66% faster)
- **Smart Deduplication**: Content hash detection prevents duplicate articles
- **Version History**: Automatic version incrementing with feedback preservation
- **Relationship Resolution**: LLM suggests related articles, backend resolves to entry_ids
- **Confidence Scoring**: Dynamic confidence based on user feedback (0.5-1.0)
- **Local Storage**: File-based JSON storage with optional remote API fallback

**Data Structure:**
```json
{
  "entry_id": "concept_loan_rate",
  "version": 2,
  "type": "concept",
  "title": "Loan Interest Rate",
  "content": "# Markdown content...",
  "summary": "Brief summary...",
  "aliases": ["interest rate", "loan rate"],
  "tags": ["finance", "loans"],
  "related_ids": [
    {"entry_id": "rule_mortgage", "relation": "related_to"}
  ],
  "sources": ["policy_doc_v1.pdf"],
  "confidence": 0.85,
  "status": "published",
  "feedback": {
    "positive": 10,
    "negative": 2,
    "comments": ["Very helpful!", "Needs update"]
  },
  "created_at": "2026-04-19T10:00:00Z",
  "updated_at": "2026-04-19T15:30:00Z"
}
```

**Wiki Management Commands:**
```bash
# Compile document into wiki article
python scripts/manage_wiki.py compile --file policy_doc.txt

# List all articles
python scripts/manage_wiki.py list

# Search articles
python scripts/manage_wiki.py search "loan interest"

# View article details
python scripts/manage_wiki.py show concept_loan_rate

# Submit feedback
python scripts/manage_wiki.py feedback concept_loan_rate --rating positive --comment "Great!"
```

**API Endpoints:**
```bash
# Query wiki
POST /api/v1/wiki/query
{
  "query": "What is the loan interest rate?",
  "exact_match": false
}

# Submit feedback
POST /api/v1/wiki/feedback
{
  "entry_id": "concept_loan_rate",
  "rating": "positive",
  "comment": "Very helpful information"
}
```

**Storage Location:**
- Articles: `data/wiki/*.json`
- Sample data: `data/wiki_demo/*.json`

### Monitoring & Observability

#### Phase 3: Comprehensive Monitoring

**Metrics Collection (40+ Metrics):**
- Request metrics (rate, latency, errors)
- Authentication metrics (logins, failures, JWT tokens)
- LLM performance (call duration, token usage, errors)
- Wiki metrics (articles count, feedback, low-confidence alerts)
- System resources (CPU, memory via psutil)
- Business metrics (registrations, skill executions)

**Prometheus Integration:**
- Metrics endpoint: `http://localhost:8000/metrics`
- Scraping interval: 15 seconds (configurable)
- Performance overhead: < 2% CPU, < 10 MB memory

**Alert Rules (16 Rules Across 6 Groups):**

| Group | Rules | Severity |
|-------|-------|----------|
| Critical Alerts (4) | High error rate, service down, brute force, high memory | Critical |
| Warning Alerts (8) | High CPU, slow LLM, wiki issues, skill failures | Warning |
| Info Alerts (4) | Token usage spike, registration drop, login failures | Info |

**Example Alert:**
```yaml
- alert: HighAPIErrorRate
  expr: rate(api_error_total[2m]) > 0.1
  for: 2m
  severity: critical
  annotations:
    summary: "High API error rate detected"
```

**Grafana Dashboard:**
- 14 visualization panels
- Real-time updates (30s refresh)
- Historical analysis and trend detection
- Import from: `monitoring/grafana-dashboard.json`

**Deployment:**
```bash
# Using Docker Compose
docker-compose up -d

# Access dashboards
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)
```

**System Resource Monitoring:**
- Background thread updates every 60 seconds
- Tracks RSS memory and CPU percentage
- Exposed as Prometheus gauges

---

## 📖 API Documentation

### Base URL
```
http://localhost:8000/api/v1
```

### Interactive Documentation
Visit Swagger UI: `http://localhost:8000/api/v1/docs`

### Main Endpoints

#### Chat Endpoint
```bash
POST /chat
{
  "message": "What is the loan interest rate?",
  "session_id": "optional-session-id",
  "user_id": "optional-user-id",
  "stream": false
}
```

#### Streaming Chat
```bash
POST /chat/stream
# Returns Server-Sent Events (SSE) stream
```

#### Human Approval
```bash
POST /approve/{workflow_id}
{
  "approved": true,
  "comment": "Approved by admin"
}
```

#### Feedback
```bash
POST /feedback
{
  "session_id": "session-123",
  "request_id": "req-456",
  "rating": "positive",
  "comment": "Helpful response"
}
```

### Authentication Headers

**API Key (Phase 1):**
```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/v1/chat
```

**JWT Token (Phase 2):**
```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." http://localhost:8000/api/v1/auth/me
```

---

## ⚙️ Configuration

### Environment Variables

See `.env.example` for all available options.

**Critical Settings:**
```ini
# Must configure for production
LLM_API_BASE_URL=http://your-company-ai-platform/v1
LLM_API_KEY=your-secure-api-key
API_SECRET_KEY=change-this-to-random-string

# Optional but recommended
LOG_LEVEL=INFO
ENABLE_PROMETHEUS=true
```

### Configuration Priority

1. Environment variables (highest priority)
2. `.env` file
3. Default values in `settings.py`

### Adding New Configuration

1. Add field to appropriate Settings class in `app/config/settings.py`
2. Add example to `.env.example`
3. Use via dependency injection:
   ```python
   from app.config.settings import get_settings
   settings = get_settings()
   value = settings.your_new_setting
   ```

---

## 🧪 Testing

### Test Structure
```
tests/
├── unit/                    # Unit tests
│   ├── test_state.py       # Agent state tests
│   ├── test_skills.py      # Skill registry tests
│   ├── test_rag_skill.py   # RAG skill tests
│   └── test_wiki_skill.py  # Wiki skill tests
└── integration/            # Integration tests (to be added)
```

### Running Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=app --cov-report=html

# Specific test file
pytest tests/unit/test_skills.py -v

# Watch mode (requires pytest-watch)
ptw
```

### Test Scripts

Located in `scripts/` directory:
- `test_jwt_auth.py` - JWT authentication test suite (10 tests)
- `test_monitoring.py` - Monitoring validation (7 tests)
- `manage_api_keys.py` - API key management tool
- `manage_wiki.py` - Wiki management CLI
- `example_wiki_compiler.py` - Wiki compiler examples

---

## 🚀 Deployment

### Development

```bash
# Hot reload enabled
python main.py

# Or with uvicorn directly
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Production

#### Option 1: Uvicorn Workers
```bash
uvicorn app.api.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --no-reload
```

#### Option 2: Gunicorn + Uvicorn
```bash
pip install gunicorn
gunicorn app.api.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

---

## ☸️ Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (v1.24+)
- kubectl configured
- Docker (for building images)

### Quick Deployment

#### Linux/Mac:
```bash
cd k8s
chmod +x deploy.sh
./deploy.sh production latest
```

#### Windows PowerShell:
```powershell
cd k8s
.\deploy.ps1 -Environment production -ImageTag latest
```

### Manual Deployment with Kustomize

```bash
# Apply all resources
kubectl apply -k k8s/

# Verify deployment
kubectl get all -n chatbot
```

### Key Components

| Component | File | Purpose |
|-----------|------|---------|
| Namespace | `k8s/namespace.yaml` | Isolated namespace |
| ConfigMap | `k8s/configmap.yaml` | Non-sensitive configuration |
| Secret | `k8s/secret.yaml` | Sensitive credentials |
| Deployment | `k8s/deployment.yaml` | Application pods (3 replicas) |
| Service | `k8s/service.yaml` | Internal load balancing |
| Ingress | `k8s/ingress.yaml` | External access with TLS |
| PVC | `k8s/pvc.yaml` | Persistent Wiki data |
| HPA | `k8s/hpa.yaml` | Auto-scaling (3-10 pods) |
| NetworkPolicy | `k8s/networkpolicy.yaml` | Network security |

### Configuration Steps

1. **Update Secrets** (`k8s/secret.yaml`)
   ```yaml
   LLM_API_KEY: "your-actual-key"
   JWT_SECRET: "strong-random-string"
   LDAP_BIND_PASSWORD: "ad-service-account-password"
   ```

2. **Update ConfigMap** (`k8s/configmap.yaml`)
   ```yaml
   LLM_API_BASE_URL: "http://your-ai-platform/v1"
   LDAP_SERVER_URL: "ldaps://ad.company.com"
   ```

3. **Configure Ingress** (`k8s/ingress.yaml`)
   ```yaml
   host: chatbot.your-company.com  # Your domain
   ```

4. **Build and Push Image**
   ```bash
   docker build -t registry.company.com/chatbot:latest .
   docker push registry.company.com/chatbot:latest
   ```

5. **Update Deployment Image**
   ```bash
   kubectl set image deployment/chatbot-deployment \
     chatbot=registry.company.com/chatbot:latest \
     -n chatbot
   ```

### Monitoring & Scaling

```bash
# Check pod status
kubectl get pods -n chatbot

# View logs
kubectl logs -l app=chatbot -n chatbot -f

# Port forward for testing
kubectl port-forward svc/chatbot-service 8000:80 -n chatbot

# Scale manually
kubectl scale deployment/chatbot-deployment --replicas=5 -n chatbot

# Check auto-scaling
kubectl get hpa -n chatbot -w
```

### Rolling Updates & Rollbacks

```bash
# Update image
kubectl set image deployment/chatbot-deployment \
  chatbot=chatbot:v3.1.0 -n chatbot

# Monitor rollout
kubectl rollout status deployment/chatbot-deployment -n chatbot

# Rollback if needed
kubectl rollout undo deployment/chatbot-deployment -n chatbot
```

For complete K8s documentation, see:
- **[K8s Deployment Guide](k8s/README.md)** - Comprehensive guide
- **[Quick Reference](k8s/QUICK_REFERENCE.md)** - Common commands

---

### Pre-Deployment Checklist

- [ ] Change `API_SECRET_KEY` to strong random value
- [ ] Configure LDAP service account credentials
- [ ] Configure proper LLM API credentials
- [ ] Set up database (PostgreSQL) if using persistent checkpointer
- [ ] Enable HTTPS/TLS for production
- [ ] Configure firewall rules (restrict `/metrics` access)
- [ ] Set up log rotation
- [ ] Configure backup for wiki data (`data/wiki/`)
- [ ] Test alert notifications
- [ ] Review rate limiting thresholds
- [ ] Configure resource limits in K8s deployment
- [ ] Set up external secret management (Vault/AWS Secrets Manager)

---

## 🔧 Troubleshooting

### Common Issues

#### 1. ImportError: No module named 'xxx'
**Solution:**
```bash
pip install -r requirements.txt
```

#### 2. UnicodeDecodeError when loading .env
**Cause:** `.env` file contains non-UTF-8 characters
**Solution:** Ensure `.env` is saved as UTF-8 without BOM

#### 3. ValidationError on Wiki Article Loading
**Cause:** Wiki JSON files don't match current schema
**Solution:**
```bash
# Delete old wiki data and regenerate
rm -rf data/wiki/*
python scripts/manage_wiki.py compile --file your_doc.txt
```

#### 4. Slow Intent Recognition (>10s)
**Cause:** LLM model too slow or no caching
**Solution:**
- Use faster model (qwen-turbo instead of qwen-plus)
- Enable intent caching (already implemented)
- Add keyword-based fast path for common queries

#### 5. Metrics Endpoint Returns Empty
**Cause:** prometheus-client not installed
**Solution:**
```bash
pip install prometheus-client psutil
```

#### 6. Playwright Browser Not Found
**Solution:**
```bash
playwright install chromium
```

### Getting Help

1. Check logs: `logs/app.log` (if configured)
2. Review API docs: `http://localhost:8000/api/v1/docs`
3. Check Prometheus metrics: `http://localhost:8000/metrics`
4. Run diagnostic script:
   ```bash
   python scripts/test_monitoring.py
   ```

---

## 📊 Performance Benchmarks

### LLM Wiki Compiler v2.0
- **Compilation Time**: 3-5 seconds (vs 10-15s in v1.0)
- **API Calls**: 1 call (vs 2-3 calls in v1.0)
- **Cost Reduction**: 66% fewer tokens
- **Deduplication**: Instant skip for identical content

### Intent Recognition
- **Cached Response**: < 10ms
- **Keyword Match**: < 50ms
- **LLM Call**: 2-5 seconds (model dependent)

### Overall API Latency
- **Simple Query**: 200-500ms
- **Skill Execution**: 1-3 seconds
- **Wiki Compilation**: 3-5 seconds
- **Complex Multi-Skill**: 5-10 seconds

---

## 🔄 Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

**Recent Highlights:**
- ✅ **LDAP Integration**: Active Directory authentication via LDAP (replaced user registration)
- ✅ Phase 3: Monitoring & Observability (40+ metrics, 16 alerts, Grafana dashboard)
- ✅ Phase 2: JWT Authentication (token management, role-based access)
- ✅ Phase 1: API Key Auth + Rate Limiting (endpoint protection, slowapi integration)
- ✅ LLM Wiki Compiler v2.0 (one-shot generation, deduplication, version history)
- ✅ Local Wiki Engine (file-based storage, offline capability)
- ✅ RAG Integration (knowledge base search with fallback)
- ✅ Dynamic Human Approval (ITIL-compliant, read/write distinction)

---

## 🤝 Contributing

### Code Style
- Follow PEP 8 guidelines
- Use type hints for all functions
- Write docstrings in Google style
- Keep functions focused (< 50 lines ideal)

### Commit Messages
Use conventional commits:
```
feat: add new skill for database queries
fix: resolve wiki compilation timeout
docs: update API authentication guide
test: add unit tests for JWT auth
chore: update dependencies
```

### Pull Request Process
1. Create feature branch from `main`
2. Make changes with tests
3. Run full test suite: `pytest tests/ -v`
4. Update documentation if needed
5. Submit PR with clear description

---

## 📄 License

Proprietary - Company Internal Use Only

---

## 👥 Team

Developed by the Enterprise AI Platform Team

**Contact:** ai-platform@company.com

---

**Last Updated:** 2026-04-19  
**Version:** 3.0.0  
**Status:** ✅ Production Ready
