"""
Prioritize discovered URLs based on gap coverage scores from discovery report.

Usage:
    python scripts/prioritize_discovered_urls.py
    python scripts/prioritize_discovered_urls.py data/discovered_urls.txt data/discovery_report.txt
"""

import sys
from pathlib import Path
import re
from typing import Dict, List, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def parse_discovery_report(report_path: str) -> Dict[str, int]:
    """
    Extract coverage scores from discovery report.
    
    Returns:
        Dict mapping topic to coverage score (0-100)
    """
    coverage_scores = {}
    
    with open(report_path, 'r', encoding='utf-8') as f:
        for line in f:
            # Match lines like: "  Vendor Lock-in: LOW (14/100)"
            match = re.match(r'\s+(.+?):\s+\w+\s+\((\d+)/100\)', line)
            if match:
                topic = match.group(1).strip()
                score = int(match.group(2))
                coverage_scores[topic] = score
    
    return coverage_scores


def extract_urls_with_metadata(urls_path: str) -> List[Dict]:
    """
    Extract URLs with associated query metadata.
    
    Returns:
        List of dicts with: url, title, source, query
    """
    urls = []
    current_query = "Unknown"
    current_title = ""
    current_source = ""
    
    with open(urls_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines and instructions
            if not line or line.startswith("# Instructions") or line.startswith("# Generated"):
                continue
            
            # Extract query
            if line.startswith("# Query:"):
                current_query = line.replace("# Query:", "").strip()
            
            # Extract title and source
            elif line.startswith("# ["):
                match = re.match(r'#\s+\[([^\]]+)\]\s+(.+)', line)
                if match:
                    current_source = match.group(1)
                    current_title = match.group(2)
            
            # Extract URL
            elif line.startswith("http"):
                urls.append({
                    'url': line,
                    'title': current_title,
                    'source': current_source,
                    'query': current_query
                })
    
    return urls


def match_query_to_topic(query: str, coverage_scores: Dict[str, int]) -> Tuple[str, int]:
    """
    Match a query to the most relevant topic based on keywords.
    
    Returns:
        (topic_name, coverage_score)
    """
    query_lower = query.lower()
    
    # Try exact keyword matching
    for topic, score in coverage_scores.items():
        topic_lower = topic.lower()
        if topic_lower in query_lower:
            return (topic, score)
    
    # Fallback: return median score
    scores = list(coverage_scores.values())
    median_score = sorted(scores)[len(scores) // 2] if scores else 50
    return ("General", median_score)


def prioritize_urls(urls: List[Dict], coverage_scores: Dict[str, int]) -> List[Dict]:
    """
    Assign priority to each URL based on coverage gap.
    
    Returns:
        URLs sorted by priority (highest priority first)
    """
    for url_data in urls:
        topic, score = match_query_to_topic(url_data['query'], coverage_scores)
        url_data['topic'] = topic
        url_data['coverage_score'] = score
        url_data['priority'] = "HIGH" if score < 30 else "MEDIUM" if score < 50 else "LOW"
    
    # Sort by coverage score (lower = higher priority)
    urls.sort(key=lambda x: x['coverage_score'])
    
    return urls


def save_prioritized_urls(urls: List[Dict], output_path: str):
    """Save URLs with priority annotations."""
    
    lines = []
    lines.append("# Prioritized Source URLs")
    lines.append("# Sorted by gap coverage (HIGH priority = biggest gaps)")
    lines.append("#")
    lines.append("# Priority: HIGH (<30), MEDIUM (30-50), LOW (>50)")
    lines.append("#")
    lines.append("# Instructions:")
    lines.append("#   1. Review URLs below (start with HIGH priority)")
    lines.append("#   2. Remove unwanted URLs (delete lines)")
    lines.append("#   3. Run: python import_urls.py data/discovered_urls_prioritized.txt")
    lines.append("#")
    lines.append("")
    
    current_priority = None
    for url_data in urls:
        # Add section header when priority changes
        if url_data['priority'] != current_priority:
            if current_priority is not None:
                lines.append("")
            lines.append(f"# ===== PRIORITY: {url_data['priority']} =====")
            lines.append(f"# Topic: {url_data['topic']} (Coverage: {url_data['coverage_score']}/100)")
            lines.append("")
            current_priority = url_data['priority']
        
        lines.append(f"# Query: {url_data['query']}")
        lines.append(f"# [{url_data['source']}] {url_data['title']}")
        lines.append(url_data['url'])
        lines.append("")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Prioritize discovered URLs by gap coverage')
    parser.add_argument('urls', nargs='?', default='data/discovered_urls.txt',
                        help='Input URLs file (default: data/discovered_urls.txt)')
    parser.add_argument('report', nargs='?', default='data/discovery_report.txt',
                        help='Discovery report file (default: data/discovery_report.txt)')
    parser.add_argument('--output', default='data/discovered_urls_prioritized.txt',
                        help='Output file (default: data/discovered_urls_prioritized.txt)')
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("URL PRIORITIZATION BY GAP COVERAGE")
    print("="*60)
    
    # Parse discovery report
    print(f"\n📊 Loading gap analysis from: {args.report}")
    coverage_scores = parse_discovery_report(args.report)
    print(f"   ✓ Loaded {len(coverage_scores)} coverage scores")
    
    # Show coverage summary
    sorted_topics = sorted(coverage_scores.items(), key=lambda x: x[1])
    print("\n   Top gaps (lowest coverage):")
    for topic, score in sorted_topics[:5]:
        priority = "HIGH" if score < 30 else "MEDIUM" if score < 50 else "LOW"
        print(f"     [{priority}] {topic}: {score}/100")
    
    # Load URLs
    print(f"\n📄 Loading URLs from: {args.urls}")
    urls = extract_urls_with_metadata(args.urls)
    print(f"   ✓ Loaded {len(urls)} URLs")
    
    # Prioritize
    print("\n🎯 Assigning priorities based on gap coverage...")
    prioritized_urls = prioritize_urls(urls, coverage_scores)
    
    # Show priority distribution
    priority_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
    for url in prioritized_urls:
        priority_counts[url['priority']] += 1
    
    print(f"   Priority distribution:")
    print(f"     HIGH:   {priority_counts['HIGH']} URLs (biggest gaps)")
    print(f"     MEDIUM: {priority_counts['MEDIUM']} URLs")
    print(f"     LOW:    {priority_counts['LOW']} URLs (already covered)")
    
    # Save
    print(f"\n💾 Saving prioritized URLs to: {args.output}")
    save_prioritized_urls(prioritized_urls, args.output)
    
    print("\n" + "="*60)
    print("✅ Prioritization complete!")
    print("="*60)
    print(f"\n📁 OUTPUT: {args.output}")
    print("\nNext steps:")
    print(f"   1. Review: {args.output} (start with HIGH priority)")
    print(f"   2. Remove unwanted URLs")
    print(f"   3. Import: python import_urls.py {args.output}")
    print()


if __name__ == "__main__":
    main()
