# PKM System - Quick Start Guide

**Get started in 5 minutes** with the Personal Knowledge Management system.

---

## ⚡ Installation (2 minutes)

```bash
# 1. Clone or navigate to repository
cd obsidian-control

# 2. Create virtual environment (recommended)
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set OpenAI API key
# Create .env file with:
# OPENAI_API_KEY=sk-your-key-here
```

---

## 🎯 Choose Your Path

Select the workflow that matches your needs:

### Path 1: Simple Chat (Beginners) 💬

**Use when:** You just want to ask questions about your documents.

```bash
# 1. Drop files in data/sources/
# Supported: .md, .txt, .pdf, .html

# 2. Start server
python server.py

# 3. Open browser
http://localhost:5000

# 4. Ask questions
# Get AI answers with source citations
```

**Done!** Chat with your knowledge base.

---

### Path 2: Knowledge Graph Research 🕸️

**Use when:** You want to build a semantic knowledge graph, manually refine it, and generate synthesis articles.

```bash
# 1. Add sources to data/sources/
cp my-papers.pdf data/sources/
cp notes.md data/sources/

# 2. Build knowledge graph
python build_graph.py

# Creates: data/graphs/knowledge_graph.ttl (RDF format)

# 3. (OPTIONAL) Edit the graph manually 🧑‍🔬
# Open data/graphs/knowledge_graph.ttl
# - Rename concepts (change skos:prefLabel)
# - Add relationships (ex:relatedTo)
# - Adjust hierarchies (skos:broader/narrower)
# - Add definitions (skos:definition)

# 4. Generate AI synthesis article from graph
python generate_article_from_graph.py data/graphs/knowledge_graph.ttl

# Creates: data/sources/knowledge_graph_article.md

# 5. Chat with everything (original sources + synthesis)
python server.py
```

**Key Feature:** You control the knowledge graph structure. Edit the TTL file to refine relationships before generating synthesis.

---

### Path 3: Automated Source Discovery 🔍

**Use when:** You need to find relevant sources to fill gaps in your research domain.

```bash
# 1. Identify coverage gaps in your knowledge graph
python discover_sources.py

# Output: data/discovery_report.txt
# - Coverage scores per topic
# - Identified gaps
# - 5 AI-generated search queries

# 2. Search 8 APIs automatically
python auto_discover_sources.py \
  --report data/discovery_report.txt \
  --min-new-sources 5

# Searches: EUR-Lex, OpenAlex, CORE, DOAJ, HAL, Zenodo, arXiv, Semantic Scholar
# Output: data/discovered_urls_expanded.txt (50-100 URLs)

# 3. Prioritize by relevance using AI embeddings
python prioritize_sources.py

# Output: data/discovered_urls_prioritized.txt
# - HIGH (≥0.50 similarity)
# - MEDIUM (0.40-0.49)
# - LOW (<0.40)

# 4. Review prioritized list 🧑‍🔬 MANUAL CHECKPOINT
notepad data/discovered_urls_prioritized.txt
# Remove any sources that don't fit your research focus
# This preserves researcher control

# 5. Auto-download open-access papers
python auto_download_papers.py --tier high --limit 10

# Downloads PDFs to: data/sources/
# Uses Unpaywall + Crossref APIs

# 6. Review downloaded papers 🧑‍🔬 MANUAL CHECKPOINT
ls data/sources/
# Check 2-3 papers to verify quality
# Remove any that don't meet your standards

# 7. Import remaining URLs and rebuild graph
python import_urls.py data/discovered_urls_prioritized.txt
python build_graph.py

# Your graph now includes new sources!
```

**Key Feature:** Two manual checkpoints (Steps 4 & 6) give you control over what enters your knowledge base.

---

### Path 4: YouTube Research 📺

**Use when:** You want to analyze YouTube video transcripts.

```bash
# 1. Create data/sources/youtube_links.txt
# Add one URL per line:
# https://www.youtube.com/watch?v=VIDEO_ID_1
# https://www.youtube.com/watch?v=VIDEO_ID_2

# 2. Process transcripts
# Option A: Preserve timestamps [MM:SS]
python process_youtube.py

# Option B: Convert to structured article (AI)
python process_youtube.py --article

# Saves transcripts to: data/sources/

# 3. Chat with video content
python server.py
```

---

### Path 5: Meta-Ontology Guided GraphRAG 🧬

**Use when:** You want to guide knowledge graph extraction using a domain-specific ontology that you can edit.

```bash
# 1. Generate initial meta-ontology from your research domain
python generate_meta_ontology.py

# Creates: data/graphs/meta_ontology.ttl

# 2. Edit meta-ontology manually 🧑‍🔬 RESEARCHER CONTROL
# Open data/graphs/meta_ontology.ttl
# - Define domain concepts (ex:DataGovernance, ex:SemanticWeb)
# - Add hierarchies (rdfs:subClassOf)
# - Specify properties (ex:regulates, ex:appliesTo)
# - Add descriptions (rdfs:comment)
# This ontology guides what concepts to extract from documents

# 3. Build knowledge graph using meta-ontology
python build_graph_with_meta.py \
  --meta-ontology data/graphs/meta_ontology.ttl

# Creates: data/graphs/knowledge_graph.ttl
# Concepts extracted according to your ontology structure

# 4. Generate synthesis article
python generate_article_from_graph.py data/graphs/knowledge_graph.ttl

# 5. Chat with GraphRAG-enhanced retrieval
python server.py
```

**Key Feature:** You define the domain structure via meta-ontology, ensuring extracted concepts match your research framework.

---

## 🔧 Common Commands

### Check System Status
```bash
# Test chat functionality
python test_chat.py

# Test graph building
python test_graph.py

# Test API integrations (8 APIs)
python test_expanded_apis.py
```

### View Knowledge Graph Statistics
```bash
# After building graph
python -c "from core.rag_engine import VaultRAG; rag = VaultRAG(); rag.build_knowledge_graph(); print(rag.get_graph_stats())"
```

### Export Knowledge Graph
```bash
# Build and export to custom location
python build_graph.py data/graphs/my_research.ttl
```

### Download Specific Paper
```bash
# Test DOI download
python download_papers.py "10.1038/sdata.2016.18"

# Test arXiv download
python download_papers.py "arXiv:1234.5678"
```

---

## 🎓 Advanced Configuration

### Adjust Source Discovery Sensitivity

**More permissive (exploratory research):**
```bash
python auto_discover_sources.py --domain-similarity 0.25
```

**Stricter filtering (narrow domain):**
```bash
python auto_discover_sources.py --domain-similarity 0.40
```

### Download Different Relevance Tiers

```bash
# HIGH only (most relevant)
python auto_download_papers.py --tier high --limit 10

# MEDIUM (broader coverage)
python auto_download_papers.py --tier medium --limit 20

# All tiers
python auto_download_papers.py --tier all --limit 50
```

### Custom Graph Building

```bash
# With meta-ontology
python build_graph_with_meta.py --meta-ontology data/graphs/meta_ontology.ttl

# Advanced mode (separate ontology + instances)
python build_graph.py --mode advanced
```

---

## 📚 Next Steps

**For comprehensive documentation:**
- See `README.md` - Complete feature reference with examples
- See `RESEARCH_PIPELINE_GUIDE.txt` - Advanced research workflows
- See `SOURCE_DISCOVERY_EXPANSION_COMPLETE.md` - Technical deep-dive on 8-API discovery

**For detailed analysis:**
- See `analysis/ENHANCED_GRAPH_ANALYSIS.md` - GraphRAG quality metrics (98/100 score)
- See `analysis/HUMAN_READABILITY_ANALYSIS.md` - Guide to editing TTL files

**For Jupyter workflows:**
- Open `notebooks/source_discovery.ipynb` - Interactive source discovery
- Open `notebooks/research_workflow.ipynb` - Advanced research pipeline

---

## ❓ Troubleshooting

### Chat returns "No relevant sources found"
```bash
# Check if sources loaded
ls data/sources/

# Lower relevance threshold in code (features/chat.py)
# Or add more sources to data/sources/
```

### Source discovery finds no results
```bash
# Lower similarity threshold
python auto_discover_sources.py --domain-similarity 0.25

# Or disable semantic filtering
python auto_discover_sources.py --no-semantic-filter
```

### Paper download fails
```bash
# Check if paper is open-access
python download_papers.py "DOI" --verbose

# arXiv papers always work
python download_papers.py "arXiv:1234.5678"
```

### Knowledge graph build errors
```bash
# Check for malformed files in data/sources/
# Remove problematic files temporarily

# Run with verbose output
python -c "from core.rag_engine import VaultRAG; rag = VaultRAG(verbose=True); rag.build_knowledge_graph()"
```

---

## 🧑‍🔬 Philosophy: Researcher Control

This system emphasizes **manual checkpoints** at critical decision points:

1. **Meta-Ontology Editing** - Define your domain structure before extraction
2. **Knowledge Graph Editing** - Refine concepts and relationships in TTL format
3. **Source List Review** - Approve discovered sources before download
4. **Content Review** - Validate downloaded papers before import

**"PKM in your hands"** - Automation assists, but you control the knowledge structure.

---

## 🎯 Quick Decision Guide

**I want to...**

- ❓ **Ask questions about my documents** → Path 1: Simple Chat
- 🕸️ **Build and edit a knowledge graph** → Path 2: Knowledge Graph Research
- 🔍 **Find new sources automatically** → Path 3: Automated Source Discovery
- 📺 **Analyze YouTube videos** → Path 4: YouTube Research
- 🧬 **Control concept extraction with ontology** → Path 5: Meta-Ontology Guided GraphRAG

**Not sure?** Start with **Path 1** (Simple Chat) and explore from there.

---

**System Version:** December 2025  
**GraphRAG Quality Score:** 98/100 (Industry-Standard Metrics)  
**API Coverage:** 8 Research APIs  
**Supported Formats:** PDF, Markdown, TXT, HTML, YouTube Transcripts
