"""
Web Discovery Agent

Discovers and extracts articles from the web based on prompts.
Uses trafilatura for high-quality content extraction.
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

import requests
from trafilatura import fetch_url, extract
from openai import OpenAI

from core.document_processor import DocumentProcessor


class WebDiscovery:
    """Discover and extract web articles"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.processor = DocumentProcessor()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def discover_articles(self, prompt: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Use AI to generate search queries and find relevant URLs"""
        
        # Generate search queries using AI
        queries = self._generate_search_queries(prompt)
        print(f"Generated {len(queries)} search queries")
        
        # For now, return placeholder URLs
        # In production, integrate with search API (Google, Bing, etc.)
        print("Note: Search API integration needed for full functionality")
        
        discovered = []
        for query in queries[:max_results]:
            discovered.append({
                'query': query,
                'url': None,  # Would be populated by search API
                'title': f"Search: {query}"
            })
        
        return discovered
    
    def _generate_search_queries(self, prompt: str) -> List[str]:
        """Generate search queries from user prompt"""
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a search query generator. Generate 3-5 specific search queries that would find relevant articles for the user's research topic. Return only the queries, one per line."
                },
                {
                    "role": "user",
                    "content": f"Generate search queries for: {prompt}"
                }
            ],
            temperature=0.7,
            max_tokens=200
        )
        
        queries = response.choices[0].message.content.strip().split('\n')
        queries = [q.strip('- ').strip() for q in queries if q.strip()]
        
        return queries
    
    def extract_article(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract article content from URL"""
        try:
            print(f"Fetching: {url}")
            
            # Fetch HTML
            downloaded = fetch_url(url)
            if not downloaded:
                print(f"Failed to fetch URL")
                return None
            
            # Extract content
            content = extract(
                downloaded,
                include_comments=False,
                include_tables=True,
                include_images=False,
                output_format='markdown'
            )
            
            if not content:
                print("No content extracted")
                return None
            
            # Extract metadata
            metadata = extract(
                downloaded,
                include_comments=False,
                output_format='json'
            )
            
            import json
            if metadata:
                metadata = json.loads(metadata)
            else:
                metadata = {}
            
            return {
                'url': url,
                'title': metadata.get('title', 'Untitled'),
                'author': metadata.get('author', 'Unknown'),
                'date': metadata.get('date', datetime.now().isoformat()),
                'content': content,
                'hostname': metadata.get('hostname', ''),
                'description': metadata.get('description', '')
            }
        
        except Exception as e:
            print(f"Error extracting article: {e}")
            return None
    
    def extract_multiple(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Extract multiple articles"""
        articles = []
        
        for url in urls:
            article = self.extract_article(url)
            if article:
                articles.append(article)
        
        return articles
    
    def save_to_vault(
        self,
        article: Dict[str, Any],
        tags: Optional[List[str]] = None
    ) -> str:
        """Save article to vault as literature note"""
        
        # Build content with metadata
        content_parts = []
        
        # Add source info
        content_parts.append(f"**Source:** {article['url']}")
        content_parts.append(f"**Author:** {article['author']}")
        content_parts.append(f"**Published:** {article['date']}")
        
        if article.get('description'):
            content_parts.append(f"\n**Description:** {article['description']}")
        
        content_parts.append("\n---\n")
        
        # Add main content
        content_parts.append(article['content'])
        
        full_content = "\n".join(content_parts)
        
        # Add web-related tags
        if tags is None:
            tags = []
        tags.extend(['web-article', 'literature'])
        
        # Create metadata
        metadata = {
            'url': article['url'],
            'author': article['author'],
            'published': article['date'],
            'hostname': article.get('hostname', '')
        }
        
        # Save to vault
        note_path = self.processor.add_text_note(
            title=article['title'],
            content=full_content,
            tags=tags,
            metadata=metadata
        )
        
        return note_path
    
    def discover_and_import(
        self,
        prompt: str,
        urls: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        auto_save: bool = False
    ) -> List[Dict[str, Any]]:
        """Discover articles from prompt and optionally import"""
        
        results = []
        
        if urls:
            # User provided URLs directly
            print(f"Extracting {len(urls)} provided URLs...")
            articles = self.extract_multiple(urls)
        else:
            # Generate and search (requires search API)
            print("Discovering articles from prompt...")
            discovered = self.discover_articles(prompt)
            print(f"Note: Manual URL input needed. Discovered queries:")
            for d in discovered:
                print(f"  - {d['query']}")
            articles = []
        
        # Process articles
        for article in articles:
            result = {
                'article': article,
                'saved': False,
                'note_path': None
            }
            
            if auto_save:
                try:
                    note_path = self.save_to_vault(article, tags=tags)
                    result['saved'] = True
                    result['note_path'] = note_path
                    print(f"✓ Saved: {article['title']}")
                except Exception as e:
                    print(f"✗ Failed to save: {e}")
            
            results.append(result)
        
        return results
    
    def assess_quality(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Assess article quality using AI"""
        
        # Create summary of article for assessment
        preview = article['content'][:2000]
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a research quality assessor. Evaluate the article and provide: 1) Quality score (1-10), 2) Relevance assessment, 3) Key topics covered. Be concise."
                },
                {
                    "role": "user",
                    "content": f"Title: {article['title']}\n\nContent preview:\n{preview}"
                }
            ],
            temperature=0.3,
            max_tokens=300
        )
        
        assessment = response.choices[0].message.content
        
        return {
            'url': article['url'],
            'title': article['title'],
            'assessment': assessment
        }


if __name__ == "__main__":
    # Demo
    discovery = WebDiscovery()
    
    # Example URL extraction
    test_url = "https://en.wikipedia.org/wiki/Knowledge_graph"
    print(f"Testing extraction from: {test_url}")
    
    article = discovery.extract_article(test_url)
    if article:
        print(f"\nExtracted article:")
        print(f"  Title: {article['title']}")
        print(f"  Author: {article['author']}")
        print(f"  Content length: {len(article['content'])} chars")
