#!/usr/bin/env python3
"""
Test Expanded API Coverage

Tests all new API search methods individually to verify functionality.
Tests include: EUR-Lex, DOAJ, HAL, Zenodo, OpenAlex, CORE.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.web_discovery import WebDiscovery
from auto_discover_sources import AutoSourceDiscovery


def test_api_individually(api_name: str, search_func, query: str, max_results: int = 5):
    """Test a single API search function."""
    print(f"\n{'='*60}")
    print(f"Testing {api_name}")
    print(f"{'='*60}")
    print(f"Query: {query}")
    print(f"Max results: {max_results}")
    print()
    
    try:
        results = search_func(query, max_results)
        
        if results:
            print(f"✅ SUCCESS: Found {len(results)} results\n")
            
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['title'][:80]}...")
                print(f"   URL: {result['url'][:100]}")
                print(f"   Snippet: {result['snippet'][:150]}...")
                print(f"   Source: {result['source']}")
                print()
            
            return True, len(results)
        else:
            print(f"⚠️  WARNING: No results found (API may be working but no matches)")
            return True, 0
    
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, 0


def main():
    print("="*60)
    print("EXPANDED API COVERAGE TEST SUITE")
    print("="*60)
    print()
    print("This script tests each new API individually to verify:")
    print("  1. API endpoint connectivity")
    print("  2. Response parsing")
    print("  3. Result format consistency")
    print()
    
    # Initialize discovery components
    web_discovery = WebDiscovery()
    auto_discovery = AutoSourceDiscovery(verbose=False)
    
    # Test queries optimized for each API
    test_cases = [
        {
            'api_name': 'EUR-Lex',
            'search_func': web_discovery._search_eurlex,
            'query': 'Data Act',
            'max_results': 5
        },
        {
            'api_name': 'OpenAlex',
            'search_func': auto_discovery._search_openalex,
            'query': 'linked data semantic web',
            'max_results': 5
        },
        {
            'api_name': 'CORE',
            'search_func': auto_discovery._search_core,
            'query': 'knowledge graphs data governance',
            'max_results': 5
        },
        {
            'api_name': 'DOAJ',
            'search_func': web_discovery._search_doaj,
            'query': 'data portability',
            'max_results': 5
        },
        {
            'api_name': 'HAL',
            'search_func': web_discovery._search_hal,
            'query': 'semantic web technologies',
            'max_results': 5
        },
        {
            'api_name': 'Zenodo',
            'search_func': web_discovery._search_zenodo,
            'query': 'EU data governance',
            'max_results': 5
        }
    ]
    
    # Run tests
    results_summary = []
    
    for test_case in test_cases:
        success, count = test_api_individually(
            test_case['api_name'],
            test_case['search_func'],
            test_case['query'],
            test_case['max_results']
        )
        
        results_summary.append({
            'api': test_case['api_name'],
            'success': success,
            'count': count
        })
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print()
    
    successful_apis = sum(1 for r in results_summary if r['success'])
    total_apis = len(results_summary)
    total_results = sum(r['count'] for r in results_summary)
    
    print(f"APIs Tested: {total_apis}")
    print(f"APIs Working: {successful_apis}")
    print(f"Total Results Found: {total_results}")
    print()
    
    for result in results_summary:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"  {status} - {result['api']}: {result['count']} results")
    
    print()
    
    if successful_apis == total_apis:
        print("🎉 ALL APIS WORKING!")
        print()
        print("Next steps:")
        print("  1. Run full discovery: python auto_discover_sources.py --report data/discovery_report.txt --semantic-filter")
        print("  2. Review results in: data/discovered_urls_semantic.txt")
        print("  3. Import sources: python import_urls.py data/discovered_urls_semantic.txt")
    else:
        print(f"⚠️  {total_apis - successful_apis} API(s) failed. Check error messages above.")
        print()
        print("Troubleshooting:")
        print("  - Check internet connectivity")
        print("  - Verify API endpoints are accessible")
        print("  - Some APIs may have temporary rate limits")
        print("  - EUR-Lex SPARQL queries may need adjustment")
    
    print("="*60)
    
    return successful_apis == total_apis


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
