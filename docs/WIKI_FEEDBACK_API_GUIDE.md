# Wiki Feedback API Documentation

## 📋 Overview

The Wiki Feedback API allows users to provide feedback on wiki articles, enabling a **continuous improvement loop** where:
- User feedback is recorded and aggregated
- Confidence scores are automatically recalculated
- Low-confidence articles can be flagged for re-compilation
- Knowledge quality improves over time through user interaction

---

## 🔗 API Endpoints

### Base URL
```
http://localhost:8000/api/v1
```

---

## 📤 Submit Feedback

**Endpoint:** `POST /wiki/feedback`

**Purpose:** Submit positive or negative feedback for a wiki article.

### Request Body

```json
{
  "entry_id": "conc_loan_prime_rate",
  "is_positive": true,
  "comment": "Very helpful explanation!"
}
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `entry_id` | string | ✅ Yes | Wiki article entry ID |
| `is_positive` | boolean | ✅ Yes | `true` for thumbs up, `false` for thumbs down |
| `comment` | string | ❌ No | Optional user comment (max 500 chars) |

### Response

**Success (200 OK):**
```json
{
  "success": true,
  "entry_id": "conc_loan_prime_rate",
  "feedback_summary": {
    "positive": 15,
    "negative": 3,
    "total": 18,
    "comments_count": 8,
    "updated_confidence": 0.923,
    "confidence_change": "increased"
  }
}
```

**Error (404 Not Found):**
```json
{
  "detail": "Wiki article not found: invalid_entry_id"
}
```

**Error (500 Internal Server Error):**
```json
{
  "detail": "Failed to process feedback"
}
```

### Example Usage

#### Using cURL
```bash
curl -X POST http://localhost:8000/api/v1/wiki/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "entry_id": "conc_loan_prime_rate",
    "is_positive": true,
    "comment": "Clear and concise!"
  }'
```

#### Using Python Requests
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/wiki/feedback",
    json={
        "entry_id": "conc_loan_prime_rate",
        "is_positive": True,
        "comment": "Very helpful!"
    }
)

result = response.json()
print(f"Updated confidence: {result['feedback_summary']['updated_confidence']}")
```

#### Using JavaScript Fetch
```javascript
fetch('http://localhost:8000/api/v1/wiki/feedback', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    entry_id: 'conc_loan_prime_rate',
    is_positive: true,
    comment: 'Great article!'
  })
})
.then(response => response.json())
.then(data => console.log('Feedback submitted:', data));
```

---

## 📊 Get Feedback Statistics

**Endpoint:** `GET /wiki/{entry_id}/feedback`

**Purpose:** Retrieve detailed feedback statistics and confidence information for a wiki article.

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entry_id` | string | ✅ Yes | Wiki article entry ID |

### Response

**Success (200 OK):**
```json
{
  "entry_id": "conc_loan_prime_rate",
  "title": "Loan Prime Rate (LPR) in China",
  "version": 3,
  "confidence": {
    "current": 0.923,
    "feedback_ratio": 0.833,
    "threshold_for_recompile": 0.7
  },
  "feedback": {
    "positive": 15,
    "negative": 3,
    "total": 18,
    "comments": [
      "Very helpful explanation!",
      "Clear and concise",
      "Needs more recent data",
      "Well structured",
      "Good examples"
    ]
  },
  "status": "active"
}
```

**Error (404 Not Found):**
```json
{
  "detail": "Wiki article not found: invalid_entry_id"
}
```

### Example Usage

#### Using cURL
```bash
curl http://localhost:8000/api/v1/wiki/conc_loan_prime_rate/feedback
```

#### Using Python Requests
```python
import requests

response = requests.get(
    "http://localhost:8000/api/v1/wiki/conc_loan_prime_rate/feedback"
)

stats = response.json()
print(f"Title: {stats['title']}")
print(f"Confidence: {stats['confidence']['current']}")
print(f"Positive/Negative: {stats['feedback']['positive']}/{stats['feedback']['negative']}")
```

---

## 🔄 Confidence Recalculation Formula

The system automatically recalculates confidence after each feedback submission using the following formula:

```
new_confidence = 0.7 × old_confidence + 0.3 × feedback_ratio
```

Where:
- `old_confidence`: Previous confidence score (0.5 - 1.0)
- `feedback_ratio`: positive_feedback / total_feedback
- `new_confidence`: Updated confidence score

### Example Calculation

**Initial State:**
- Confidence: 0.95
- Positive feedback: 0
- Negative feedback: 0

**After 3 positive, 1 negative feedback:**
```
feedback_ratio = 3 / (3 + 1) = 0.75
new_confidence = 0.7 × 0.95 + 0.3 × 0.75
               = 0.665 + 0.225
               = 0.89
```

**Result:** Confidence decreased from 0.95 to 0.89 due to mixed feedback.

---

## 🎯 Use Cases

### 1. Simple Thumbs Up/Down

Users can quickly rate articles without comments:

```bash
curl -X POST http://localhost:8000/api/v1/wiki/feedback \
  -H "Content-Type: application/json" \
  -d '{"entry_id": "qa_vpn_setup", "is_positive": true}'
```

### 2. Detailed Feedback with Comments

Users can provide constructive feedback:

```bash
curl -X POST http://localhost:8000/api/v1/wiki/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "entry_id": "proc_it_equipment_request",
    "is_positive": false,
    "comment": "The approval process has changed. Please update step 3."
  }'
```

### 3. Monitor Article Quality

Administrators can track article quality over time:

```python
import requests

def monitor_article_quality(entry_id):
    response = requests.get(
        f"http://localhost:8000/api/v1/wiki/{entry_id}/feedback"
    )
    stats = response.json()
    
    confidence = stats['confidence']['current']
    threshold = stats['confidence']['threshold_for_recompile']
    
    if confidence < threshold:
        print(f"⚠️  Article needs review! Confidence: {confidence}")
        # Trigger re-compilation
        trigger_recompilation(entry_id)
    else:
        print(f"✅ Article quality good. Confidence: {confidence}")
```

### 4. Build Interactive UI

Frontend applications can implement thumbs up/down buttons:

```javascript
// React component example
function FeedbackButtons({ entryId }) {
  const handleFeedback = async (isPositive) => {
    await fetch('/api/v1/wiki/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        entry_id: entryId,
        is_positive: isPositive,
        comment: prompt('Optional comment:')
      })
    });
    
    // Update UI with new confidence score
    refreshStats();
  };
  
  return (
    <div>
      <button onClick={() => handleFeedback(true)}>👍 Helpful</button>
      <button onClick={() => handleFeedback(false)}>👎 Needs Improvement</button>
    </div>
  );
}
```

---

## 🧪 Testing

### Run Automated Tests

```bash
cd e:\Python\chatbot
python scripts/test_wiki_feedback_api.py
```

This script will:
1. Submit multiple feedback entries
2. Verify confidence recalculation
3. Test error handling
4. Display detailed statistics

### Manual Testing with Swagger UI

1. Start the FastAPI server:
   ```bash
   cd e:\Python\chatbot
   uvicorn app.api.main:app --reload --port 8000
   ```

2. Open Swagger UI:
   ```
   http://localhost:8000/api/v1/docs
   ```

3. Find the **Wiki** section and test:
   - `POST /wiki/feedback`
   - `GET /wiki/{entry_id}/feedback`

---

## ⚙️ Configuration

### Confidence Thresholds

The system uses the following thresholds:

| Threshold | Value | Purpose |
|-----------|-------|---------|
| Minimum confidence | 0.5 | Below this indicates very low quality |
| Recompile threshold | 0.7 | Articles below this are flagged for review |
| High confidence | 0.9+ | Indicates trusted, high-quality content |

### Feedback Weighting

Current formula weights:
- **Historical confidence:** 70% (0.7)
- **User feedback ratio:** 30% (0.3)

These weights can be adjusted in [`app/wiki/engine.py`](file://e:\Python\chatbot\app\wiki\engine.py#L517-L520):

```python
# Current implementation
article.confidence = 0.7 * article.confidence + 0.3 * feedback_ratio

# To increase feedback impact:
article.confidence = 0.5 * article.confidence + 0.5 * feedback_ratio
```

---

## 🔒 Security Considerations

### Rate Limiting (Recommended)

Implement rate limiting to prevent abuse:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post(f"{prefix}/wiki/feedback")
@limiter.limit("10/minute")  # Max 10 feedback submissions per minute per IP
async def submit_wiki_feedback(request: Request, req: WikiFeedbackRequest):
    # ... existing logic
```

### Input Validation

The API already validates:
- `entry_id` must exist
- `comment` max length: 500 characters
- `is_positive` must be boolean

### Authentication (Future Enhancement)

For production, consider adding:
- JWT token authentication
- User-specific feedback tracking
- Spam detection for comments

---

## 📈 Monitoring & Analytics

### Track Feedback Metrics

Monitor these key metrics:

```python
# Example: Calculate overall knowledge base health
def calculate_kb_health(wiki_engine):
    articles = list(wiki_engine.articles.values())
    
    avg_confidence = sum(a.confidence for a in articles) / len(articles)
    total_feedback = sum(
        a.feedback.positive + a.feedback.negative 
        for a in articles
    )
    low_confidence_count = sum(
        1 for a in articles if a.confidence < 0.7
    )
    
    return {
        "average_confidence": round(avg_confidence, 3),
        "total_feedback_received": total_feedback,
        "articles_needing_review": low_confidence_count,
        "health_score": "good" if avg_confidence > 0.8 else "needs_improvement"
    }
```

### Alert on Low Confidence

Set up alerts when articles drop below threshold:

```python
def check_articles_for_review(wiki_engine):
    for article in wiki_engine.articles.values():
        if article.confidence < 0.7:
            send_alert(
                f"Article '{article.title}' has low confidence: {article.confidence}"
            )
            # Optionally trigger auto-recompilation
            # await compiler.recompile_article(article.entry_id)
```

---

## 🚀 Integration Examples

### Frontend Integration (React)

```jsx
import { useState, useEffect } from 'react';

function WikiArticleFeedback({ entryId }) {
  const [stats, setStats] = useState(null);
  
  useEffect(() => {
    fetchStats();
  }, [entryId]);
  
  const fetchStats = async () => {
    const res = await fetch(`/api/v1/wiki/${entryId}/feedback`);
    const data = await res.json();
    setStats(data);
  };
  
  const submitFeedback = async (isPositive) => {
    await fetch('/api/v1/wiki/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        entry_id: entryId,
        is_positive: isPositive,
        comment: window.prompt('Add a comment (optional):')
      })
    });
    fetchStats(); // Refresh stats
  };
  
  if (!stats) return <div>Loading...</div>;
  
  return (
    <div className="feedback-section">
      <h3>Was this article helpful?</h3>
      <button onClick={() => submitFeedback(true)}>
        👍 Yes ({stats.feedback.positive})
      </button>
      <button onClick={() => submitFeedback(false)}>
        👎 No ({stats.feedback.negative})
      </button>
      
      <div className="confidence-meter">
        <label>Article Confidence:</label>
        <progress 
          value={stats.confidence.current} 
          max="1.0"
        />
        <span>{(stats.confidence.current * 100).toFixed(1)}%</span>
      </div>
    </div>
  );
}
```

### Backend Integration (Python Service)

```python
class WikiQualityMonitor:
    def __init__(self, base_url="http://localhost:8000/api/v1"):
        self.base_url = base_url
    
    def submit_feedback(self, entry_id, is_positive, comment=None):
        """Submit feedback programmatically"""
        response = requests.post(
            f"{self.base_url}/wiki/feedback",
            json={
                "entry_id": entry_id,
                "is_positive": is_positive,
                "comment": comment
            }
        )
        return response.json()
    
    def get_quality_report(self, entry_id):
        """Get detailed quality metrics"""
        response = requests.get(
            f"{self.base_url}/wiki/{entry_id}/feedback"
        )
        return response.json()
    
    def identify_low_quality_articles(self, threshold=0.7):
        """Find articles that need improvement"""
        # This would require a list endpoint (future enhancement)
        pass
```

---

## 📝 Best Practices

### For Users
1. **Provide specific comments** when giving negative feedback
2. **Use feedback consistently** - don't spam thumbs up/down
3. **Check confidence scores** before relying on article content

### For Administrators
1. **Monitor feedback trends** weekly
2. **Review low-confidence articles** monthly
3. **Encourage user feedback** through UI prompts
4. **Act on constructive comments** to improve content

### For Developers
1. **Handle errors gracefully** in frontend code
2. **Cache feedback stats** to reduce API calls
3. **Implement optimistic UI updates** for better UX
4. **Log feedback events** for analytics

---

## 🔮 Future Enhancements

Planned improvements:
- [ ] **User authentication** - Track feedback by user
- [ ] **Feedback moderation** - Filter spam/inappropriate comments
- [ ] **Batch feedback API** - Submit multiple feedbacks at once
- [ ] **Feedback analytics dashboard** - Visualize trends
- [ ] **Automated recompilation** - Trigger when confidence drops
- [ ] **A/B testing** - Compare article versions based on feedback
- [ ] **Sentiment analysis** - Analyze comment tone automatically

---

## 📚 Related Documentation

- [Enhanced Wiki Compiler v2.0](ENHANCED_WIKI_COMPILER_V2.md)
- [Knowledge Graph Architecture](ENHANCED_WIKI_KNOWLEDGE_GRAPH.md)
- [Final Verification Report](FINAL_VERIFICATION_REPORT.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

**API Version:** 1.0  
**Last Updated:** 2026-04-19  
**Status:** ✅ **Production Ready**  

🎉 **Your Wiki now has a complete feedback loop for continuous improvement!**
