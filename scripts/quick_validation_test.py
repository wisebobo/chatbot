"""
Quick validation test for Enhanced Wiki Compiler v2.0
Tests core functionality without requiring external LLM API
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.wiki.engine import (
    LocalWikiEngine, 
    WikiArticle, 
    KnowledgeType, 
    RelationType, 
    EntryStatus,
    SourceReference,
    RelatedEntry,
    UserFeedback
)


def test_data_models():
    """Test that all new data models work correctly"""
    print("=" * 80)
    print("Test 1: Data Models Validation")
    print("=" * 80)
    
    # Test WikiArticle creation with new fields
    article = WikiArticle(
        entry_id="test_concept_001",
        title="Test Concept",
        aliases=["test alias", "alternative name"],
        type=KnowledgeType.CONCEPT,
        content="# Test Content\n\nThis is a test.",
        summary="Test summary",
        parent_ids=[],
        related_ids=[
            RelatedEntry(entry_id="related_001", relation=RelationType.RELATED_TO)
        ],
        tags=["test", "validation"],
        sources=[
            SourceReference(
                source_id="doc_abc123",
                file_name="test.pdf",
                page=1,
                content_snippet="Test snippet",
                url="https://example.com"
            )
        ],
        confidence=0.95,
        status=EntryStatus.ACTIVE,
        version=1,
        feedback=UserFeedback(positive=5, negative=1, comments=["Good!"])
    )
    
    print(f"✅ WikiArticle created successfully")
    print(f"   Entry ID: {article.entry_id}")
    print(f"   Type: {article.type}")
    print(f"   Version: {article.version}")
    print(f"   Confidence: {article.confidence}")
    print(f"   Status: {article.status}")
    print(f"   Aliases: {len(article.aliases)}")
    print(f"   Related IDs: {len(article.related_ids)}")
    print(f"   Sources: {len(article.sources)}")
    print(f"   Feedback: +{article.feedback.positive}/-{article.feedback.negative}")
    
    # Test serialization
    data = article.model_dump()
    assert 'entry_id' in data
    assert 'related_ids' in data
    assert 'sources' in data
    print(f"✅ Serialization works correctly")
    
    return True


def test_wiki_engine():
    """Test enhanced Wiki engine features"""
    print("\n" + "=" * 80)
    print("Test 2: Enhanced Wiki Engine")
    print("=" * 80)
    
    # Create temporary engine
    engine = LocalWikiEngine(storage_dir="data/wiki_test_validation")
    
    # Test adding article with new schema
    article_data = {
        "entry_id": "validate_test_001",
        "title": "Validation Test Article",
        "aliases": ["test", "validation"],
        "type": "concept",
        "content": "# Test\n\nValidation content.",
        "summary": "Test summary",
        "tags": ["test", "validation"],
        "confidence": 0.9,
        "status": "active",
        "version": 1,
        "sources": [
            {
                "source_id": "doc_xyz789",
                "file_name": "test.txt",
                "page": 1,
                "content_snippet": "Test content",
                "url": None
            }
        ],
        "feedback": {
            "positive": 0,
            "negative": 0,
            "comments": []
        }
    }
    
    article = engine.add_article(article_data)
    print(f"✅ Article added: {article.entry_id}")
    print(f"   Title: {article.title}")
    print(f"   Version: {article.version}")
    
    # Test feedback submission
    engine.submit_feedback(article.entry_id, is_positive=True, comment="Great!")
    updated = engine.get_article(article.entry_id)
    print(f"✅ Feedback submitted: +{updated.feedback.positive}/-{updated.feedback.negative}")
    print(f"   Comments: {len(updated.feedback.comments)}")
    print(f"   Updated confidence: {updated.confidence:.3f}")
    
    # Test search with new filters
    results = engine.search_articles(
        query="validation",
        min_confidence=0.8,
        max_results=5
    )
    print(f"✅ Search works: found {len(results)} results")
    
    # Test knowledge graph report
    report = {
        "total_articles": engine.get_article_count(),
        "by_type": {},
        "by_status": {},
        "avg_confidence": 0.0
    }
    
    for art in engine.articles.values():
        type_key = art.type.value if isinstance(art.type, KnowledgeType) else art.type
        report["by_type"][type_key] = report["by_type"].get(type_key, 0) + 1
        
        status_key = art.status.value if isinstance(art.status, EntryStatus) else art.status
        report["by_status"][status_key] = report["by_status"].get(status_key, 0) + 1
        
        report["avg_confidence"] += art.confidence
    
    if engine.get_article_count() > 0:
        report["avg_confidence"] /= engine.get_article_count()
    
    print(f"✅ Analytics report generated:")
    print(f"   Total articles: {report['total_articles']}")
    print(f"   By type: {report['by_type']}")
    print(f"   By status: {report['by_status']}")
    print(f"   Avg confidence: {report['avg_confidence']:.3f}")
    
    # Cleanup
    import shutil
    from pathlib import Path as PPath
    test_dir = PPath("data/wiki_test_validation")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    print(f"✅ Cleanup completed")
    
    return True


def test_compiler_structure():
    """Test that compiler has all required methods"""
    print("\n" + "=" * 80)
    print("Test 3: Compiler Structure Validation")
    print("=" * 80)
    
    from app.wiki.compiler import LLMPoweredWikiCompiler
    
    # Check class exists and has required methods
    required_methods = [
        'compile_document',
        '_generate_wiki_entry_json',
        '_post_process_article',
        '_resolve_relationships',
        '_incremental_update',
        '_parse_llm_json_response',
        '_validate_and_normalize',
        '_find_article_by_title_or_alias',
        'batch_compile_documents',
        'recompile_low_confidence_articles',
        'generate_knowledge_graph_report'
    ]
    
    missing = []
    for method in required_methods:
        if not hasattr(LLMPoweredWikiCompiler, method):
            missing.append(method)
    
    if missing:
        print(f"❌ Missing methods: {missing}")
        return False
    else:
        print(f"✅ All {len(required_methods)} required methods present")
    
    # Check constants
    if hasattr(LLMPoweredWikiCompiler, 'TYPE_ABBREVIATIONS'):
        print(f"✅ TYPE_ABBREVIATIONS constant defined")
        print(f"   Types: {list(LLMPoweredWikiCompiler.TYPE_ABBREVIATIONS.keys())}")
    else:
        print(f"❌ TYPE_ABBREVIATIONS constant missing")
        return False
    
    return True


def test_sample_data():
    """Test that sample data follows new schema"""
    print("\n" + "=" * 80)
    print("Test 4: Sample Data Validation")
    print("=" * 80)
    
    from app.wiki.sample_data import get_sample_articles
    
    articles = get_sample_articles()
    print(f"✅ Loaded {len(articles)} sample articles")
    
    # Validate first article
    if articles:
        first = articles[0]
        required_fields = [
            'entry_id', 'title', 'type', 'content', 'create_time', 
            'update_time', 'version', 'sources'
        ]
        
        missing = [f for f in required_fields if f not in first]
        if missing:
            print(f"❌ Missing required fields: {missing}")
            return False
        
        print(f"✅ First article has all required fields")
        print(f"   Entry ID: {first['entry_id']}")
        print(f"   Title: {first['title']}")
        print(f"   Type: {first['type']}")
        print(f"   Version: {first['version']}")
        print(f"   Has aliases: {'aliases' in first}")
        print(f"   Has related_ids: {'related_ids' in first}")
        print(f"   Has sources: {len(first.get('sources', []))} sources")
        print(f"   Has feedback: {'feedback' in first}")
    
    return True


async def main():
    """Run all validation tests"""
    print("\n" + "🧪" * 40)
    print("Enhanced Wiki Compiler v2.0 - Quick Validation")
    print("🧪" * 40 + "\n")
    
    results = []
    
    try:
        # Test 1: Data Models
        results.append(("Data Models", test_data_models()))
        
        # Test 2: Wiki Engine
        results.append(("Wiki Engine", test_wiki_engine()))
        
        # Test 3: Compiler Structure
        results.append(("Compiler Structure", test_compiler_structure()))
        
        # Test 4: Sample Data
        results.append(("Sample Data", test_sample_data()))
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Error", False))
    
    # Summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10} - {name}")
    
    print("-" * 80)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All validation tests passed!")
        print("\nNext steps:")
        print("1. Run full example: python scripts/example_enhanced_wiki_compiler.py")
        print("2. Test with real LLM API (requires valid API key)")
        print("3. Review documentation: docs/ENHANCED_WIKI_COMPILER_V2.md")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review errors above.")
    
    print("=" * 80)
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
