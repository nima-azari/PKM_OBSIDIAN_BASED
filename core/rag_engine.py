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
    
    def build_knowledge_graph(self) -> int:
        """Build RDF graph from loaded documents"""
        if not RDF_AVAILABLE:
            if self.verbose:
                print("Warning: RDF libraries not available. Install rdflib and networkx.")
            return 0
        
        if self.verbose:
            print(f"Building knowledge graph from {len(self.documents)} documents...")
        
        for doc in self.documents:
            self._add_document_to_graph(doc)
        
        # Extract relationships (wikilinks)
        for doc in self.documents:
            self._extract_relationships(doc)
        
        if self.verbose:
            print(f"Graph built: {len(self.rdf_graph)} triples")
        
        return len(self.rdf_graph)
    
    def _add_document_to_graph(self, doc: Document):
        """Add document as RDF resource"""
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
        """Export RDF graph to Turtle file"""
        if not RDF_AVAILABLE or self.rdf_graph is None:
            if self.verbose:
                print("Warning: RDF graph not available")
            return ""
        
        if filename is None:
            filename = "knowledge_graph.ttl"
        
        output_path = self.graphs_cache / filename
        self.rdf_graph.serialize(destination=str(output_path), format='turtle')
        
        if self.verbose:
            print(f"Exported graph to {output_path}")
        
        return str(output_path)
    
    def create_ontology(self, filename: str = None) -> str:
        """Create custom ontology file"""
        if not RDF_AVAILABLE:
            if self.verbose:
                print("Warning: RDF libraries not available")
            return ""
        
        if filename is None:
            filename = "pkm_ontology.ttl"
        
        onto_graph = Graph()
        onto_graph.bind("onto", self.ONTO)
        onto_graph.bind("owl", OWL)
        
        # Define classes
        onto_graph.add((self.ONTO.Document, RDF.type, OWL.Class))
        onto_graph.add((self.ONTO.Document, RDFS.label, Literal("Document")))
        
        onto_graph.add((self.ONTO.Concept, RDF.type, OWL.Class))
        onto_graph.add((self.ONTO.Concept, RDFS.label, Literal("Concept")))
        
        onto_graph.add((self.ONTO.Tag, RDF.type, OWL.Class))
        onto_graph.add((self.ONTO.Tag, RDFS.label, Literal("Tag")))
        
        # Define properties
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
        concepts_count = len(list(self.rdf_graph.subjects(RDF.type, self.ONTO.Concept)))
        links_count = len(list(self.rdf_graph.triples((None, self.ONTO.linksTo, None))))
        
        # NetworkX stats
        try:
            avg_degree = sum(dict(self.nx_graph.degree()).values()) / len(self.nx_graph.nodes()) if len(self.nx_graph.nodes()) > 0 else 0
        except:
            avg_degree = 0
        
        return {
            'available': True,
            'total_triples': len(self.rdf_graph),
            'documents': docs_count,
            'tags': tags_count,
            'concepts': concepts_count,
            'links': links_count,
            'nodes': len(self.nx_graph.nodes()),
            'edges': len(self.nx_graph.edges()),
            'avg_degree': round(avg_degree, 2)
        }
    
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
