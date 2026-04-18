"""
Test script to verify LLM API connection and functionality
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.llm.adapter import get_llm_adapter
from langchain_core.messages import HumanMessage, SystemMessage


async def test_llm_basic_connection():
    """Test basic LLM API connection"""
    print("=" * 80)
    print("Test 1: Basic LLM API Connection")
    print("=" * 80)
    
    try:
        adapter = get_llm_adapter()
        print(f"✓ LLM Adapter initialized successfully")
        print(f"  - Base URL: {adapter._settings.api_base_url}")
        print(f"  - Model: {adapter._settings.model_name}")
        print(f"  - Temperature: {adapter._settings.temperature}")
        
        # Test simple message
        response = await adapter.ainvoke([
            HumanMessage(content="Hello! Please respond with 'Connection successful' if you can read this.")
        ])
        
        print(f"\n✓ LLM API call successful!")
        print(f"  Response: {response.content[:100]}...")
        return True
        
    except Exception as e:
        print(f"\n✗ LLM API connection failed!")
        print(f"  Error: {e}")
        return False


async def test_llm_wiki_compilation():
    """Test LLM-powered Wiki compilation"""
    print("\n" + "=" * 80)
    print("Test 2: LLM Wiki Compilation Capability")
    print("=" * 80)
    
    try:
        from app.wiki.compiler import LLMPoweredWikiCompiler
        
        compiler = LLMPoweredWikiCompiler()
        
        # Test document
        test_doc = """
        Company IT Security Policy
        
        All employees must use strong passwords with at least 12 characters.
        Passwords should include uppercase, lowercase, numbers, and special characters.
        Change passwords every 90 days.
        Multi-factor authentication (MFA) is required for all remote access.
        Do not share passwords with anyone.
        Report suspicious activity to IT security team immediately.
        """
        
        print("Compiling test document with LLM...")
        article = await compiler.compile_document(
            raw_content=test_doc,
            source_type="text",
            category="IT"
        )
        
        print(f"\n✓ Wiki compilation successful!")
        print(f"  Title: {article.title}")
        print(f"  Category: {article.category}")
        print(f"  Tags: {', '.join(article.tags[:5])}")
        print(f"  Content length: {len(article.content)} characters")
        print(f"\n  Preview:\n  {article.content[:300]}...")
        return True
        
    except Exception as e:
        print(f"\n✗ Wiki compilation failed!")
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_llm_structured_extraction():
    """Test LLM's ability to extract structured information"""
    print("\n" + "=" * 80)
    print("Test 3: Structured Information Extraction")
    print("=" * 80)
    
    try:
        adapter = get_llm_adapter()
        
        prompt = """
        Extract the key information from this policy text and format as JSON:
        
        "Employees get 15 days vacation in first 2 years, 20 days after 2 years, 
        and 25 days after 5 years. Requests must be submitted 2 weeks in advance."
        
        Return only JSON with keys: title, categories, key_points
        """
        
        response = await adapter.ainvoke([HumanMessage(content=prompt)])
        
        print(f"✓ Structured extraction successful!")
        print(f"  Response: {response.content[:200]}...")
        return True
        
    except Exception as e:
        print(f"\n✗ Structured extraction failed!")
        print(f"  Error: {e}")
        return False


async def main():
    """Run all LLM tests"""
    print("\n🧪 LLM API Configuration Test Suite\n")
    print("Testing your configured LLM API settings...\n")
    
    results = []
    
    # Test 1: Basic connection
    result1 = await test_llm_basic_connection()
    results.append(("Basic Connection", result1))
    
    # Test 2: Wiki compilation
    result2 = await test_llm_wiki_compilation()
    results.append(("Wiki Compilation", result2))
    
    # Test 3: Structured extraction
    result3 = await test_llm_structured_extraction()
    results.append(("Structured Extraction", result3))
    
    # Summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<60} {status}")
    
    print("-" * 80)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your LLM API configuration is working correctly.")
        print("You can now use the LLM Wiki Compiler to process documents!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check:")
        print("  1. LLM_API_BASE_URL is correct")
        print("  2. LLM_API_KEY is valid")
        print("  3. Network connectivity to the API endpoint")
        print("  4. API service is running and accessible")
    
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
