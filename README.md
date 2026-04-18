# LangGraph Enterprise Agent Platform

An enterprise-level Agent platform based on LangGraph, supporting stateful workflow orchestration, Control-M job management, Playwright web automation, and more.

## 📁 Project Structure

```
chatbot/
├── app/
│   ├── api/
│   │   └── main.py           # FastAPI entry point, RESTful API + streaming endpoints
│   ├── cli.py                # Command-line interaction entry point
│   ├── config/
│   │   └── settings.py       # Pydantic Settings configuration management
│   ├── graph/
│   │   ├── graph.py          # StateGraph construction and Checkpointer configuration
│   │   ├── nodes.py          # Workflow nodes (intent recognition, skill execution, response generation)
│   │   └── routing.py        # Conditional routing functions
│   ├── llm/
│   │   └── adapter.py        # LLM adapter layer, wraps company AI platform calls
│   ├── monitoring/
│   │   ├── logger.py         # Structured logging (structlog/standard library)
│   │   └── metrics.py        # Prometheus monitoring metrics
│   ├── persistence/          # Extension: custom persistence logic
│   ├── skills/
│   │   ├── base.py           # BaseSkill base class + SkillRegistry
│   │   ├── controlm_skill.py # Control-M job scheduling skill
│   │   ├── playwright_skill.py # Playwright web automation skill
│   │   ├── rag_skill.py      # RAG knowledge base search skill (requires API configuration)
│   │   └── wiki_skill.py     # LLM Wiki structured knowledge query skill (works locally or with API)
│   ├── wiki/
│   │   ├── __init__.py       # Wiki module initialization
│   │   ├── engine.py         # Local wiki engine with file-based storage
│   │   └── sample_data.py    # Sample wiki articles for demonstration
│   └── state/
│       └── agent_state.py    # AgentState workflow state definition
├── tests/
│   ├── unit/
│   │   ├── test_state.py
│   │   ├── test_skills.py
│   │   ├── test_rag_skill.py
│   │   └── test_wiki_skill.py
│   └── integration/
├── docs/
├── scripts/
├── main.py                   # Service startup entry point
├── requirements.txt
├── .env.example
└── README.md
```

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

## 🏗️ Architecture Overview

### Workflow Nodes

```
User Input
    ↓
intent_recognition_node   ← Call LLM to recognize intent and decide routing
    ↓ (conditional routing)
skill_execution_node      ← Execute Control-M / Playwright and other skills
    ↓                       (supports human-in-the-loop approval)
response_generation_node  ← Stream natural language response generation
    ↓
Output to user
```

### Adding New Skills

```python
# 1. Inherit from BaseSkill
from app.skills.base import BaseSkill, SkillOutput

class MyNewSkill(BaseSkill):
    name = "my_skill"
    description = "Do something specific"
    require_human_approval = False

    async def execute(self, params):
        # Implement your business logic
        return SkillOutput(success=True, data={"result": "done"})

# 2. Register in app/api/main.py
skill_registry.register(MyNewSkill())
```

### Knowledge Base Search (RAG & Wiki)

The project includes two complementary knowledge search skills:

#### RAG (Retrieval-Augmented Generation)
Supports retrieving information from unstructured enterprise documents using semantic search. Configure the Group AI Platform API before use:

1. Edit `.env` file and set `RAG_API_URL` and `RAG_API_KEY`
2. Fill in the actual API call logic in `app/skills/rag_skill.py` (see TODO comments)
3. Restart the service to use

For detailed integration guide, please refer to: [docs/RAG_INTEGRATION_GUIDE.md](docs/RAG_INTEGRATION_GUIDE.md)

#### LLM Wiki

Provides access to structured wiki knowledge base with curated articles and clear organization. **Works out of the box with local engine - no API required!**

**Mode 1: Local Engine (Default - No Configuration Needed)** ✅
- Uses built-in wiki engine with file-based storage
- Pre-loaded with 6 sample articles (HR, IT, Finance policies)
- Works immediately without any setup
- Full control over your data

**Mode 2: Remote API (Optional)**
If your company provides a Group AI Platform Wiki API:
1. Edit `.env` file and set `WIKI_API_URL` and `WIKI_API_KEY`
2. System automatically switches to remote mode
3. Restart the service

For detailed guides:
- [Local Wiki Engine Guide](docs/LOCAL_WIKI_ENGINE_GUIDE.md) - Complete local usage instructions
- [Wiki Integration Guide](docs/WIKI_INTEGRATION_GUIDE.md) - Remote API integration

**When to Use Which:**
- **Wiki**: Official documentation, known policies, structured procedures
- **RAG**: Exploratory queries, cross-document search, unstructured content

**Example Conversations:**
```
User: What is the annual leave policy?
Assistant: [Automatically calls wiki_search skill] → [Returns official HR policy article]
           According to the Annual Leave Policy wiki article, employees are entitled to...

User: How do I troubleshoot network issues?
Assistant: [Automatically calls rag_search skill] → [Searches across IT documents]
           Based on multiple IT support documents, here are common troubleshooting steps...
```

### Human-in-the-Loop

The platform supports **dynamic human approval** based on operation type (following ITIL change management standards):

#### How It Works

Skills can define which operations require approval using `CHG_REQUIRE_ACTIONS`:

```python
class ControlMSkill(BaseSkill):
    name = "controlm_job"
    
    # Operations requiring change management approval
    CHG_REQUIRE_ACTIONS = {"run", "hold", "free", "delete"}
    
    async def requires_approval_for(self, params: Dict[str, Any]) -> bool:
        """Dynamically check if this action needs approval"""
        action = params.get("action", "").lower()
        return action in self.CHG_REQUIRE_ACTIONS
```

#### Approval Behavior

| Operation Type | Example | Requires Approval? | Reason |
|---------------|---------|-------------------|--------|
| **Read-only** | `status`, `query`, `list` | ❌ No | Safe operations execute immediately |
| **Change** | `run`, `delete`, `update` | ✅ Yes | Risky operations need human approval |

#### Workflow Example

```bash
# 1. Read-only query (executes immediately)
User: "Check status of job DailyReport"
→ Intent: controlm_job (action=status)
→ Approval check: False (read-only)
→ ✅ Executes without waiting

# 2. Change operation (requires approval)
User: "Run the monthly backup job"
→ Intent: controlm_job (action=run)
→ Approval check: True (change operation)
→ ⏸️ Pauses with status: waiting_human

# 3. Approve the pending request
POST /api/v1/approval
{
  "session_id": "xxx",
  "request_id": "yyy",
  "approved": true
}
→ ✅ Continues execution after approval
```

#### Benefits

- ✅ **Better UX**: Safe queries don't wait for approval
- ✅ **Enhanced Security**: Risky operations still require review
- ✅ **ITIL Compliant**: Follows enterprise change management standards
- ✅ **Flexible**: Easy to customize per skill and operation

For detailed implementation guide, see: [docs/DYNAMIC_HUMAN_APPROVAL_GUIDE.md](docs/DYNAMIC_HUMAN_APPROVAL_GUIDE.md)

## 📊 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/chat` | Standard chat |
| POST | `/api/v1/chat/stream` | Streaming chat (SSE) |
| POST | `/api/v1/approval` | Submit human approval |
| GET | `/api/v1/metrics` | Prometheus metrics |

## ⚙️ Production Configuration

Replace `MemorySaver` in `.env` with PostgreSQL:

```bash
pip install langgraph-checkpoint-postgres
```

Call `get_postgres_checkpointer()` in `app/graph/graph.py` to initialize persistent checkpointer.
