# Local Wiki Engine Guide

## 📋 Overview

The chatbot now includes a **built-in local Wiki engine** that works without any external API dependency. This means you can use the Wiki search feature immediately, even if your Group AI Platform doesn't provide a Wiki API.

### Two Operating Modes

| Mode | Description | When to Use |
|------|-------------|-------------|
| **Local Mode** ✅ | Uses built-in wiki engine with file-based storage | No external API available, or want full control |
| **Remote Mode** | Uses Group AI Platform Wiki API | Company provides dedicated Wiki API |

The system **automatically detects** which mode to use based on your configuration.

---

## 🚀 Quick Start (No Configuration Needed!)

The local Wiki engine works out of the box with sample articles:

### 1. Start the Service

```bash
cd E:\Python\chatbot
python main.py
```

You'll see:
```
LocalWikiEngine initialized with 6 articles
Wiki skill using local engine mode
Skill registered: wiki_search
```

### 2. Test It!

Ask questions like:
- "What is the annual leave policy?"
- "How do I request IT equipment?"
- "What are the expense reimbursement rules?"

The chatbot will automatically search the local wiki and return relevant articles.

---

## 📦 What's Included

### Sample Articles (Pre-loaded)

The system comes with 6 sample articles covering common enterprise topics:

1. **Annual Leave Policy** (HR)
2. **IT Equipment Request Process** (IT)
3. **Expense Reimbursement Guidelines** (Finance)
4. **Remote Work Policy** (HR)
5. **Code Review Best Practices** (Engineering)
6. **Meeting Room Booking System** (Operations)

### Storage Location

Wiki articles are stored as JSON files in:
```
E:\Python\chatbot\data\wiki\
```

Each article is a separate JSON file for easy management.

---

## 🔧 Managing Wiki Articles

### Method 1: Command-Line Tool

A comprehensive CLI tool is provided for managing articles.

#### View All Articles
```bash
python scripts\manage_wiki.py list
```

#### Search Articles
```bash
python scripts\manage_wiki.py search "leave policy"
python scripts\manage_wiki.py search "IT equipment"
```

#### Show Statistics
```bash
python scripts\manage_wiki.py stats
```

#### Add New Article
Create a JSON file `my_article.json`:
```json
{
  "title": "My New Policy",
  "content": "Full markdown content here...",
  "category": "HR",
  "tags": ["policy", "new"],
  "author": "Your Name"
}
```

Then import it:
```bash
python scripts\manage_wiki.py add my_article.json
```

#### Delete Article
```bash
python scripts\manage_wiki.py delete wiki_0001
```

#### Export All Articles
```bash
python scripts\manage_wiki.py export > backup.json
```

#### Import Articles
```bash
python scripts\manage_wiki.py import backup.json
```

#### Reset to Sample Data
```bash
python scripts\manage_wiki.py init-sample
```

### Method 2: Direct File Editing

Since articles are stored as JSON files, you can:

1. Navigate to `data/wiki/` directory
2. Open any `.json` file in a text editor
3. Edit the content
4. Save the file

Changes take effect immediately (no restart needed).

### Method 3: Programmatic Access

```python
from app.wiki.engine import LocalWikiEngine

# Initialize engine
wiki = LocalWikiEngine()

# Add article
wiki.add_article({
    "title": "New Policy",
    "content": "Content here...",
    "category": "HR",
    "tags": ["policy"]
})

# Search articles
results = wiki.search_articles(query="policy", category="HR")

# Get statistics
print(f"Total articles: {wiki.get_article_count()}")
print(f"Categories: {wiki.get_all_categories()}")
```

---

## 📝 Article Format

Each wiki article follows this structure:

```json
{
  "id": "wiki_0007",
  "title": "Article Title",
  "content": "Full article content in Markdown format...",
  "category": "HR",
  "tags": ["tag1", "tag2", "tag3"],
  "url": "/wiki/hr/article-slug",
  "author": "Author Name",
  "version": "1.0",
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00",
  "metadata": {
    "department": "Human Resources",
    "custom_field": "value"
  }
}
```

### Required Fields
- `title`: Article title
- `content`: Article content (supports Markdown)

### Optional Fields
- `category`: Category for filtering (e.g., HR, IT, Finance)
- `tags`: List of tags for better searchability
- `author`: Article author
- `url`: Web URL (if article exists on a website)
- `metadata`: Any additional custom fields

---

## 🔍 Search Features

### Basic Search
```python
results = wiki.search_articles(query="leave policy")
```

### Exact Title Match
```python
results = wiki.search_articles(
    query="Annual Leave Policy",
    exact_match=True
)
```

### Filter by Category
```python
results = wiki.search_articles(
    query="policy",
    category="HR"
)
```

### Limit Results
```python
results = wiki.search_articles(
    query="IT",
    max_results=5
)
```

### Relevance Scoring
Results include relevance scores (0.0 - 1.0):
- **Title match**: +0.7
- **Content match**: +0.2
- **Tag match**: +0.1

---

## 🔄 Switching to Remote API Mode

If your company later provides a Wiki API, you can easily switch:

### 1. Configure Environment

Edit `.env` file:
```ini
WIKI_API_URL=http://your-group-ai-platform/wiki/query
WIKI_API_KEY=your-wiki-api-key-here
```

### 2. Restart Service

```bash
python main.py
```

You'll see:
```
Wiki skill using remote API mode
```

The system will automatically use the remote API instead of the local engine.

### 3. Keep Local as Backup

Your local articles remain in `data/wiki/` as backup. You can switch back anytime by removing the API configuration.

---

## 💡 Best Practices

### 1. Organize with Categories
Use consistent category names:
- HR, IT, Finance, Engineering, Operations, etc.

### 2. Add Descriptive Tags
Tags improve search accuracy:
```json
"tags": ["leave", "vacation", "holiday", "time-off"]
```

### 3. Use Markdown Formatting
Format content for readability:
```markdown
# Main Heading

## Subheading

- Bullet points
- Easy to read

**Bold** and *italic* text
```

### 4. Regular Updates
Update articles when policies change:
```bash
python scripts\manage_wiki.py delete wiki_0001
python scripts\manage_wiki.py add updated_policy.json
```

### 5. Backup Regularly
Export articles periodically:
```bash
python scripts\manage_wiki.py export > wiki_backup_2024.json
```

---

## 🎯 Use Cases

### Scenario 1: Small/Medium Company
**Problem:** No dedicated knowledge base platform  
**Solution:** Use local Wiki engine with custom articles

### Scenario 2: Development/Testing
**Problem:** Need to test features without API access  
**Solution:** Use local mode during development

### Scenario 3: Offline Operation
**Problem:** Must work without internet connection  
**Solution:** Local engine works completely offline

### Scenario 4: Data Privacy
**Problem:** Sensitive information can't leave premises  
**Solution:** All data stays local on your servers

### Scenario 5: Custom Integration
**Problem:** Need full control over data format  
**Solution:** Direct JSON file manipulation

---

## 📊 Comparison: Local vs Remote

| Feature | Local Engine | Remote API |
|---------|--------------|------------|
| **Setup** | Instant (pre-configured) | Requires API credentials |
| **Dependency** | None | External API required |
| **Customization** | Full control | Limited by API |
| **Performance** | Very fast (local files) | Depends on network |
| **Offline** | ✅ Works offline | ❌ Requires connection |
| **Scalability** | Good for < 1000 articles | Better for large datasets |
| **Maintenance** | Manual file management | Handled by provider |
| **Cost** | Free | May have API costs |
| **Data Control** | Complete ownership | Provider controls data |

---

## 🛠️ Troubleshooting

### Issue: Articles Not Found

**Check:**
1. Verify articles exist: `python scripts\manage_wiki.py list`
2. Check search query spelling
3. Try broader search terms

### Issue: Changes Not Reflecting

**Solution:**
- Local engine reloads on each search
- Ensure JSON files are valid
- Check file permissions

### Issue: Want to Clear All Articles

**Solution:**
```bash
# Delete all article files
rm data/wiki/*.json  # Linux/Mac
del data\wiki\*.json  # Windows

# Reinitialize with samples
python scripts\manage_wiki.py init-sample
```

### Issue: JSON Format Errors

**Validate JSON:**
```bash
python -m json.tool data/wiki/wiki_0001.json
```

---

## 📚 Examples

### Example 1: Add Company-Specific Policy

Create `company_travel_policy.json`:
```json
{
  "title": "Business Travel Policy",
  "content": "# Business Travel Policy\n\n## Approval Process\n...\n",
  "category": "Finance",
  "tags": ["travel", "business", "expense", "approval"],
  "author": "Finance Team",
  "version": "1.0"
}
```

Import it:
```bash
python scripts\manage_wiki.py add company_travel_policy.json
```

### Example 2: Update Existing Article

1. Export current articles:
```bash
python scripts\manage_wiki.py export > all_articles.json
```

2. Edit the JSON file
3. Clear and reimport:
```bash
# Delete old files
del data\wiki\*.json

# Import updated version
python scripts\manage_wiki.py import all_articles.json
```

### Example 3: Bulk Import from External Source

If you have articles from another system:
```python
import json
from app.wiki.engine import LocalWikiEngine

wiki = LocalWikiEngine()

# Load external data
with open('external_articles.json') as f:
    external_data = json.load(f)

# Convert to wiki format
wiki_articles = []
for ext in external_data:
    wiki_articles.append({
        "title": ext['name'],
        "content": ext['body'],
        "category": ext.get('dept', 'General'),
        "tags": ext.get('keywords', []),
        "author": ext.get('author', 'Unknown')
    })

# Import
wiki.import_articles(wiki_articles)
print(f"Imported {len(wiki_articles)} articles")
```

---

## 🎉 Summary

The local Wiki engine provides:

✅ **Zero configuration** - Works immediately  
✅ **Full control** - Manage your own data  
✅ **Offline capable** - No internet needed  
✅ **Easy management** - CLI tools and direct file editing  
✅ **Flexible** - Switch to remote API anytime  
✅ **Sample data** - Pre-loaded with common articles  

**Perfect for teams without a dedicated Wiki API!** 🚀

---

## 🔗 Related Documentation

- [Wiki Skill Implementation](../app/skills/wiki_skill.py)
- [Wiki Engine Code](../app/wiki/engine.py)
- [Management Tool](../scripts/manage_wiki.py)
- [Sample Data](../app/wiki/sample_data.py)
- [Wiki vs RAG Comparison](WIKI_VS_RAG_COMPARISON.md)
