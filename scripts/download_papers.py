#!/usr/bin/env python3
"""
DOI-based Paper Downloader

Downloads academic papers using DOI identifiers via open-access sources:
- Unpaywall API (primary source)
- Crossref API (metadata)
- Direct arXiv/bioRxiv links
- Publisher open-access repositories

Automatically extracts DOIs from URLs and downloads PDFs with proper metadata.
"""

import os
import sys
import re
import time
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import requests
from urllib.parse import urlparse, unquote

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


class DOIPaperDownloader:
    """Download academic papers using DOI identifiers."""
    
    def __init__(self, output_dir: str = "data/sources", verbose: bool = True):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose
        
        # API endpoints
        self.unpaywall_api = "https://api.unpaywall.org/v2/{doi}"
        self.crossref_api = "https://api.crossref.org/works/{doi}"
        self.unpaywall_email = "research@pkm.local"  # Required for Unpaywall
        
        # Session for requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Academic-Research-Tool/1.0 (mailto:research@pkm.local)'
        })
    
    def normalize_doi(self, doi: str) -> Optional[str]:
        """
        Normalize DOI to standard format.
        
        Args:
            doi: DOI string or URL containing DOI
            
        Returns:
            Normalized DOI (e.g., "10.1234/abcd") or None
        """
        # Remove common prefixes
        doi = doi.strip()
        doi = re.sub(r'^(https?://)?(dx\.)?doi\.org/', '', doi)
        doi = re.sub(r'^doi:', '', doi, flags=re.IGNORECASE)
        
        # Extract DOI pattern (10.xxxx/...)
        match = re.search(r'10\.\d{4,}/[^\s]+', doi)
        if match:
            return match.group(0)
        
        return None
    
    def extract_doi_from_url(self, url: str) -> Optional[str]:
        """
        Extract DOI from various URL formats.
        
        Supports:
        - https://doi.org/10.xxxx/yyyy
        - https://dx.doi.org/10.xxxx/yyyy
        - Direct DOI in URL path
        """
        # Direct DOI URL
        if 'doi.org' in url:
            doi = self.normalize_doi(url)
            if doi:
                return doi
        
        # Try to find DOI pattern in URL
        doi = self.normalize_doi(url)
        return doi
    
    def get_arxiv_pdf_url(self, url: str) -> Optional[str]:
        """
        Convert arXiv abstract URL to PDF URL.
        
        Args:
            url: arXiv URL (abstract or PDF)
            
        Returns:
            PDF download URL or None
        """
        # Extract arXiv ID
        arxiv_match = re.search(r'arxiv\.org/(abs|pdf)/(\d+\.\d+)(v\d+)?', url)
        if arxiv_match:
            arxiv_id = arxiv_match.group(2)
            version = arxiv_match.group(3) or ''
            return f"https://arxiv.org/pdf/{arxiv_id}{version}.pdf"
        
        return None
    
    def query_unpaywall(self, doi: str) -> Optional[Dict]:
        """
        Query Unpaywall API for open-access locations.
        
        Args:
            doi: Normalized DOI
            
        Returns:
            Unpaywall data dict or None
        """
        try:
            url = self.unpaywall_api.format(doi=doi)
            params = {'email': self.unpaywall_email}
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                if self.verbose:
                    print(f"   ⚠️  DOI not found in Unpaywall")
                return None
            else:
                if self.verbose:
                    print(f"   ⚠️  Unpaywall returned status {response.status_code}")
                return None
        
        except Exception as e:
            if self.verbose:
                print(f"   ✗ Unpaywall query failed: {e}")
            return None
    
    def query_crossref(self, doi: str) -> Optional[Dict]:
        """
        Query Crossref API for paper metadata.
        
        Args:
            doi: Normalized DOI
            
        Returns:
            Metadata dict or None
        """
        try:
            url = self.crossref_api.format(doi=doi)
            
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('message', {})
            else:
                return None
        
        except Exception as e:
            if self.verbose:
                print(f"   ⚠️  Crossref query failed: {e}")
            return None
    
    def get_best_pdf_url(self, unpaywall_data: Dict) -> Optional[str]:
        """
        Extract best PDF URL from Unpaywall data.
        
        Priority:
        1. best_oa_location.url_for_pdf
        2. First oa_location with url_for_pdf
        3. best_oa_location.url (landing page, fallback)
        
        Args:
            unpaywall_data: Unpaywall API response
            
        Returns:
            PDF URL or None
        """
        # Try best OA location first
        best_location = unpaywall_data.get('best_oa_location')
        if best_location:
            pdf_url = best_location.get('url_for_pdf')
            if pdf_url:
                return pdf_url
        
        # Try all OA locations
        oa_locations = unpaywall_data.get('oa_locations', [])
        for location in oa_locations:
            pdf_url = location.get('url_for_pdf')
            if pdf_url:
                return pdf_url
        
        # Fallback: landing page from best location
        if best_location:
            url = best_location.get('url')
            if url:
                return url
        
        return None
    
    def sanitize_filename(self, title: str, max_length: int = 100) -> str:
        """
        Sanitize title for use as filename.
        
        Args:
            title: Paper title
            max_length: Maximum filename length
            
        Returns:
            Safe filename string
        """
        # Remove invalid characters
        title = re.sub(r'[<>:"/\\|?*]', '', title)
        
        # Replace multiple spaces with single space
        title = re.sub(r'\s+', ' ', title)
        
        # Trim and limit length
        title = title.strip()[:max_length]
        
        return title
    
    def download_pdf(self, url: str, output_path: Path) -> bool:
        """
        Download PDF from URL.
        
        Args:
            url: PDF URL
            output_path: Output file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.session.get(url, timeout=30, stream=True)
            
            if response.status_code != 200:
                if self.verbose:
                    print(f"   ✗ Download failed: HTTP {response.status_code}")
                return False
            
            # Check if content is PDF
            content_type = response.headers.get('Content-Type', '')
            if 'pdf' not in content_type.lower() and not url.endswith('.pdf'):
                if self.verbose:
                    print(f"   ⚠️  URL may not be a direct PDF link (Content-Type: {content_type})")
            
            # Download file
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Verify file is not empty
            if output_path.stat().st_size == 0:
                output_path.unlink()
                if self.verbose:
                    print(f"   ✗ Downloaded file is empty")
                return False
            
            return True
        
        except Exception as e:
            if self.verbose:
                print(f"   ✗ Download failed: {e}")
            
            # Clean up partial download
            if output_path.exists():
                output_path.unlink()
            
            return False
    
    def download_paper_by_doi(self, doi: str, custom_filename: Optional[str] = None) -> Tuple[bool, str]:
        """
        Download paper using DOI.
        
        Args:
            doi: DOI string or URL
            custom_filename: Optional custom filename (without extension)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        # Normalize DOI
        normalized_doi = self.normalize_doi(doi)
        
        if not normalized_doi:
            return False, "Invalid DOI format"
        
        if self.verbose:
            print(f"\n📄 Processing DOI: {normalized_doi}")
        
        # Query Unpaywall for open-access locations
        if self.verbose:
            print("   🔍 Querying Unpaywall API...")
        
        unpaywall_data = self.query_unpaywall(normalized_doi)
        
        if not unpaywall_data:
            return False, "No open-access version available in Unpaywall"
        
        # Check if paper is open access
        is_oa = unpaywall_data.get('is_oa', False)
        
        if not is_oa:
            if self.verbose:
                print("   ⚠️  Paper is not open access")
            return False, "Paper is not open access"
        
        # Get best PDF URL
        pdf_url = self.get_best_pdf_url(unpaywall_data)
        
        if not pdf_url:
            return False, "Open-access record found, but no PDF available"
        
        if self.verbose:
            print(f"   ✓ Found PDF URL: {pdf_url[:60]}...")
        
        # Fetch metadata from Crossref
        if self.verbose:
            print("   📚 Fetching metadata from Crossref...")
        
        metadata = self.query_crossref(normalized_doi)
        
        # Extract title
        if metadata:
            title = metadata.get('title', ['Untitled'])[0] if 'title' in metadata else 'Untitled'
        else:
            title = unpaywall_data.get('title', 'Untitled')
        
        # Generate filename
        if custom_filename:
            filename = self.sanitize_filename(custom_filename) + ".pdf"
        else:
            filename = self.sanitize_filename(title) + ".pdf"
        
        output_path = self.output_dir / filename
        
        # Check if file already exists
        if output_path.exists():
            if self.verbose:
                print(f"   ⚠️  File already exists: {filename}")
            return False, f"File already exists: {filename}"
        
        # Download PDF
        if self.verbose:
            print(f"   ⬇️  Downloading: {filename}")
        
        success = self.download_pdf(pdf_url, output_path)
        
        if success:
            file_size = output_path.stat().st_size / 1024 / 1024  # MB
            if self.verbose:
                print(f"   ✅ Downloaded successfully: {file_size:.2f} MB")
            return True, f"Downloaded: {filename} ({file_size:.2f} MB)"
        else:
            return False, "PDF download failed"
    
    def download_from_url(self, url: str) -> Tuple[bool, str]:
        """
        Download paper from URL (DOI URL, arXiv, etc.).
        
        Args:
            url: Paper URL
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        # Check if arXiv
        if 'arxiv.org' in url:
            pdf_url = self.get_arxiv_pdf_url(url)
            if pdf_url:
                if self.verbose:
                    print(f"\n📄 Processing arXiv URL: {url}")
                    print(f"   ✓ Converted to PDF URL: {pdf_url}")
                
                # Extract arXiv ID for filename
                arxiv_match = re.search(r'(\d+\.\d+)(v\d+)?', url)
                if arxiv_match:
                    filename = f"arxiv_{arxiv_match.group(0)}.pdf"
                else:
                    filename = "arxiv_paper.pdf"
                
                output_path = self.output_dir / filename
                
                if output_path.exists():
                    return False, f"File already exists: {filename}"
                
                success = self.download_pdf(pdf_url, output_path)
                if success:
                    file_size = output_path.stat().st_size / 1024 / 1024
                    return True, f"Downloaded: {filename} ({file_size:.2f} MB)"
                else:
                    return False, "arXiv download failed"
        
        # Try to extract DOI from URL
        doi = self.extract_doi_from_url(url)
        
        if doi:
            return self.download_paper_by_doi(doi)
        else:
            return False, f"Could not extract DOI from URL: {url}"
    
    def batch_download(self, dois_or_urls: List[str]) -> Dict[str, Tuple[bool, str]]:
        """
        Download multiple papers.
        
        Args:
            dois_or_urls: List of DOIs or URLs
            
        Returns:
            Dict mapping input -> (success, message)
        """
        results = {}
        
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"BATCH DOWNLOAD: {len(dois_or_urls)} papers")
            print(f"{'='*60}")
        
        for i, item in enumerate(dois_or_urls, 1):
            if self.verbose:
                print(f"\n[{i}/{len(dois_or_urls)}]")
            
            success, message = self.download_from_url(item)
            results[item] = (success, message)
            
            # Rate limiting
            time.sleep(1)
        
        # Summary
        if self.verbose:
            successful = sum(1 for s, _ in results.values() if s)
            print(f"\n{'='*60}")
            print(f"✅ Batch download complete: {successful}/{len(dois_or_urls)} successful")
            print(f"{'='*60}")
        
        return results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Download academic papers by DOI')
    parser.add_argument('inputs', nargs='+',
                        help='DOIs or URLs to download')
    parser.add_argument('--output', default='data/sources',
                        help='Output directory (default: data/sources)')
    parser.add_argument('--quiet', action='store_true',
                        help='Suppress verbose output')
    parser.add_argument('--from-file', metavar='FILE',
                        help='Read DOIs/URLs from file (one per line)')
    
    args = parser.parse_args()
    
    downloader = DOIPaperDownloader(
        output_dir=args.output,
        verbose=not args.quiet
    )
    
    # Collect inputs
    inputs = []
    
    if args.from_file:
        with open(args.from_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    inputs.append(line)
    
    inputs.extend(args.inputs)
    
    if not inputs:
        print("No inputs provided")
        return
    
    # Download
    if len(inputs) == 1:
        success, message = downloader.download_from_url(inputs[0])
        print(f"\n{message}")
        sys.exit(0 if success else 1)
    else:
        results = downloader.batch_download(inputs)
        
        # Print summary
        print("\nResults:")
        for item, (success, message) in results.items():
            status = "✅" if success else "❌"
            print(f"  {status} {item[:60]}... - {message}")


if __name__ == '__main__':
    main()
