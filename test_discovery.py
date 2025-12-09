"""
Test Web Discovery Search Functions

Tests arXiv, Semantic Scholar, and Google (if API key available) search.
"""

from core.web_discovery import WebDiscovery
import os
from dotenv import load_dotenv

load_dotenv()

def test_arxiv():
    """Test arXiv search"""
    print("\n" + "="*80)
    print("TEST 1: arXiv Search")
    print("="*80)
    
    discovery = WebDiscovery()
    query = "knowledge graphs semantic web"
    
    print(f"\nSearching arXiv for: '{query}'")
    results = discovery._search_arxiv(query, max_results=5)
    
    print(f"\n✓ Found {len(results)} results from arXiv:\n")
    for i, result in enumerate(results, 1):
        print(f"[{i}] {result['title']}")
        print(f"    URL: {result['url']}")
        print(f"    Snippet: {result['snippet'][:150]}...")
        print()
    
    return len(results) > 0

def test_semantic_scholar():
    """Test Semantic Scholar search"""
    print("\n" + "="*80)
    print("TEST 2: Semantic Scholar Search")
    print("="*80)
    
    discovery = WebDiscovery()
    query = "EU Data Act governance"
    
    print(f"\nSearching Semantic Scholar for: '{query}'")
    results = discovery._search_semantic_scholar(query, max_results=5)
    
    print(f"\n✓ Found {len(results)} results from Semantic Scholar:\n")
    for i, result in enumerate(results, 1):
        print(f"[{i}] {result['title']}")
        print(f"    URL: {result['url']}")
        print(f"    Snippet: {result['snippet'][:150]}...")
        print()
    
    return len(results) > 0

def test_google():
    """Test Google search (requires SERPAPI_KEY)"""
    print("\n" + "="*80)
    print("TEST 3: Google Search (via SerpAPI)")
    print("="*80)
    
    api_key = os.getenv('SERPAPI_KEY')
    
    if not api_key:
        print("\n⚠️  SERPAPI_KEY not found in environment variables")
        print("\nTo enable Google search:")
        print("1. Sign up at https://serpapi.com (100 free searches/month)")
        print("2. Get your API key")
        print("3. Add to .env file: SERPAPI_KEY=your_key_here")
        print("\n❌ Skipping Google search test")
        return False
    
    print(f"\n✓ SERPAPI_KEY found: {api_key[:10]}...{api_key[-4:]}")
    
    discovery = WebDiscovery()
    query = "linked data best practices"
    
    print(f"\nSearching Google for: '{query}'")
    results = discovery._search_google(query, max_results=5)
    
    print(f"\n✓ Found {len(results)} results from Google:\n")
    for i, result in enumerate(results, 1):
        print(f"[{i}] {result['title']}")
        print(f"    URL: {result['url']}")
        print(f"    Snippet: {result['snippet'][:150]}...")
        print()
    
    return len(results) > 0

def test_combined_search():
    """Test combined search (all sources)"""
    print("\n" + "="*80)
    print("TEST 4: Combined Search (All Sources)")
    print("="*80)
    
    discovery = WebDiscovery()
    query = "RDF knowledge graph"
    
    print(f"\nSearching all sources for: '{query}'")
    results = discovery.search_web(query, max_results=10, source='all')
    
    print(f"\n✓ Found {len(results)} total results:\n")
    
    # Group by source
    by_source = {}
    for result in results:
        source = result['source']
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(result)
    
    for source, source_results in by_source.items():
        print(f"\n{source}: {len(source_results)} results")
        for i, result in enumerate(source_results[:3], 1):  # Show first 3 from each
            print(f"  [{i}] {result['title'][:80]}...")
    
    print(f"\n✓ Combined search returned results from {len(by_source)} source(s)")
    
    return len(results) > 0

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("WEB DISCOVERY SEARCH TESTS")
    print("="*80)
    
    results = {
        'arXiv': False,
        'Semantic Scholar': False,
        'Google': False,
        'Combined': False
    }
    
    try:
        results['arXiv'] = test_arxiv()
    except Exception as e:
        print(f"\n❌ arXiv test failed: {e}")
    
    try:
        results['Semantic Scholar'] = test_semantic_scholar()
    except Exception as e:
        print(f"\n❌ Semantic Scholar test failed: {e}")
    
    try:
        results['Google'] = test_google()
    except Exception as e:
        print(f"\n❌ Google test failed: {e}")
    
    try:
        results['Combined'] = test_combined_search()
    except Exception as e:
        print(f"\n❌ Combined search test failed: {e}")
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80 + "\n")
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:20s} {status}")
    
    passed_count = sum(results.values())
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if not results['Google']:
        print("\n💡 TIP: To enable Google search, add SERPAPI_KEY to your .env file")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()
