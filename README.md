# PKM - Personal Knowledge Management System

A powerful, directory-based knowledge management system with RAG (Retrieval-Augmented Generation), Knowledge Graph support, and web scraping capabilities.

## 🌟 Features

- **Simple Chat Interface** - ChatGPT-like UI for querying your knowledge base
- **RAG Engine** - Keyword + semantic search with OpenAI embeddings
- **Knowledge Graphs** - RDF/SPARQL support with TTL export
- **Web Discovery** - AI-powered article extraction and quality assessment
- **Jupyter Workflows** - Interactive notebooks for research and source discovery
- **Caching System** - Automatic caching of embeddings and keywords
- **Obsidian Integration** - Optional API for Obsidian vault management

## 📁 Project Structure

```
obsidian-control/
├── core/                       # Core backend modules
│   ├── rag_engine.py          # RAG with graph capabilities
│   ├── document_processor.py  # PDF/txt/md processing
│   ├── web_discovery.py       # Web scraping & extraction
│   └── obsidian_api.py        # Obsidian vault API
├── features/                   # Feature modules
│   ├── chat.py                # Chat interface logic
│   ├── research_agent.py      # Deep research workflows
│   └── artifacts.py           # Content generation
├── data/                       # Data directory (cached & sources)
│   ├── sources/               # 📂 DROP YOUR FILES HERE
│   ├── processed/             # Processed documents cache
│   ├── keywords/              # TF-IDF keyword cache
│   ├── embeddings/            # OpenAI embeddings cache
│   ├── graphs/                # RDF/TTL graph exports
│   └── index/                 # JSON index files
├── notebooks/                  # Jupyter notebooks
│   ├── source_discovery.ipynb # Web source discovery workflow
│   └── research_workflow.ipynb # Advanced research pipeline
├── static/                     # Web UI assets
│   ├── index.html             # Main HTML page
│   ├── style.css              # Styling
│   └── script.js              # Frontend JavaScript
├── server.py                   # Flask web server
├── test_chat.py               # Test chat functionality
├── test_graph.py              # Test graph building
└── requirements.txt           # Python dependencies
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or download the repository
cd obsidian-control

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file in the root directory:

```env
# Required for RAG and chat
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Obsidian vault integration
OBSIDIAN_API_KEY=your_obsidian_api_key_here
OBSIDIAN_VAULT_NAME=your_vault_name
```

### 3. Add Your Sources

Drop your documents into `data/sources/`:

```bash
data/sources/
├── my-research-paper.pdf
├── notes.md
├── article.txt
├── webpage.html
└── ...
```

Supported formats: `.md`, `.txt`, `.pdf`, `.html`, `.htm`

**For YouTube videos:**

1. Add URLs to `data/sources/youtube_links.txt` (one per line)
2. Run: `python process_youtube.py` (preserves timestamps)
   - Or: `python process_youtube.py --article` (AI converts to clean article format)
3. Transcripts are saved as markdown files in `data/sources/`

Example `youtube_links.txt`:
```
# YouTube Links to Process
https://www.youtube.com/watch?v=VIDEO_ID_1
https://www.youtube.com/watch?v=VIDEO_ID_2
```

**Two formats available:**
- **Timestamp mode** (default): Preserves `[MM:SS]` timestamps for each line
- **Article mode** (`--article` flag): AI converts to structured article with headings, cleaned grammar, and continuous text

### 4. (Optional) Build Knowledge Graph with GraphRAG Support

**⚠️ Note:** This is an **advanced feature** for researchers who want semantic graph navigation and multi-layered knowledge representation. The basic chat functionality works without this step.

The system supports a **three-layer semantic model** for knowledge graphs:

1. **Domain Layer**: Real-world concepts (Building, Regulation, Energy Label, etc.)
2. **Topic Layer**: Human-understandable topics/domain areas for navigation
3. **Information Layer**: Documents, chunks, and evidence

#### Quick Start (Simple Mode)

```bash
# Generate basic knowledge graph from all sources
python build_graph.py

# This creates:
# - data/graphs/knowledge_graph.ttl (RDF instances)
# - data/graphs/ontology.ttl (schema definitions)
```

#### Advanced Mode (Semantic Layers)

For researchers who need structured topic navigation and graph editing:

```bash
# Step 1: Build graph with ontology + instances
python build_graph.py --mode advanced

# This creates:
# - ontology.ttl: Schema (DomainConcept, TopicNode, Document, Chunk classes)
# - instances.ttl: Data (actual concepts, topics, documents, chunks)
```

**What this generates:**

- **Domain Concepts** (`ex:DomainConcept`):
  - Real-world concepts extracted from documents
  - Hierarchies via `skos:broader` / `skos:narrower`
  - Alternative labels via `skos:altLabel`

- **Topic Nodes** (`ex:TopicNode`):
  - Human topics/domain areas for GraphRAG navigation
  - Cover concepts via `ex:coversConcept`
  - Related topics via `skos:related`

- **Documents & Chunks** (`ex:Document`, `ex:Chunk`):
  - Text chunks linked to concepts via `ex:mentionsConcept`
  - Full document metadata (title, creator, source path)

#### Manual Editing & Graph UI

**Option A: Edit TTL files directly**

```bash
# Edit the generated instances.ttl to:
# - Rename topics/concepts (change skos:prefLabel)
# - Adjust hierarchies (skos:broader/narrower)
# - Connect topics to concepts (ex:coversConcept)
# - Add definitions (skos:definition)
```

**Option B: Use Interactive Graph Editor (Dash + Cytoscape)**

```bash
# Launch graph editor UI
python graph_editor.py

# Features:
# - Visual graph of topics + concepts
# - Click to rename topics/concepts
# - Drag-and-drop to assign concepts to topics
# - Add/remove relationships
# - Save changes back to TTL (graph_updated.ttl)
```

#### GraphRAG Integration

The graph supports **graph-based retrieval**:

```python
from core.rag_engine import VaultRAG

rag = VaultRAG()
rag.build_knowledge_graph()

# GraphRAG retrieval flow:
# User query → Topic nodes → Domain concepts → Chunks → Documents
# Embeddings computed for topics, concepts, and chunks
```

**Retrieval steps:**
1. Encode user query
2. Retrieve nearest topic(s) and/or concept(s)
3. Expand through graph: Topic → concepts → chunks
4. Feed both text + graph context to LLM

#### Generate Synthesis Article (Optional)

After building the graph, you can generate an AI article:

```bash
# Generate article from knowledge graph
python generate_article_from_graph.py data/graphs/instances.ttl

# This creates: data/sources/knowledge_graph_article.md
```

**Custom paths:**
```bash
python build_graph.py data/graphs/my_research_instances.ttl
python generate_article_from_graph.py data/graphs/my_research_instances.ttl my_synthesis.md
```

### 5. Launch the UI

```bash
python server.py
```

Open your browser to **http://localhost:5000**

## 📖 Step-by-Step Workflow

### Option A: Simple Chat (Recommended for Beginners)

1. **Add sources**: Drop files in `data/sources/`
2. **Start server**: `python server.py`
3. **Ask questions**: Use the web UI at http://localhost:5000
4. **Get answers**: Receive AI responses with source citations

### Option B: Web Research Workflow (Using Jupyter)

1. **Open notebook**: Launch Jupyter and open `notebooks/source_discovery.ipynb`
2. **Enter topic**: Specify your research topic
3. **Generate queries**: AI creates optimized search queries
4. **Search & paste URLs**: Copy URLs from Google Scholar, arXiv, etc.
5. **Extract & save**: Articles are automatically saved to `data/sources/`
6. **Chat**: Ask questions about your new sources

### Option C: Advanced Research (Deep Dive)

1. **Open notebook**: Launch `notebooks/research_workflow.ipynb`
2. **Batch URLs**: Paste multiple source URLs
3. **Quality filtering**: AI assesses each source (scores 1-10)
4. **Synthesis**: AI creates a literature review combining all sources
5. **Save**: High-quality sources + synthesis saved to `data/sources/`

### Option D: Knowledge Graph → Article Workflow

This workflow lets you create a knowledge graph, manually refine it, and generate a synthesis article:

```bash
# 1. Build knowledge graph
python build_graph.py data/graphs/my_research.ttl

# 2. (Optional) Edit the TTL file manually
#    - Add custom relationships
#    - Adjust entity labels
#    - Connect concepts differently

# 3. Generate article from graph
python generate_article_from_graph.py data/graphs/my_research.ttl

# 4. Launch UI to chat with the generated article
python server.py
```

**This creates:**
- `data/graphs/my_research.ttl` - RDF graph in Turtle format (editable!)
- `data/sources/my_research_article.md` - AI-generated synthesis article

**Query with SPARQL:**
```python
from core.rag_engine import VaultRAG

rag = VaultRAG()
rag.build_knowledge_graph()

query = """
PREFIX onto: <http://pkm.local/ontology/>

SELECT ?label WHERE {
    ?doc a onto:Document .
    ?doc rdfs:label ?label .
}
"""

results = rag.query_sparql(query)
```

**Testing (simple):**
```bash
python test_graph.py  # Creates test_graph.ttl and test_ontology.ttl
```

## 🔧 Advanced Usage

### Python API

```python
from core.rag_engine import VaultRAG
from features.chat import VaultChat

# Initialize
rag = VaultRAG(sources_dir="data/sources", verbose=True)
chat = VaultChat(verbose=True)

# Ask a question
result = chat.ask("What are the main themes?")
print(result['answer'])
print(result['sources'])

# Build knowledge graph
rag.build_knowledge_graph()
stats = rag.get_graph_stats()
print(stats)

# Export graph
rag.export_graph_ttl("my_graph.ttl")
```

### Web Discovery

```python
from core.web_discovery import WebDiscovery

discovery = WebDiscovery()

# Extract article from URL
article = discovery.extract_article("https://example.com/article")

# Assess quality
assessment = discovery.assess_quality(article)

# Save to sources
from pathlib import Path
sources_dir = Path("data/sources")
# ... save article as markdown
```

### Document Processing

```python
from core.document_processor import DocumentProcessor

processor = DocumentProcessor()

# Process PDF
note_path = processor.process_file("document.pdf", tags=["research"])

# Process HTML file
note_path = processor.process_file("webpage.html", tags=["web"])

# Extract YouTube transcript (saves to data/sources/)
note_path = processor.process_youtube_url(
    "https://www.youtube.com/watch?v=VIDEO_ID",
    tags=["youtube", "video"]
)

# Add text note
note_path = processor.add_text_note(
    title="My Note",
    content="Note content here",
    tags=["idea"]
)
```

### Batch YouTube Processing

```bash
# Add URLs to data/sources/youtube_links.txt

# Extract with timestamps (default)
python process_youtube.py

# Convert to article format with AI
python process_youtube.py --article
```

**Timestamp mode:**
```markdown
**[00:03]** hello everyone
**[00:05]** my name is jason stokov
**[00:07]** and i want to welcome you all to...
```

**Article mode (--article flag):**
```markdown
## Introduction

Hello everyone, my name is Jason Stokov and I want to 
welcome you all to our latest webinar...

## Main Points

[Clean, structured content with proper paragraphs and headings]
```

This will:
- Extract transcripts for all YouTube URLs
- Save them as markdown files in `data/sources/`
- Automatically comment out processed URLs

## 📊 System Architecture

```
┌─────────────────┐
│   Web UI        │  ← Flask + HTML/CSS/JS
│  (port 5000)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Chat Engine    │  ← Question answering
│  (VaultChat)    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│      RAG Engine (VaultRAG)      │
│                                 │
│  • Keyword Search (TF-IDF)     │
│  • Semantic Search (Embeddings) │
│  • Knowledge Graph (RDF)        │
│  • SPARQL Queries              │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│      Document Loading           │
│                                 │
│  data/sources/ → Documents      │
│     • Caching (embeddings)      │
│     • Indexing (keywords)       │
└─────────────────────────────────┘
```

## 🛠️ Testing

```bash
# Test chat functionality
python test_chat.py

# Test knowledge graph
python test_graph.py

# Test in Jupyter
jupyter notebook notebooks/
```

## 📦 Dependencies

- **Core**: Python 3.10+, Flask, OpenAI
- **RAG**: rdflib, networkx, scikit-learn, numpy
- **Processing**: pypdf, trafilatura, beautifulsoup4, html2text
- **Media**: youtube-transcript-api (for video transcripts)
- **Optional**: Jupyter, anthropic

Install all:
```bash
pip install -r requirements.txt
```

## 🎯 Use Cases

- **Academic Research**: Collect papers, extract insights, build literature reviews
- **Knowledge Base**: Personal wiki with AI-powered Q&A
- **Web Research**: Scrape articles (HTML/web pages), assess quality, synthesize findings
- **Video Learning**: Extract and search YouTube transcripts
- **Graph Analysis**: Discover connections between concepts
- **Note-taking**: Obsidian integration for structured notes

## 🤝 Contributing

This is a personal knowledge management system. Feel free to fork and customize for your needs.

## 📄 License

MIT License - See LICENSE file for details

## 🔗 Resources

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [RDFLib Documentation](https://rdflib.readthedocs.io/)
- [SPARQL Tutorial](https://www.w3.org/TR/sparql11-query/)
- [Obsidian API](https://docs.obsidian.md/API)

---

**Made with ❤️ for knowledge workers**
