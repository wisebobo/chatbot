# RAG Integration Checklist

## ✅ Completed Work

- [x] Created RAG skill module (`app/skills/rag_skill.py`)
- [x] Added RAG configuration class (`RagSettings` in `app/config/settings.py`)
- [x] Registered RAG skill in API entry point (`app/api/main.py`)
- [x] Updated `.env.example` configuration file
- [x] Created integration guide document (`docs/RAG_INTEGRATION_GUIDE.md`)
- [x] Updated README.md usage instructions
- [x] Created unit tests (`tests/unit/test_rag_skill.py`)

## 📝 Pending Configuration (Requires Your Action)

### 1. Configure Environment Variables

Edit the `.env` file (if it doesn't exist, copy from `.env.example`):

```bash
copy .env.example .env
```

Then modify the following configuration items:

```ini
# ===== RAG Knowledge Base Configuration (Group AI Platform) =====
RAG_API_URL=http://your-group-ai-platform/rag/search  # ← Replace with actual API URL
RAG_API_KEY=your-rag-api-key-here                      # ← Replace with actual API key
RAG_REQUEST_TIMEOUT=30
RAG_DEFAULT_TOP_K=5
RAG_MIN_RELEVANCE_SCORE=0.7
```

### 2. Implement API Call Logic

Open the file `app/skills/rag_skill.py` and find the TODO section at lines 60-90.

**What you need to do:**
1. Review your company's Group AI Platform API documentation
2. Confirm the API request format (URL, Headers, Body)
3. Confirm the API response format (JSON structure)
4. Replace the placeholder code with actual API calls

**Reference location:**
```python
# In the execute method of rag_skill.py
async def execute(self, params: Dict[str, Any]) -> SkillOutput:
    # ... previous code ...
    
    try:
        # ========================================
        # ↓↓↓ Fill in your API call code here ↓↓↓
        # ========================================
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=self._settings.api_url,  # Read from .env
                headers={...},               # Set according to API requirements
                json={...},                  # Request body
                timeout=self._settings.request_timeout,
            )
            # ... parse response ...
        
        # ========================================
        # ↑↑↑ Fill in your API call code here ↑↑↑
        # ========================================
```

### 3. Testing and Validation

#### Method 1: Run Unit Tests

```bash
cd E:\Python\chatbot
pytest tests/unit/test_rag_skill.py -v
```

Expected output: All tests should pass if the implementation is correct.

#### Method 2: Start Full Service

```bash
python main.py
```

Then access `http://localhost:8000/api/v1/docs` in your browser and use Swagger UI to test the chat endpoint.

#### Method 3: Use curl Command

```bash
curl -X POST "http://localhost:8000/api/v1/chat" ^
  -H "Content-Type: application/json" ^
  -d "{\"message\": \"Help me check the company reimbursement policy\", \"stream\": false}"
```

## 🔍 Debugging Tips

### If you encounter issues:

1. **Check Log Output**
   ```bash
   # Enable DEBUG level in .env
   LOG_LEVEL=DEBUG
   ```

2. **Verify Network Connection**
   ```bash
   # Test if API is reachable
   curl -I http://your-group-ai-platform/rag/search
   ```

3. **Test RAG Skill Independently**
   ```python
   # Create a temporary test script
   import asyncio
   from app.skills.rag_skill import RagSkill
   
   async def test():
       skill = RagSkill()
       result = await skill.execute({"query": "test query"})
       print(result)
   
   asyncio.run(test())
   ```

4. **Check Common Errors**
   - `ConnectionError`: Verify API URL is correct
   - `401 Unauthorized`: Check if API Key is valid
   - `404 Not Found`: Confirm API endpoint path
   - `Timeout`: Increase `RAG_REQUEST_TIMEOUT` value

## 📚 Related Documentation

- [RAG Integration Guide](RAG_INTEGRATION_GUIDE.md) - Detailed API integration instructions
- [README.md](../README.md) - Project overview
- [.env.example](../.env.example) - Configuration template

## 🎯 Next Steps

After completing the above configuration, your chatbot will have the following capabilities:

1. ✅ **Web Interface for Questions** - FastAPI RESTful API
2. ✅ **Intelligent Intent Understanding** - LLM automatically analyzes user intent
3. ✅ **Knowledge Base Query** - RAG skill retrieves enterprise knowledge ⭐ New
4. ✅ **Action Execution** - Control-M, Playwright and other skills
5. ✅ **LLM Analysis and Response** - Generates natural language responses based on retrieved results

Complete conversation flow:
```
User Question → Intent Recognition → [Routing Decision] → RAG Search → LLM Integrates Results → Returns Answer
```

---

**Need help?** Check `docs/RAG_INTEGRATION_GUIDE.md` for detailed API integration examples and troubleshooting guides.
