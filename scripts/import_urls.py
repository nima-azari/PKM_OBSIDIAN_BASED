#!/usr/bin/env python3
"""
URL Importer

Imports articles from a list of URLs, extracts content, and saves to data/sources/.
Supports batch processing with progress tracking and error handling.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import time
import re
import requests
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.web_discovery import WebDiscovery


class URLImporter:
    """Import articles from URL list."""
    
    def __init__(self, sources_dir: str = "data/sources", verbose: bool = True):
        self.sources_dir = Path(sources_dir)
        self.sources_dir.mkdir(parents=True, exist_ok=True)
        
        self.verbose = verbose
        self.web_discovery = WebDiscovery()
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
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
    
    def _extract_arxiv_id(self, url: str) -> Optional[str]:
        """Extract arXiv ID from URL."""
        match = re.search(r'arxiv\.org/abs/([\w\.]+)', url)
        return match.group(1) if match else None
    
    def _get_arxiv_metadata(self, arxiv_id: str) -> Optional[Dict[str, str]]:
        """Get metadata from arXiv API."""
        try:
            api_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
            response = self.session.get(api_url, timeout=10)
            response.raise_for_status()
            
            # Parse XML response
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            # Extract title and authors
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            entry = root.find('.//atom:entry', ns)
            
            if entry is not None:
                title = entry.find('atom:title', ns)
                authors = entry.findall('atom:author/atom:name', ns)
                
                return {
                    'title': title.text.strip().replace('\n', ' ') if title is not None else arxiv_id,
                    'authors': ', '.join([a.text for a in authors]) if authors else 'Unknown',
                    'pdf_url': f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                }
        except Exception as e:
            if self.verbose:
                print(f"  Warning: Could not fetch arXiv metadata: {e}")
        
        return None
    
    def _get_openalex_pdf(self, doi: str) -> Optional[Dict[str, str]]:
        """Get PDF URL and metadata from OpenAlex API for a DOI."""
        try:
            # OpenAlex API endpoint
            api_url = f"https://api.openalex.org/works/https://doi.org/{doi}"
            params = {'mailto': 'researcher@example.com'}  # Polite pool
            
            response = self.session.get(api_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Look for open access PDF
            if data.get('open_access', {}).get('is_oa'):
                pdf_url = data.get('open_access', {}).get('oa_url')
                
                if pdf_url:
                    return {
                        'title': data.get('title', doi),
                        'authors': ', '.join([a.get('author', {}).get('display_name', '') 
                                            for a in data.get('authorships', [])[:3]]),
                        'pdf_url': pdf_url
                    }
        except Exception as e:
            if self.verbose:
                print(f"  Info: OpenAlex lookup failed: {e}")
        
        return None
    
    def _download_pdf(self, url: str, output_path: Path) -> bool:
        """Download PDF from URL."""
        try:
            response = self.session.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Check if it's actually a PDF
            content_type = response.headers.get('Content-Type', '')
            if 'pdf' not in content_type.lower():
                if self.verbose:
                    print(f"  Warning: Content-Type is {content_type}, not PDF")
                return False
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
        except Exception as e:
            if self.verbose:
                print(f"  Error downloading PDF: {e}")
            return False
    
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
        Import single URL - tries PDF download for DOI/arXiv links first.
        
        Args:
            url_info: Dict with 'url', 'query', 'title'
            
        Returns:
            Result dict with 'success', 'filepath', 'error'
        """
        
        url = url_info['url']
        
        try:
            # Strategy 1: Try arXiv PDF download
            arxiv_id = self._extract_arxiv_id(url)
            if arxiv_id:
                metadata = self._get_arxiv_metadata(arxiv_id)
                if metadata:
                    # Generate filename from title
                    safe_title = self.sanitize_filename(metadata['title'])
                    filename = f"{safe_title}.pdf"
                    filepath = self.sources_dir / filename
                    
                    # Handle duplicate filenames
                    counter = 1
                    while filepath.exists():
                        filename = f"{safe_title}_{counter}.pdf"
                        filepath = self.sources_dir / filename
                        counter += 1
                    
                    # Download PDF
                    if self._download_pdf(metadata['pdf_url'], filepath):
                        return {
                            'success': True,
                            'url': url,
                            'filepath': str(filepath),
                            'title': metadata['title']
                        }
            
            # Strategy 2: Try OpenAlex for DOI links
            doi_match = re.search(r'doi\.org/(.+)$', url)
            if doi_match:
                doi = doi_match.group(1)
                metadata = self._get_openalex_pdf(doi)
                if metadata and metadata.get('pdf_url'):
                    # Generate filename from title
                    safe_title = self.sanitize_filename(metadata['title'])
                    filename = f"{safe_title}.pdf"
                    filepath = self.sources_dir / filename
                    
                    # Handle duplicate filenames
                    counter = 1
                    while filepath.exists():
                        filename = f"{safe_title}_{counter}.pdf"
                        filepath = self.sources_dir / filename
                        counter += 1
                    
                    # Download PDF
                    if self._download_pdf(metadata['pdf_url'], filepath):
                        return {
                            'success': True,
                            'url': url,
                            'filepath': str(filepath),
                            'title': metadata['title']
                        }
            
            # Strategy 3: Try direct PDF download if URL ends with .pdf
            if url.lower().endswith('.pdf'):
                # Extract filename from URL
                url_filename = url.split('/')[-1]
                safe_filename = self.sanitize_filename(url_filename)
                filepath = self.sources_dir / safe_filename
                
                # Handle duplicate filenames
                counter = 1
                base_name = filepath.stem
                while filepath.exists():
                    filepath = self.sources_dir / f"{base_name}_{counter}.pdf"
                    counter += 1
                
                # Download PDF
                if self._download_pdf(url, filepath):
                    return {
                        'success': True,
                        'url': url,
                        'filepath': str(filepath),
                        'title': filepath.stem
                    }
            
            # Strategy 4: Fall back to web extraction (for HTML pages)
            article = self.web_discovery.extract_article(url)
            
            if not article:
                return {
                    'success': False,
                    'url': url,
                    'error': 'Failed to extract content'
                }
            
            # Save article as markdown
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
