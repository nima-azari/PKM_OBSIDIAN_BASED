#!/usr/bin/env python3
"""
Auto-Download Papers from Prioritized List

Automatically extracts DOIs from prioritized source list and downloads
papers in batches, prioritizing HIGH relevance sources.
"""

import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from download_papers import DOIPaperDownloader


def parse_prioritized_list(file_path: str) -> Dict[str, List[Dict[str, str]]]:
    """
    Parse prioritized URLs file and extract DOIs by relevance tier.
    
    Returns:
        Dict with keys 'high', 'medium', 'low' containing source info
    """
    sources = {
        'high': [],
        'medium': [],
        'low': []
    }
    
    current_tier = None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line in lines:
        line = line.strip()
        
        # Detect tier section
        if line.startswith('## HIGH RELEVANCE'):
            current_tier = 'high'
            continue
        elif line.startswith('## MEDIUM RELEVANCE'):
            current_tier = 'medium'
            continue
        elif line.startswith('## LOW RELEVANCE'):
            current_tier = 'low'
            continue
        
        # Skip empty lines and pure comments
        if not line or (line.startswith('#') and not line.startswith('# [')):
            continue
        
        # Parse source metadata line
        # Format: # [Score] [Source] Title
        if line.startswith('# [') and current_tier:
            match = re.match(r'# \[([0-9.]+)\] \[(.+?)\] (.+)', line)
            if match:
                score = float(match.group(1))
                source_type = match.group(2)
                title = match.group(3)
                
                sources[current_tier].append({
                    'score': score,
                    'source': source_type,
                    'title': title,
                    'url': None  # Will be filled by next line
                })
        
        # Parse URL line
        elif line.startswith('http') and current_tier and sources[current_tier]:
            # Assign URL to last source
            if sources[current_tier][-1]['url'] is None:
                sources[current_tier][-1]['url'] = line
    
    return sources


def extract_downloadable_sources(sources: Dict[str, List[Dict[str, str]]]) -> List[Dict[str, str]]:
    """
    Filter sources that have DOIs or are from downloadable sources (arXiv, etc.).
    
    Returns:
        List of sources with DOI/downloadable URL
    """
    downloadable = []
    
    for tier in ['high', 'medium', 'low']:
        for source in sources[tier]:
            url = source.get('url', '')
            
            # Check if DOI-based (doi.org links)
            if 'doi.org' in url:
                downloadable.append(source)
            
            # Check if arXiv
            elif 'arxiv.org' in url:
                downloadable.append(source)
            
            # Check if URL contains DOI pattern
            elif re.search(r'10\.\d{4,}/[^\s]+', url):
                downloadable.append(source)
    
    return downloadable


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Auto-download papers from prioritized source list'
    )
    parser.add_argument('--input', default='data/discovered_urls_prioritized.txt',
                        help='Prioritized URLs file (default: data/discovered_urls_prioritized.txt)')
    parser.add_argument('--output', default='data/sources',
                        help='Output directory for PDFs (default: data/sources)')
    parser.add_argument('--tier', choices=['high', 'medium', 'low', 'all'],
                        default='high',
                        help='Which relevance tier to download (default: high)')
    parser.add_argument('--limit', type=int,
                        help='Maximum number of papers to download')
    parser.add_argument('--quiet', action='store_true',
                        help='Suppress verbose output')
    
    args = parser.parse_args()
    
    verbose = not args.quiet
    
    if verbose:
        print("="*60)
        print("AUTO-DOWNLOAD PAPERS FROM PRIORITIZED LIST")
        print("="*60)
    
    # Parse prioritized list
    if verbose:
        print(f"\n📄 Parsing prioritized list: {args.input}")
    
    sources = parse_prioritized_list(args.input)
    
    if verbose:
        print(f"✓ Found sources:")
        print(f"   HIGH relevance:   {len(sources['high'])} sources")
        print(f"   MEDIUM relevance: {len(sources['medium'])} sources")
        print(f"   LOW relevance:    {len(sources['low'])} sources")
    
    # Select sources based on tier
    if args.tier == 'all':
        selected_sources = sources['high'] + sources['medium'] + sources['low']
    else:
        selected_sources = sources[args.tier]
    
    if verbose:
        print(f"\n🎯 Target tier: {args.tier.upper()}")
        print(f"   Selected: {len(selected_sources)} sources")
    
    # Filter downloadable sources
    downloadable = []
    for source in selected_sources:
        url = source.get('url', '')
        if 'doi.org' in url or 'arxiv.org' in url or re.search(r'10\.\d{4,}/[^\s]+', url):
            downloadable.append(source)
    
    if verbose:
        print(f"\n🔍 Downloadable sources: {len(downloadable)}/{len(selected_sources)}")
        if len(downloadable) < len(selected_sources):
            non_downloadable = len(selected_sources) - len(downloadable)
            print(f"   ⚠️  {non_downloadable} sources don't have DOI/arXiv links")
    
    # Apply limit
    if args.limit:
        downloadable = downloadable[:args.limit]
        if verbose:
            print(f"   📊 Limited to: {len(downloadable)} sources")
    
    if not downloadable:
        print("\n❌ No downloadable sources found")
        return
    
    # Initialize downloader
    downloader = DOIPaperDownloader(
        output_dir=args.output,
        verbose=verbose
    )
    
    # Download papers
    if verbose:
        print(f"\n{'='*60}")
        print(f"STARTING DOWNLOADS")
        print(f"{'='*60}")
    
    results = []
    
    for i, source in enumerate(downloadable, 1):
        if verbose:
            print(f"\n[{i}/{len(downloadable)}] {source['title'][:60]}...")
            print(f"   Score: {source['score']:.3f} | Source: {source['source']}")
        
        success, message = downloader.download_from_url(source['url'])
        
        results.append({
            'source': source,
            'success': success,
            'message': message
        })
        
        # Rate limiting
        import time
        time.sleep(1)
    
    # Summary
    if verbose:
        print(f"\n{'='*60}")
        print("DOWNLOAD SUMMARY")
        print(f"{'='*60}")
        
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        print(f"\n✅ Successfully downloaded: {successful}/{len(results)}")
        if failed > 0:
            print(f"❌ Failed: {failed}")
        
        print(f"\n📊 Results by status:")
        for result in results:
            status = "✅" if result['success'] else "❌"
            title = result['source']['title'][:50]
            message = result['message'][:40]
            print(f"   {status} {title}... - {message}...")
        
        print(f"\n{'='*60}")
        print("✅ Download process complete!")
        print(f"\nNext steps:")
        print(f"   1. Check downloaded PDFs in: {args.output}")
        print(f"   2. Convert PDFs to markdown: python process_pdfs.py")
        print(f"   3. Rebuild knowledge graph: python build_graph.py")
        print(f"{'='*60}")


if __name__ == '__main__':
    main()
