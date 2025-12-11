"""
Web Discovery Agent

Discovers and extracts articles from the web based on prompts.
Uses trafilatura for high-quality content extraction.
Supports automated search via SerpAPI (Google), arXiv, and Semantic Scholar.
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
    
    def extract_research_topic(self, content: str, max_words: int = 15) -> str:
        """
        Extract a focused research topic from document content.
        
        Args:
            content: Document content to analyze
            max_words: Maximum words in the extracted topic
            
        Returns:
            Concise research topic string
        """
        # Limit content to first 5000 characters
        content_sample = content[:5000]
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a research topic extraction expert. Extract the main research topic from the provided document.

Guidelines:
- Return ONE concise sentence (max {max_words} words)
- Use specific domain terminology (e.g., "EU Data Act", "cloud portability", "RDF graphs")
- Focus on the PRIMARY research question or theme
- Be specific enough to generate relevant search queries
- Avoid generic terms like "data governance" or "technology trends"

Output format: Just the topic sentence, nothing else."""
                },
                {
                    "role": "user",
                    "content": f"Extract the main research topic from this document:\n\n{content_sample}"
                }
            ],
            temperature=0.2,
            max_tokens=100
        )
        
        topic = response.choices[0].message.content.strip()
        
        # Remove quotes if present
        topic = topic.strip('"').strip("'")
        
        return topic
    
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
                    "content": """You are a research search query expert. Generate 3-5 highly specific and targeted search queries for academic and professional articles.

Guidelines:
- Use exact terminology from the research topic
- Include key domain-specific terms and concepts
- Combine main topic with specific subtopics
- Make queries specific enough to avoid irrelevant results
- Focus on the EXACT topic provided, not tangentially related fields

Return only the search queries, one per line, without numbering or bullet points."""
                },
                {
                    "role": "user",
                    "content": f"Research topic: {prompt}\n\nGenerate search queries that will find articles SPECIFICALLY about this topic."
                }
            ],
            temperature=0.3,
            max_tokens=300
        )
        
        queries = response.choices[0].message.content.strip().split('\n')
        queries = [q.strip('- ').strip('0123456789. ').strip() for q in queries if q.strip()]
        
        return queries
    
    def generate_queries_from_graph_concepts(
        self, 
        topics: List[Dict[str, Any]] = None,
        concepts: List[str] = None,
        num_queries: int = 5
    ) -> List[str]:
        """
        Generate search queries from knowledge graph topics and concepts.
        
        Args:
            topics: List of topic dicts with 'label', 'description', 'concepts'
            concepts: List of concept strings
            num_queries: Number of queries to generate
            
        Returns:
            List of targeted search query strings
        """
        # Build context from graph data
        context_parts = []
        
        if topics:
            context_parts.append("Research Topics:")
            for i, topic in enumerate(topics[:3], 1):
                context_parts.append(f"{i}. {topic['label']}")
                if topic.get('description'):
                    context_parts.append(f"   Description: {topic['description']}")
                if topic.get('concepts'):
                    context_parts.append(f"   Key concepts: {', '.join(topic['concepts'][:5])}")
        
        if concepts:
            context_parts.append("\nDomain Concepts:")
            context_parts.append(", ".join(concepts[:15]))
        
        context = "\n".join(context_parts)
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a research search query expert. Generate {num_queries} highly specific search queries based on the provided knowledge graph structure.

Guidelines:
- Use the EXACT concepts and topics from the knowledge graph
- Combine multiple concepts to create focused queries
- Target academic papers, technical articles, and industry reports
- Make queries specific enough to avoid irrelevant results
- Focus on relationships between concepts

Return only the search queries, one per line, without numbering or bullet points."""
                },
                {
                    "role": "user",
                    "content": f"Based on this knowledge graph:\n\n{context}\n\nGenerate {num_queries} search queries that will find NEW articles to expand this research."
                }
            ],
            temperature=0.4,
            max_tokens=400
        )
        
        queries = response.choices[0].message.content.strip().split('\n')
        queries = [q.strip('- ').strip('0123456789. ').strip() for q in queries if q.strip()]
        
        return queries[:num_queries]
    
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
                    "content": """You are a research quality assessor. Evaluate the article based on:
- Content depth and detail (not just length)
- Academic/professional quality
- Clarity and structure
- Credibility and sources

Provide your response in this exact format:
Quality Score: [number 1-10]
Relevance: [brief assessment]
Key Topics: [list main topics]"""
                },
                {
                    "role": "user",
                    "content": f"Title: {article['title']}\n\nContent preview:\n{preview}"
                }
            ],
            temperature=0.3,
            max_tokens=300
        )
        
        assessment_text = response.choices[0].message.content
        
        # Extract numeric quality score
        quality_score = 0
        try:
            import re
            match = re.search(r'Quality Score:\s*(\d+)', assessment_text)
            if match:
                quality_score = int(match.group(1))
        except:
            quality_score = 5  # Default to middle score
        
        return {
            'url': article['url'],
            'title': article['title'],
            'assessment': assessment_text,
            'quality_score': quality_score
        }
    
    def search_web(self, query: str, max_results: int = 10, source: str = 'all') -> List[Dict[str, str]]:
        """
        Search the web using free APIs.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            source: 'all', 'arxiv', 'semantic_scholar', or 'google' (requires SERPAPI_KEY)
        
        Returns:
            List of dicts with 'title', 'url', 'snippet', 'source'
        """
        results = []
        
        if source in ['all', 'arxiv']:
            results.extend(self._search_arxiv(query, max_results))
        
        if source in ['all', 'semantic_scholar']:
            results.extend(self._search_semantic_scholar(query, max_results))
        
        if source == 'google' and os.getenv('SERPAPI_KEY'):
            results.extend(self._search_google(query, max_results))
        
        return results[:max_results]
    
    def _search_arxiv(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """Search arXiv for academic papers (FREE)."""
        try:
            import urllib.parse
            
            encoded_query = urllib.parse.quote(query)
            url = f"http://export.arxiv.org/api/query?search_query=all:{encoded_query}&start=0&max_results={max_results}"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                return []
            
            # Parse XML response
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            results = []
            for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                title = entry.find('{http://www.w3.org/2005/Atom}title').text.strip()
                link = entry.find('{http://www.w3.org/2005/Atom}id').text.strip()
                summary = entry.find('{http://www.w3.org/2005/Atom}summary').text.strip()
                
                results.append({
                    'title': title,
                    'url': link,
                    'snippet': summary[:300] + '...' if len(summary) > 300 else summary,
                    'source': 'arXiv'
                })
            
            return results
        except Exception as e:
            print(f"  Warning: arXiv search failed: {e}")
            return []
    
    def _search_semantic_scholar(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """Search Semantic Scholar for academic papers (FREE)."""
        try:
            url = "https://api.semanticscholar.org/graph/v1/paper/search"
            params = {
                'query': query,
                'limit': max_results,
                'fields': 'title,abstract,url,authors'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                print(f"  Warning: Semantic Scholar returned status {response.status_code}")
                print(f"  Response: {response.text[:200]}")
                return []
            
            data = response.json()
            
            if 'data' not in data:
                print(f"  Warning: Semantic Scholar response missing 'data' field")
                print(f"  Response keys: {list(data.keys())}")
                return []
            
            results = []
            
            for paper in data.get('data', []):
                # Get paper URL (prefer external URL, fallback to Semantic Scholar)
                paper_url = paper.get('url') or f"https://www.semanticscholar.org/paper/{paper.get('paperId')}"
                
                abstract = paper.get('abstract', 'No abstract available')
                snippet = abstract[:300] + '...' if len(abstract) > 300 else abstract
                
                results.append({
                    'title': paper.get('title', 'Untitled'),
                    'url': paper_url,
                    'snippet': snippet,
                    'source': 'Semantic Scholar'
                })
            
            return results
        except Exception as e:
            print(f"  Warning: Semantic Scholar search failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _search_google(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """Search Google using SerpAPI (requires SERPAPI_KEY env var)."""
        try:
            api_key = os.getenv('SERPAPI_KEY')
            if not api_key:
                print("  Warning: SERPAPI_KEY not set. Skipping Google search.")
                return []
            
            url = "https://serpapi.com/search"
            params = {
                'q': query,
                'api_key': api_key,
                'num': max_results
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            results = []
            
            for result in data.get('organic_results', []):
                results.append({
                    'title': result.get('title', 'Untitled'),
                    'url': result.get('link', ''),
                    'snippet': result.get('snippet', 'No description'),
                    'source': 'Google'
                })
            
            return results
        except Exception as e:
            print(f"  Warning: Google search failed: {e}")
            return []


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
