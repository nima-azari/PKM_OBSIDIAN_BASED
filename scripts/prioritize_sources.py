#!/usr/bin/env python3
"""
Prioritize Discovered Sources

Ranks discovered sources by relevance to main research topics using OpenAI embeddings.
Outputs a sorted list with relevance scores.
"""

import sys
from pathlib import Path
from typing import List, Dict, Tuple
import re
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


def extract_main_topics(report_path: str) -> List[str]:
    """Extract main research topics from discovery report."""
    topics = []
    
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract topics from "Top Focus Areas" section
    focus_section = re.search(r'## Top Focus Areas\n\n(.+?)(?=\n##|\Z)', content, re.DOTALL)
    if focus_section:
        lines = focus_section.group(1).strip().split('\n')
        for line in lines:
            # Format: "  1. Data Portability"
            match = re.match(r'\s+\d+\.\s+(.+)', line)
            if match:
                topics.append(match.group(1).strip())
    
    # Also extract from queries as they represent research focus
    queries_section = re.search(r'## Recommended Search Queries\n\n(.+?)(?=\n##|\Z)', content, re.DOTALL)
    if queries_section:
        query_lines = queries_section.group(1).strip().split('\n')
        for line in query_lines:
            match = re.match(r'\s+\d+\.\s+(.+)', line)
            if match:
                query = match.group(1).strip()
                # Extract key concepts from query
                key_terms = extract_key_terms(query)
                topics.extend(key_terms)
    
    # Deduplicate while preserving order
    seen = set()
    unique_topics = []
    for topic in topics:
        if topic.lower() not in seen:
            seen.add(topic.lower())
            unique_topics.append(topic)
    
    return unique_topics[:10]  # Top 10 topics


def extract_key_terms(text: str) -> List[str]:
    """Extract key domain terms from text."""
    # Key terms that indicate research focus
    key_terms = []
    important_phrases = [
        'EU Data Act', 'data governance', 'vendor lock-in', 'data portability',
        'knowledge graph', 'semantic web', 'linked data', 'data interoperability',
        'cloud portability', 'data sovereignty', 'GDPR', 'data protection',
        'RDF', 'ontology', 'SPARQL', 'graph database'
    ]
    
    text_lower = text.lower()
    for phrase in important_phrases:
        if phrase.lower() in text_lower:
            key_terms.append(phrase)
    
    return key_terms


def parse_discovered_sources(urls_file: str) -> List[Dict[str, str]]:
    """Parse discovered URLs file and extract metadata."""
    sources = []
    
    with open(urls_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    current_query = None
    current_title = None
    current_source = None
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines and instructions
        if not line or line.startswith('#   '):
            continue
        
        # Query header
        if line.startswith('# Query:'):
            current_query = line.replace('# Query:', '').strip()
        
        # Source metadata
        elif line.startswith('# ['):
            # Format: # [OpenAlex] Title text
            match = re.match(r'# \[(.+?)\] (.+)', line)
            if match:
                current_source = match.group(1)
                current_title = match.group(2)
        
        # URL line
        elif line.startswith('http'):
            if current_title and current_query:
                sources.append({
                    'title': current_title,
                    'url': line,
                    'source': current_source or 'Unknown',
                    'query': current_query
                })
            current_title = None
            current_source = None
    
    return sources


def compute_relevance_scores(
    sources: List[Dict[str, str]], 
    topics: List[str],
    verbose: bool = True
) -> List[Dict[str, any]]:
    """Compute relevance scores for sources using OpenAI embeddings."""
    
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    if verbose:
        print(f"\n📊 Computing relevance scores for {len(sources)} sources...")
        print(f"   Research topics: {', '.join(topics[:5])}{'...' if len(topics) > 5 else ''}")
    
    # Create combined topic representation
    topic_text = ". ".join(topics)
    
    if verbose:
        print(f"\n🔄 Generating topic embedding...")
    
    # Get topic embedding
    topic_response = client.embeddings.create(
        model="text-embedding-3-small",
        input=topic_text
    )
    topic_embedding = topic_response.data[0].embedding
    
    if verbose:
        print(f"   ✓ Topic embedding generated")
        print(f"\n🔄 Computing source embeddings...")
    
    # Compute embeddings for all sources (batch)
    source_texts = [f"{s['title']}. {s['query']}" for s in sources]
    
    # Batch process embeddings (max 100 at a time)
    batch_size = 100
    all_embeddings = []
    
    for i in range(0, len(source_texts), batch_size):
        batch = source_texts[i:i + batch_size]
        batch_response = client.embeddings.create(
            model="text-embedding-3-small",
            input=batch
        )
        all_embeddings.extend([item.embedding for item in batch_response.data])
        
        if verbose:
            print(f"   ✓ Processed {min(i + batch_size, len(source_texts))}/{len(source_texts)} sources")
    
    # Compute cosine similarity scores
    import numpy as np
    
    topic_vec = np.array(topic_embedding)
    
    scored_sources = []
    for source, embedding in zip(sources, all_embeddings):
        source_vec = np.array(embedding)
        
        # Cosine similarity
        similarity = np.dot(topic_vec, source_vec) / (np.linalg.norm(topic_vec) * np.linalg.norm(source_vec))
        
        scored_sources.append({
            **source,
            'relevance_score': float(similarity)
        })
    
    # Sort by relevance score (descending)
    scored_sources.sort(key=lambda x: x['relevance_score'], reverse=True)
    
    if verbose:
        print(f"\n✅ Scoring complete!")
        print(f"   Score range: {scored_sources[-1]['relevance_score']:.3f} - {scored_sources[0]['relevance_score']:.3f}")
    
    return scored_sources


def save_prioritized_list(
    scored_sources: List[Dict[str, any]], 
    output_path: str,
    topics: List[str],
    verbose: bool = True
):
    """Save prioritized list to file."""
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    lines = []
    lines.append("# Prioritized Source URLs")
    lines.append(f"# Ranked by relevance to research topics")
    lines.append("#")
    lines.append(f"# Research Topics:")
    for i, topic in enumerate(topics, 1):
        lines.append(f"#   {i}. {topic}")
    lines.append("#")
    lines.append(f"# Total Sources: {len(scored_sources)}")
    lines.append(f"# Relevance Score Range: {scored_sources[-1]['relevance_score']:.3f} - {scored_sources[0]['relevance_score']:.3f}")
    lines.append("#")
    lines.append("# Format: [Score] [Source] Title")
    lines.append("#         URL")
    lines.append("#")
    lines.append("")
    
    # Add sources grouped by relevance tier
    high_threshold = 0.50
    medium_threshold = 0.40
    
    high_relevance = [s for s in scored_sources if s['relevance_score'] >= high_threshold]
    medium_relevance = [s for s in scored_sources if medium_threshold <= s['relevance_score'] < high_threshold]
    low_relevance = [s for s in scored_sources if s['relevance_score'] < medium_threshold]
    
    if high_relevance:
        lines.append("## HIGH RELEVANCE (Score ≥ 0.50)")
        lines.append(f"# {len(high_relevance)} sources")
        lines.append("")
        
        for i, source in enumerate(high_relevance, 1):
            lines.append(f"# [{source['relevance_score']:.3f}] [{source['source']}] {source['title']}")
            lines.append(source['url'])
            lines.append("")
    
    if medium_relevance:
        lines.append("## MEDIUM RELEVANCE (Score 0.40-0.49)")
        lines.append(f"# {len(medium_relevance)} sources")
        lines.append("")
        
        for source in medium_relevance:
            lines.append(f"# [{source['relevance_score']:.3f}] [{source['source']}] {source['title']}")
            lines.append(source['url'])
            lines.append("")
    
    if low_relevance:
        lines.append("## LOW RELEVANCE (Score < 0.40)")
        lines.append(f"# {len(low_relevance)} sources - Consider removing these")
        lines.append("")
        
        for source in low_relevance:
            lines.append(f"# [{source['relevance_score']:.3f}] [{source['source']}] {source['title']}")
            lines.append(source['url'])
            lines.append("")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    
    if verbose:
        print(f"\n✅ Prioritized list saved to: {output_path}")
        print(f"\n📊 Relevance Distribution:")
        print(f"   HIGH (≥0.50):    {len(high_relevance)} sources")
        print(f"   MEDIUM (0.40-0.49): {len(medium_relevance)} sources")
        print(f"   LOW (<0.40):     {len(low_relevance)} sources")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Prioritize discovered sources by relevance')
    parser.add_argument('--report', default='data/discovery_report.txt',
                        help='Path to discovery report (default: data/discovery_report.txt)')
    parser.add_argument('--urls', default='data/discovered_urls_expanded.txt',
                        help='Path to discovered URLs (default: data/discovered_urls_expanded.txt)')
    parser.add_argument('--output', default='data/discovered_urls_prioritized.txt',
                        help='Path to save prioritized URLs (default: data/discovered_urls_prioritized.txt)')
    parser.add_argument('--quiet', action='store_true',
                        help='Suppress verbose output')
    
    args = parser.parse_args()
    verbose = not args.quiet
    
    if verbose:
        print("="*60)
        print("SOURCE PRIORITIZATION")
        print("="*60)
    
    # Extract research topics
    if verbose:
        print(f"\n📖 Extracting research topics from: {args.report}")
    
    topics = extract_main_topics(args.report)
    
    if verbose:
        print(f"✓ Extracted {len(topics)} research topics:")
        for i, topic in enumerate(topics, 1):
            print(f"   {i}. {topic}")
    
    # Parse discovered sources
    if verbose:
        print(f"\n📄 Parsing discovered sources from: {args.urls}")
    
    sources = parse_discovered_sources(args.urls)
    
    if verbose:
        print(f"✓ Parsed {len(sources)} sources")
    
    # Compute relevance scores
    scored_sources = compute_relevance_scores(sources, topics, verbose=verbose)
    
    # Save prioritized list
    save_prioritized_list(scored_sources, args.output, topics, verbose=verbose)
    
    if verbose:
        print(f"\n{'='*60}")
        print("✅ Prioritization complete!")
        print(f"\nNext steps:")
        print(f"   1. Review: {args.output}")
        print(f"   2. Remove LOW relevance URLs (optional)")
        print(f"   3. Import: python import_urls.py {args.output}")
        print(f"{'='*60}")


if __name__ == '__main__':
    main()
