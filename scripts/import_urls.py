#!/usr/bin/env python3
"""
URL Importer

Imports articles from a list of URLs, extracts content, and saves to data/sources/.
Supports batch processing with progress tracking and error handling.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import time
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.web_discovery import WebDiscovery


class URLImporter:
    """Import articles from URL list."""
    
    def __init__(self, sources_dir: str = "data/sources", verbose: bool = True):
        self.sources_dir = Path(sources_dir)
        self.sources_dir.mkdir(parents=True, exist_ok=True)
        
        self.verbose = verbose
        self.web_discovery = WebDiscovery()
        
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0
        }
    
    def load_urls_from_file(self, filepath: str) -> List[Dict[str, str]]:
        """
        Load URLs from file, supporting comments and metadata.
        
        Format:
            # Comment or query context
            # [Source] Title
            https://example.com/article
            
        Returns:
            List of dicts with 'url', 'context' (query), 'title' (if available)
        """
        
        if self.verbose:
            print(f"\n📄 Loading URLs from: {filepath}")
        
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"URL file not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        urls = []
        current_query = None
        current_title = None
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                current_title = None
                continue
            
            # Comments/metadata
            if line.startswith('#'):
                # Extract query context
                if 'Query:' in line:
                    current_query = line.split('Query:', 1)[1].strip()
                # Extract title
                elif '[' in line and ']' in line:
                    current_title = line
                continue
            
            # URL line
            if line.startswith('http://') or line.startswith('https://'):
                url_info = {
                    'url': line,
                    'query': current_query,
                    'title': current_title
                }
                urls.append(url_info)
                current_title = None  # Reset after use
        
        if self.verbose:
            print(f"✓ Loaded {len(urls)} URLs")
        
        return urls
    
    def sanitize_filename(self, title: str) -> str:
        """Convert title to safe filename."""
        # Remove/replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '', title)
        # Replace spaces and special chars with underscores
        filename = re.sub(r'[\s\-]+', '_', filename)
        # Remove multiple underscores
        filename = re.sub(r'_+', '_', filename)
        # Limit length
        filename = filename[:100]
        # Remove trailing underscore
        filename = filename.strip('_')
        
        return filename
    
    def save_article(self, article: Dict[str, Any], query_context: str = None) -> str:
        """
        Save article to data/sources/ with frontmatter.
        
        Args:
            article: Article dict from web_discovery
            query_context: Optional query that led to this article
            
        Returns:
            Path to saved file
        """
        
        # Generate filename
        safe_title = self.sanitize_filename(article['title'])
        filename = f"{safe_title}.md"
        filepath = self.sources_dir / filename
        
        # Handle duplicate filenames
        counter = 1
        while filepath.exists():
            filename = f"{safe_title}_{counter}.md"
            filepath = self.sources_dir / filename
            counter += 1
        
        # Build content with frontmatter
        content_parts = []
        
        # YAML frontmatter
        content_parts.append("---")
        content_parts.append(f"title: {article['title']}")
        content_parts.append(f"author: {article.get('author', 'Unknown')}")
        content_parts.append(f"url: {article['url']}")
        content_parts.append(f"date_extracted: {datetime.now().strftime('%Y-%m-%d')}")
        content_parts.append(f"source_type: web-article")
        
        if query_context:
            content_parts.append(f"discovery_query: {query_context}")
        
        if article.get('date'):
            content_parts.append(f"published: {article['date']}")
        
        if article.get('hostname'):
            content_parts.append(f"hostname: {article['hostname']}")
        
        content_parts.append("tags: [web-article, imported, research]")
        content_parts.append("---")
        content_parts.append("")
        
        # Title
        content_parts.append(f"# {article['title']}")
        content_parts.append("")
        
        # Metadata section
        content_parts.append("## Source Information")
        content_parts.append("")
        content_parts.append(f"- **URL:** {article['url']}")
        content_parts.append(f"- **Author:** {article.get('author', 'Unknown')}")
        
        if article.get('date'):
            content_parts.append(f"- **Published:** {article['date']}")
        
        if article.get('description'):
            content_parts.append(f"- **Description:** {article['description']}")
        
        if query_context:
            content_parts.append(f"- **Discovery Query:** {query_context}")
        
        content_parts.append("")
        content_parts.append("---")
        content_parts.append("")
        
        # Main content
        content_parts.append("## Content")
        content_parts.append("")
        content_parts.append(article['content'])
        
        # Save file
        full_content = "\n".join(content_parts)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        return str(filepath)
    
    def import_url(self, url_info: Dict[str, str]) -> Dict[str, Any]:
        """
        Import single URL.
        
        Args:
            url_info: Dict with 'url', 'query', 'title'
            
        Returns:
            Result dict with 'success', 'filepath', 'error'
        """
        
        url = url_info['url']
        
        try:
            # Extract article
            article = self.web_discovery.extract_article(url)
            
            if not article:
                return {
                    'success': False,
                    'url': url,
                    'error': 'Failed to extract content'
                }
            
            # Save article
            filepath = self.save_article(article, query_context=url_info.get('query'))
            
            return {
                'success': True,
                'url': url,
                'filepath': filepath,
                'title': article['title']
            }
        
        except Exception as e:
            return {
                'success': False,
                'url': url,
                'error': str(e)
            }
    
    def import_batch(
        self, 
        url_infos: List[Dict[str, str]], 
        delay: float = 1.0,
        skip_existing: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Import batch of URLs with progress tracking.
        
        Args:
            url_infos: List of URL info dicts
            delay: Delay between requests (seconds)
            skip_existing: Skip if similar file exists
            
        Returns:
            List of result dicts
        """
        
        if self.verbose:
            print("\n" + "="*60)
            print("BATCH URL IMPORT")
            print("="*60)
            print(f"\nImporting {len(url_infos)} URLs...")
        
        results = []
        
        for i, url_info in enumerate(url_infos, 1):
            url = url_info['url']
            
            if self.verbose:
                print(f"\n[{i}/{len(url_infos)}] {url}")
            
            # Import URL
            result = self.import_url(url_info)
            results.append(result)
            
            # Update stats
            self.stats['total'] += 1
            if result['success']:
                self.stats['success'] += 1
                if self.verbose:
                    print(f"   ✓ Saved: {result['filepath']}")
            else:
                self.stats['failed'] += 1
                if self.verbose:
                    print(f"   ✗ Failed: {result['error']}")
            
            # Delay between requests
            if i < len(url_infos):
                time.sleep(delay)
        
        return results
    
    def generate_import_report(self, results: List[Dict[str, Any]], output_path: str = None):
        """Generate import report with statistics."""
        
        if output_path:
            output_path = Path(output_path)
        else:
            output_path = self.sources_dir.parent / "import_report.txt"
        
        lines = []
        lines.append("="*60)
        lines.append("URL IMPORT REPORT")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("="*60)
        lines.append("")
        
        lines.append("## Statistics")
        lines.append("")
        lines.append(f"  Total URLs: {self.stats['total']}")
        lines.append(f"  Successful: {self.stats['success']} ({self.stats['success']*100//self.stats['total'] if self.stats['total'] > 0 else 0}%)")
        lines.append(f"  Failed: {self.stats['failed']}")
        lines.append("")
        
        lines.append("## Successful Imports")
        lines.append("")
        for result in results:
            if result['success']:
                lines.append(f"  ✓ {result['title']}")
                lines.append(f"    URL: {result['url']}")
                lines.append(f"    Saved: {result['filepath']}")
                lines.append("")
        
        if any(not r['success'] for r in results):
            lines.append("## Failed Imports")
            lines.append("")
            for result in results:
                if not result['success']:
                    lines.append(f"  ✗ {result['url']}")
                    lines.append(f"    Error: {result['error']}")
                    lines.append("")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        
        if self.verbose:
            print(f"\n✅ Import report saved: {output_path}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Import articles from URL list')
    parser.add_argument('url_file', help='Path to file with URLs')
    parser.add_argument('--output-dir', default='data/sources',
                        help='Output directory for articles (default: data/sources)')
    parser.add_argument('--delay', type=float, default=1.0,
                        help='Delay between requests in seconds (default: 1.0)')
    parser.add_argument('--report', default='data/import_report.txt',
                        help='Path to save import report (default: data/import_report.txt)')
    
    args = parser.parse_args()
    
    # Create importer
    importer = URLImporter(sources_dir=args.output_dir, verbose=True)
    
    # Load URLs
    url_infos = importer.load_urls_from_file(args.url_file)
    
    if not url_infos:
        print("❌ No URLs found in file")
        return
    
    # Import batch
    results = importer.import_batch(url_infos, delay=args.delay)
    
    # Generate report
    importer.generate_import_report(results, output_path=args.report)
    
    # Summary
    print(f"\n{'='*60}")
    print("✅ Import complete!")
    print(f"\nStatistics:")
    print(f"   Total: {importer.stats['total']}")
    print(f"   Success: {importer.stats['success']}")
    print(f"   Failed: {importer.stats['failed']}")
    print(f"\nNext steps:")
    print(f"   1. Review imported files in {args.output_dir}")
    print(f"   2. Rebuild knowledge graph: python build_graph.py --meta-ontology data/graphs/meta_ontology.ttl")
    print(f"   3. Re-run discovery to assess improvement: python discover_sources.py")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
