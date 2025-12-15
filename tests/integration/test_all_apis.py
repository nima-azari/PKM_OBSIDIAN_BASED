#!/usr/bin/env python3
"""
Test Expanded API Integration (24+ APIs)

Tests all 8 categories of research source APIs:
1. Scientific / Academic (Crossref, OpenAlex, Semantic Scholar)
2. Scholarly Reports (CORE, Zenodo, Figshare, arXiv, EUR-Lex, DOAJ, HAL)
3. News (Guardian, NYTimes, GDELT)
4. Educational (Wikipedia, Wikidata, Open Library)
5. Technical (arXiv, Dev.to)
6. Opinion (Guardian, NYTimes, Wikinews)
7. Community (Stack Exchange, Hacker News)
8. Documentation (Read the Docs, W3C)
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.web_discovery import WebDiscovery


def test_api_category(category_name: str, sources: list, query: str):
    """Test a category of APIs"""
    print(f"\n{'='*80}")
    print(f"Category: {category_name}")
    print(f"{'='*80}\n")
    
    discovery = WebDiscovery()
    total_results = 0
    successful_apis = 0
    failed_apis = []
    
    for source in sources:
        print(f"\n[{source.upper()}]")
        try:
            results = discovery.search_web(query, max_results=3, source=source)
            
            if results:
                successful_apis += 1
                print(f"  ✓ Found {len(results)} results")
                for i, result in enumerate(results[:2], 1):
                    print(f"    {i}. {result['title'][:60]}...")
                    print(f"       URL: {result['url'][:70]}...")
                total_results += len(results)
            else:
                print(f"  ⚠ No results (API may require key or query needs adjustment)")
                failed_apis.append(f"{source} (no results)")
        except Exception as e:
            print(f"  ✗ Error: {str(e)[:100]}")
            failed_apis.append(f"{source} (error)")
    
    print(f"\n{'-'*80}")
    print(f"Category Summary:")
    print(f"  APIs tested: {len(sources)}")
    print(f"  Successful: {successful_apis}")
    print(f"  Total results: {total_results}")
    if failed_apis:
        print(f"  Failed/Empty: {', '.join(failed_apis)}")
    print(f"{'-'*80}")
    
    return successful_apis, len(sources), total_results


def main():
    """Run comprehensive API tests"""
    
    print("\n" + "="*80)
    print("  Source Discovery API Expansion Test Suite")
    print("  24+ APIs across 8 Categories")
    print("="*80)
    
    # Test query
    test_query = "knowledge graphs semantic web"
    print(f"\nTest Query: '{test_query}'")
    
    all_stats = []
    
    # Category 1: Scientific / Academic
    stats = test_api_category(
        "1. Scientific / Academic (Peer-Reviewed)",
        ['crossref', 'openalex', 'semantic_scholar'],
        test_query
    )
    all_stats.append(("Scientific", *stats))
    
    # Category 2: Scholarly Reports/Preprints
    stats = test_api_category(
        "2. Scholarly (Reports, Preprints, White Papers)",
        ['core', 'zenodo', 'figshare', 'arxiv', 'eurlex', 'doaj', 'hal'],
        test_query
    )
    all_stats.append(("Scholarly", *stats))
    
    # Category 3: News
    stats = test_api_category(
        "3. News (Reputable Journalism)",
        ['guardian', 'nytimes', 'gdelt'],
        test_query
    )
    all_stats.append(("News", *stats))
    
    # Category 4: Educational / Reference
    stats = test_api_category(
        "4. Educational / Reference Knowledge",
        ['wikipedia', 'wikidata', 'openlibrary'],
        test_query
    )
    all_stats.append(("Educational", *stats))
    
    # Category 5: Expert / Technical
    stats = test_api_category(
        "5. Expert / Technical Articles",
        ['arxiv', 'devto'],
        test_query
    )
    all_stats.append(("Technical", *stats))
    
    # Category 6: Opinion / Editorial
    stats = test_api_category(
        "6. Opinion / Editorial (Credible Publishers)",
        ['guardian', 'nytimes', 'wikinews'],
        test_query
    )
    all_stats.append(("Opinion", *stats))
    
    # Category 7: Community Knowledge
    stats = test_api_category(
        "7. Community Knowledge (Moderated)",
        ['stackexchange', 'hackernews'],
        test_query
    )
    all_stats.append(("Community", *stats))
    
    # Category 8: Documentation / Standards
    stats = test_api_category(
        "8. Documentation / Standards",
        ['readthedocs', 'w3c'],
        test_query
    )
    all_stats.append(("Documentation", *stats))
    
    # Final summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    
    total_apis_tested = sum(stat[2] for stat in all_stats)
    total_successful = sum(stat[1] for stat in all_stats)
    total_results = sum(stat[3] for stat in all_stats)
    
    print(f"\nTotal APIs tested: {total_apis_tested}")
    print(f"Successful APIs: {total_successful}")
    print(f"Success rate: {(total_successful/total_apis_tested*100):.1f}%")
    print(f"Total results retrieved: {total_results}")
    
    print("\n\nCategory Breakdown:")
    for category, successful, tested, results in all_stats:
        success_rate = (successful/tested*100) if tested > 0 else 0
        print(f"  {category:20s}: {successful}/{tested} APIs ({success_rate:.0f}%) - {results} results")
    
    print("\n" + "="*80)
    print("API Expansion Complete!")
    print("="*80)
    
    # API key reminder
    print("\n📝 Note: Some APIs require keys (set in .env):")
    print("  - GUARDIAN_API_KEY (The Guardian)")
    print("  - NYTIMES_API_KEY (New York Times)")
    print("  - CORE_API_KEY (CORE - optional, works without)")
    print("  - SERPAPI_KEY (Google - optional)")
    print("\nAPIs work without keys will use free tier or public access.\n")


if __name__ == "__main__":
    main()
