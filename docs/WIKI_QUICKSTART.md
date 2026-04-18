# LLM Wiki Feature Quick Start

## ⚡ 3-Minute Quick Configuration

### Step 1: Configure API (2 minutes)

1. Open the `.env` file (if it doesn't exist, run `copy .env.example .env`)

2. Find the Wiki configuration section and modify the following two items:

```ini
WIKI_API_URL=http://your-group-ai-platform/wiki/query  # ← Change to your Wiki API URL
WIKI_API_KEY=your-wiki-api-key-here                     # ← Change to your Wiki API key
```

### Step 2: Fill in API Call Code (1 minute)

1. Open `app/skills/wiki_skill.py`

2. Search for `TODO: Fill in the LLM Wiki API call logic for the company Group AI Platform here`

3. Refer to the example code in the comments and replace it with your actual API call

**Simplest implementation template:**

```python
async with httpx.AsyncClient() as client:
    response = await client.post(
        url=self._settings.api_url,
        headers={"Authorization": f"Bearer {self._settings.api_key}"},
        json={
            "query": search_params.query,
            "exact_match": search_params.exact_match,
            "category": search_params.category,
        },
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
pytest tests/unit/test_wiki_skill.py -v
```

If all tests pass (PASSED), the Wiki skill code is correct.

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
  "message": "What is the annual leave policy?",
  "stream": false
}
```

Click "Execute" to view the returned results.

---

## 📖 Detailed Documentation

- [Integration Guide](WIKI_INTEGRATION_GUIDE.md) - Complete API integration instructions
- [RAG Integration Guide](RAG_INTEGRATION_GUIDE.md) - For unstructured document search
- [README](../README.md) - Project overview

---

## ❓ Frequently Asked Questions

**Q: When should I use Wiki vs RAG?**  
A: Use Wiki for official documentation and known policies. Use RAG for exploratory queries across unstructured documents.

**Q: What if the wiki article is too long?**  
A: Use the `max_length` parameter to limit content length: `{"query": "...", "max_length": 500}`

**Q: How do I know which skill was used?**  
A: Check the API response - it includes `skill_executed` field showing which skill was called.

**Q: Want to temporarily disable Wiki functionality?**  
A: Comment out the line `skill_registry.register(WikiSkill())` in `app/api/main.py`.

---

**Need help?** Check [`docs/WIKI_INTEGRATION_GUIDE.md`](WIKI_INTEGRATION_GUIDE.md) for detailed instructions.
