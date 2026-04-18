# LLM-Powered Wiki: Automated Knowledge Compilation

## 📋 Overview

This is a **true LLM-powered Wiki system** that automatically transforms raw, unstructured documents into well-organized, structured wiki articles.

### The Complete Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Raw Documents Ingestion                             │
│ ─────────────────────────────────                           │
│ • PDF documents                                             │
│ • Word files                                                │
│ • Web pages                                                 │
│ • Email threads                                             │
│ • Meeting notes                                             │
│ • Any text content                                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 2: LLM Analysis & Extraction                           │
│ ───────────────────────────────────                         │
│ • Understand document structure                             │
│ • Extract key information                                   │
│ • Identify main topics                                      │
│ • Detect category                                           │
│ • Generate relevant tags                                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Structured Article Generation                       │
│ ───────────────────────────────────────                     │
│ • Create professional title                                 │
│ • Write clear summary                                       │
│ • Organize into sections                                    │
│ • Format in clean Markdown                                  │
│ • Add practical examples                                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 4: Cross-Linking & Indexing                            │
│ ────────────────────────────────────                        │
│ • Find related articles                                     │
│ • Add cross-reference links                                 │
│ • Update category index                                     │
│ • Generate tag connections                                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 5: Persistent Storage                                  │
│ ──────────────────────────────                              │
│ • Save as structured JSON                                   │
│ • Maintain version history                                  │
│ • Track compilation metadata                                │
│ • Enable incremental updates                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Result: Searchable, Structured Wiki                         │
│ ─────────────────────────────────────                       │
│ Users can now query the wiki and get accurate,              │
│ well-organized answers from compiled knowledge.             │
└─────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

### 1. **Active Knowledge Processing**
- ✅ LLM actively reads and understands documents
- ✅ Automatic extraction of key concepts
- ✅ Intelligent categorization
- ✅ Smart tag generation

### 2. **Stateful & Persistent**
- ✅ All knowledge permanently stored
- ✅ Version tracking for updates
- ✅ Document hash detection (avoid reprocessing)
- ✅ Incremental compilation support

### 3. **Structured Output**
- ✅ Professional Markdown formatting
- ✅ Clear section organization
- ✅ Concise summaries
- ✅ Practical examples included

### 4. **Intelligent Linking**
- ✅ Automatic cross-reference discovery
- ✅ Related article suggestions
- ✅ Category-based grouping
- ✅ Tag-based connections

### 5. **Continuous Improvement**
- ✅ Batch processing capability
- ✅ Re-compilation when source changes
- ✅ Index auto-generation
- ✅ Quality metadata

---

## 🚀 Quick Start

### Basic Usage

```python
import asyncio
from app.wiki.compiler import LLMPoweredWikiCompiler

async def compile_document():
    # Initialize compiler
    compiler = LLMPoweredWikiCompiler()
    
    # Raw document content (from PDF, web, email, etc.)
    raw_content = """
    Your raw, unstructured document content here...
    Could be extracted from PDF, copied from webpage, etc.
    """
    
    # Compile into structured wiki article
    article = await compiler.compile_document(
        raw_content=raw_content,
        source_url="https://example.com/source",
        source_type="text",  # or "pdf", "webpage", "docx"
        category="HR"  # optional, LLM can auto-detect
    )
    
    print(f"Created: {article.title}")
    print(f"Category: {article.category}")
    print(f"Tags: {article.tags}")

asyncio.run(compile_document())
```

### Batch Processing

```python
# Process multiple documents at once
documents = [
    {
        "content": "Raw content from document 1...",
        "source_url": "https://example.com/doc1",
        "category": "IT"
    },
    {
        "content": "Raw content from document 2...",
        "source_url": "https://example.com/doc2",
        "category": "Finance"
    }
]

articles = await compiler.batch_compile_documents(documents)
print(f"Compiled {len(articles)} articles")
```

### Generate Index

```python
# Create comprehensive wiki index
index = compiler.generate_index()
print(index)
```

---

## 📖 Detailed Examples

### Example 1: From PDF to Wiki Article

```python
# Step 1: Extract text from PDF (using PyPDF2, pdfplumber, etc.)
import pdfplumber

def extract_pdf_text(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

# Step 2: Compile with LLM
raw_text = extract_pdf_text("company_handbook.pdf")

article = await compiler.compile_document(
    raw_content=raw_text,
    source_url="file://company_handbook.pdf",
    source_type="pdf",
    category="HR"
)

# Result: Beautifully structured wiki article!
```

### Example 2: From Web Page to Wiki

```python
# Step 1: Scrape web content (using requests + BeautifulSoup)
import requests
from bs4 import BeautifulSoup

def scrape_webpage(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract main content (adjust selector based on site structure)
    content = soup.find('article').get_text()
    return content

# Step 2: Compile
url = "https://company-intranet.com/policies/remote-work"
web_content = scrape_webpage(url)

article = await compiler.compile_document(
    raw_content=web_content,
    source_url=url,
    source_type="webpage"
)
```

### Example 3: From Email Thread to Wiki

```python
# Step 1: Parse email thread
email_content = """
From: HR Team
Subject: Updated Vacation Policy

Hi everyone,

We're updating our vacation policy effective Jan 1, 2025:
- New employees: 12 days (was 10)
- 2+ years: 18 days (was 15)
- 5+ years: 25 days (was 20)

Please submit requests 3 weeks in advance (was 2 weeks).

Best,
HR Team
"""

# Step 2: Compile
article = await compiler.compile_document(
    raw_content=email_content,
    source_type="email",
    category="HR"
)

# LLM will structure this into a proper policy document!
```

---

## 🔧 Configuration

### LLM Requirements

The compiler requires a configured LLM adapter. Ensure your `.env` has:

```ini
LLM_API_BASE_URL=http://your-llm-api/v1
LLM_API_KEY=your-api-key
LLM_MODEL=gpt-4-or-equivalent
```

### Compiler Settings

You can customize compilation behavior:

```python
compiler = LLMPoweredWikiCompiler()

# Adjust rate limiting for batch processing
articles = await compiler.batch_compile_documents(
    documents,
    delay_between=2.0  # seconds between requests
)
```

---

## 📊 What Gets Generated

### Sample Input (Raw Text)

```
Company travel policy. Employees can book flights up to $500 domestic, $1500 international. 
Hotels should be company-approved. Keep all receipts. Submit expense report within 2 weeks. 
Manager approval needed for trips over 5 days.
```

### Sample Output (Structured Wiki)

```markdown
# Corporate Travel Policy

## Overview
This policy outlines guidelines and procedures for employee business travel, including booking limits, approval requirements, and expense reporting.

## Booking Limits

### Domestic Travel
- Maximum flight cost: **$500**
- Hotel: Company-approved vendors only
- Ground transportation: Reasonable costs covered

### International Travel
- Maximum flight cost: **$1,500**
- Hotel: Company-approved vendors only
- Additional allowances may apply for extended stays

## Approval Process

1. **Standard Trips** (≤5 days)
   - Submit travel request form
   - Obtain manager approval
   - Book through approved channels

2. **Extended Trips** (>5 days)
   - Manager approval required
   - Department head notification
   - Justification document needed

## Expense Reporting

### Requirements
- Keep **all original receipts**
- Submit expense report within **2 weeks** of return
- Use company expense system
- Categorize expenses appropriately

### Reimbursable Items
✓ Flights (within limits)
✓ Hotels (approved vendors)
✓ Meals (reasonable amounts)
✓ Ground transportation
✓ Business-related incidentals

### Non-Reimbursable
✗ Personal entertainment
✗ Upgrades beyond policy
✗ Late submission penalties

## Related Articles
- [Expense Reimbursement Guidelines](/wiki/wiki_0003)
- [Approval Workflows](/wiki/wiki_0012)
```

---

## 🎯 Use Cases

### 1. **Company Handbook Digitization**
- Convert PDF handbooks into searchable wiki
- Auto-update when policies change
- Maintain version history

### 2. **Meeting Notes to Knowledge Base**
- Transform meeting transcripts into actionable docs
- Extract decisions and action items
- Link to related projects

### 3. **Email Archive to Wiki**
- Convert important email threads into permanent records
- Extract policies announced via email
- Preserve institutional knowledge

### 4. **Web Content Curation**
- Archive important external resources
- Summarize industry best practices
- Maintain competitive intelligence

### 5. **Training Material Creation**
- Convert raw training docs into structured guides
- Add examples and clarifications
- Create learning paths

---

## 🔄 Continuous Maintenance

### Automatic Updates

When source documents change:

```python
# Re-compile if source changed
article = await compiler.compile_document(
    raw_content=updated_content,
    force_recompile=True  # Force update even if hash matches
)
```

### Index Regeneration

```python
# Periodically regenerate index
index = compiler.generate_index()
with open("WIKI_INDEX.md", "w") as f:
    f.write(index)
```

### Quality Checks

```python
# Review compiled articles
for article in wiki_engine.articles.values():
    print(f"{article.title}: {len(article.content)} words, {len(article.tags)} tags")
```

---

## 💡 Best Practices

### 1. **Source Document Quality**
- Provide clean, readable text
- Remove irrelevant content (headers, footers, ads)
- Preserve document structure where possible

### 2. **Category Assignment**
- Let LLM auto-detect when unsure
- Override for specific organizational needs
- Keep categories consistent

### 3. **Batch Processing Strategy**
- Group similar documents together
- Use appropriate delays to avoid rate limits
- Monitor for failures and retry

### 4. **Review & Refinement**
- Periodically review auto-generated articles
- Manually edit if needed
- Provide feedback to improve future compilations

### 5. **Incremental Updates**
- Use document hashing to avoid reprocessing
- Only recompile when content actually changes
- Track compilation timestamps

---

## 🆚 Comparison: Manual vs LLM-Powered

| Aspect | Manual Wiki | LLM-Powered Wiki |
|--------|-------------|------------------|
| **Setup Time** | Hours per article | Minutes per article |
| **Consistency** | Varies by author | Uniform quality |
| **Structure** | Depends on writer | Always well-organized |
| **Cross-linking** | Manual effort | Automatic |
| **Updates** | Easy to forget | Can be automated |
| **Scalability** | Limited by human capacity | Highly scalable |
| **Cost** | High labor cost | API costs only |
| **Quality** | Expert-dependent | Consistently good |

---

## 🛠️ Advanced Features

### Custom Prompts

You can customize the LLM prompts for specific domains:

```python
# Modify _extract_structure() prompt for technical docs
# Modify _generate_wiki_article() prompt for specific tone
# Adjust in compiler.py as needed
```

### Metadata Enrichment

Add custom metadata fields:

```python
metadata = {
    "department": "Engineering",
    "review_cycle": "quarterly",
    "owner": "tech-lead@company.com",
    "compliance_required": True
}
```

### Integration with External Systems

```python
# Hook into document management systems
# Trigger compilation on file upload
# Sync with SharePoint, Confluence, etc.
```

---

## 📈 Performance Considerations

### Token Usage
- Structure extraction: ~1000-2000 tokens
- Article generation: ~2000-4000 tokens
- Metadata extraction: ~500-1000 tokens
- **Total per document**: ~3500-7000 tokens

### Optimization Tips
- Truncate very long documents (>10k words)
- Process in batches with delays
- Cache results to avoid reprocessing
- Use cheaper models for initial drafts

---

## 🔗 Related Documentation

- [Local Wiki Engine Guide](LOCAL_WIKI_ENGINE_GUIDE.md) - Storage and management
- [Wiki Integration Guide](WIKI_INTEGRATION_GUIDE.md) - Remote API setup
- [Example Script](../scripts/example_wiki_compiler.py) - Working examples
- [Compiler Implementation](../app/wiki/compiler.py) - Source code

---

## 🎉 Summary

The **LLM-Powered Wiki Compiler** transforms your approach to knowledge management:

✅ **Passive → Active**: No more manual article writing  
✅ **Unstructured → Structured**: Automatic organization  
✅ **Fragmented → Connected**: Intelligent cross-linking  
✅ **Static → Dynamic**: Continuous improvement  
✅ **Labor-intensive → Automated**: Scale effortlessly  

**True knowledge automation!** 🚀
