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
    
    def search_web(self, query: str, max_results: int = 10, source: str = 'all', categories: List[str] = None) -> List[Dict[str, str]]:
        """
        Search the web using 24+ free APIs across 8 categories.
        
        Args:
            query: Search query
            max_results: Maximum results to return per source
            source: Specific API name or 'all' for multi-source search
            categories: List of categories to search (scientific, scholarly, news, educational, technical, opinion, community, documentation)
        
        Returns:
            List of dicts with 'title', 'url', 'snippet', 'source'
        
        Available sources:
            Scientific: crossref, openalex, semantic_scholar
            Scholarly: core, zenodo, figshare, arxiv, eurlex, doaj, hal
            News: guardian, nytimes, gdelt
            Educational: wikipedia, wikidata, openlibrary
            Technical: arxiv, devto
            Opinion: guardian, nytimes, wikinews
            Community: stackexchange, hackernews
            Documentation: readthedocs, w3c
        """
        results = []
        
        # Define category mappings
        category_map = {
            'scientific': ['crossref', 'openalex', 'semantic_scholar'],
            'scholarly': ['core', 'zenodo', 'figshare', 'arxiv', 'eurlex', 'doaj', 'hal'],
            'news': ['guardian', 'nytimes', 'gdelt'],
            'educational': ['wikipedia', 'wikidata', 'openlibrary'],
            'technical': ['arxiv', 'devto'],
            'opinion': ['guardian', 'nytimes', 'wikinews'],
            'community': ['stackexchange', 'hackernews'],
            'documentation': ['readthedocs', 'w3c']
        }
        
        # Build list of sources to search
        sources_to_search = []
        
        if source == 'all':
            if categories:
                # Search specified categories
                for cat in categories:
                    if cat in category_map:
                        sources_to_search.extend(category_map[cat])
            else:
                # Search all sources
                sources_to_search = [
                    'crossref', 'openalex', 'semantic_scholar',
                    'core', 'zenodo', 'figshare', 'arxiv', 'eurlex', 'doaj', 'hal',
                    'guardian', 'nytimes', 'gdelt',
                    'wikipedia', 'wikidata', 'openlibrary',
                    'devto',
                    'wikinews',
                    'stackexchange', 'hackernews',
                    'readthedocs', 'w3c'
                ]
        else:
            sources_to_search = [source]
        
        # Remove duplicates while preserving order
        sources_to_search = list(dict.fromkeys(sources_to_search))
        
        # Map source names to methods
        source_methods = {
            'crossref': self._search_crossref,
            'openalex': self._search_openalex,
            'semantic_scholar': self._search_semantic_scholar,
            'core': self._search_core,
            'zenodo': self._search_zenodo,
            'figshare': self._search_figshare,
            'arxiv': self._search_arxiv,
            'eurlex': self._search_eurlex,
            'doaj': self._search_doaj,
            'hal': self._search_hal,
            'guardian': self._search_guardian,
            'nytimes': self._search_nytimes,
            'gdelt': self._search_gdelt,
            'wikipedia': self._search_wikipedia,
            'wikidata': self._search_wikidata,
            'openlibrary': self._search_openlibrary,
            'devto': self._search_devto,
            'wikinews': self._search_wikinews,
            'stackexchange': self._search_stackexchange,
            'hackernews': self._search_hackernews,
            'readthedocs': self._search_readthedocs,
            'w3c': self._search_w3c,
            'google': self._search_google
        }
        
        # Search each source
        for src in sources_to_search:
            if src in source_methods:
                try:
                    source_results = source_methods[src](query, max_results)
                    results.extend(source_results)
                except Exception as e:
                    print(f"  Error searching {src}: {e}")
        
        return results
    
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
    
    def _search_eurlex(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """Search EUR-Lex Cellar for EU legislation and documents."""
        try:
            # EUR-Lex SPARQL endpoint
            endpoint = "http://publications.europa.eu/webapi/rdf/sparql"
            
            # Build SPARQL query
            sparql_query = f"""
            PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
            PREFIX dc: <http://purl.org/dc/elements/1.1/>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            
            SELECT DISTINCT ?work ?title ?date WHERE {{
              ?expr a cdm:expression ;
                    dc:title ?title ;
                    cdm:expression_uses_language <http://publications.europa.eu/resource/authority/language/ENG> .
              
              ?work cdm:work_has_expression ?expr .
              
              OPTIONAL {{ ?expr cdm:date_document ?date }}
              
              FILTER(CONTAINS(LCASE(?title), LCASE("{query}")))
            }}
            ORDER BY DESC(?date)
            LIMIT {max_results}
            """
            
            params = {
                'query': sparql_query,
                'format': 'application/sparql-results+json'
            }
            
            response = self.session.get(endpoint, params=params, timeout=20)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            results = []
            
            for binding in data.get('results', {}).get('bindings', []):
                title = binding.get('title', {}).get('value', 'Untitled')
                work_uri = binding.get('work', {}).get('value', '')
                
                # Extract CELEX number from URI if available
                celex_match = re.search(r'CELEX:(\d+[A-Z]\d+)', work_uri)
                if celex_match:
                    celex = celex_match.group(1)
                    url = f"https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:{celex}"
                else:
                    url = work_uri
                
                results.append({
                    'title': title,
                    'url': url,
                    'snippet': f"EU legislation document from EUR-Lex matching '{query}'",
                    'source': 'EUR-Lex'
                })
            
            return results
        except Exception as e:
            print(f"  Warning: EUR-Lex search failed: {e}")
            return []
    
    def _search_doaj(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """Search DOAJ (Directory of Open Access Journals) for open access articles."""
        try:
            url = "https://doaj.org/api/search/articles/{}".format(query)
            params = {
                'page': 1,
                'pageSize': max_results
            }
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            results = []
            
            for article in data.get('results', []):
                bibjson = article.get('bibjson', {})
                title = bibjson.get('title', 'Untitled')
                abstract = bibjson.get('abstract', 'No abstract available')
                snippet = abstract[:300] + '...' if len(abstract) > 300 else abstract
                
                # Get article URL
                links = bibjson.get('link', [])
                url = ''
                for link in links:
                    if link.get('type') == 'fulltext':
                        url = link.get('url', '')
                        break
                
                if not url and links:
                    url = links[0].get('url', '')
                
                if url:
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet,
                        'source': 'DOAJ'
                    })
            
            return results
        except Exception as e:
            print(f"  Warning: DOAJ search failed: {e}")
            return []
    
    def _search_hal(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """Search HAL (Hyper Articles en Ligne) Open Science repository."""
        try:
            url = "https://api.archives-ouvertes.fr/search/"
            params = {
                'q': query,
                'rows': max_results,
                'fl': 'docid,title_s,abstract_s,uri_s,fileMain_s',
                'wt': 'json'
            }
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            results = []
            
            for doc in data.get('response', {}).get('docs', []):
                title = doc.get('title_s', ['Untitled'])
                if isinstance(title, list):
                    title = title[0] if title else 'Untitled'
                
                abstract = doc.get('abstract_s', ['No abstract available'])
                if isinstance(abstract, list):
                    abstract = abstract[0] if abstract else 'No abstract available'
                
                snippet = abstract[:300] + '...' if len(abstract) > 300 else abstract
                
                # Prefer full text URL, fallback to record URL
                url = doc.get('fileMain_s', doc.get('uri_s', ['']))
                if isinstance(url, list):
                    url = url[0] if url else ''
                
                if url:
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet,
                        'source': 'HAL'
                    })
            
            return results
        except Exception as e:
            print(f"  Warning: HAL search failed: {e}")
            return []
    
    def _search_zenodo(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """Search Zenodo for research outputs (papers, datasets, software)."""
        try:
            url = "https://zenodo.org/api/records"
            params = {
                'q': query,
                'size': max_results,
                'sort': 'mostrecent',
                'type': 'publication'  # Focus on publications
            }
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            results = []
            
            for hit in data.get('hits', {}).get('hits', []):
                metadata = hit.get('metadata', {})
                title = metadata.get('title', 'Untitled')
                description = metadata.get('description', 'No description available')
                snippet = description[:300] + '...' if len(description) > 300 else description
                
                # Get DOI link
                doi = metadata.get('doi', '')
                if doi:
                    url = f"https://doi.org/{doi}"
                else:
                    # Fallback to Zenodo record link
                    links = hit.get('links', {})
                    url = links.get('html', '')
                
                if url:
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet,
                        'source': 'Zenodo'
                    })
            
            return results
        except Exception as e:
            print(f"  Warning: Zenodo search failed: {e}")
            return []
    
    def _search_openalex(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Search OpenAlex scholarly graph (250M+ papers across all fields).
        Free and open, no API key required.
        """
        try:
            url = "https://api.openalex.org/works"
            params = {
                'search': query,
                'filter': 'is_oa:true',  # Open access only
                'per_page': max_results,
                'mailto': 'research@example.com'  # Polite pool (faster rate limit)
            }
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            results = []
            
            for work in data.get('results', []):
                title = work.get('title', 'Untitled')
                
                # Get abstract or first 300 chars of inverted abstract
                abstract = work.get('abstract', '')
                if not abstract:
                    inverted_abstract = work.get('abstract_inverted_index', {})
                    if inverted_abstract:
                        # Reconstruct abstract from inverted index (simplified)
                        words = []
                        for word, positions in sorted(inverted_abstract.items(), key=lambda x: min(x[1]) if x[1] else 0):
                            words.append(word)
                        abstract = ' '.join(words[:100])
                
                snippet = (abstract[:300] + '...') if len(abstract) > 300 else (abstract or 'No abstract available')
                
                # Get DOI or landing page URL
                doi = work.get('doi', '')
                if doi and doi.startswith('https://doi.org/'):
                    url = doi
                else:
                    url = work.get('landing_page_url', work.get('id', ''))
                
                if url:
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet,
                        'source': 'OpenAlex'
                    })
            
            return results
        except Exception as e:
            print(f"  Warning: OpenAlex search failed: {e}")
            return []
    
    def _search_core(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Search CORE (100M+ open access papers).
        Note: Requires API key for full access, but works in limited mode without.
        """
        try:
            # CORE API v3
            url = "https://api.core.ac.uk/v3/search/works"
            
            # Check if API key is available
            api_key = os.getenv('CORE_API_KEY')
            headers = {}
            if api_key:
                headers['Authorization'] = f'Bearer {api_key}'
            
            params = {
                'q': query,
                'limit': max_results,
                'stats': 'false'
            }
            
            response = self.session.get(url, params=params, headers=headers, timeout=15)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            results = []
            
            for item in data.get('results', []):
                title = item.get('title', 'Untitled')
                abstract = item.get('abstract', '')
                snippet = (abstract[:300] + '...') if len(abstract) > 300 else (abstract or 'No abstract available')
                
                # Get DOI or download URL
                doi = item.get('doi', '')
                if doi:
                    url = f"https://doi.org/{doi}" if not doi.startswith('http') else doi
                else:
                    # Try download URL or source URL
                    url = item.get('downloadUrl') or item.get('sourceFulltextUrls', [None])[0]
                
                if url:
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet,
                        'source': 'CORE'
                    })
            
            return results
        except Exception as e:
            print(f"  Warning: CORE search failed: {e}")
            return []
    
    # ========================================
    # Category 1: Scientific / Academic APIs
    # ========================================
    
    def _search_crossref(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Search Crossref REST API for DOI metadata (scholarly papers, books, datasets).
        """
        try:
            url = "https://api.crossref.org/works"
            params = {
                'query': query,
                'rows': max_results,
                'mailto': 'research@example.com'  # Polite pool
            }
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            results = []
            
            for item in data.get('message', {}).get('items', []):
                # Get title (may be array)
                title_arr = item.get('title', ['Untitled'])
                title = title_arr[0] if isinstance(title_arr, list) and title_arr else 'Untitled'
                
                # Get abstract if available
                abstract = item.get('abstract', '')
                snippet = (abstract[:300] + '...') if len(abstract) > 300 else (abstract or 'No abstract available')
                
                # Get DOI URL
                doi = item.get('DOI', '')
                url = f"https://doi.org/{doi}" if doi else ''
                
                if url:
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet,
                        'source': 'Crossref'
                    })
            
            return results
        except Exception as e:
            print(f"  Warning: Crossref search failed: {e}")
            return []
    
    # ========================================
    # Category 2: Scholarly Reports/Preprints
    # ========================================
    
    def _search_figshare(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Search Figshare API for research outputs (papers, datasets, figures).
        """
        try:
            url = "https://api.figshare.com/v2/articles/search"
            payload = {
                'search_for': query,
                'page_size': max_results,
                'item_type': 3  # 3 = paper
            }
            
            response = self.session.post(url, json=payload, timeout=15)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            results = []
            
            for item in data:
                title = item.get('title', 'Untitled')
                description = item.get('description', 'No description available')
                
                # Strip HTML tags from description
                import re
                description = re.sub(r'<[^>]+>', '', description)
                snippet = (description[:300] + '...') if len(description) > 300 else description
                
                # Get DOI or figshare URL
                doi = item.get('doi', '')
                if doi:
                    url = f"https://doi.org/{doi}"
                else:
                    url = item.get('url', '')
                
                if url:
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet,
                        'source': 'Figshare'
                    })
            
            return results
        except Exception as e:
            print(f"  Warning: Figshare search failed: {e}")
            return []
    
    # ========================================
    # Category 3: News APIs
    # ========================================
    
    def _search_guardian(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Search The Guardian Open Platform for news articles.
        Requires GUARDIAN_API_KEY environment variable.
        """
        try:
            api_key = os.getenv('GUARDIAN_API_KEY')
            if not api_key:
                print("  Note: GUARDIAN_API_KEY not set. Skipping Guardian search.")
                return []
            
            url = "https://content.guardianapis.com/search"
            params = {
                'q': query,
                'api-key': api_key,
                'page-size': max_results,
                'show-fields': 'trailText,headline',
                'order-by': 'relevance'
            }
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            results = []
            
            for item in data.get('response', {}).get('results', []):
                title = item.get('webTitle', 'Untitled')
                fields = item.get('fields', {})
                snippet = fields.get('trailText', 'No description available')
                url = item.get('webUrl', '')
                
                if url:
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet,
                        'source': 'The Guardian'
                    })
            
            return results
        except Exception as e:
            print(f"  Warning: Guardian search failed: {e}")
            return []
    
    def _search_nytimes(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Search New York Times Article Search API.
        Requires NYTIMES_API_KEY environment variable.
        """
        try:
            api_key = os.getenv('NYTIMES_API_KEY')
            if not api_key:
                print("  Note: NYTIMES_API_KEY not set. Skipping NYTimes search.")
                return []
            
            url = "https://api.nytimes.com/svc/search/v2/articlesearch.json"
            params = {
                'q': query,
                'api-key': api_key,
                'sort': 'relevance'
            }
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            results = []
            
            for doc in data.get('response', {}).get('docs', [])[:max_results]:
                title = doc.get('headline', {}).get('main', 'Untitled')
                snippet = doc.get('abstract', 'No description available')
                web_url = doc.get('web_url', '')
                
                if web_url:
                    results.append({
                        'title': title,
                        'url': web_url,
                        'snippet': snippet,
                        'source': 'New York Times'
                    })
            
            return results
        except Exception as e:
            print(f"  Warning: NYTimes search failed: {e}")
            return []
    
    def _search_gdelt(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Search GDELT 2.1 API for global news mentions.
        """
        try:
            url = "https://api.gdeltproject.org/api/v2/doc/doc"
            params = {
                'query': query,
                'mode': 'artlist',
                'maxrecords': max_results,
                'format': 'json'
            }
            
            response = self.session.get(url, params=params, timeout=20)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            results = []
            
            for article in data.get('articles', []):
                title = article.get('title', 'Untitled')
                url = article.get('url', '')
                # GDELT doesn't provide snippets, use domain + date as context
                domain = article.get('domain', '')
                snippet = f"News article from {domain}"
                
                if url:
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet,
                        'source': 'GDELT'
                    })
            
            return results
        except Exception as e:
            print(f"  Warning: GDELT search failed: {e}")
            return []
    
    # ========================================
    # Category 4: Educational / Reference
    # ========================================
    
    def _search_wikipedia(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Search Wikipedia REST API for encyclopedia articles.
        """
        try:
            url = "https://en.wikipedia.org/w/api.php"
            params = {
                'action': 'query',
                'list': 'search',
                'srsearch': query,
                'srlimit': max_results,
                'srprop': 'snippet',
                'format': 'json'
            }
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            results = []
            
            for item in data.get('query', {}).get('search', []):
                title = item.get('title', 'Untitled')
                page_id = item.get('pageid', '')
                url = f"https://en.wikipedia.org/?curid={page_id}" if page_id else ''
                
                # Clean HTML from snippet
                snippet = item.get('snippet', 'No description available')
                import re
                snippet = re.sub(r'<[^>]+>', '', snippet)
                
                if url:
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet,
                        'source': 'Wikipedia'
                    })
            
            return results
        except Exception as e:
            print(f"  Warning: Wikipedia search failed: {e}")
            return []
    
    def _search_wikidata(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Search Wikidata SPARQL endpoint for structured knowledge.
        """
        try:
            endpoint = "https://query.wikidata.org/sparql"
            
            # Simple entity search query
            sparql_query = f"""
            SELECT ?item ?itemLabel ?itemDescription WHERE {{
              SERVICE wikibase:mwapi {{
                bd:serviceParam wikibase:endpoint "www.wikidata.org";
                                wikibase:api "EntitySearch";
                                mwapi:search "{query}";
                                mwapi:language "en".
                ?item wikibase:apiOutputItem mwapi:item.
              }}
              SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
            }}
            LIMIT {max_results}
            """
            
            params = {
                'query': sparql_query,
                'format': 'json'
            }
            
            response = self.session.get(endpoint, params=params, timeout=20)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            results = []
            
            for binding in data.get('results', {}).get('bindings', []):
                item_uri = binding.get('item', {}).get('value', '')
                title = binding.get('itemLabel', {}).get('value', 'Untitled')
                description = binding.get('itemDescription', {}).get('value', 'Wikidata entity')
                
                # Extract Q-id and build URL
                q_id = item_uri.split('/')[-1]
                url = f"https://www.wikidata.org/wiki/{q_id}" if q_id.startswith('Q') else ''
                
                if url:
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': description,
                        'source': 'Wikidata'
                    })
            
            return results
        except Exception as e:
            print(f"  Warning: Wikidata search failed: {e}")
            return []
    
    def _search_openlibrary(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Search Open Library API for books and publications.
        """
        try:
            url = "https://openlibrary.org/search.json"
            params = {
                'q': query,
                'limit': max_results
            }
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            results = []
            
            for doc in data.get('docs', []):
                title = doc.get('title', 'Untitled')
                author_names = doc.get('author_name', [])
                author = ', '.join(author_names[:2]) if author_names else 'Unknown'
                
                # Get first sentence or subject as snippet
                first_sentence = doc.get('first_sentence', [''])[0] if doc.get('first_sentence') else ''
                subjects = doc.get('subject', [])
                snippet = first_sentence if first_sentence else f"Topics: {', '.join(subjects[:3])}" if subjects else 'No description'
                
                # Build Open Library URL
                key = doc.get('key', '')
                url = f"https://openlibrary.org{key}" if key else ''
                
                if url:
                    results.append({
                        'title': f"{title} by {author}",
                        'url': url,
                        'snippet': snippet,
                        'source': 'Open Library'
                    })
            
            return results
        except Exception as e:
            print(f"  Warning: Open Library search failed: {e}")
            return []
    
    # ========================================
    # Category 5: Expert / Technical Articles
    # ========================================
    
    def _search_devto(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Search Dev.to API for technical articles.
        """
        try:
            url = "https://dev.to/api/articles"
            params = {
                'per_page': max_results,
                'tag': query  # Dev.to works better with tags
            }
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            results = []
            
            for article in data[:max_results]:
                title = article.get('title', 'Untitled')
                description = article.get('description', 'No description available')
                url = article.get('url', '')
                
                if url:
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': description,
                        'source': 'Dev.to'
                    })
            
            return results
        except Exception as e:
            print(f"  Warning: Dev.to search failed: {e}")
            return []
    
    # ========================================
    # Category 6: Opinion / Editorial
    # ========================================
    
    def _search_wikinews(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Search Wikinews for news articles.
        """
        try:
            url = "https://en.wikinews.org/w/api.php"
            params = {
                'action': 'query',
                'list': 'search',
                'srsearch': query,
                'srlimit': max_results,
                'srprop': 'snippet|timestamp',
                'format': 'json'
            }
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            results = []
            
            for item in data.get('query', {}).get('search', []):
                title = item.get('title', 'Untitled')
                page_id = item.get('pageid', '')
                url = f"https://en.wikinews.org/?curid={page_id}" if page_id else ''
                
                # Clean HTML from snippet
                snippet = item.get('snippet', 'No description available')
                import re
                snippet = re.sub(r'<[^>]+>', '', snippet)
                
                if url:
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet,
                        'source': 'Wikinews'
                    })
            
            return results
        except Exception as e:
            print(f"  Warning: Wikinews search failed: {e}")
            return []
    
    # ========================================
    # Category 7: Community Knowledge
    # ========================================
    
    def _search_stackexchange(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Search Stack Exchange API for Q&A content.
        """
        try:
            url = "https://api.stackexchange.com/2.3/search/advanced"
            params = {
                'q': query,
                'order': 'desc',
                'sort': 'relevance',
                'site': 'stackoverflow',  # Can be changed to other SE sites
                'pagesize': max_results,
                'filter': 'withbody'
            }
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            results = []
            
            for item in data.get('items', []):
                title = item.get('title', 'Untitled')
                url = item.get('link', '')
                
                # Get body excerpt (first 300 chars)
                body = item.get('body', '')
                import re
                body = re.sub(r'<[^>]+>', '', body)  # Strip HTML
                snippet = (body[:300] + '...') if len(body) > 300 else body
                
                if url:
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet or 'Stack Exchange Q&A',
                        'source': 'Stack Exchange'
                    })
            
            return results
        except Exception as e:
            print(f"  Warning: Stack Exchange search failed: {e}")
            return []
    
    def _search_hackernews(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Search Hacker News using Algolia API.
        """
        try:
            url = "https://hn.algolia.com/api/v1/search"
            params = {
                'query': query,
                'tags': 'story',
                'hitsPerPage': max_results
            }
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            results = []
            
            for hit in data.get('hits', []):
                title = hit.get('title', 'Untitled')
                story_url = hit.get('url', '')
                object_id = hit.get('objectID', '')
                
                # Prefer external URL, fallback to HN discussion
                if not story_url:
                    story_url = f"https://news.ycombinator.com/item?id={object_id}"
                
                # Get excerpt from story text
                story_text = hit.get('story_text', '') or hit.get('_highlightResult', {}).get('title', {}).get('value', '')
                import re
                story_text = re.sub(r'<[^>]+>', '', story_text)
                snippet = (story_text[:300] + '...') if len(story_text) > 300 else (story_text or 'Hacker News discussion')
                
                if story_url:
                    results.append({
                        'title': title,
                        'url': story_url,
                        'snippet': snippet,
                        'source': 'Hacker News'
                    })
            
            return results
        except Exception as e:
            print(f"  Warning: Hacker News search failed: {e}")
            return []
    
    # ========================================
    # Category 8: Documentation / Standards
    # ========================================
    
    def _search_readthedocs(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Search Read the Docs for documentation.
        Note: This searches across all RTD-hosted documentation.
        """
        try:
            # Use Read the Docs search API
            url = "https://readthedocs.org/api/v3/search/"
            params = {
                'q': query,
                'page_size': max_results
            }
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            results = []
            
            for item in data.get('results', []):
                title = item.get('title', 'Untitled')
                project = item.get('project', {})
                project_name = project.get('name', '')
                
                # Build snippet from blocks
                blocks = item.get('blocks', [])
                snippet_parts = []
                for block in blocks[:2]:
                    content = block.get('content', '')
                    if content:
                        snippet_parts.append(content)
                snippet = ' '.join(snippet_parts)[:300]
                if not snippet:
                    snippet = f"Documentation for {project_name}"
                
                # Get URL
                url = item.get('link', '')
                
                if url:
                    results.append({
                        'title': f"{title} ({project_name})",
                        'url': url,
                        'snippet': snippet,
                        'source': 'Read the Docs'
                    })
            
            return results
        except Exception as e:
            print(f"  Warning: Read the Docs search failed: {e}")
            return []
    
    def _search_w3c(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Search W3C specifications and standards.
        """
        try:
            # W3C doesn't have a direct search API, use their spec list + filtering
            url = "https://www.w3.org/TR/tr.json"
            
            response = self.session.get(url, timeout=20)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            results = []
            query_lower = query.lower()
            
            # Filter specifications by query match
            for spec in data:
                title = spec.get('title', '')
                shortname = spec.get('shortname', '')
                
                # Check if query matches title or shortname
                if query_lower in title.lower() or query_lower in shortname.lower():
                    url = spec.get('url', '')
                    description = spec.get('description', f"W3C {spec.get('type', 'specification')}")
                    
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': description[:300],
                        'source': 'W3C'
                    })
                    
                    if len(results) >= max_results:
                        break
            
            return results
        except Exception as e:
            print(f"  Warning: W3C search failed: {e}")
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
