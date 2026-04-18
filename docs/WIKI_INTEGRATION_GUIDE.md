# LLM Wiki Integration Guide

## 📋 Overview

This document explains how to integrate your company's Group AI Platform Wiki API into the chatbot project. The Wiki skill provides access to structured, curated knowledge base articles with clear organization.

### When to Use Wiki vs RAG

| Feature | Wiki Search | RAG Search |
|---------|-------------|------------|
| **Content Type** | Structured articles, documented procedures | Unstructured documents, scattered information |
| **Organization** | Clear hierarchy, categories, tags | Semantic similarity based |
| **Best For** | Official policies, technical docs, known topics | Exploratory queries, cross-document search |
| **Accuracy** | High (curated content) | Variable (depends on relevance) |
| **Update Frequency** | Regularly maintained | May contain outdated info |

**Recommendation:** Use Wiki for well-documented topics, RAG for exploratory searches.

---

## 🔧 Configuration Steps

### 1. Environment Variable Configuration

Edit the `.env` file and add the following configuration:

```bash
# ===== LLM Wiki Configuration (Group AI Platform) =====
WIKI_API_URL=http://your-group-ai-platform/wiki/query
WIKI_API_KEY=your-wiki-api-key-here
WIKI_REQUEST_TIMEOUT=30
WIKI_EXACT_MATCH_DEFAULT=false
WIKI_MAX_CONTENT_LENGTH=5000
```

**Parameter Descriptions:**
- `WIKI_API_URL`: Group AI Platform Wiki API endpoint URL
- `WIKI_API_KEY`: API authentication key (if required)
- `WIKI_REQUEST_TIMEOUT`: Request timeout in seconds
- `WIKI_EXACT_MATCH_DEFAULT`: Default exact title matching behavior
- `WIKI_MAX_CONTENT_LENGTH`: Maximum content length to return (characters)

### 2. API Implementation

Open the file `app/skills/wiki_skill.py` and find the TODO section in the `execute` method (around lines 70-110). Replace it with actual API call code.

#### Example: Standard REST API Call

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
            "exact_match": search_params.exact_match,
            "category": search_params.category,
            "include_sections": search_params.include_sections,
            "max_length": search_params.max_length,
        },
        timeout=self._settings.request_timeout,
    )
    response.raise_for_status()
    data = response.json()
    
    # Parse response results (adjust according to actual API response format)
    results = []
    for item in data.get("articles", []):
        results.append(WikiSearchResult(
            title=item.get("title", ""),
            url=item.get("url"),
            content=item.get("content", ""),
            category=item.get("category"),
            last_updated=item.get("last_updated"),
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

### 3. Response Format Adaptation

Adjust the result parsing logic based on your company API's actual response format. Common response formats:

#### Format A: Article List
```json
{
  "articles": [
    {
      "title": "Annual Leave Policy",
      "url": "https://wiki.company.com/hr/annual-leave",
      "content": "Full article content...",
      "category": "HR",
      "last_updated": "2024-01-15T10:30:00Z",
      "metadata": {"author": "HR Team", "version": "2.1"}
    }
  ],
  "total_count": 1
}
```

#### Format B: Nested Structure
```json
{
  "data": {
    "search": {
      "items": [
        {
          "article": {
            "name": "Annual Leave Policy",
            "link": "/hr/annual-leave",
            "body": "Full article content..."
          },
          "meta": {
            "category": "HR",
            "updated": "2024-01-15"
          }
        }
      ]
    }
  }
}
```

Corresponding parsing code:
```python
for item in data.get("data", {}).get("search", {}).get("items", []):
    article = item.get("article", {})
    meta = item.get("meta", {})
    results.append(WikiSearchResult(
        title=article.get("name", ""),
        url=article.get("link", ""),
        content=article.get("body", ""),
        category=meta.get("category"),
        last_updated=meta.get("updated"),
    ).dict())
```

---

## 🧪 Testing and Validation

### Method 1: Run Unit Tests

```bash
cd E:\Python\chatbot
pytest tests/unit/test_wiki_skill.py -v
```

This will run all unit tests for the Wiki skill, including:
- Parameter validation tests
- API call mock tests
- Error handling tests
- Result formatting tests

### Method 2: Start Full Service

```bash
cd E:\Python\chatbot
python main.py
```

Then test Wiki search using curl or Postman:

```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the annual leave policy?",
    "stream": false
  }'
```

Expected behavior:
1. LLM recognizes intent as wiki query
2. Automatically calls `wiki_search` skill
3. Returns retrieved wiki articles
4. LLM generates natural language response based on wiki content

### 3. Check Logs

Check console output to confirm Wiki API is being called correctly:

```
[skill.wiki_search] Wiki search: query='annual leave policy...', exact_match=False
[skill.wiki_search] Skill 'wiki_search' succeeded on attempt 1
```

---

## 🎯 Usage Examples

### Example 1: Basic Wiki Query
```json
{
  "query": "Annual Leave Policy"
}
```

### Example 2: Exact Title Match
```json
{
  "query": "IT Equipment Request Process",
  "exact_match": true
}
```

### Example 3: Filter by Category
```json
{
  "query": "Reimbursement Guidelines",
  "category": "Finance"
}
```

### Example 4: Get Concise Version
```json
{
  "query": "Project Management Best Practices",
  "max_length": 500
}
```

---

## 🔍 Debugging Tips

### 1. Enable Verbose Logging

Set in `.env`:
```bash
LOG_LEVEL=DEBUG
```

### 2. Test Wiki Skill Independently

Create a test script:

```python
import asyncio
from app.skills.wiki_skill import WikiSkill

async def test_wiki():
    skill = WikiSkill()
    result = await skill.execute({
        "query": "How to apply for reimbursement?",
        "category": "Finance"
    })
    print(f"Success: {result.success}")
    print(f"Data: {result.data}")
    if result.error_message:
        print(f"Error: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(test_wiki())
```

Run the test:
```bash
python test_wiki.py
```

### 3. Check Common Errors
- `ConnectionError`: Verify API URL is correct
- `401 Unauthorized`: Check if API Key is valid
- `404 Not Found`: Confirm API endpoint path
- `Timeout`: Increase `WIKI_REQUEST_TIMEOUT` value

---

## 📊 Performance Optimization Suggestions

### 1. Caching Mechanism

For frequently accessed wiki articles, add Redis caching:

```python
import redis.asyncio as redis

class WikiSkill(BaseSkill):
    def __init__(self):
        super().__init__()
        self._redis = redis.from_url(get_settings().database.redis_url)
    
    async def execute(self, params: Dict[str, Any]) -> SkillOutput:
        cache_key = f"wiki:{hash(search_params.query)}"
        
        # Try to read from cache
        cached = await self._redis.get(cache_key)
        if cached:
            return SkillOutput(success=True, data=json.loads(cached))
        
        # Execute API call
        result = await self._call_api(search_params)
        
        # Write to cache (valid for 24 hours for wiki content)
        await self._redis.setex(cache_key, 86400, json.dumps(result.data))
        
        return result
```

### 2. Category-Based Routing

If you know the category, specify it to improve search accuracy:

```python
# Instead of generic search
{"query": "reimbursement"}

# Use category filter
{"query": "reimbursement", "category": "Finance"}
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

---

## ❓ Frequently Asked Questions

### Q1: When should I use Wiki vs RAG?

**Answer:**
- **Use Wiki when:** You're looking for official documentation, known policies, or structured procedures
- **Use RAG when:** You need to search across multiple unstructured documents or explore related topics

### Q2: What if the wiki article is too long?

**Solutions:**
- Use `max_length` parameter to limit content length
- Set `include_sections=false` to get only summary
- Request specific sections if API supports it

### Q3: How to handle missing wiki articles?

**Solution:**
The skill returns "No relevant wiki articles found" message. Consider fallback to RAG search:

```python
# In your workflow logic
if wiki_result indicates no results:
    fallback_to_rag_search()
```

### Q4: Can I search across multiple categories?

**Solution:**
If your API supports it, modify the request:

```python
json={
    "query": search_params.query,
    "categories": ["HR", "Finance", "IT"],  # Multiple categories
}
```

---

## 📞 Technical Support

If you encounter issues, please check:
1. `.env` configuration file is correct
2. API URL and key are valid
3. Network connection is normal
4. Check error messages in application logs

---

## 🔄 Comparison: Wiki vs RAG Skills

| Aspect | Wiki Skill | RAG Skill |
|--------|-----------|-----------|
| **Skill Name** | `wiki_search` | `rag_search` |
| **Content Source** | Structured wiki articles | Unstructured documents |
| **Search Method** | Title/category matching | Semantic similarity |
| **Best For** | Known topics, official docs | Exploratory queries |
| **Parameters** | query, exact_match, category, max_length | query, top_k, knowledge_base, filters |
| **Response Format** | Articles with metadata | Snippets with relevance scores |

---

**Next Step:** After completing API integration, test both Wiki and RAG skills to determine which works better for different query types.
