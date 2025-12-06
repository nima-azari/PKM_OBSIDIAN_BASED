# GitHub Copilot Instructions for PKM System

## Project Overview

This is a **Personal Knowledge Management (PKM) system** with RAG (Retrieval-Augmented Generation), Knowledge Graphs, and web scraping capabilities. The architecture is **directory-based** (not Obsidian vault-based), with a simple Flask UI for chat and Jupyter notebooks for research workflows.

**Core Philosophy:** "PKM in our hands" - Users control their knowledge through directory structure, not complex UIs.

## Architecture Principles

### 1. Separation of Concerns
- **Web UI** (`server.py` + `static/`): Simple chat interface only
- **Jupyter Notebooks** (`notebooks/`): Web discovery and research workflows
- **Directory** (`data/sources/`): Users drop files here manually
- **Backend** (`core/`, `features/`): Processing and RAG engine

### 2. Data Flow
```
data/sources/ → VaultRAG → Embeddings Cache → Chat Responses
                  ↓
            Knowledge Graph → TTL Export → data/graphs/
```

### 3. No Obsidian Vault Dependency
- The system works **independently** of Obsidian
- `obsidian_api.py` is **optional** integration only
- Default source: `data/sources/` directory
- Never assume vault paths or Obsidian-specific features

## Code Style & Conventions

### Python Style
```python
# Good: Clear, descriptive variable names
sources_dir = Path("data/sources")
embedding_cache = {}

# Good: Verbose logging for debugging
if self.verbose:
    print(f"✓ Loaded {len(documents)} documents")

# Good: Pathlib over os.path
from pathlib import Path
filepath = sources_dir / "document.md"

# Bad: Hardcoded paths
vault_path = "C:/Users/someone/vault"  # ❌ Never do this

# Good: Configurable paths with defaults
def __init__(self, sources_dir="data/sources", verbose=False):
    self.sources_dir = Path(sources_dir)
```

### File Organization
```python
# Core modules (core/): Low-level, reusable
# - rag_engine.py: RAG + Graph RAG (unified)
# - document_processor.py: File processing
# - web_discovery.py: Article extraction
# - obsidian_api.py: Optional vault integration

# Features (features/): High-level workflows
# - chat.py: Chat interface wrapper
# - research_agent.py: Multi-source research
# - artifacts.py: Content generation

# Server: Flask REST API only
# - Endpoints: /api/ask, /api/stats
# - No complex logic, delegates to features/
```

### Error Handling
```python
# Good: Graceful degradation
try:
    article = discovery.extract_article(url)
    if article:
        articles.append(article)
    else:
        print(f"  ✗ Could not extract article from {url}")
except Exception as e:
    if self.verbose:
        print(f"  ✗ Error: {str(e)}")
    continue  # Don't crash entire workflow

# Bad: Silent failures
try:
    article = discovery.extract_article(url)
except:
    pass  # ❌ User has no idea what happened
```

## Key Design Patterns

### 1. Caching Strategy
All caches use **MD5 hash** of content for cache keys:

```python
import hashlib

def _get_cache_key(self, text: str) -> str:
    """Generate MD5 hash for caching."""
    return hashlib.md5(text.encode()).hexdigest()

# Embedding cache: data/embeddings/{md5}.npy
# Keyword cache: data/keywords/{md5}.json
```

### 2. Graph RAG Integration
**Do NOT create separate `graph_rag.py`** - it's integrated into `rag_engine.py`:

```python
class VaultRAG:
    # RAG methods
    def keyword_search(self, query, top_k=5): ...
    def semantic_search(self, query, top_k=5): ...
    def ask(self, question, context_size=3): ...
    
    # Graph methods (same class!)
    def build_knowledge_graph(self): ...
    def query_sparql(self, query): ...
    def export_graph_ttl(self, output_path): ...
    def create_ontology(self, output_path): ...
    def get_graph_stats(self): ...
```

### 3. Namespace Conventions
```python
# RDF namespaces
SOURCE_NS = "http://pkm.local/sources/"
ONTO_NS = "http://pkm.local/ontology/"

# Never use external ontologies without user permission
# Keep graphs self-contained and portable
```

### 4. Frontmatter for Documents
```python
# All saved documents should have YAML frontmatter
content = f"""---
title: {title}
author: {author}
url: {url}
date_extracted: {datetime.now().strftime('%Y-%m-%d')}
tags: [web-article, research]
---

# {title}

{article_content}
"""
```

## Common Patterns

### Pattern 1: Document Loading
```python
def _load_documents(self):
    """Load documents from sources directory."""
    documents = []
    sources_dir = Path(self.sources_dir)
    
    for ext in ['.md', '.txt']:
        for filepath in sources_dir.glob(f'**/*{ext}'):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    documents.append({
                        'title': filepath.stem,
                        'content': content,
                        'source': str(filepath)
                    })
            except Exception as e:
                if self.verbose:
                    print(f"Error loading {filepath}: {e}")
    
    return documents
```

### Pattern 2: OpenAI API Calls
```python
from openai import OpenAI

client = OpenAI()  # Uses OPENAI_API_KEY from env

# Embeddings
response = client.embeddings.create(
    model="text-embedding-3-small",
    input=text
)
embedding = response.data[0].embedding

# Chat completions
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query}
    ],
    temperature=0.7
)
answer = response.choices[0].message.content
```

### Pattern 3: Jupyter Notebook Structure
```python
# Cell 1: Setup
import sys
sys.path.insert(0, '..')  # Access parent directory

from core.web_discovery import WebDiscovery
from pathlib import Path

# Cell 2: Markdown heading
# Use ## for steps

# Cell 3: User input
research_topic = "Your topic here"

# Cell 4: Processing with progress
for i, item in enumerate(items, 1):
    print(f"[{i}/{len(items)}] Processing...")

# Cell 5: Results summary
print(f"✅ Successfully processed {count} items")
```

## Anti-Patterns (Avoid These!)

### ❌ Don't Use Gradio
```python
# BAD - We switched away from Gradio
import gradio as gr
demo = gr.ChatInterface(...)
```

### ❌ Don't Assume Obsidian Vault
```python
# BAD - Hardcoded vault assumptions
vault = ObsidianVault("path/to/vault")
notes = vault.get_all_notes()

# GOOD - Directory-based
sources_dir = Path("data/sources")
files = list(sources_dir.glob("**/*.md"))
```

### ❌ Don't Create Complex UIs
```python
# BAD - Multi-column complex interfaces
gr.Blocks():
    with gr.Row():
        with gr.Column():
            sources_panel = ...
        with gr.Column():
            chat_panel = ...
        with gr.Column():
            artifacts_panel = ...

# GOOD - Simple single-purpose UIs
# Chat UI: Just chat messages
# Discovery: Use Jupyter notebooks
```

### ❌ Don't Duplicate Graph RAG
```python
# BAD - Separate graph class
class GraphRAG:
    def build_graph(self): ...

# GOOD - Integrated into VaultRAG
class VaultRAG:
    def build_knowledge_graph(self): ...
```

## Testing Conventions

### Test Files
```python
# test_chat.py - Simple chat test
from features.chat import VaultChat

chat = VaultChat(verbose=True)
result = chat.ask("What is the project about?")
print(result['answer'])

# test_graph.py - Graph functionality
from core.rag_engine import VaultRAG

rag = VaultRAG(verbose=True)
rag.build_knowledge_graph()
rag.export_graph_ttl("data/graphs/test_graph.ttl")
stats = rag.get_graph_stats()
print(stats)
```

### No Unit Tests (Yet)
- Focus on **integration tests** and **manual testing**
- Use `verbose=True` for debugging
- Test workflows end-to-end in Jupyter notebooks

## Environment Variables

```python
# Required
OPENAI_API_KEY=sk-...

# Optional (for Obsidian integration)
OBSIDIAN_API_KEY=...
OBSIDIAN_VAULT_NAME=...
```

## File Naming Conventions

```python
# Core modules: lowercase with underscores
rag_engine.py
document_processor.py
web_discovery.py

# Features: descriptive nouns
chat.py
research_agent.py
artifacts.py

# Tests: test_ prefix
test_chat.py
test_graph.py

# Data files: descriptive names
test_document.md
research_paper.pdf
test_graph.ttl
```

## Import Organization

```python
# Standard library
import sys
import re
from pathlib import Path
from datetime import datetime

# Third-party
import numpy as np
from openai import OpenAI
from flask import Flask, request, jsonify
from rdflib import Graph, Namespace, Literal, URIRef

# Local
from core.rag_engine import VaultRAG
from features.chat import VaultChat
```

## Documentation Style

```python
def build_knowledge_graph(self):
    """
    Build RDF knowledge graph from loaded documents.
    
    Creates triples for:
    - Documents and their metadata
    - Named entities (people, organizations, locations)
    - Relationships between entities
    - Topics and keywords
    
    Returns:
        int: Number of triples created
    """
```

## When Suggesting Code

1. **Check context first**: Is this for web UI, Jupyter notebook, or core module?
2. **Use existing patterns**: Look at similar code in the same module
3. **Respect the architecture**: Don't mix UI and backend logic
4. **Cache when possible**: Use MD5-based caching for expensive operations
5. **Verbose logging**: Add `if self.verbose: print(...)` statements
6. **Error handling**: Graceful degradation, never silent failures
7. **Type hints**: Use them for complex functions
8. **Pathlib**: Always use `Path()` instead of string paths

## Common User Workflows

### Workflow 1: Adding Documents
```bash
# User drops files in data/sources/
cp research.pdf data/sources/
cp notes.md data/sources/

# Server automatically picks them up
python server.py
```

### Workflow 2: Web Research
```python
# In source_discovery.ipynb
research_topic = "AI alignment"
# → Generate queries
# → Paste URLs
# → Extract and save
```

### Workflow 3: Knowledge Graph
```python
from core.rag_engine import VaultRAG

rag = VaultRAG()
rag.build_knowledge_graph()
rag.export_graph_ttl("my_knowledge.ttl")
```

## Version Compatibility

- **Python**: 3.10+
- **OpenAI**: 2.9.0+ (new client style)
- **Flask**: 3.1.2+
- **RDFLib**: 7.4.0+

## Summary

**Remember:**
- Simple > Complex
- Directory-based > Vault-based
- Caching > Recomputing
- Verbose logging > Silent execution
- Jupyter for workflows > Complex UIs
- Integrated graph > Separate modules

**When in doubt:**
- Check existing code in the same module
- Prioritize user control over automation
- Keep the system modular and testable
