# Knowledge Search Skills: Wiki vs RAG

## 📋 Overview

The chatbot project now supports two complementary knowledge search skills:
- **Wiki Search** (`wiki_search`): Structured, curated wiki articles
- **RAG Search** (`rag_search`): Unstructured document retrieval with semantic similarity

Both skills integrate with your company's Group AI Platform but serve different use cases.

---

## 🎯 When to Use Which?

### Use Wiki Search When:
✅ Looking for official company policies  
✅ Querying documented procedures or guidelines  
✅ Searching for known topics with clear titles  
✅ Need structured, well-organized content  
✅ Accessing technical documentation with sections  
✅ Information has clear categories (HR, IT, Finance, etc.)  

**Example Queries:**
- "What is the annual leave policy?"
- "How to submit expense reports?"
- "IT equipment request procedure"
- "Project management guidelines"

### Use RAG Search When:
✅ Exploring topics without knowing exact terminology  
✅ Searching across multiple unstructured documents  
✅ Finding related information from various sources  
✅ Dealing with scattered or informal content  
✅ Need semantic understanding beyond keywords  
✅ Cross-referencing multiple documents  

**Example Queries:**
- "How do I troubleshoot network connectivity issues?"
- "Best practices for team collaboration"
- "Tips for improving code quality"
- "Common problems with database performance"

---

## 🔍 Feature Comparison

| Feature | Wiki Search | RAG Search |
|---------|-------------|------------|
| **Content Type** | Structured articles | Unstructured documents |
| **Organization** | Clear hierarchy, categories | Flat collection |
| **Search Method** | Title/category matching | Semantic similarity |
| **Accuracy** | High (curated) | Variable (depends on relevance) |
| **Update Frequency** | Regularly maintained | May be outdated |
| **Metadata** | Author, version, last updated | Source, relevance score |
| **Best For** | Official docs, policies | Exploratory queries |
| **Response Format** | Full articles with structure | Snippets with scores |
| **Parameters** | query, exact_match, category, max_length | query, top_k, knowledge_base, filters |

---

## 💡 Implementation Details

### Wiki Skill
**File:** `app/skills/wiki_skill.py`  
**API Endpoint:** `/wiki/query`  
**Configuration:** `WIKI_API_URL`, `WIKI_API_KEY`

**Key Features:**
- Exact title matching option
- Category-based filtering
- Configurable content length
- Article metadata (author, version, update date)

**Example Request:**
```json
{
  "query": "Annual Leave Policy",
  "exact_match": true,
  "category": "HR",
  "max_length": 2000
}
```

### RAG Skill
**File:** `app/skills/rag_skill.py`  
**API Endpoint:** `/rag/search`  
**Configuration:** `RAG_API_URL`, `RAG_API_KEY`

**Key Features:**
- Semantic similarity search
- Relevance scoring
- Multiple knowledge base support
- Custom filters

**Example Request:**
```json
{
  "query": "vacation time off rules",
  "top_k": 5,
  "knowledge_base": "HR Policies",
  "min_relevance_score": 0.7
}
```

---

## 🔄 Intelligent Routing Strategy

For optimal results, consider implementing intelligent routing in your workflow:

### Option 1: LLM-Based Routing
Let the LLM decide which skill to use based on intent:

```python
# In intent_recognition_node
if "official policy" in intent or "procedure" in intent:
    route_to = "wiki_search"
elif "troubleshoot" in intent or "how to fix" in intent:
    route_to = "rag_search"
```

### Option 2: Parallel Search
Run both searches and combine results:

```python
# Execute both skills
wiki_result = await wiki_skill.execute(params)
rag_result = await rag_skill.execute(params)

# Combine and deduplicate
combined_results = merge_results(wiki_result, rag_result)
```

### Option 3: Fallback Strategy
Try Wiki first, fall back to RAG if no results:

```python
wiki_result = await wiki_skill.execute(params)
if not wiki_result.data.get("results"):
    rag_result = await rag_skill.execute(params)
    return rag_result
return wiki_result
```

---

## 📊 Performance Considerations

### Wiki Search
- ✅ Faster response (structured data)
- ✅ More predictable results
- ✅ Lower API cost (single article lookup)
- ⚠️ Limited to documented content

### RAG Search
- ⚠️ Slower response (semantic processing)
- ⚠️ Variable result quality
- ⚠️ Higher API cost (vector search)
- ✅ Broader coverage

---

## 🧪 Testing Both Skills

### Test Wiki Search
```bash
pytest tests/unit/test_wiki_skill.py -v
```

### Test RAG Search
```bash
pytest tests/unit/test_rag_skill.py -v
```

### Test All Skills
```bash
pytest tests/unit/ -v
```

---

## 📝 Configuration Checklist

### Wiki Configuration
- [ ] Set `WIKI_API_URL` in `.env`
- [ ] Set `WIKI_API_KEY` in `.env`
- [ ] Implement API call in `wiki_skill.py`
- [ ] Test with sample queries
- [ ] Verify response format

### RAG Configuration
- [ ] Set `RAG_API_URL` in `.env`
- [ ] Set `RAG_API_KEY` in `.env`
- [ ] Implement API call in `rag_skill.py`
- [ ] Test with sample queries
- [ ] Verify response format

---

## 🎓 Best Practices

### 1. Use Descriptive Queries
**Wiki:** Use exact terminology from your organization  
**RAG:** Use natural language, include context

### 2. Leverage Metadata
**Wiki:** Filter by category when known  
**RAG:** Adjust `min_relevance_score` based on needs

### 3. Handle Empty Results
Always check if results are empty and provide fallback options

### 4. Cache Frequently Accessed Content
Both skills benefit from caching, especially Wiki articles

### 5. Monitor Usage
Track which skill is used more often to optimize your knowledge base

---

## 🔗 Related Documentation

- [Wiki Integration Guide](WIKI_INTEGRATION_GUIDE.md)
- [Wiki Quick Start](WIKI_QUICKSTART.md)
- [RAG Integration Guide](RAG_INTEGRATION_GUIDE.md)
- [RAG Quick Start](RAG_QUICKSTART.md)
- [README](../README.md)

---

## 💬 Example Conversation Flows

### Scenario 1: Policy Query (Wiki)
```
User: What's our vacation policy?
→ Intent: Looking for official policy
→ Route: wiki_search
→ Result: Annual Leave Policy article
→ Response: According to the official Annual Leave Policy...
```

### Scenario 2: Troubleshooting (RAG)
```
User: My laptop keeps crashing when running large datasets
→ Intent: Technical troubleshooting
→ Route: rag_search
→ Result: Multiple IT support articles
→ Response: Based on several IT support documents, try these steps...
```

### Scenario 3: Ambiguous Query (Both)
```
User: How do I request time off?
→ Could be: Policy question OR Process question
→ Strategy: Try wiki_search first
→ If no results: Fall back to rag_search
→ Response: Here's the official procedure...
```

---

**Summary:** Use Wiki for structured, official content. Use RAG for exploratory, unstructured search. Together they provide comprehensive knowledge access! 🚀
