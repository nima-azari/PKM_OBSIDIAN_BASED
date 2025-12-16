#!/usr/bin/env python3
"""
Automated Source Discovery

Automatically searches the web for sources based on discovery report queries.
Uses free APIs (arXiv, Semantic Scholar) to find relevant articles.
Saves discovered URLs to a file for manual review before importing.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple
import time
from datetime import datetime
from fuzzywuzzy import fuzz
import re
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.web_discovery import WebDiscovery

# Import semantic models (lazy load) - supports both PyTorch and TensorFlow
SEMANTIC_MODEL_AVAILABLE = False
semantic_model = None
semantic_backend = None  # 'pytorch', 'tensorflow', or None

def load_semantic_model():
    """Lazy load semantic similarity model - tries TensorFlow first, then PyTorch."""
    global SEMANTIC_MODEL_AVAILABLE, semantic_model, semantic_backend
    
    if not SEMANTIC_MODEL_AVAILABLE:
        # Try TensorFlow Hub's Universal Sentence Encoder first (more stable)
        try:
            import tensorflow_hub as hub
            import tensorflow as tf
            # Suppress TF warnings
            tf.get_logger().setLevel('ERROR')
            
            print("   Loading TensorFlow Hub Universal Sentence Encoder...")
            semantic_model = hub.load("https://tfhub.dev/google/universal-sentence-encoder/4")
            SEMANTIC_MODEL_AVAILABLE = True
            semantic_backend = 'tensorflow'
            print("✓ Loaded semantic model (TensorFlow - Universal Sentence Encoder)")
            return True
        except Exception as e:
            print(f"   TensorFlow model unavailable: {e}")
        
        # Fallback: Try PyTorch-based sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer
            print("   Loading PyTorch sentence-transformers...")
            semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
            SEMANTIC_MODEL_AVAILABLE = True
            semantic_backend = 'pytorch'
            print("✓ Loaded semantic model (PyTorch - all-MiniLM-L6-v2)")
            return True
        except Exception as e:
            print(f"   PyTorch model unavailable: {e}")
        
        print("⚠️  No semantic model available - using keyword filtering only")
        SEMANTIC_MODEL_AVAILABLE = False
        semantic_backend = None
        return False
    
    return SEMANTIC_MODEL_AVAILABLE


class AutoSourceDiscovery:
    """Automated source discovery using free search APIs."""
    
    def __init__(self, sources_dir: str = "data/sources", verbose: bool = True):
        self.verbose = verbose
        self.sources_dir = Path(sources_dir)
        self.web_discovery = WebDiscovery()
        self.discovered_urls = []
        self.query_results = {}
        self.existing_sources = []
        self.filtered_count = 0
        self.semantic_filtered_count = 0
        
        # Caches for semantic filtering
        self.existing_embeddings = []
        self.domain_embedding = None
        
        # Load existing sources for fuzzy matching
        self._load_existing_sources()
    
    def load_queries_from_report(self, report_path: str) -> List[Dict[str, Any]]:
        """Extract search queries with coverage scores from discovery report.
        
        Returns:
            List of dicts with keys: 'query', 'topic', 'score' (0-100)
        """
        
        if self.verbose:
            print(f"\n📄 Loading queries from: {report_path}")
        
        # Parse coverage scores first
        coverage_scores = {}  # topic -> score
        with open(report_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Extract coverage scores (e.g., "Vendor Lock-in: LOW (14/100)")
        for line in lines:
            if "LOW (" in line or "MEDIUM (" in line or "HIGH (" in line:
                import re
                match = re.match(r'\s+(.+?):\s+\w+\s+\((\d+)/100\)', line)
                if match:
                    topic = match.group(1).strip()
                    score = int(match.group(2))
                    coverage_scores[topic] = score
        
        queries = []
        
        # Find "Recommended Search Queries" section
        in_queries_section = False
        for line in lines:
            if "## Recommended Search Queries" in line:
                in_queries_section = True
                continue
            
            if in_queries_section:
                # Stop at next section
                if line.strip().startswith("##"):
                    break
                
                # Extract query (format: "  1. Query text")
                line = line.strip()
                if line and not line.startswith("##"):
                    # Remove numbering (1., 2., etc.)
                    import re
                    match = re.match(r'^\d+\.\s*(.+)$', line)
                    if match:
                        query_text = match.group(1).strip()
                        
                        # Try to match query to a topic based on keywords
                        query_lower = query_text.lower()
                        matched_topic = None
                        matched_score = 50  # Default medium priority
                        
                        for topic, score in coverage_scores.items():
                            topic_lower = topic.lower()
                            # Check if topic keywords appear in query
                            if topic_lower in query_lower:
                                matched_topic = topic
                                matched_score = score
                                break
                        
                        queries.append({
                            'query': query_text,
                            'topic': matched_topic or "General",
                            'score': matched_score
                        })
        
        if self.verbose:
            print(f"✓ Loaded {len(queries)} queries with priorities")
            for i, q in enumerate(queries, 1):
                priority = "HIGH" if q['score'] < 30 else "MEDIUM" if q['score'] < 50 else "LOW"
                print(f"   {i}. [{priority}] {q['query']}")
            print()
        
        return queries
    
    def load_queries_from_report_legacy(self, report_path: str) -> List[str]:
        """Legacy method returning only query strings."""
        queries_with_meta = self.load_queries_from_report(report_path)
        return [q['query'] for q in queries_with_meta]
    
    def _old_code(self):
        """Placeholder for old code - can be removed"""
        if self.verbose:
            print(f"✓ Loaded {len([])} queries")
            for i, query in enumerate([], 1):
                print(f"   {i}. {query}")
        
        return queries
    
    def _load_existing_sources(self):
        """Load existing source files for duplicate detection."""
        
        if not self.sources_dir.exists():
            return
        
        if self.verbose:
            print(f"\n📂 Loading existing sources from: {self.sources_dir}")
        
        for ext in ['.md', '.txt', '.pdf', '.html', '.htm']:
            for filepath in self.sources_dir.glob(f'**/*{ext}'):
                try:
                    # Extract title and URL from file
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(2000)  # First 2000 chars
                    
                    # Extract title (first heading or filename)
                    title = filepath.stem
                    
                    # Try to extract title from content
                    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                    if title_match:
                        title = title_match.group(1).strip()
                    
                    # Try to extract URL from frontmatter or content
                    url = None
                    url_match = re.search(r'url:\s*(.+)$', content, re.MULTILINE | re.IGNORECASE)
                    if url_match:
                        url = url_match.group(1).strip()
                    
                    # Extract a snippet of actual content for semantic analysis
                    # Remove frontmatter and get first few paragraphs
                    content_clean = re.sub(r'^---.*?---', '', content, flags=re.DOTALL)
                    content_clean = re.sub(r'#+ ', '', content_clean)  # Remove markdown headers
                    content_clean = ' '.join(content_clean.split())[:500]  # First 500 chars
                    
                    self.existing_sources.append({
                        'filepath': str(filepath),
                        'title': title,
                        'url': url,
                        'content': content_clean  # Add content for semantic analysis
                    })
                
                except Exception as e:
                    if self.verbose:
                        print(f"  Warning: Could not read {filepath}: {e}")
                    continue
        
        if self.verbose:
            print(f"✓ Loaded {len(self.existing_sources)} existing sources")
    
    def _is_duplicate(self, title: str, url: str, similarity_threshold: int = 85) -> Tuple[bool, str]:
        """
        Check if article is duplicate using fuzzy matching.
        
        Args:
            title: Article title
            url: Article URL
            similarity_threshold: Minimum similarity score (0-100)
            
        Returns:
            Tuple of (is_duplicate, reason)
        """
        
        # Check exact URL match
        if url:
            for existing in self.existing_sources:
                if existing['url'] and existing['url'] == url:
                    return True, f"Exact URL match: {existing['filepath']}"
        
        # Check fuzzy title match
        for existing in self.existing_sources:
            similarity = fuzz.ratio(title.lower(), existing['title'].lower())
            
            if similarity >= similarity_threshold:
                return True, f"Title similarity {similarity}% with: {existing['filepath']}"
        
        return False, ""
    
    def _compute_domain_embedding(self):
        """Compute aggregate embedding representing the existing knowledge domain."""
        
        if not load_semantic_model():
            return None
        
        if self.verbose:
            print("\n🧠 Computing domain embedding from existing sources...")
        
        # Collect text samples from existing sources (title + content snippet)
        texts = []
        for source in self.existing_sources[:20]:  # Use up to 20 sources
            text = f"{source['title']}. {source.get('content', '')[:200]}"
            texts.append(text)
        
        if not texts:
            if self.verbose:
                print("   ⚠️  No existing sources found for domain embedding")
            return None
        
        # Compute embeddings (backend-specific)
        try:
            if semantic_backend == 'tensorflow':
                # TensorFlow Hub - batch processing
                embeddings = semantic_model(texts).numpy()
            elif semantic_backend == 'pytorch':
                # PyTorch sentence-transformers
                embeddings = semantic_model.encode(texts, convert_to_numpy=True)
            else:
                return None
        except Exception as e:
            if self.verbose:
                print(f"   ⚠️  Failed to compute embeddings: {e}")
            return None
        
        if len(embeddings) > 0:
            # Average embeddings to represent domain
            self.domain_embedding = np.mean(embeddings, axis=0)
            
            if self.verbose:
                print(f"   ✓ Domain embedding computed from {len(embeddings)} sources")
                print(f"   Embedding shape: {self.domain_embedding.shape}")
                print(f"   Sample sources: {', '.join([s['title'][:40] for s in self.existing_sources[:3]])}")
            
            return self.domain_embedding
        
        return None
    
    def _compute_text_embedding(self, text: str) -> np.ndarray:
        """Compute embedding for text - supports both TensorFlow and PyTorch backends."""
        
        if not SEMANTIC_MODEL_AVAILABLE or not text:
            return None
        
        try:
            if semantic_backend == 'tensorflow':
                # TensorFlow Hub Universal Sentence Encoder
                embeddings = semantic_model([text]).numpy()
                return embeddings[0] if len(embeddings) > 0 else None
            elif semantic_backend == 'pytorch':
                # PyTorch sentence-transformers
                embedding = semantic_model.encode([text], convert_to_numpy=True)
                return embedding[0] if len(embedding) > 0 else None
        except Exception as e:
            if self.verbose:
                print(f"   Warning: Embedding computation failed: {e}")
            return None
        
        return None
    
    def _semantic_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Compute cosine similarity between two embeddings."""
        
        if embedding1 is None or embedding2 is None:
            return 0.0
        
        # Cosine similarity
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return float(similarity)
    
    def _is_keyword_relevant(self, title: str, snippet: str) -> Tuple[bool, str]:
        """
        Fallback keyword-based relevance check when semantic model unavailable.
        Filters out obviously irrelevant papers based on domain keywords.
        
        Returns:
            Tuple of (is_relevant, reason)
        """
        text = f"{title} {snippet}".lower()
        
        # Define domain keywords from existing sources
        domain_keywords = [
            'data', 'eu', 'regulation', 'gdpr', 'governance', 'quality',
            'semantic', 'web', 'linked', 'rdf', 'ontology', 'knowledge',
            'graph', 'interoperability', 'portability', 'vendor', 'lock-in',
            'cloud', 'api', 'standard', 'compliance', 'policy', 'legal'
        ]
        
        # Irrelevant domains to filter out
        irrelevant_keywords = [
            'astrophysics', 'astronomy', 'cosmology', 'dark energy', 'galaxy',
            'particle physics', 'quantum', 'chemistry', 'biology', 'medical',
            'clinical', 'patient', 'disease', 'drug', 'therapy', 'genome',
            'protein', 'molecular', 'neural network', 'image classification',
            'computer vision', 'robotics', 'autonomous vehicle', 'drone',
            'cryptocurrency', 'blockchain mining', 'weather', 'climate model',
            'earthquake', 'geology', 'material science', 'manufacturing'
        ]
        
        # Check for irrelevant keywords first (strong filter)
        irrelevant_matches = [kw for kw in irrelevant_keywords if kw in text]
        if len(irrelevant_matches) >= 2:  # At least 2 irrelevant keywords
            return False, f"Irrelevant domain: {', '.join(irrelevant_matches[:2])}"
        
        # Check for domain keyword presence (weak requirement)
        domain_matches = [kw for kw in domain_keywords if kw in text]
        if len(domain_matches) >= 1:  # At least 1 domain keyword
            return True, f"Keyword match: {', '.join(domain_matches[:3])}"
        
        # If no clear signal, accept (conservative filtering)
        return True, "No strong irrelevance signal"
    
    def _is_semantically_relevant(
        self, 
        title: str, 
        snippet: str,
        domain_similarity_threshold: float = 0.5,
        diversity_threshold: float = 0.85
    ) -> Tuple[bool, str]:
        """
        Check if article is semantically relevant to the domain and diverse enough.
        
        Args:
            title: Article title
            snippet: Article snippet/abstract
            domain_similarity_threshold: Minimum similarity to domain (0-1)
            diversity_threshold: Maximum similarity to existing sources (0-1)
            
        Returns:
            Tuple of (is_relevant, reason)
        """
        
        if not SEMANTIC_MODEL_AVAILABLE or self.domain_embedding is None:
            # Fallback: Use keyword-based filtering when semantic model unavailable
            return self._is_keyword_relevant(title, snippet)
        
        # Combine title and snippet for analysis
        text = f"{title}. {snippet[:200]}"
        
        # Compute embedding
        embedding = self._compute_text_embedding(text)
        if embedding is None:
            return True, ""
        
        # Check domain relevance
        domain_sim = self._semantic_similarity(embedding, self.domain_embedding)
        
        if domain_sim < domain_similarity_threshold:
            return False, f"Low domain relevance: {domain_sim:.2f} < {domain_similarity_threshold}"
        
        # Check diversity (shouldn't be too similar to existing sources)
        if len(self.existing_embeddings) > 0:
            max_sim = max([self._semantic_similarity(embedding, existing_emb) 
                          for existing_emb in self.existing_embeddings])
            
            if max_sim > diversity_threshold:
                return False, f"Too similar to existing source: {max_sim:.2f} > {diversity_threshold}"
        
        return True, f"Domain similarity: {domain_sim:.2f}"
    
    def _build_embedding_cache(self):
        """Build cache of embeddings for existing sources."""
        
        if not load_semantic_model():
            return
        
        if self.verbose:
            print("\n🔄 Building embedding cache for existing sources...")
        
        # Build text samples (title + content snippet)
        texts = []
        for source in self.existing_sources:
            text = f"{source['title']}. {source.get('content', '')[:200]}"
            texts.append(text)
        
        if texts:
            # Batch encode for efficiency
            embeddings = semantic_model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            self.existing_embeddings = [emb for emb in embeddings]
            
            if self.verbose:
                print(f"   ✓ Cached {len(self.existing_embeddings)} embeddings")
    
    def _search_openalex(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Search OpenAlex API for scholarly papers."""
        import requests
        
        results = []
        try:
            # OpenAlex API endpoint
            url = "https://api.openalex.org/works"
            params = {
                'search': query,
                'per_page': max_results,
                'filter': 'is_oa:true',  # Open access only
                'sort': 'cited_by_count:desc'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for work in data.get('results', []):
                    title = work.get('title', 'Untitled')
                    doi = work.get('doi', '')
                    url = work.get('primary_location', {}).get('landing_page_url', doi)
                    abstract = work.get('abstract_inverted_index', {})
                    
                    # Reconstruct abstract from inverted index
                    snippet = "No abstract available"
                    if abstract:
                        words = []
                        for word, positions in abstract.items():
                            for pos in positions:
                                words.append((pos, word))
                        words.sort()
                        snippet = ' '.join([w[1] for w in words])[:300]
                    
                    if url:
                        results.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet,
                            'source': 'OpenAlex'
                        })
            
        except Exception as e:
            if self.verbose:
                print(f"  Warning: OpenAlex search failed: {e}")
        
        return results
    
    def _search_core(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Search CORE API for open access papers."""
        import requests
        
        results = []
        try:
            url = "https://core.ac.uk/api-v2/search"
            params = {
                'query': query,
                'page': 1,
                'pageSize': max_results
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get('data', []):
                    title = item.get('title', 'Untitled')
                    url = item.get('downloadUrl') or item.get('urls', [''])[0]
                    abstract = item.get('description', '') or item.get('abstract', '')
                    snippet = abstract[:300] + '...' if len(abstract) > 300 else abstract
                    
                    if url and title:
                        results.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet,
                            'source': 'CORE'
                        })
            
        except Exception as e:
            if self.verbose:
                print(f"  Warning: CORE search failed: {e}")
        
        return results
    
    def search_all_sources(
        self, 
        query: str, 
        max_per_source: int = 5
    ) -> List[Dict[str, str]]:
        """
        Search all available free sources for a query.
        
        Args:
            query: Search query
            max_per_source: Maximum results per source
            
        Returns:
            List of result dicts with 'title', 'url', 'snippet', 'source'
        """
        all_results = []
        
        if self.verbose:
            print(f"\n🔍 Searching: {query}")
        
        # Priority 1: EU-specific sources (critical for EU Data Act domain)
        if self.verbose:
            print("   🇪🇺 Searching EUR-Lex...")
        
        try:
            eurlex_results = self.web_discovery._search_eurlex(query, max_per_source)
            if eurlex_results:
                all_results.extend(eurlex_results)
                if self.verbose:
                    print(f"      ✓ Found {len(eurlex_results)} results")
            else:
                if self.verbose:
                    print("      ✗ No results")
        except Exception as e:
            if self.verbose:
                print(f"      ✗ Error: {e}")
        
        time.sleep(0.5)
        
        # Priority 2: Open scholarly sources (broad coverage)
        if self.verbose:
            print("   🌐 Searching OpenAlex...")
        
        try:
            openalex_results = self._search_openalex(query, max_per_source)
            if openalex_results:
                all_results.extend(openalex_results)
                if self.verbose:
                    print(f"      ✓ Found {len(openalex_results)} results")
            else:
                if self.verbose:
                    print("      ✗ No results")
        except Exception as e:
            if self.verbose:
                print(f"      ✗ Error: {e}")
        
        time.sleep(0.5)
        
        if self.verbose:
            print("   📖 Searching CORE...")
        
        try:
            core_results = self._search_core(query, max_per_source)
            if core_results:
                all_results.extend(core_results)
                if self.verbose:
                    print(f"      ✓ Found {len(core_results)} results")
            else:
                if self.verbose:
                    print("      ✗ No results")
        except Exception as e:
            if self.verbose:
                print(f"      ✗ Error: {e}")
        
        time.sleep(0.5)
        
        if self.verbose:
            print("   🔬 Searching HAL...")
        
        try:
            hal_results = self.web_discovery._search_hal(query, max_per_source)
            if hal_results:
                all_results.extend(hal_results)
                if self.verbose:
                    print(f"      ✓ Found {len(hal_results)} results")
            else:
                if self.verbose:
                    print("      ✗ No results")
        except Exception as e:
            if self.verbose:
                print(f"      ✗ Error: {e}")
        
        time.sleep(0.5)
        
        if self.verbose:
            print("   📦 Searching Zenodo...")
        
        try:
            zenodo_results = self.web_discovery._search_zenodo(query, max_per_source)
            if zenodo_results:
                all_results.extend(zenodo_results)
                if self.verbose:
                    print(f"      ✓ Found {len(zenodo_results)} results")
            else:
                if self.verbose:
                    print("      ✗ No results")
        except Exception as e:
            if self.verbose:
                print(f"      ✗ Error: {e}")
        
        time.sleep(0.5)
        
        # Priority 3: Open access journals
        if self.verbose:
            print("   📄 Searching DOAJ...")
        
        try:
            doaj_results = self.web_discovery._search_doaj(query, max_per_source)
            if doaj_results:
                all_results.extend(doaj_results)
                if self.verbose:
                    print(f"      ✓ Found {len(doaj_results)} results")
            else:
                if self.verbose:
                    print("      ✗ No results")
        except Exception as e:
            if self.verbose:
                print(f"      ✗ Error: {e}")
        
        time.sleep(0.5)
        
        # Priority 4: Traditional academic sources
        if self.verbose:
            print("   📚 Searching arXiv...")
        
        try:
            arxiv_results = self.web_discovery._search_arxiv(query, max_per_source)
            if arxiv_results:
                all_results.extend(arxiv_results)
                if self.verbose:
                    print(f"      ✓ Found {len(arxiv_results)} results")
            else:
                if self.verbose:
                    print("      ✗ No results")
        except Exception as e:
            if self.verbose:
                print(f"      ✗ Error: {e}")
        
        time.sleep(0.5)
        
        if self.verbose:
            print("   🎓 Searching Semantic Scholar...")
        
        try:
            scholar_results = self.web_discovery._search_semantic_scholar(query, max_per_source)
            if scholar_results:
                all_results.extend(scholar_results)
                if self.verbose:
                    print(f"      ✓ Found {len(scholar_results)} results")
            else:
                if self.verbose:
                    print("      ✗ No results")
        except Exception as e:
            if self.verbose:
                print(f"      ✗ Error: {e}")
        
        time.sleep(0.5)
        
        return all_results
    
    def run_discovery(
        self, 
        queries, 
        max_per_source: int = 5,
        min_quality_score: int = 0,
        filter_duplicates: bool = True,
        similarity_threshold: int = 85,
        min_new_sources: int = 10,
        max_query_iterations: int = 3,
        semantic_filter: bool = True,
        domain_similarity_threshold: float = 0.5,
        diversity_threshold: float = 0.85
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Run discovery for all queries with duplicate filtering, semantic filtering, and dynamic query generation.
        
        Accepts queries as either:
        - List[str]: Raw query strings
        - List[Dict]: Dicts with 'query', 'topic', 'score' keys
        
        Args:
            queries: List of search queries (strings or dicts with metadata)
            max_per_source: Maximum results per source per query
            min_quality_score: Minimum quality score to include (0-10, currently unused)
            filter_duplicates: Whether to filter duplicate sources
            similarity_threshold: Minimum similarity score for duplicate detection (0-100)
            min_new_sources: Minimum new sources needed before stopping
            max_query_iterations: Maximum iterations for generating additional queries
            semantic_filter: Whether to use semantic filtering
            domain_similarity_threshold: Minimum semantic similarity to domain (0-1)
            diversity_threshold: Maximum similarity to existing sources (0-1)
            
        Returns:
            Dict mapping query to list of results (with priority metadata)
        """
        
        # Convert queries to metadata format if needed
        query_metadata = {}
        query_strings = []
        for q in queries:
            if isinstance(q, dict):
                query_str = q['query']
                query_metadata[query_str] = {'score': q.get('score', 50), 'topic': q.get('topic', 'General')}
                query_strings.append(query_str)
            else:
                query_str = q
                query_metadata[query_str] = {'score': 50, 'topic': 'General'}
                query_strings.append(query_str)
        
        if self.verbose:
            print("\n" + "="*60)
            print("AUTOMATED SOURCE DISCOVERY WITH SEMANTIC FILTERING")
            print("="*60)
            if filter_duplicates:
                print(f"   Existing sources: {len(self.existing_sources)}")
                print(f"   Title similarity threshold: {similarity_threshold}%")
                print(f"   Target new sources: {min_new_sources}")
            if semantic_filter:
                print(f"   Semantic filtering: ENABLED")
                print(f"   Domain similarity threshold: {domain_similarity_threshold}")
                print(f"   Diversity threshold: {diversity_threshold}")
            print(f"   Query priorities (coverage scores):")
            for query_str in sorted(query_strings, key=lambda q: query_metadata[q]['score']):
                priority = "🔴 HIGH" if query_metadata[query_str]['score'] < 30 else "🟡 MEDIUM" if query_metadata[query_str]['score'] < 50 else "🟢 LOW"
                print(f"      {priority} [{query_metadata[query_str]['score']:3d}] {query_metadata[query_str]['topic']}")
        
        # Initialize semantic filtering
        if semantic_filter:
            self._build_embedding_cache()
            self._compute_domain_embedding()
        
        all_results = {}
        iteration = 0
        current_queries = query_strings[:]
        
        while iteration < max_query_iterations:
            iteration += 1
            
            if self.verbose and iteration > 1:
                print(f"\n{'='*60}")
                print(f"ITERATION {iteration}: Generating additional queries")
                print(f"{'='*60}")
            
            for i, query in enumerate(current_queries, 1):
                if self.verbose:
                    priority = "🔴 HIGH" if query_metadata[query]['score'] < 30 else "🟡 MEDIUM" if query_metadata[query]['score'] < 50 else "🟢 LOW"
                    print(f"\n[Query {i}/{len(current_queries)}] {priority} [{query_metadata[query]['score']:3d}] {query_metadata[query]['topic']}")
                
                results = self.search_all_sources(query, max_per_source)
                
                if results:
                    # Filter duplicates and apply semantic filtering
                    filtered_results = []
                    
                    for result in results:
                        # Fuzzy duplicate detection
                        if filter_duplicates:
                            is_dup, reason = self._is_duplicate(result['title'], result['url'], similarity_threshold)
                            
                            if is_dup:
                                self.filtered_count += 1
                                if self.verbose:
                                    print(f"   🔄 Skipped duplicate: {result['title'][:60]}...")
                                    print(f"      Reason: {reason}")
                                continue
                        
                        # Semantic filtering
                        if semantic_filter and SEMANTIC_MODEL_AVAILABLE:
                            is_relevant, reason = self._is_semantically_relevant(
                                result['title'], 
                                result['snippet'],
                                domain_similarity_threshold,
                                diversity_threshold
                            )
                            
                            if not is_relevant:
                                self.semantic_filtered_count += 1
                                if self.verbose:
                                    print(f"   🧠 Filtered: {result['title'][:60]}...")
                                    print(f"      {reason}")
                                continue
                            elif self.verbose:
                                print(f"   ✅ Accepted: {result['title'][:60]}...")
                                print(f"      {reason}")
                        
                        # Add priority score metadata to result
                        result['priority_score'] = query_metadata[query]['score']
                        result['priority_topic'] = query_metadata[query]['topic']
                        filtered_results.append(result)
                        
                        # Add to discovered URLs
                        if result['url'] and result['url'] not in self.discovered_urls:
                            self.discovered_urls.append(result['url'])
                            
                            # Cache embedding for diversity checking in next iterations
                            if semantic_filter and SEMANTIC_MODEL_AVAILABLE:
                                embedding = self._compute_text_embedding(f"{result['title']}. {result['snippet'][:200]}")
                                if embedding is not None:
                                    self.existing_embeddings.append(embedding)
                    
                    if filtered_results:
                        if query in all_results:
                            all_results[query].extend(filtered_results)
                        else:
                            all_results[query] = filtered_results
                else:
                    if self.verbose:
                        print("   ⚠️  No results found for this query")
            
            # Check if we have enough new sources
            new_sources_count = len(self.discovered_urls)
            
            if self.verbose:
                print(f"\n{'='*60}")
                print(f"Iteration {iteration} Complete")
                print(f"   New sources found: {new_sources_count}")
                print(f"   Fuzzy duplicates filtered: {self.filtered_count}")
                if semantic_filter:
                    print(f"   Semantic filtered: {self.semantic_filtered_count}")
                print(f"{'='*60}")
            
            # Stop if we have enough new sources
            if new_sources_count >= min_new_sources:
                break
            
            # Generate more queries if needed
            if iteration < max_query_iterations and new_sources_count < min_new_sources:
                if self.verbose:
                    print(f"\n⚠️  Only {new_sources_count}/{min_new_sources} new sources found")
                    print("   Generating additional queries...")
                
                # Generate new queries based on existing results
                additional_queries = self._generate_additional_queries(
                    original_queries=queries,
                    current_results=all_results,
                    num_queries=3
                )
                
                if additional_queries:
                    current_queries = additional_queries
                    if self.verbose:
                        print(f"   ✓ Generated {len(additional_queries)} new queries")
                        for j, q in enumerate(additional_queries, 1):
                            print(f"      {j}. {q}")
                else:
                    if self.verbose:
                        print("   ✗ Could not generate more queries, stopping")
                    break
            else:
                break
        
        self.query_results = all_results
        
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"✅ Discovery Complete")
            print(f"   Total new URLs: {len(self.discovered_urls)}")
            print(f"   Fuzzy duplicates filtered: {self.filtered_count}")
            if semantic_filter:
                print(f"   Semantic filtered: {self.semantic_filtered_count}")
                total_filtered = self.filtered_count + self.semantic_filtered_count
                if total_filtered > 0:
                    print(f"   Total filtered: {total_filtered} ({total_filtered*100//(total_filtered+len(self.discovered_urls))}%)")
            print(f"   Queries processed: {sum(1 for _ in all_results)}")
            print(f"   Iterations: {iteration}")
            print(f"{'='*60}")
        
        return all_results
    
    def _generate_additional_queries(
        self, 
        original_queries: List[str],
        current_results: Dict[str, List[Dict[str, str]]],
        num_queries: int = 3
    ) -> List[str]:
        """
        Generate additional search queries when initial results are insufficient.
        
        Args:
            original_queries: Original search queries
            current_results: Results found so far
            num_queries: Number of queries to generate
            
        Returns:
            List of new search queries
        """
        
        # Build context from original queries and found titles
        found_titles = []
        for results in current_results.values():
            for result in results[:3]:  # Top 3 per query
                found_titles.append(result['title'])
        
        prompt = f"""Based on these original research queries:
{chr(10).join([f"- {q}" for q in original_queries])}

And these articles we found:
{chr(10).join([f"- {t}" for t in found_titles[:10]])}

Generate {num_queries} NEW search queries that are:
1. Related to the same research domain but with different angles
2. More specific or explore sub-topics
3. Different enough to find NEW articles (not duplicates)
4. Focused on practical applications, case studies, or technical implementations

Return only the queries, one per line, without numbering."""
        
        try:
            from openai import OpenAI
            client = OpenAI()
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a research query expert. Generate diverse search queries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            queries = response.choices[0].message.content.strip().split('\n')
            queries = [q.strip('- ').strip('0123456789. ').strip() for q in queries if q.strip()]
            
            return queries[:num_queries]
        
        except Exception as e:
            if self.verbose:
                print(f"   ✗ Error generating queries: {e}")
            return []
    
    def save_urls(self, output_path: str = "data/discovered_urls.txt"):
        """Save discovered URLs prioritized by coverage score."""
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Collect all results with priority scores
        all_results_with_priority = []
        for query, results in self.query_results.items():
            for result in results:
                result_with_priority = result.copy()
                # Extract priority metadata if available, otherwise use defaults
                result_with_priority['priority_score'] = result.get('priority_score', 50)
                result_with_priority['priority_topic'] = result.get('priority_topic', 'General')
                result_with_priority['query'] = query
                all_results_with_priority.append(result_with_priority)
        
        # Sort by priority score (lowest = highest priority = biggest gap)
        all_results_with_priority.sort(key=lambda x: x['priority_score'])
        
        # Create header with metadata
        lines = []
        lines.append("# Automatically Discovered Source URLs (Priority-Ordered)")
        lines.append(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"# Total URLs: {len(self.discovered_urls)}")
        lines.append("#")
        lines.append("# Priority Legend (based on coverage gap scores):")
        lines.append("#   🔴 HIGH   (0-30):   Critical gaps - highest priority")
        lines.append("#   🟡 MEDIUM (30-60):  Moderate gaps - medium priority")
        lines.append("#   🟢 LOW    (60-100): Minor gaps - lower priority")
        lines.append("#")
        lines.append("# Instructions:")
        lines.append("#   1. Review URLs below (already sorted by priority)")
        lines.append("#   2. Remove irrelevant URLs (delete lines)")
        lines.append("#   3. Run: python import_urls.py " + str(output_path))
        lines.append("#")
        lines.append("")
        
        # Add URLs sorted by priority
        current_topic = None
        for result in all_results_with_priority:
            topic = result['priority_topic']
            score = result['priority_score']
            
            if topic != current_topic:
                lines.append("")
                priority_label = "🔴 HIGH" if score < 30 else "🟡 MEDIUM" if score < 60 else "🟢 LOW"
                lines.append(f"# {priority_label} PRIORITY - {topic} (coverage: {score}/100)")
                lines.append(f"# Query: {result['query']}")
                lines.append("#")
                current_topic = topic
            
            lines.append(f"# [{result['source']}] {result['title']}")
            lines.append(result['url'])
            lines.append("")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        
        if self.verbose:
            print(f"\n✅ Saved {len(self.discovered_urls)} prioritized URLs to: {output_path}")
            print(f"\nURLs organized by priority (coverage gap):")
            priority_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
            for result in all_results_with_priority:
                score = result['priority_score']
                if score < 30:
                    priority_counts['HIGH'] += 1
                elif score < 60:
                    priority_counts['MEDIUM'] += 1
                else:
                    priority_counts['LOW'] += 1
            print(f"   🔴 HIGH priority:   {priority_counts['HIGH']} URLs")
            print(f"   🟡 MEDIUM priority: {priority_counts['MEDIUM']} URLs")
            print(f"   🟢 LOW priority:    {priority_counts['LOW']} URLs")
            print(f"\nNext steps:")
            print(f"   1. Review: {output_path}")
            print(f"   2. Remove unwanted URLs")
            print(f"   3. Import: python import_urls.py {output_path}")
    
    def save_detailed_report(self, output_path: str = "data/discovery_results.txt"):
        """Save detailed report with snippets and metadata."""
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        lines = []
        lines.append("="*60)
        lines.append("AUTOMATED SOURCE DISCOVERY RESULTS")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("="*60)
        lines.append("")
        
        lines.append(f"## Summary")
        lines.append("")
        lines.append(f"  Total URLs discovered: {len(self.discovered_urls)}")
        lines.append(f"  Queries processed: {len(self.query_results)}")
        lines.append("")
        
        lines.append(f"## Results by Query")
        lines.append("")
        
        for i, (query, results) in enumerate(self.query_results.items(), 1):
            lines.append(f"### Query {i}: {query}")
            lines.append("")
            lines.append(f"Found {len(results)} results:")
            lines.append("")
            
            for j, result in enumerate(results, 1):
                lines.append(f"{j}. **{result['title']}**")
                lines.append(f"   Source: {result['source']}")
                lines.append(f"   URL: {result['url']}")
                lines.append(f"   Snippet: {result['snippet'][:200]}...")
                lines.append("")
            
            lines.append("-" * 60)
            lines.append("")
        
        lines.append("## All Unique URLs")
        lines.append("")
        for url in self.discovered_urls:
            lines.append(f"  - {url}")
        lines.append("")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        
        if self.verbose:
            print(f"✅ Saved detailed report to: {output_path}")
    
    def filter_by_relevance(self, min_score: int = 7) -> List[str]:
        """
        Filter URLs by relevance using AI assessment (optional, costs tokens).
        
        Args:
            min_score: Minimum relevance score (1-10)
            
        Returns:
            List of high-quality URLs
        """
        # Note: This would require extracting each URL and running quality assessment
        # For now, return all URLs (filtering can be done manually)
        if self.verbose:
            print(f"\n⚠️  Relevance filtering requires extracting all articles (time + API cost)")
            print(f"   Recommendation: Manually review discovered_urls.txt instead")
        
        return self.discovered_urls


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Automated source discovery from discovery report')
    parser.add_argument('--report', default='data/discovery_report.txt',
                        help='Path to discovery report with queries (default: data/discovery_report.txt)')
    parser.add_argument('--output', default='data/discovered_urls.txt',
                        help='Path to save discovered URLs (default: data/discovered_urls.txt)')
    parser.add_argument('--detailed-report', default='data/discovery_results.txt',
                        help='Path to save detailed report (default: data/discovery_results.txt)')
    parser.add_argument('--sources-dir', default='data/sources',
                        help='Directory with existing sources for duplicate detection (default: data/sources)')
    parser.add_argument('--max-per-source', type=int, default=10,
                        help='Maximum results per source per query (default: 10, increased for better coverage)')
    parser.add_argument('--similarity-threshold', type=int, default=85,
                        help='Similarity threshold for duplicate detection 0-100 (default: 85)')
    parser.add_argument('--min-new-sources', type=int, default=5,
                        help='Minimum new sources before stopping (default: 5, realistic for EU Data Act domain)')
    parser.add_argument('--max-iterations', type=int, default=3,
                        help='Maximum query generation iterations (default: 3)')
    parser.add_argument('--no-filter', action='store_true',
                        help='Disable duplicate filtering')
    parser.add_argument('--semantic-filter', action='store_true',
                        help='Enable semantic filtering using sentence-transformers')
    parser.add_argument('--domain-similarity', type=float, default=0.30,
                        help='Minimum semantic similarity to domain 0-1 (default: 0.30, permissive for interdisciplinary research)')
    parser.add_argument('--diversity-threshold', type=float, default=0.75,
                        help='Maximum similarity to existing sources 0-1 (default: 0.75, balanced novelty)')
    parser.add_argument('--queries', nargs='+',
                        help='Custom queries (overrides report queries)')
    
    args = parser.parse_args()
    
    # Create discovery engine
    discovery = AutoSourceDiscovery(sources_dir=args.sources_dir, verbose=True)
    
    # Load queries
    if args.queries:
        queries = args.queries
        print(f"Using {len(queries)} custom queries")
    else:
        queries = discovery.load_queries_from_report(args.report)
    
    if not queries:
        print("❌ No queries found. Provide --queries or ensure report has queries.")
        return
    
    # Run discovery
    results = discovery.run_discovery(
        queries, 
        max_per_source=args.max_per_source,
        filter_duplicates=not args.no_filter,
        similarity_threshold=args.similarity_threshold,
        min_new_sources=args.min_new_sources,
        max_query_iterations=args.max_iterations,
        semantic_filter=args.semantic_filter,
        domain_similarity_threshold=args.domain_similarity,
        diversity_threshold=args.diversity_threshold
    )
    
    # Save results
    discovery.save_urls(output_path=args.output)
    discovery.save_detailed_report(output_path=args.detailed_report)
    
    print(f"\n{'='*60}")
    print("✅ Automated discovery complete!")
    print(f"\nFiles created:")
    print(f"   1. {args.output} - URLs for import")
    print(f"   2. {args.detailed_report} - Full report with snippets")
    print(f"\nNext steps:")
    print(f"   1. Review URLs in {args.output}")
    print(f"   2. Remove unwanted URLs (optional)")
    print(f"   3. Import: python import_urls.py {args.output}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
