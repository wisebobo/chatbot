"""
Example script demonstrating the enhanced LLM Wiki Compiler
Shows versioning, incremental updates, relationship resolution, and feedback loop
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.wiki.compiler import LLMPoweredWikiCompiler
from app.wiki.engine import LocalWikiEngine


async def main():
    """Demonstrate enhanced Wiki compiler features"""
    
    print("=" * 80)
    print("Enhanced LLM Wiki Compiler - Feature Demonstration")
    print("=" * 80)
    
    # Initialize compiler
    wiki_engine = LocalWikiEngine(storage_dir="data/wiki_demo")
    compiler = LLMPoweredWikiCompiler(wiki_engine=wiki_engine)
    
    # Example 1: Compile a new document (creates new entry)
    print("\n[Example 1] Creating New Wiki Entry")
    print("-" * 80)
    
    sample_content_1 = """
    The Loan Prime Rate (LPR) is a benchmark interest rate for loans in China. 
    It is calculated and published by the National Interbank Funding Center 
    authorized by the People's Bank of China on the 20th of each month.
    
    There are two tenors: 1-year LPR and over-5-year LPR. Commercial banks 
    use LPR as the base rate and add or subtract basis points to determine 
    the actual loan interest rate for customers.
    
    The LPR reform was implemented in August 2019 to improve the transmission 
    of monetary policy and reduce financing costs for enterprises.
    """
    
    article1, operation1 = await compiler.compile_document(
        raw_content=sample_content_1,
        source_url="https://www.pboc.gov.cn/lpr-policy",
        source_type="webpage",
        suggested_category="Finance"
    )
    
    print(f"✅ Operation: {operation1}")
    print(f"   Entry ID: {article1.entry_id}")
    print(f"   Title: {article1.title}")
    print(f"   Type: {article1.type}")
    print(f"   Version: {article1.version}")
    print(f"   Confidence: {article1.confidence}")
    print(f"   Tags: {', '.join(article1.tags[:5])}")
    print(f"   Sources: {len(article1.sources)} source(s)")
    
    # Example 2: Update existing entry (version increment)
    print("\n[Example 2] Updating Existing Entry (Version Increment)")
    print("-" * 80)
    
    updated_content = """
    The Loan Prime Rate (LPR) is the primary benchmark interest rate for loans in China.
    It is calculated and published by the National Interbank Funding Center 
    authorized by the People's Bank of China on the 20th of each month (postponed if holiday).
    
    There are two standard tenors: 1-year LPR and over-5-year LPR. 
    Since 2023, a 5-year LPR has been the reference for mortgage rates.
    
    Commercial banks use LPR as the pricing base and add/subtract basis points 
    based on customer creditworthiness to determine final loan rates.
    
    Key Updates (2024):
    - LPR cut by 10 basis points in February 2024
    - Further 25 bps reduction in July 2024 to stimulate economy
    - Over-5-year LPR now at historic low of 3.85%
    
    The LPR mechanism improves monetary policy transmission and reduces 
    corporate financing costs effectively.
    """
    
    article2, operation2 = await compiler.compile_document(
        raw_content=updated_content,
        source_url="https://www.pboc.gov.cn/lpr-policy-updated",
        source_type="webpage",
        suggested_category="Finance",
        force_recompile=True  # Force recompile despite same doc hash
    )
    
    print(f"✅ Operation: {operation2}")
    print(f"   Entry ID: {article2.entry_id}")
    print(f"   Title: {article2.title}")
    print(f"   Version: {article2.version} (incremented from {article1.version})")
    print(f"   Update Time: {article2.update_time}")
    print(f"   Content Length: {len(article2.content)} chars")
    
    # Example 3: Submit user feedback
    print("\n[Example 3] User Feedback Loop")
    print("-" * 80)
    
    # Simulate positive feedback
    wiki_engine.submit_feedback(article2.entry_id, is_positive=True, comment="Very clear explanation!")
    wiki_engine.submit_feedback(article2.entry_id, is_positive=True)
    wiki_engine.submit_feedback(article2.entry_id, is_positive=False, comment="Needs more recent data")
    
    updated_article = wiki_engine.get_article(article2.entry_id)
    print(f"[OK] Feedback Recorded:")
    print(f"   Positive: {updated_article.feedback.positive}")
    print(f"   Negative: {updated_article.feedback.negative}")
    print(f"   Comments: {len(updated_article.feedback.comments)}")
    print(f"   Updated Confidence: {updated_article.confidence:.3f}")
    
    # Example 4: Compile related content (relationship resolution)
    print("\n[Example 4] Relationship Resolution")
    print("-" * 80)
    
    related_content = """
    Mortgage Interest Rate Calculation
    
    Mortgage rates in China are based on the 5-year LPR plus/minus basis points.
    Formula: Mortgage Rate = 5-year LPR + BP adjustment
    
    For first-time homebuyers, banks may offer LPR - 20bps.
    For second homes, typically LPR + 60bps.
    
    Example: If 5-year LPR is 3.85%, first-home buyer gets 3.65%.
    """
    
    article3, operation3 = await compiler.compile_document(
        raw_content=related_content,
        source_url="https://www.pboc.gov.cn/mortgage-rates",
        source_type="webpage",
        suggested_category="Finance"
    )
    
    print(f"[OK] Operation: {operation3}")
    print(f"   Entry ID: {article3.entry_id}")
    print(f"   Title: {article3.title}")
    print(f"   Related Articles: {len(article3.related_ids)}")
    
    for rel in article3.related_ids:
        related_article = wiki_engine.get_article(rel.entry_id)
        if related_article:
            print(f"      - {related_article.title} ({rel.relation})")
    
    # Example 5: Knowledge Graph Report
    print("\n[Example 5] Knowledge Graph Statistics")
    print("-" * 80)
    
    report = compiler.generate_knowledge_graph_report()
    print(f"[OK] Total Articles: {report['total_articles']}")
    print(f"   By Type: {report['by_type']}")
    print(f"   By Status: {report['by_status']}")
    print(f"   Average Confidence: {report['avg_confidence']}")
    print(f"   Total Relationships: {report['total_relationships']}")
    print(f"   Average Version: {report['avg_version']}")
    print(f"   Feedback Summary:")
    print(f"      - Positive: {report['feedback_summary']['total_positive']}")
    print(f"      - Negative: {report['feedback_summary']['total_negative']}")
    print(f"      - Articles with Feedback: {report['feedback_summary']['articles_with_feedback']}")
    
    # Example 6: Search with confidence filtering
    print("\n[Example 6] Advanced Search")
    print("-" * 80)
    
    search_results = wiki_engine.search_articles(
        query="LPR loan rate",
        min_confidence=0.8,
        max_results=5
    )
    
    print(f"[OK] Found {len(search_results)} articles (confidence >= 0.8)")
    for i, result in enumerate(search_results, 1):
        print(f"   {i}. {result['title']}")
        print(f"      Entry ID: {result['entry_id']}")
        print(f"      Confidence: {result['confidence']:.3f}")
        print(f"      Relevance: {result['relevance_score']:.3f}")
        print(f"      Version: {result['version']}")
    
    print("\n" + "=" * 80)
    print("[OK] All examples completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
