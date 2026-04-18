"""
Wiki management CLI tool
Provides commands to manage local wiki articles
"""
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.wiki.engine import LocalWikiEngine
from app.wiki.sample_data import get_sample_articles


def print_usage():
    """Print usage instructions"""
    print("""
Wiki Management Tool
====================

Usage:
    python manage_wiki.py <command> [options]

Commands:
    list                    List all wiki articles
    search <query>          Search wiki articles
    add <file.json>         Add article from JSON file
    delete <article_id>     Delete an article
    export                  Export all articles to JSON
    import <file.json>      Import articles from JSON file
    init-sample             Initialize with sample articles
    stats                   Show wiki statistics

Examples:
    python manage_wiki.py list
    python manage_wiki.py search "leave policy"
    python manage_wiki.py add my_article.json
    python manage_wiki.py delete wiki_0001
    python manage_wiki.py export > backup.json
    python manage_wiki.py import backup.json
    python manage_wiki.py init-sample
    python manage_wiki.py stats
""")


def cmd_list(wiki: LocalWikiEngine):
    """List all articles"""
    articles = wiki.export_articles()
    
    if not articles:
        print("No articles found.")
        return
    
    print(f"\nFound {len(articles)} articles:\n")
    print("-" * 80)
    
    for article in sorted(articles, key=lambda x: x['title']):
        print(f"ID:       {article['id']}")
        print(f"Title:    {article['title']}")
        print(f"Category: {article.get('category', 'N/A')}")
        print(f"Author:   {article.get('author', 'N/A')}")
        print(f"Updated:  {article.get('updated_at', 'N/A')[:10]}")
        print(f"Tags:     {', '.join(article.get('tags', []))}")
        print("-" * 80)


def cmd_search(wiki: LocalWikiEngine, query: str):
    """Search articles"""
    results = wiki.search_articles(query=query, max_results=20)
    
    if not results:
        print(f"No articles found matching '{query}'")
        return
    
    print(f"\nFound {len(results)} articles matching '{query}':\n")
    
    for i, article in enumerate(results, 1):
        print(f"{i}. {article['title']} (Score: {article['relevance_score']:.2f})")
        print(f"   Category: {article.get('category', 'N/A')}")
        print(f"   Preview: {article['content'][:200]}...")
        print()


def cmd_add(wiki: LocalWikiEngine, filepath: str):
    """Add article from JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both single article and list of articles
        if isinstance(data, list):
            for item in data:
                wiki.add_article(item)
            print(f"Added {len(data)} articles")
        else:
            wiki.add_article(data)
            print(f"Added article: {data.get('title', 'Unknown')}")
    
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}")
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}")
    except Exception as e:
        print(f"Error adding article: {e}")


def cmd_delete(wiki: LocalWikiEngine, article_id: str):
    """Delete an article"""
    article = wiki.get_article(article_id)
    
    if not article:
        print(f"Error: Article not found: {article_id}")
        return
    
    confirm = input(f"Delete article '{article.title}'? (yes/no): ")
    
    if confirm.lower() == 'yes':
        if wiki.delete_article(article_id):
            print(f"Deleted article: {article.title}")
        else:
            print("Error deleting article")
    else:
        print("Deletion cancelled")


def cmd_export(wiki: LocalWikiEngine):
    """Export all articles to stdout as JSON"""
    articles = wiki.export_articles()
    print(json.dumps(articles, indent=2, ensure_ascii=False))


def cmd_import(wiki: LocalWikiEngine, filepath: str):
    """Import articles from JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print("Error: JSON file must contain a list of articles")
            return
        
        wiki.import_articles(data)
        print(f"Imported {len(data)} articles")
    
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}")
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}")
    except Exception as e:
        print(f"Error importing articles: {e}")


def cmd_init_sample(wiki: LocalWikiEngine):
    """Initialize with sample articles"""
    if wiki.get_article_count() > 0:
        confirm = input("Wiki already has articles. Add samples anyway? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Cancelled")
            return
    
    samples = get_sample_articles()
    wiki.import_articles(samples)
    print(f"Initialized with {len(samples)} sample articles")


def cmd_stats(wiki: LocalWikiEngine):
    """Show statistics"""
    categories = wiki.get_all_categories()
    tags = wiki.get_all_tags()
    
    print("\nWiki Statistics")
    print("=" * 50)
    print(f"Total Articles: {wiki.get_article_count()}")
    print(f"Categories:     {len(categories)}")
    print(f"Tags:           {len(tags)}")
    print()
    
    if categories:
        print("Categories:")
        for cat in categories:
            count = sum(1 for a in wiki.articles.values() if a.category == cat)
            print(f"  - {cat}: {count} articles")
        print()
    
    if tags:
        print("Top Tags:")
        tag_counts = {}
        for article in wiki.articles.values():
            for tag in article.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  - {tag}: {count} articles")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    # Initialize wiki engine
    wiki = LocalWikiEngine()
    
    # Execute command
    if command == "list":
        cmd_list(wiki)
    
    elif command == "search":
        if len(sys.argv) < 3:
            print("Error: Please provide a search query")
            print("Usage: python manage_wiki.py search <query>")
            sys.exit(1)
        query = " ".join(sys.argv[2:])
        cmd_search(wiki, query)
    
    elif command == "add":
        if len(sys.argv) < 3:
            print("Error: Please provide a JSON file path")
            print("Usage: python manage_wiki.py add <file.json>")
            sys.exit(1)
        cmd_add(wiki, sys.argv[2])
    
    elif command == "delete":
        if len(sys.argv) < 3:
            print("Error: Please provide an article ID")
            print("Usage: python manage_wiki.py delete <article_id>")
            sys.exit(1)
        cmd_delete(wiki, sys.argv[2])
    
    elif command == "export":
        cmd_export(wiki)
    
    elif command == "import":
        if len(sys.argv) < 3:
            print("Error: Please provide a JSON file path")
            print("Usage: python manage_wiki.py import <file.json>")
            sys.exit(1)
        cmd_import(wiki, sys.argv[2])
    
    elif command == "init-sample":
        cmd_init_sample(wiki)
    
    elif command == "stats":
        cmd_stats(wiki)
    
    else:
        print(f"Error: Unknown command '{command}'")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
