# RAG Feature Quick Start

## ⚡ 3-Minute Quick Configuration

### Step 1: Configure API (2 minutes)

1. Open the `.env` file (if it doesn't exist, run `copy .env.example .env`)

2. Find the RAG configuration section and modify the following two items:

```ini
RAG_API_URL=http://your-group-ai-platform/rag/search  # ← Change to your API URL
RAG_API_KEY=your-rag-api-key-here                      # ← Change to your API key
```

### Step 2: Fill in API Call Code (1 minute)

1. Open `app/skills/rag_skill.py`

2. Search for `TODO: Fill in the RAG API call logic for the company Group AI Platform here`

3. Refer to the example code in the comments and replace it with your actual API call

**Simplest implementation template:**

```python
async with httpx.AsyncClient() as client:
    response = await client.post(
        url=self._settings.api_url,
        headers={"Authorization": f"Bearer {self._settings.api_key}"},
        json={"query": search_params.query, "top_k": search_params.top_k},
        timeout=self._settings.request_timeout,
    )
    response.raise_for_status()
    data = response.json()
    
    return SkillOutput(success=True, data=data)
```

### Step 3: Testing and Validation

#### Run Unit Tests

```bash
cd E:\Python\chatbot
pytest tests/unit/test_rag_skill.py -v
```

If all tests pass (PASSED), the RAG skill code is correct.

#### Start Service and Test API

```bash
cd E:\Python\chatbot
python main.py
```

Seeing output results indicates success! ✅

---

## 🎯 Complete Usage Flow

### Start Service

```bash
python main.py
```

### Access API Documentation

Open in browser: http://localhost:8000/api/v1/docs

### Test Conversation

In Swagger UI, find the `POST /api/v1/chat` endpoint, click "Try it out", and enter:

```json
{
  "message": "Help me check the company annual leave policy",
  "stream": false
}
```

Click "Execute" to view the returned results.

---

## 📖 Detailed Documentation

- [Integration Guide](RAG_INTEGRATION_GUIDE.md) - Complete API integration instructions
- [Configuration Checklist](RAG_CHECKLIST.md) - Step-by-step configuration guide
- [Completion Summary](RAG_SUMMARY.md) - Feature overview and architecture description

---

## ❓ Frequently Asked Questions

**Q: How do I know if the API is configured successfully?**  
A: Run `pytest tests/unit/test_rag_skill.py -v`. If all tests pass, the API is working correctly.

**Q: What if the API response format doesn't match?**  
A: Check the "Response Format Adaptation" section in `docs/RAG_INTEGRATION_GUIDE.md` and adjust the parsing code.

**Q: Want to temporarily disable RAG functionality?**  
A: Comment out the line `skill_registry.register(RagSkill())` in `app/api/main.py`.

---

**Need help?** Check [`docs/RAG_INTEGRATION_GUIDE.md`](RAG_INTEGRATION_GUIDE.md) for detailed instructions.
