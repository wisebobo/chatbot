"""
Example: Using LLM-powered Wiki Compiler
Demonstrates how to automatically compile raw documents into structured wiki articles
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.wiki.compiler import LLMPoweredWikiCompiler


async def example_compile_single_document():
    """Example: Compile a single raw document into wiki article"""
    print("=" * 80)
    print("Example 1: Compile Single Document")
    print("=" * 80)
    
    # Initialize compiler
    compiler = LLMPoweredWikiCompiler()
    
    # Sample raw document (could be from PDF, webpage, Word doc, etc.)
    raw_document = """
    Company Vacation Policy 2024
    
    All employees are entitled to vacation time. New employees get 10 days in their first year.
    After 2 years, they get 15 days. After 5 years, they get 20 days.
    
    To request vacation:
    1. Submit request at least 2 weeks in advance
    2. Get manager approval
    3. HR will process the request
    
    Unused vacation days can be carried over, but maximum 5 days.
    If you leave the company, unused vacation will be paid out.
    
    National holidays don't count against your vacation days.
    Sick leave is separate from vacation.
    """
    
    print("\n📄 Raw Document:")
    print(raw_document[:200] + "...")
    
    print("\n⚙️  Compiling with LLM...")
    
    try:
        article = await compiler.compile_document(
            raw_content=raw_document,
            source_url="https://intranet.company.com/hr/vacation-policy",
            source_type="text",
            category="HR"
        )
        
        print(f"\n✅ Compiled Successfully!")
        print(f"Title: {article.title}")
        print(f"Category: {article.category}")
        print(f"Tags: {', '.join(article.tags)}")
        print(f"\nGenerated Wiki Content (first 500 chars):")
        print(article.content[:500] + "...")
        
    except Exception as e:
        print(f"\n❌ Compilation failed: {e}")
        print("Note: This requires a configured LLM API. See docs for setup.")


async def example_batch_compilation():
    """Example: Compile multiple documents in batch"""
    print("\n" + "=" * 80)
    print("Example 2: Batch Compilation")
    print("=" * 80)
    
    compiler = LLMPoweredWikiCompiler()
    
    # Multiple raw documents
    documents = [
        {
            "content": "IT Security Policy: All employees must use strong passwords. Passwords should be changed every 90 days. Multi-factor authentication is required for remote access.",
            "source_url": "https://intranet.company.com/it/security",
            "source_type": "text",
            "category": "IT"
        },
        {
            "content": "Expense Report Guidelines: Keep all receipts over $25. Submit reports within 30 days. Manager approval required. Finance processes payments in 10 business days.",
            "source_url": "https://intranet.company.com/finance/expenses",
            "source_type": "text",
            "category": "Finance"
        }
    ]
    
    print(f"\n📦 Processing {len(documents)} documents...")
    
    try:
        articles = await compiler.batch_compile_documents(documents, delay_between=0.5)
        
        print(f"\n✅ Batch compilation complete: {len(articles)} articles created")
        
        for article in articles:
            print(f"  - {article.title} ({article.category})")
            
    except Exception as e:
        print(f"\n❌ Batch compilation failed: {e}")


async def example_generate_index():
    """Example: Generate comprehensive wiki index"""
    print("\n" + "=" * 80)
    print("Example 3: Generate Wiki Index")
    print("=" * 80)
    
    compiler = LLMPoweredWikiCompiler()
    
    print("\n📑 Generating index...")
    index = compiler.generate_index()
    
    print(f"\n{index}")


async def main():
    """Run all examples"""
    print("\n🚀 LLM-Powered Wiki Compiler Examples\n")
    print("Note: These examples require a configured LLM API.")
    print("If LLM is not available, the compiler will show error messages.\n")
    
    # Example 1: Single document
    await example_compile_single_document()
    
    # Example 2: Batch compilation
    await example_batch_compilation()
    
    # Example 3: Generate index
    await example_generate_index()
    
    print("\n" + "=" * 80)
    print("Examples complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
