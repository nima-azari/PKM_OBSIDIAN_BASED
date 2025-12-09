"""
RAG (Retrieval-Augmented Generation) Engine.
Directory-based with caching for keywords, embeddings, and index.
Includes RDF/SPARQL graph capabilities.
"""

import os
import re
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

try:
    from rdflib import Graph, Namespace, RDF, RDFS, OWL, Literal, URIRef
    from rdflib.namespace import SKOS, DCTERMS
    import networkx as nx
    RDF_AVAILABLE = True
except ImportError:
    RDF_AVAILABLE = False


class Document:
    """Represents a document/note from the vault."""
    
    def __init__(self, path: str, content: str):
        self.path = path
        self.content = content
        self.title = self._extract_title()
        self.sections = self._split_sections()
        self.embedding = None
    
    def _extract_title(self) -> str:
        """Extract title from first # heading or filename."""
        lines = self.content.split('\n')
        for line in lines:
            if line.strip().startswith('# '):
                return line.strip()[2:].strip()
        # Fallback to filename
        return self.path.split('/')[-1].replace('.md', '')
    
    def _split_sections(self) -> List[Dict]:
        """Split document into sections by headings."""
        sections = []
        current_heading = "Introduction"
        current_content = []
        
        lines = self.content.split('\n')
        for line in lines:
            if line.strip().startswith('## '):
                # Save previous section
                if current_content:
                    sections.append({
                        'heading': current_heading,
                        'content': '\n'.join(current_content).strip()
                    })
                # Start new section
                current_heading = line.strip()[3:].strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_content:
            sections.append({
                'heading': current_heading,
                'content': '\n'.join(current_content).strip()
            })
        
        return sections


class VaultRAG:
    """RAG engine with directory-based loading and caching."""
    
    def __init__(
        self, 
        sources_dir: str = "data/sources",
        cache_dir: str = "data",
        verbose: bool = False
    ):
        self.sources_dir = Path(sources_dir)
        self.cache_dir = Path(cache_dir)
        self.verbose = verbose
        
        # Cache subdirectories
        self.keywords_cache = self.cache_dir / "keywords"
        self.embeddings_cache = self.cache_dir / "embeddings"
        self.index_cache = self.cache_dir / "index"
        self.graphs_cache = self.cache_dir / "graphs"
        
        # Ensure cache directories exist
        self.keywords_cache.mkdir(parents=True, exist_ok=True)
        self.embeddings_cache.mkdir(parents=True, exist_ok=True)
        self.index_cache.mkdir(parents=True, exist_ok=True)
        self.graphs_cache.mkdir(parents=True, exist_ok=True)
        
        self.documents: List[Document] = []
        self.client = None
        
        # RDF Graph components
        self.rdf_graph = None
        self.nx_graph = None
        if RDF_AVAILABLE:
            self.rdf_graph = Graph()
            self.nx_graph = nx.DiGraph()
            # Define namespaces
            self.NS = Namespace("http://pkm.local/sources/")
            self.ONTO = Namespace("http://pkm.local/ontology/")
            self.rdf_graph.bind("sources", self.NS)
            self.rdf_graph.bind("onto", self.ONTO)
            self.rdf_graph.bind("owl", OWL)
            self.rdf_graph.bind("skos", SKOS)
            self.rdf_graph.bind("dct", DCTERMS)
            self.rdf_graph.bind("rdfs", RDFS)
        
        if OPENAI_AVAILABLE and os.getenv('OPENAI_API_KEY'):
            self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        self._load_documents()
    
    def _get_file_hash(self, filepath: Path) -> str:
        """Get MD5 hash of file for cache invalidation."""
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            hasher.update(f.read())
        return hasher.hexdigest()
    
    def _load_documents(self):
        """Load all documents from sources directory."""
        if not self.sources_dir.exists():
            if self.verbose:
                print(f"Warning: Sources directory does not exist: {self.sources_dir}")
            self.sources_dir.mkdir(parents=True, exist_ok=True)
            return
        
        if self.verbose:
            print(f"Loading documents from {self.sources_dir}...")
        
        # Find all supported files
        supported_extensions = ['.md', '.txt', '.pdf', '.html', '.htm']
        files = []
        for ext in supported_extensions:
            files.extend(self.sources_dir.glob(f'**/*{ext}'))
        
        if self.verbose:
            print(f"Found {len(files)} files")
        
        for filepath in files:
            try:
                # Read content based on file type
                if filepath.suffix == '.pdf':
                    content = self._read_pdf(filepath)
                elif filepath.suffix in ['.html', '.htm']:
                    content = self._read_html(filepath)
                else:
                    content = filepath.read_text(encoding='utf-8', errors='ignore')
                
                # Create document with relative path from sources_dir
                rel_path = str(filepath.relative_to(self.sources_dir))
                doc = Document(rel_path, content)
                
                # Try to load cached embedding
                file_hash = self._get_file_hash(filepath)
                embedding_cache_file = self.embeddings_cache / f"{file_hash}.npy"
                
                if EMBEDDINGS_AVAILABLE and embedding_cache_file.exists():
                    try:
                        doc.embedding = np.load(embedding_cache_file)
                    except Exception as e:
                        if self.verbose:
                            print(f"  Warning: Could not load cached embedding: {e}")
                
                self.documents.append(doc)
                if self.verbose:
                    print(f"  ✓ Loaded: {doc.title}")
            except Exception as e:
                if self.verbose:
                    print(f"  ✗ Error loading {filepath}: {e}")
        
        if self.verbose:
            print(f"Loaded {len(self.documents)} documents\n")
    
    def _read_pdf(self, filepath: Path) -> str:
        """Extract text from PDF file."""
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(filepath))
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"  Warning: Could not read PDF {filepath}: {e}")
            return ""
    
    def _read_html(self, filepath: Path) -> str:
        """Extract text from HTML file."""
        try:
            from bs4 import BeautifulSoup
            import html2text
            
            with open(filepath, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Parse HTML
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Convert to markdown for better readability
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.body_width = 0
            markdown_content = h.handle(str(soup))
            
            return markdown_content.strip()
        except Exception as e:
            print(f"  Warning: Could not read HTML {filepath}: {e}")
            return ""
    
    def keyword_search(self, query: str, top_k: int = 5) -> List[Tuple[float, Document]]:
        """Simple keyword-based search."""
        query_lower = query.lower()
        query_terms = set(query_lower.split())
        
        results = []
        for doc in self.documents:
            content_lower = doc.content.lower()
            
            # Score based on term frequency and position
            score = 0
            
            # Title match (high weight)
            if query_lower in doc.title.lower():
                score += 10
            
            # Exact phrase match
            score += content_lower.count(query_lower) * 5
            
            # Individual term matches
            for term in query_terms:
                score += content_lower.count(term)
            
            if score > 0:
                results.append((score, doc))
        
        results.sort(reverse=True, key=lambda x: x[0])
        return results[:top_k]
    
    def semantic_search(self, query: str, top_k: int = 5) -> List[Tuple[float, Document]]:
        """Embedding-based semantic search with caching."""
        if not EMBEDDINGS_AVAILABLE or not self.client:
            print("Falling back to keyword search (embeddings not available)")
            return self.keyword_search(query, top_k)
        
        # Get query embedding
        query_embedding = self._get_embedding(query)
        
        # Compute or retrieve document embeddings with caching
        results = []
        for doc in self.documents:
            if doc.embedding is None:
                # Try to get from cache first
                doc_hash = hashlib.md5(doc.content[:8000].encode()).hexdigest()
                embedding_file = self.embeddings_cache / f"{doc_hash}.npy"
                
                if embedding_file.exists():
                    try:
                        doc.embedding = np.load(embedding_file)
                    except Exception as e:
                        print(f"Warning: Could not load cached embedding: {e}")
                        doc.embedding = self._get_embedding(doc.content[:8000])
                        np.save(embedding_file, doc.embedding)
                else:
                    # Compute and cache
                    doc.embedding = self._get_embedding(doc.content[:8000])
                    np.save(embedding_file, doc.embedding)
            
            similarity = cosine_similarity(
                [query_embedding],
                [doc.embedding]
            )[0][0]
            
            results.append((similarity, doc))
        
        results.sort(reverse=True, key=lambda x: x[0])
        return results[:top_k]
    
    def _get_embedding(self, text: str):
        """Get embedding from OpenAI."""
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return np.array(response.data[0].embedding)
    
    def ask(self, question: str, model: str = "gpt-4o-mini", use_semantic: bool = False) -> Dict:
        """
        Ask a question grounded in vault sources.
        Returns answer with citations.
        """
        if not self.client:
            return {
                "error": "OpenAI client not configured. Set OPENAI_API_KEY in .env",
                "answer": None,
                "sources": []
            }
        
        if self.verbose:
            print(f"\nQuestion: {question}\n")
            print("Retrieving relevant sources...")
        
        # Retrieve relevant documents
        if use_semantic:
            results = self.semantic_search(question, top_k=5)
        else:
            results = self.keyword_search(question, top_k=5)
        
        if not results:
            return {
                "answer": "No relevant sources found in the vault.",
                "sources": []
            }
        
        # Build context with source numbers
        context_parts = []
        sources = []
        
        for i, (score, doc) in enumerate(results, 1):
            context_parts.append(f"\n[Source {i}: {doc.title}]")
            context_parts.append(f"Path: {doc.path}")
            context_parts.append(f"\n{doc.content}\n")
            context_parts.append("-" * 80)
            
            sources.append({
                "title": doc.title,
                "path": doc.path,
                "score": float(score)
            })
            
            if self.verbose:
                print(f"  [{i}] {doc.title} (score: {score:.2f})")
        
        context = "\n".join(context_parts)
        
        # Generate answer
        if self.verbose:
            print("\nGenerating answer...")
        
        system_prompt = """You are a research assistant that answers questions based ONLY on the provided source documents.

Rules:
1. Only use information from the provided sources
2. Include citations like [1], [2], [3] referring to source numbers
3. If sources don't contain enough information, say so
4. Be precise and cite specific sources for each claim
5. Synthesize information across sources when relevant"""
        
        user_prompt = f"""Sources:
{context}

Question: {question}

Provide a comprehensive answer using only the information from the sources above. Include citations [1], [2], etc. for each fact."""
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3  # Lower temperature for factual responses
            )
            
            answer = response.choices[0].message.content
            
            return {
                "answer": answer,
                "sources": sources,
                "model": model
            }
        
        except Exception as e:
            return {
                "error": f"Error generating response: {str(e)}",
                "answer": None,
                "sources": sources
            }
    
    # === GRAPH RAG METHODS ===
    
    def build_knowledge_graph(self, enable_chunking: bool = True, enable_topics: bool = False) -> int:
        """
        Build RDF graph from loaded documents with full semantic model.
        
        Args:
            enable_chunking: Split documents into chunks (Information Layer)
            enable_topics: Auto-generate topic nodes from clustering (Topic Layer)
        
        Returns:
            Number of triples created
        """
        if not RDF_AVAILABLE:
            if self.verbose:
                print("Warning: RDF libraries not available. Install rdflib and networkx.")
            return 0
        
        if self.verbose:
            print(f"Building knowledge graph from {len(self.documents)} documents...")
            print(f"  Chunking: {'enabled' if enable_chunking else 'disabled'}")
            print(f"  Topic extraction: {'enabled' if enable_topics else 'disabled'}")
        
        # Process each document
        for doc in self.documents:
            if enable_chunking:
                self._add_document_with_chunks(doc)
            else:
                self._add_document_to_graph(doc)  # Legacy method
        
        # Extract relationships (wikilinks)
        for doc in self.documents:
            self._extract_relationships(doc)
        
        # Auto-generate topics if enabled
        if enable_topics:
            self._generate_topics()
        
        if self.verbose:
            print(f"Graph built: {len(self.rdf_graph)} triples")
        
        return len(self.rdf_graph)
    
    def _add_document_with_chunks(self, doc: Document):
        """Add document with full semantic model: chunks, domain concepts, metadata"""
        # Create URI for document
        doc_uri = self.NS[self._sanitize_uri(doc.title)]
        
        # === Document metadata ===
        self.rdf_graph.add((doc_uri, RDF.type, self.ONTO.Document))
        self.rdf_graph.add((doc_uri, RDFS.label, Literal(doc.title)))
        self.rdf_graph.add((doc_uri, self.ONTO.path, Literal(doc.path)))
        
        # Add source format
        source_format = self._detect_format(doc.path)
        if source_format:
            self.rdf_graph.add((doc_uri, self.ONTO.sourceFormat, Literal(source_format)))
        
        # Extract frontmatter
        frontmatter = self._extract_frontmatter(doc.content)
        
        # Add DCT metadata if available
        if 'title' in frontmatter:
            self.rdf_graph.add((doc_uri, DCTERMS.title, Literal(frontmatter['title'])))
        if 'author' in frontmatter:
            self.rdf_graph.add((doc_uri, DCTERMS.creator, Literal(frontmatter['author'])))
        if 'date' in frontmatter or 'created' in frontmatter:
            date_val = frontmatter.get('date') or frontmatter.get('created')
            self.rdf_graph.add((doc_uri, DCTERMS.created, Literal(date_val)))
        
        # Add tags
        for tag in frontmatter.get('tags', []):
            tag_uri = self.ONTO[self._sanitize_uri(tag)]
            self.rdf_graph.add((doc_uri, self.ONTO.hasTag, tag_uri))
            self.rdf_graph.add((tag_uri, RDF.type, self.ONTO.Tag))
            self.rdf_graph.add((tag_uri, RDFS.label, Literal(tag)))
        
        # === Chunking ===
        chunks = self._split_into_chunks(doc.content)
        domain_concepts = set()  # Collect concepts from this document
        
        for i, chunk_text in enumerate(chunks):
            chunk_uri = self.NS[f"{self._sanitize_uri(doc.title)}_chunk_{i}"]
            
            # Chunk instance
            self.rdf_graph.add((chunk_uri, RDF.type, self.ONTO.Chunk))
            self.rdf_graph.add((chunk_uri, self.ONTO.chunkIndex, Literal(i)))
            self.rdf_graph.add((chunk_uri, self.ONTO.chunkText, Literal(chunk_text)))
            
            # Link chunk to document
            self.rdf_graph.add((doc_uri, self.ONTO.hasChunk, chunk_uri))
            
            # Extract domain concepts from chunk
            concepts = self._extract_domain_concepts(chunk_text)
            for concept_label in concepts:
                concept_uri = self.ONTO[self._sanitize_uri(concept_label)]
                
                # Create DomainConcept if not exists
                if (concept_uri, RDF.type, self.ONTO.DomainConcept) not in self.rdf_graph:
                    self.rdf_graph.add((concept_uri, RDF.type, self.ONTO.DomainConcept))
                    self.rdf_graph.add((concept_uri, SKOS.prefLabel, Literal(concept_label)))
                
                # Link chunk to concept
                self.rdf_graph.add((chunk_uri, self.ONTO.mentionsConcept, concept_uri))
                domain_concepts.add(concept_uri)
        
        # === Legacy: Extract concepts from headings (backward compatibility) ===
        for section in doc.sections:
            heading = section.get('heading', '')
            if heading and heading != "Introduction":
                concept_uri = self.ONTO[self._sanitize_uri(heading)]
                # Use DomainConcept instead of Concept
                if (concept_uri, RDF.type, self.ONTO.DomainConcept) not in self.rdf_graph:
                    self.rdf_graph.add((concept_uri, RDF.type, self.ONTO.DomainConcept))
                    self.rdf_graph.add((concept_uri, SKOS.prefLabel, Literal(heading)))
                # Also add legacy mentions for backward compatibility
                self.rdf_graph.add((doc_uri, self.ONTO.mentions, concept_uri))
        
        # Add to NetworkX graph
        self.nx_graph.add_node(doc.title)
    
    def _split_into_chunks(self, text: str, chunk_size: int = 500) -> List[str]:
        """
        Split text into chunks for semantic processing.
        
        Args:
            text: Full document text
            chunk_size: Approximate number of tokens per chunk
        
        Returns:
            List of text chunks
        """
        # Remove frontmatter
        if text.startswith('---'):
            parts = text.split('---', 2)
            if len(parts) >= 3:
                text = parts[2]
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # Rough token count (words * 1.3)
            para_tokens = len(para.split()) * 1.3
            
            if current_length + para_tokens > chunk_size and current_chunk:
                # Save current chunk
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_length = para_tokens
            else:
                current_chunk.append(para)
                current_length += para_tokens
        
        # Add remaining chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks if chunks else [text[:1000]]  # Fallback: at least one chunk
    
    def _extract_domain_concepts(self, text: str) -> List[str]:
        """
        Extract domain concepts from text chunk.
        Uses simple heuristics: capitalized phrases, noun phrases from headings.
        
        For production, this could use NER or LLM-based extraction.
        """
        concepts = []
        
        # Extract markdown headings
        heading_pattern = r'^#{1,6}\s+(.+)$'
        for match in re.finditer(heading_pattern, text, re.MULTILINE):
            heading = match.group(1).strip()
            if len(heading) > 3 and heading != "Introduction":
                concepts.append(heading)
        
        # Extract capitalized phrases (2-4 words, basic heuristic)
        cap_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b'
        for match in re.finditer(cap_pattern, text):
            phrase = match.group(1)
            # Filter common words
            if not any(word in phrase.lower() for word in ['the', 'this', 'that', 'with', 'from']):
                if len(phrase) > 5:  # Minimum length
                    concepts.append(phrase)
        
        # Deduplicate
        return list(set(concepts))[:10]  # Limit to top 10 concepts per chunk
    
    def _detect_format(self, path: str) -> str:
        """Detect MIME type from file extension"""
        ext = Path(path).suffix.lower()
        format_map = {
            '.md': 'text/markdown',
            '.txt': 'text/plain',
            '.pdf': 'application/pdf',
            '.html': 'text/html',
            '.htm': 'text/html'
        }
        return format_map.get(ext, 'application/octet-stream')
    
    def _generate_topics(self):
        """
        Auto-generate TopicNode instances from clustering DomainConcepts.
        This is a basic implementation - production would use embeddings + clustering.
        """
        if self.verbose:
            print("  Generating topic nodes from domain concepts...")
        
        # Get all domain concepts
        concepts = list(self.rdf_graph.subjects(RDF.type, self.ONTO.DomainConcept))
        
        if len(concepts) < 3:
            if self.verbose:
                print("    Not enough concepts for topic generation")
            return
        
        # Simple grouping: one topic per 5-10 concepts
        # In production, use embeddings + k-means clustering
        topic_size = min(10, max(5, len(concepts) // 3))
        
        for i, concept_batch in enumerate([concepts[j:j+topic_size] 
                                           for j in range(0, len(concepts), topic_size)]):
            topic_uri = self.ONTO[f"topic_{i}"]
            
            # Get concept labels for topic naming
            labels = []
            for concept in concept_batch[:3]:  # First 3 concepts
                for label in self.rdf_graph.objects(concept, SKOS.prefLabel):
                    # Clean label: remove line breaks and extra whitespace
                    clean_label = str(label).replace('\n', ' ').replace('\r', ' ').strip()
                    clean_label = ' '.join(clean_label.split())  # Normalize whitespace
                    labels.append(clean_label)
            
            # Create readable topic label (max 80 chars)
            topic_label = f"Topic: {', '.join(labels[:2])}"
            if len(topic_label) > 80:
                topic_label = topic_label[:77] + "..."
            
            topic_def = f"Auto-generated topic covering {len(concept_batch)} domain concepts"
            
            # Add descriptive comment
            concept_names = ', '.join(labels[:5])
            if len(labels) > 5:
                concept_names += f" (and {len(labels)-5} more)"
            topic_comment = f"Clusters concepts: {concept_names}"
            
            # Create TopicNode
            self.rdf_graph.add((topic_uri, RDF.type, self.ONTO.TopicNode))
            self.rdf_graph.add((topic_uri, SKOS.prefLabel, Literal(topic_label)))
            self.rdf_graph.add((topic_uri, SKOS.definition, Literal(topic_def)))
            self.rdf_graph.add((topic_uri, RDFS.comment, Literal(topic_comment)))
            
            # Link topic to concepts
            for concept in concept_batch:
                self.rdf_graph.add((topic_uri, self.ONTO.coversConcept, concept))
            
            # Link topic to chunks that mention these concepts
            for concept in concept_batch:
                for chunk in self.rdf_graph.subjects(self.ONTO.mentionsConcept, concept):
                    self.rdf_graph.add((topic_uri, self.ONTO.coversChunk, chunk))
        
        if self.verbose:
            topics_count = len(list(self.rdf_graph.subjects(RDF.type, self.ONTO.TopicNode)))
            print(f"    Created {topics_count} topic nodes")
    
    def _add_document_to_graph(self, doc: Document):
        """Legacy: Add document as RDF resource (backward compatibility)"""
        # Create URI for document
        doc_uri = self.NS[self._sanitize_uri(doc.title)]
        
        # Add basic triples
        self.rdf_graph.add((doc_uri, RDF.type, self.ONTO.Document))
        self.rdf_graph.add((doc_uri, RDFS.label, Literal(doc.title)))
        self.rdf_graph.add((doc_uri, self.ONTO.path, Literal(doc.path)))
        
        # Extract and add tags from frontmatter
        frontmatter = self._extract_frontmatter(doc.content)
        for tag in frontmatter.get('tags', []):
            tag_uri = self.ONTO[self._sanitize_uri(tag)]
            self.rdf_graph.add((doc_uri, self.ONTO.hasTag, tag_uri))
            self.rdf_graph.add((tag_uri, RDF.type, self.ONTO.Tag))
            self.rdf_graph.add((tag_uri, RDFS.label, Literal(tag)))
        
        # Extract concepts from headers
        for section in doc.sections:
            heading = section.get('heading', '')
            if heading and heading != "Introduction":
                concept_uri = self.ONTO[self._sanitize_uri(heading)]
                self.rdf_graph.add((doc_uri, self.ONTO.mentions, concept_uri))
                self.rdf_graph.add((concept_uri, RDF.type, self.ONTO.Concept))
                self.rdf_graph.add((concept_uri, RDFS.label, Literal(heading)))
        
        # Add to NetworkX graph
        self.nx_graph.add_node(doc.title)
    
    def _extract_relationships(self, doc: Document):
        """Extract wikilinks as relationships"""
        doc_uri = self.NS[self._sanitize_uri(doc.title)]
        
        # Find wikilinks [[Target]]
        wikilinks = re.findall(r'\[\[([^\]]+)\]\]', doc.content)
        
        for link in wikilinks:
            target_title = link.split('|')[0]  # Handle [[Page|Alias]]
            target_uri = self.NS[self._sanitize_uri(target_title)]
            
            # Add link relationship
            self.rdf_graph.add((doc_uri, self.ONTO.linksTo, target_uri))
            
            # Add to NetworkX
            if target_title in [d.title for d in self.documents]:
                self.nx_graph.add_edge(doc.title, target_title)
    
    def _extract_frontmatter(self, content: str) -> Dict[str, Any]:
        """Extract YAML frontmatter"""
        frontmatter = {}
        
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                fm_text = parts[1]
                for line in fm_text.strip().split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if key == 'tags':
                            # Handle tags as list
                            tags = [t.strip() for t in value.strip('[]').split(',')]
                            frontmatter[key] = tags
                        else:
                            frontmatter[key] = value
        
        return frontmatter
    
    def _sanitize_uri(self, text: str) -> str:
        """Sanitize text for URI"""
        sanitized = re.sub(r'[^\w\s-]', '', text)
        sanitized = re.sub(r'[\s]+', '_', sanitized)
        return sanitized
    
    def query_sparql(self, query: str) -> List[Dict[str, Any]]:
        """Execute SPARQL query on knowledge graph"""
        if not RDF_AVAILABLE or self.rdf_graph is None:
            return []
        
        try:
            results = self.rdf_graph.query(query)
            
            # Convert to list of dicts
            output = []
            for row in results:
                result_dict = {}
                for var in results.vars:
                    value = row[var]
                    if isinstance(value, Literal):
                        result_dict[str(var)] = str(value)
                    elif isinstance(value, URIRef):
                        result_dict[str(var)] = str(value)
                    else:
                        result_dict[str(var)] = value
                output.append(result_dict)
            
            return output
        
        except Exception as e:
            if self.verbose:
                print(f"SPARQL query error: {e}")
            return []
    
    def export_graph_ttl(self, filename: str = None) -> str:
        """Export RDF graph to TTL file with human-readable section comments"""
        if self.rdf_graph is None:
            if self.verbose:
                print("Warning: RDF graph not available")
            return ""
        
        if filename is None:
            filename = "knowledge_graph.ttl"
        
        # Check if filename is already a full path
        from pathlib import Path
        from datetime import datetime
        filepath = Path(filename)
        if filepath.is_absolute() or str(filename).startswith('data'):
            output_path = filepath
        else:
            output_path = self.graphs_cache / filename
        
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Serialize to string first to add comments
        ttl_content = self.rdf_graph.serialize(format='turtle')
        
        # Get statistics for header
        stats = self.get_graph_stats()
        
        # Add human-readable header with section guide
        header = f"""# Knowledge Graph Export
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# 
# Graph Statistics:
#   - Documents: {stats.get('documents', 0)}
#   - Chunks: {stats.get('chunks', 0)}
#   - Domain Concepts: {stats.get('domain_concepts', 0)}
#   - Topic Nodes: {stats.get('topic_nodes', 0)}
#   - Total Triples: {stats.get('total_triples', 0)}
# 
# Structure Guide:
#   1. Topic Nodes (onto:TopicNode) - Navigation layer organizing concepts
#   2. Documents (onto:Document) - Source files with metadata
#   3. Chunks (onto:Chunk) - Text segments from documents
#   4. Domain Concepts (onto:DomainConcept) - Knowledge entities
#   5. Tags (onto:Tag) - Document categorization
# 
# Relationships:
#   - onto:hasChunk: Document → Chunk (1-to-many)
#   - onto:mentionsConcept: Chunk → DomainConcept (many-to-many)
#   - onto:coversConcept: TopicNode → DomainConcept (many-to-many)
#   - onto:coversChunk: TopicNode → Chunk (many-to-many)
# 
# For more information, see: README.md
#

"""
        
        # Write combined content
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(header)
            f.write(ttl_content)
        
        if self.verbose:
            print(f"Exported graph to {output_path}")
        
        return str(output_path)
    
    def create_ontology(self, filename: str = None) -> str:
        """Create ontology file with full semantic model (DomainConcept, TopicNode, Chunk)"""
        if not RDF_AVAILABLE:
            if self.verbose:
                print("Warning: RDF libraries not available")
            return ""
        
        if filename is None:
            filename = "pkm_ontology.ttl"
        
        onto_graph = Graph()
        onto_graph.bind("onto", self.ONTO)
        onto_graph.bind("owl", OWL)
        onto_graph.bind("skos", SKOS)
        onto_graph.bind("dct", DCTERMS)
        onto_graph.bind("rdfs", RDFS)
        
        # ===== CLASSES =====
        
        # Document class
        onto_graph.add((self.ONTO.Document, RDF.type, OWL.Class))
        onto_graph.add((self.ONTO.Document, RDFS.subClassOf, DCTERMS.BibliographicResource))
        onto_graph.add((self.ONTO.Document, RDFS.label, Literal("Document")))
        onto_graph.add((self.ONTO.Document, RDFS.comment, 
                       Literal("A source document such as Markdown, PDF, or HTML.")))
        
        # Chunk class (Information Layer)
        onto_graph.add((self.ONTO.Chunk, RDF.type, OWL.Class))
        onto_graph.add((self.ONTO.Chunk, RDFS.label, Literal("Chunk")))
        onto_graph.add((self.ONTO.Chunk, RDFS.comment,
                       Literal("A text span extracted from a document for retrieval and annotation.")))
        
        # DomainConcept class (Domain Layer)
        onto_graph.add((self.ONTO.DomainConcept, RDF.type, OWL.Class))
        onto_graph.add((self.ONTO.DomainConcept, RDFS.subClassOf, SKOS.Concept))
        onto_graph.add((self.ONTO.DomainConcept, RDFS.label, Literal("Domain Concept")))
        onto_graph.add((self.ONTO.DomainConcept, RDFS.comment,
                       Literal("Real-world or domain-level concept represented in the knowledge graph.")))
        
        # TopicNode class (Topic Layer)
        onto_graph.add((self.ONTO.TopicNode, RDF.type, OWL.Class))
        onto_graph.add((self.ONTO.TopicNode, RDFS.subClassOf, SKOS.Concept))
        onto_graph.add((self.ONTO.TopicNode, RDFS.label, Literal("Topic Node")))
        onto_graph.add((self.ONTO.TopicNode, RDFS.comment,
                       Literal("A topic or domain area summarising a set of domain concepts and supporting documents.")))
        
        # Legacy classes (for backward compatibility)
        onto_graph.add((self.ONTO.Concept, RDF.type, OWL.Class))
        onto_graph.add((self.ONTO.Concept, RDFS.label, Literal("Concept")))
        
        onto_graph.add((self.ONTO.Tag, RDF.type, OWL.Class))
        onto_graph.add((self.ONTO.Tag, RDFS.label, Literal("Tag")))
        
        # ===== DATA PROPERTIES =====
        
        # Document properties
        onto_graph.add((self.ONTO.path, RDF.type, OWL.DatatypeProperty))
        onto_graph.add((self.ONTO.path, RDFS.domain, self.ONTO.Document))
        onto_graph.add((self.ONTO.path, RDFS.range, RDFS.Literal))
        
        onto_graph.add((self.ONTO.sourceFormat, RDF.type, OWL.DatatypeProperty))
        onto_graph.add((self.ONTO.sourceFormat, RDFS.domain, self.ONTO.Document))
        onto_graph.add((self.ONTO.sourceFormat, RDFS.label, Literal("source format")))
        onto_graph.add((self.ONTO.sourceFormat, RDFS.comment,
                       Literal("MIME type of the source document (e.g., text/markdown, application/pdf)")))
        
        # Chunk properties
        onto_graph.add((self.ONTO.chunkIndex, RDF.type, OWL.DatatypeProperty))
        onto_graph.add((self.ONTO.chunkIndex, RDFS.domain, self.ONTO.Chunk))
        onto_graph.add((self.ONTO.chunkIndex, RDFS.range, RDFS.Literal))
        onto_graph.add((self.ONTO.chunkIndex, RDFS.label, Literal("chunk index")))
        
        onto_graph.add((self.ONTO.chunkText, RDF.type, OWL.DatatypeProperty))
        onto_graph.add((self.ONTO.chunkText, RDFS.domain, self.ONTO.Chunk))
        onto_graph.add((self.ONTO.chunkText, RDFS.range, RDFS.Literal))
        onto_graph.add((self.ONTO.chunkText, RDFS.label, Literal("chunk text")))
        
        # ===== OBJECT PROPERTIES =====
        
        # Document-Chunk relationship
        onto_graph.add((self.ONTO.hasChunk, RDF.type, OWL.ObjectProperty))
        onto_graph.add((self.ONTO.hasChunk, RDFS.domain, self.ONTO.Document))
        onto_graph.add((self.ONTO.hasChunk, RDFS.range, self.ONTO.Chunk))
        onto_graph.add((self.ONTO.hasChunk, RDFS.label, Literal("has chunk")))
        
        # Chunk-Concept relationship
        onto_graph.add((self.ONTO.mentionsConcept, RDF.type, OWL.ObjectProperty))
        onto_graph.add((self.ONTO.mentionsConcept, RDFS.domain, self.ONTO.Chunk))
        onto_graph.add((self.ONTO.mentionsConcept, RDFS.range, self.ONTO.DomainConcept))
        onto_graph.add((self.ONTO.mentionsConcept, RDFS.label, Literal("mentions concept")))
        onto_graph.add((self.ONTO.mentionsConcept, RDFS.comment,
                       Literal("Indicates that the chunk mentions or refers to a domain concept.")))
        
        # Topic-Concept relationship
        onto_graph.add((self.ONTO.coversConcept, RDF.type, OWL.ObjectProperty))
        onto_graph.add((self.ONTO.coversConcept, RDFS.domain, self.ONTO.TopicNode))
        onto_graph.add((self.ONTO.coversConcept, RDFS.range, self.ONTO.DomainConcept))
        onto_graph.add((self.ONTO.coversConcept, RDFS.label, Literal("covers concept")))
        onto_graph.add((self.ONTO.coversConcept, RDFS.comment,
                       Literal("Associates a topic with domain concepts that fall under it.")))
        
        # Topic-Chunk relationship
        onto_graph.add((self.ONTO.coversChunk, RDF.type, OWL.ObjectProperty))
        onto_graph.add((self.ONTO.coversChunk, RDFS.domain, self.ONTO.TopicNode))
        onto_graph.add((self.ONTO.coversChunk, RDFS.range, self.ONTO.Chunk))
        onto_graph.add((self.ONTO.coversChunk, RDFS.label, Literal("covers chunk")))
        onto_graph.add((self.ONTO.coversChunk, RDFS.comment,
                       Literal("Associates a topic with supporting text chunks.")))
        
        # Legacy properties (for backward compatibility)
        onto_graph.add((self.ONTO.linksTo, RDF.type, OWL.ObjectProperty))
        onto_graph.add((self.ONTO.linksTo, RDFS.domain, self.ONTO.Document))
        onto_graph.add((self.ONTO.linksTo, RDFS.range, self.ONTO.Document))
        
        onto_graph.add((self.ONTO.hasTag, RDF.type, OWL.ObjectProperty))
        onto_graph.add((self.ONTO.hasTag, RDFS.domain, self.ONTO.Document))
        onto_graph.add((self.ONTO.hasTag, RDFS.range, self.ONTO.Tag))
        
        onto_graph.add((self.ONTO.mentions, RDF.type, OWL.ObjectProperty))
        onto_graph.add((self.ONTO.mentions, RDFS.domain, self.ONTO.Document))
        onto_graph.add((self.ONTO.mentions, RDFS.range, self.ONTO.Concept))
        
        output_path = self.graphs_cache / filename
        onto_graph.serialize(destination=str(output_path), format='turtle')
        
        if self.verbose:
            print(f"Created ontology: {output_path}")
        
        return str(output_path)
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """Get knowledge graph statistics"""
        if not RDF_AVAILABLE or self.rdf_graph is None:
            return {
                'available': False,
                'message': 'RDF graph not available'
            }
        
        # Count by type
        docs_count = len(list(self.rdf_graph.subjects(RDF.type, self.ONTO.Document)))
        tags_count = len(list(self.rdf_graph.subjects(RDF.type, self.ONTO.Tag)))
        
        # New semantic model counts
        chunks_count = len(list(self.rdf_graph.subjects(RDF.type, self.ONTO.Chunk)))
        domain_concepts_count = len(list(self.rdf_graph.subjects(RDF.type, self.ONTO.DomainConcept)))
        topics_count = len(list(self.rdf_graph.subjects(RDF.type, self.ONTO.TopicNode)))
        
        # Legacy counts
        concepts_count = len(list(self.rdf_graph.subjects(RDF.type, self.ONTO.Concept)))
        links_count = len(list(self.rdf_graph.triples((None, self.ONTO.linksTo, None))))
        
        # Relationship counts
        mentions_count = len(list(self.rdf_graph.triples((None, self.ONTO.mentionsConcept, None))))
        covers_concepts_count = len(list(self.rdf_graph.triples((None, self.ONTO.coversConcept, None))))
        covers_chunks_count = len(list(self.rdf_graph.triples((None, self.ONTO.coversChunk, None))))
        
        # NetworkX stats
        try:
            avg_degree = sum(dict(self.nx_graph.degree()).values()) / len(self.nx_graph.nodes()) if len(self.nx_graph.nodes()) > 0 else 0
        except:
            avg_degree = 0
        
        stats = {
            'available': True,
            'total_triples': len(self.rdf_graph),
            'documents': docs_count,
            'chunks': chunks_count,
            'domain_concepts': domain_concepts_count,
            'topic_nodes': topics_count,
            'tags': tags_count,
            'concepts': concepts_count,  # Legacy
            'links': links_count,
            'chunk_mentions': mentions_count,
            'topic_covers_concepts': covers_concepts_count,
            'topic_covers_chunks': covers_chunks_count,
            'nodes': len(self.nx_graph.nodes()),
            'edges': len(self.nx_graph.edges()),
            'avg_degree': round(avg_degree, 2)
        }
        
        return stats
    
    # === END GRAPH RAG METHODS ===
    
    def get_stats(self) -> Dict:
        """Get statistics about loaded documents."""
        total_chars = sum(len(doc.content) for doc in self.documents)
        total_sections = sum(len(doc.sections) for doc in self.documents)
        
        return {
            "num_documents": len(self.documents),
            "total_characters": total_chars,
            "total_sections": total_sections,
            "avg_doc_length": total_chars // len(self.documents) if self.documents else 0
        }


def main():
    """Demo the RAG engine."""
    from dotenv import load_dotenv
    load_dotenv()
    
    print("=" * 80)
    print("Obsidian Vault RAG Engine - NotebookLM Style")
    print("=" * 80)
    print()
    
    # Initialize
    rag = VaultRAG(project_path="10-Projects/Cloud-vs-KG-Data-Centric")
    
    # Show stats
    stats = rag.get_stats()
    print(f"Vault Statistics:")
    print(f"  Documents: {stats['num_documents']}")
    print(f"  Total characters: {stats['total_characters']:,}")
    print(f"  Sections: {stats['total_sections']}")
    print(f"  Avg doc length: {stats['avg_doc_length']:,} chars")
    print()
    
    # Example questions
    questions = [
        "How do knowledge graphs help break data silos?",
        "What are the main differences between cloud data warehouses and data lakes?",
        "What is the data mesh pattern and how does it relate to our research?"
    ]
    
    for q in questions:
        print("\n" + "=" * 80)
        result = rag.ask(q)
        
        if result.get('error'):
            print(f"ERROR: {result['error']}")
            continue
        
        print(f"\n{result['answer']}\n")
        
        print("Sources:")
        for src in result['sources']:
            print(f"  [{src['number']}] {src['title']}")
            print(f"      {src['path']}")
        
        print("=" * 80)
        input("\nPress Enter for next question...")


if __name__ == "__main__":
    main()
