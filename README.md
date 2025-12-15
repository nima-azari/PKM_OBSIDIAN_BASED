# PKM - Personal Knowledge Management System

A powerful, directory-based knowledge management system with RAG (Retrieval-Augmented Generation), Knowledge Graph support, and automated source discovery.

## 🚀 Quick Start

**Installation:**
```bash
pip install -r requirements.txt

# Set OpenAI API key in .env file:
# OPENAI_API_KEY=sk-your-key-here
```

**Get Started:**
1. Drop files in `data/sources/`
2. Run `python server.py`
3. Open http://localhost:5000

**Full documentation:** See [docs/QUICKSTART.md](docs/QUICKSTART.md)

## 📁 Project Structure

```
obsidian-control/
├── core/                       # Core backend modules
│   ├── rag_engine.py          # RAG with GraphRAG capabilities
│   ├── document_processor.py  # PDF/HTML/YouTube processing
│   ├── web_discovery.py       # 8-API source discovery
│   └── obsidian_api.py        # Optional Obsidian integration
├── features/                   # Feature modules
│   ├── chat.py                # Chat interface logic
│   ├── research_agent.py      # Research workflows
│   └── artifacts.py           # Content generation
├── scripts/                    # Utility scripts
│   ├── discover_sources.py            # Gap analysis
│   ├── auto_discover_sources.py       # Multi-API search (8 APIs)
│   ├── prioritize_sources.py          # AI ranking
│   ├── download_papers.py             # DOI downloader
│   ├── auto_download_papers.py        # Batch downloader
│   ├── import_urls.py                 # URL importer
│   ├── build_graph.py                 # Knowledge graph builder
│   ├── build_graph_with_meta.py       # Meta-ontology guided
│   ├── generate_article_from_graph.py # Graph → article
│   ├── generate_meta_ontology.py      # Ontology generator
│   ├── process_youtube.py             # YouTube transcripts
│   └── interactive_chat.py            # CLI chat
├── tests/                      # Test suite
│   ├── integration/           # Integration tests
│   └── archive/               # Archived component tests
├── docs/                       # Documentation
│   ├── QUICKSTART.md          # Quick start guide
│   ├── README.md              # Complete documentation
│   ├── SOURCE_DISCOVERY_EXPANSION_COMPLETE.md
│   ├── RESEARCH_PIPELINE_GUIDE.txt
│   └── ...
├── data/                       # Data directory
│   ├── sources/               # 📂 DROP YOUR FILES HERE
│   ├── graphs/                # RDF/TTL graph exports
│   ├── embeddings/            # OpenAI embeddings cache
│   ├── keywords/              # TF-IDF keyword cache
│   └── processed/             # Processed documents cache
├── notebooks/                  # Jupyter notebooks
├── static/                     # Web UI assets
├── analysis/                   # Quality metrics & evaluation
├── server.py                   # Flask web server
└── requirements.txt           # Python dependencies
```

## 🌟 Key Features

### Core Capabilities
- **RAG Engine** - Hybrid search (keyword + semantic + graph-guided)
- **Knowledge Graphs** - RDF/SPARQL with 98/100 quality score
- **Chat Interface** - Web UI for querying your knowledge base
- **Caching System** - MD5-based embeddings and keywords

### Advanced Research 🔬
- **Meta-Ontology Editing** 🧑‍🔬 - Define domain structure (editable TTL)
- **Knowledge Graph Editing** 🧑‍🔬 - Refine concepts and relationships
- **8-API Source Discovery** - EUR-Lex, OpenAlex, CORE, DOAJ, HAL, Zenodo, arXiv, S2
- **AI Prioritization** - Rank sources by semantic relevance
- **Auto-Download Papers** - Fetch open-access PDFs (60-80% success)
- **Manual Checkpoints** 🧑‍🔬 - Researcher control at key decisions

## 📖 Usage Paths

### Path 1: Simple Chat
```bash
# Add files to data/sources/ then:
python server.py
# Open http://localhost:5000
```

### Path 2: Knowledge Graph Research
```bash
python scripts/build_graph.py
# Edit data/graphs/knowledge_graph.ttl manually 🧑‍🔬
python scripts/generate_article_from_graph.py data/graphs/knowledge_graph.ttl
python server.py
```

### Path 3: Automated Source Discovery
```bash
# 1. Identify gaps
python scripts/discover_sources.py

# 2. Search 8 APIs
python scripts/auto_discover_sources.py --report data/discovery_report.txt

# 3. Prioritize by relevance
python scripts/prioritize_sources.py

# 4. Review list 🧑‍🔬 MANUAL CHECKPOINT
notepad data/discovered_urls_prioritized.txt

# 5. Auto-download papers
python scripts/auto_download_papers.py --tier high --limit 10

# 6. Review downloads 🧑‍🔬 MANUAL CHECKPOINT
ls data/sources/

# 7. Import & rebuild
python scripts/import_urls.py data/discovered_urls_prioritized.txt
python scripts/build_graph.py
```

### Path 4: Meta-Ontology Guided GraphRAG
```bash
# 1. Generate meta-ontology
python scripts/generate_meta_ontology.py

# 2. Edit ontology 🧑‍🔬 RESEARCHER CONTROL
# Edit data/graphs/meta_ontology.ttl

# 3. Build graph using ontology
python scripts/build_graph_with_meta.py --meta-ontology data/graphs/meta_ontology.ttl

# 4. Generate synthesis
python scripts/generate_article_from_graph.py data/graphs/knowledge_graph.ttl
```

## 🧪 Testing

```bash
# Integration tests
python tests/integration/test_chat.py
python tests/integration/test_graph.py
python tests/integration/test_expanded_apis.py
python tests/integration/test_meta_ontology.py
python tests/integration/test_part4_pipeline.py
```

## 📚 Documentation

- **[docs/QUICKSTART.md](docs/QUICKSTART.md)** - 5 detailed usage paths
- **[docs/README.md](docs/README.md)** - Complete feature reference (850+ lines)
- **[docs/SOURCE_DISCOVERY_EXPANSION_COMPLETE.md](docs/SOURCE_DISCOVERY_EXPANSION_COMPLETE.md)** - 8-API technical deep-dive
- **[docs/RESEARCH_PIPELINE_GUIDE.txt](docs/RESEARCH_PIPELINE_GUIDE.txt)** - Advanced workflows
- **[analysis/ENHANCED_GRAPH_ANALYSIS.md](analysis/ENHANCED_GRAPH_ANALYSIS.md)** - GraphRAG quality metrics

## 🧑‍🔬 Philosophy: Researcher Control

**Manual Control Points:**
1. **Meta-Ontology Editing** - Define domain structure before extraction
2. **Knowledge Graph Editing** - Refine concepts in TTL format
3. **Source List Review** - Approve sources before download
4. **Content Review** - Validate papers before import

**"PKM in your hands"** - Automation assists, researcher controls.

## 🎯 System Capabilities

- **8 Research APIs** - Comprehensive source coverage
- **98/100 GraphRAG Score** - Industry-standard quality
- **50-100 URLs per run** - Typical discovery results
- **60-70% high relevance** - AI prioritization accuracy
- **60-80% download success** - Open-access papers

## 💡 Requirements

```bash
pip install -r requirements.txt
```

**Key dependencies:**
- openai>=1.0.0 (embeddings + LLM)
- rdflib>=7.0.0 (knowledge graphs)
- sentence-transformers>=2.2.0 (semantic filtering)
- flask>=3.1.2 (web UI)

## 🔧 Configuration

Create `.env` file:
```env
OPENAI_API_KEY=sk-your-key-here
```

## 📊 Quality Metrics

- **GraphRAG Quality:** 98/100 (708 triples, 3-layer architecture)
- **Retrieval Precision@5:** 100%
- **Generation Faithfulness:** 0.95-1.0 (RAGAS)
- **API Coverage:** 8 research databases

---

**Version:** December 2025  
**License:** MIT  
**Status:** Production Ready ✅
