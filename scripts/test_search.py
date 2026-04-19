"""Quick test to verify search functionality"""
from app.wiki.engine import LocalWikiEngine

engine = LocalWikiEngine('data/wiki_demo')

print("All articles:")
for article in engine.articles.values():
    print(f"  - {article.entry_id}: confidence={article.confidence:.3f}")

print("\nSearch results (query='LPR loan rate', min_confidence=0.8):")
results = engine.search_articles(query='LPR loan rate', min_confidence=0.8, max_results=5)
print(f"Found {len(results)} results")
for r in results:
    print(f"  - {r['title']}: confidence={r['confidence']:.3f}, relevance={r['relevance_score']:.3f}")
