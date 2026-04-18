# RAG Knowledge Base Integration Guide

## 📋 Overview

This document explains how to integrate your company's Group AI Platform RAG API into the chatbot project.

## 🔧 Configuration Steps

### 1. Environment Variable Configuration

Edit the `.env` file and add the following configuration:

```bash
# ===== RAG Knowledge Base Configuration (Group AI Platform) =====
RAG_API_URL=http://your-group-ai-platform/rag/search
RAG_API_KEY=your-rag-api-key-here
RAG_REQUEST_TIMEOUT=30
RAG_DEFAULT_TOP_K=5
RAG_MIN_RELEVANCE_SCORE=0.7
```

**Parameter Descriptions:**
- `RAG_API_URL`: Group AI Platform RAG API endpoint URL
- `RAG_API_KEY`: API authentication key (if required)
- `RAG_REQUEST_TIMEOUT`: Request timeout in seconds
- `RAG_DEFAULT_TOP_K`: Default number of results to return
- `RAG_MIN_RELEVANCE_SCORE`: Minimum relevance score threshold (0.0-1.0)

### 2. API Implementation

Open the file `app/skills/rag_skill.py` and find the TODO section in the `execute` method (around lines 60-90). Replace it with actual API call code.

#### Example 1: Standard REST API Call

```python
async with httpx.AsyncClient() as client:
    response = await client.post(
        url=self._settings.api_url,
        headers={
            "Authorization": f"Bearer {self._settings.api_key}",
            "Content-Type": "application/json",
        },
        json={
            "query": search_params.query,
            "top_k": search_params.top_k,
            "knowledge_base": search_params.knowledge_base,
            "filters": search_params.filters,
            "min_relevance_score": search_params.min_relevance_score,
        },
        timeout=self._settings.request_timeout,
    )
    response.raise_for_status()
    data = response.json()
    
    # Parse response results (adjust according to actual API response format)
    results = []
    for item in data.get("results", []):
        results.append(RagSearchResult(
            content=item.get("content", ""),
            source=item.get("source", ""),
            relevance_score=item.get("relevance_score", 0.0),
            metadata=item.get("metadata"),
        ).dict())
    
    return SkillOutput(
        success=True,
        data={
            "query": search_params.query,
            "results": results,
            "total_count": len(results),
        }
    )
```

#### Example 2: GraphQL API Call

If your Group AI Platform uses GraphQL:

```python
async with httpx.AsyncClient() as client:
    response = await client.post(
        url=self._settings.api_url,
        headers={
            "Authorization": f"Bearer {self._settings.api_key}",
            "Content-Type": "application/json",
        },
        json={
            "query": """
                query SearchKnowledgeBase($query: String!, $topK: Int!) {
                    search(query: $query, topK: $topK) {
                        results {
                            content
                            source
                            relevanceScore
                            metadata
                        }
                        totalCount
                    }
                }
            """,
            "variables": {
                "query": search_params.query,
                "topK": search_params.top_k,
            }
        },
        timeout=self._settings.request_timeout,
    )
    response.raise_for_status()
    data = response.json()
    
    # Parse GraphQL response
    search_data = data.get("data", {}).get("search", {})
    results = []
    for item in search_data.get("results", []):
        results.append(RagSearchResult(
            content=item.get("content", ""),
            source=item.get("source", ""),
            relevance_score=item.get("relevanceScore", 0.0),
            metadata=item.get("metadata"),
        ).dict())
    
    return SkillOutput(
        success=True,
        data={
            "query": search_params.query,
            "results": results,
            "total_count": search_data.get("totalCount", len(results)),
        }
    )
```

#### Example 3: Custom Authentication

If the API requires special authentication headers:

```python
headers = {
    "X-API-Key": self._settings.api_key,
    "X-Tenant-ID": "your-tenant-id",  # Multi-tenant scenario
    "Content-Type": "application/json",
}

# If you need to obtain a token first
if not self._cached_token:
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            f"{self._settings.api_url}/auth/token",
            json={"api_key": self._settings.api_key}
        )
        self._cached_token = token_resp.json()["access_token"]

headers["Authorization"] = f"Bearer {self._cached_token}"
```

### 3. Response Format Adaptation

Adjust the result parsing logic based on your company API's actual response format. Common response formats:

#### Format A: Flat Structure
```json
{
  "results": [
    {
      "content": "Document content...",
      "source": "Document title or path",
      "relevance_score": 0.95,
      "metadata": {"doc_id": "123", "category": "HR"}
    }
  ],
  "total_count": 5
}
```

#### Format B: Nested Structure
```json
{
  "data": {
    "hits": [
      {
        "document": {
          "text": "Document content...",
          "title": "Document title"
        },
        "score": 0.95,
        "fields": {"category": "HR"}
      }
    ]
  }
}
```

Corresponding parsing code:
```python
for hit in data.get("data", {}).get("hits", []):
    doc = hit.get("document", {})
    results.append(RagSearchResult(
        content=doc.get("text", ""),
        source=doc.get("title", ""),
        relevance_score=hit.get("score", 0.0),
        metadata=hit.get("fields", {}),
    ).dict())
```

## 🧪 Testing and Validation

### Method 1: Run Unit Tests

```bash
cd E:\Python\chatbot
pytest tests/unit/test_rag_skill.py -v
```

This will run all unit tests for the RAG skill, including:
- Parameter validation tests
- API call mock tests
- Error handling tests
- Result formatting tests

### Method 2: Start Full Service

```bash
cd E:\Python\chatbot
python main.py
```

Then test RAG search using curl or Postman:

```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Help me check the company annual leave policy",
    "stream": false
  }'
```

Expected behavior:
1. LLM recognizes intent as knowledge base query
2. Automatically calls `rag_search` skill
3. Returns retrieved relevant knowledge
4. LLM generates natural language response based on retrieved results

### 3. Check Logs

Check console output to confirm RAG API is being called correctly:

```
[skill.rag_search] RAG search: query='annual leave policy...', top_k=5
[skill.rag_search] Skill 'rag_search' succeeded on attempt 1
```

## 🔍 Debugging Tips

### 1. Enable Verbose Logging

Set in `.env`:
```bash
LOG_LEVEL=DEBUG
```

### 2. Temporarily Disable Mock Data

Comment out the mock data section in `rag_skill.py` to force use of real API:

```python
# Comment out this line
# self.logger.warning("RAG API not configured, returning mock data")

# Directly execute real API call code
async with httpx.AsyncClient() as client:
    # ... Your API call code
```

### 3. Test RAG Skill Independently

Create a test script `test_rag.py`:

```python
import asyncio
from app.skills.rag_skill import RagSkill

async def test_rag():
    skill = RagSkill()
    result = await skill.execute({
        "query": "How to apply for reimbursement?",
        "top_k": 3
    })
    print(f"Success: {result.success}")
    print(f"Data: {result.data}")
    if result.error_message:
        print(f"Error: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(test_rag())
```

Run the test:
```bash
python test_rag.py
```

## 📊 Performance Optimization Suggestions

### 1. Caching Mechanism

For high-frequency queries, add Redis caching:

```python
import redis.asyncio as redis

class RagSkill(BaseSkill):
    def __init__(self):
        super().__init__()
        self._redis = redis.from_url(get_settings().database.redis_url)
    
    async def execute(self, params: Dict[str, Any]) -> SkillOutput:
        cache_key = f"rag:{hash(search_params.query)}"
        
        # Try to read from cache
        cached = await self._redis.get(cache_key)
        if cached:
            return SkillOutput(success=True, data=json.loads(cached))
        
        # Execute API call
        result = await self._call_api(search_params)
        
        # Write to cache (valid for 1 hour)
        await self._redis.setex(cache_key, 3600, json.dumps(result.data))
        
        return result
```

### 2. Batch Query Optimization

If batch queries are supported, merge multiple related queries:

```python
# Query multiple related questions at once
batch_queries = [
    search_params.query,
    f"{search_params.query} process",
    f"{search_params.query} regulations"
]
```

### 3. Connection Pooling

Use httpx connection pooling to improve concurrent performance:

```python
# Create client during class initialization
self._client = httpx.AsyncClient(
    timeout=self._settings.request_timeout,
    limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
)
```

## ❓ Frequently Asked Questions

### Q1: What if the API returns empty results?

**Solutions:**
- Check if `min_relevance_score` is set too high
- Confirm that relevant content exists in the knowledge base
- Try adjusting the query with more specific keywords

### Q2: Response time is too long?

**Solutions:**
- Reduce `top_k` value (e.g., from 10 to 3)
- Increase `min_relevance_score` to filter low-quality results
- Check network connection and API server performance

### Q3: How to handle API rate limiting?

**Solution:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def call_rag_api(self, params):
    # API call code
    pass
```

## 📞 Technical Support

If you encounter issues, please check:
1. `.env` configuration file is correct
2. API URL and key are valid
3. Network connection is normal
4. Check error messages in application logs

---

**Next Step:** After completing API integration, it is recommended to add unit tests for the RAG skill in `tests/unit/test_skills.py`.
