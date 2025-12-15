# UX Integration & Code Cleanup Plan

**Date:** December 15, 2025  
**Purpose:** Integrate new source discovery features into main UX, clean up legacy code, update documentation

---

## 📊 Analysis Summary

### Documentation Files Status

| File | Lines | Purpose | Status | Action |
|------|-------|---------|--------|--------|
| **HANDOUT_SOURCE_DISCOVERY_EXPANSION.md** | 300 | Original requirements spec | Legacy | ➡️ Archive |
| **SOURCE_DISCOVERY_EXPANSION_COMPLETE.md** | 527 | Complete technical reference | Authoritative | ✅ Keep |
| **IMPLEMENTATION_STATUS.md** | 402 | Implementation summary | Redundant | ❓ Consolidate into README |
| **QUICKSTART_EXPANDED_DISCOVERY.md** | 211 | Quick start guide for discovery | Current | ➡️ Merge into QUICKSTART.md |
| **QUICKSTART_GRAPH_DISCOVERY.txt** | 144 | Quick start for graph workflow | Current | ➡️ Merge into QUICKSTART.md |
| **RESEARCH_PIPELINE_GUIDE.txt** | - | Complete research workflow | Current | ✅ Keep (comprehensive guide) |

### Code Files Timeline

**New Discovery Pipeline (Dec 13-15, 2025):**
- ✅ `discover_sources.py` - Gap analysis from knowledge graph
- ✅ `auto_discover_sources.py` - Multi-API search (8 APIs)
- ✅ `prioritize_sources.py` - Embedding-based relevance ranking
- ✅ `download_papers.py` - DOI-based paper downloader
- ✅ `auto_download_papers.py` - Batch downloader with tier filtering
- ✅ `test_expanded_apis.py` - API integration tests

**Core System (Dec 6-11, 2025):**
- ✅ `build_graph.py` - Knowledge graph builder
- ✅ `generate_article_from_graph.py` - Graph → article synthesis
- ✅ `import_urls.py` - Batch URL import
- ✅ `server.py` - Flask chat UI
- ✅ `test_chat.py`, `test_graph.py` - Core system tests

**Research Tools (Dec 9-11, 2025):**
- ✅ `research_priorities.py` - Priority-based research planning
- ✅ `generate_meta_ontology.py` - Meta-ontology generation
- ✅ `build_graph_with_meta.py` - Graph builder with meta-ontology

**Legacy/Older Tests:**
- ⚠️ `test_discovery.py` (Dec 9) - Superseded by test_expanded_apis.py?
- ⚠️ `test_graph_extraction.py` (Dec 10) - Component test
- ⚠️ `test_topic_extraction.py` (Dec 10) - Component test
- ⚠️ `test_relationship_extraction.py` (Dec 13) - Component test

### Test Files Assessment

| Test File | Purpose | Keep? | Reason |
|-----------|---------|-------|--------|
| `test_chat.py` | End-to-end chat test | ✅ Yes | Core system validation |
| `test_graph.py` | Graph building test | ✅ Yes | Core system validation |
| `test_expanded_apis.py` | API integration test | ✅ Yes | Validates 8-API expansion |
| `test_meta_ontology.py` | Meta-ontology test | ✅ Yes | Validates meta-ontology features |
| `test_part4_pipeline.py` | Pipeline integration test | ✅ Yes | Validates full workflow |
| `test_discovery.py` | Old discovery test | ⚠️ Maybe | Check if superseded by test_expanded_apis.py |
| `test_graph_extraction.py` | Component test | ⚠️ Maybe | Check if needed for debugging |
| `test_topic_extraction.py` | Component test | ⚠️ Maybe | Check if needed for debugging |
| `test_relationship_extraction.py` | Component test | ⚠️ Maybe | Check if needed for debugging |
| `test_youtube.py` | YouTube processing test | ✅ Yes | Validates YouTube workflow |

---

## 🎯 Proposed Changes

### Phase 1: README Integration ⭐ (High Priority)

**Current README Structure:**
```
1. Features (lines 1-50)
2. Architecture (lines 50-100)
3. Quick Start (lines 100-130)
4. Knowledge Graphs (lines 130-280)
5. Workflows A/B/C/D (lines 280-400)
6. API Reference (lines 400-500)
7. Quality Metrics (lines 500-535)
```

**Proposed Addition: Option E - Automated Source Discovery**

Insert after "Option D: Knowledge Graph → Article Workflow" (~line 280):

```markdown
### Option E: Automated Source Discovery (NEW) 🔍

**Purpose:** Intelligently discover, prioritize, and import relevant sources using multi-API search and semantic filtering.

**When to use:** When you need to find specific sources related to gaps in your knowledge graph.

#### Complete Workflow (7 Steps)

**Step 1: Identify Coverage Gaps**
```bash
# Analyze knowledge graph against research domain
python discover_sources.py

# Output: data/discovery_report.txt
#   - Coverage scores per topic
#   - Identified gaps (<50% coverage)
#   - 5 targeted search queries
```

**Step 2: Search 8 APIs Automatically**
```bash
# Multi-API search with semantic filtering
python auto_discover_sources.py \
  --report data/discovery_report.txt \
  --min-new-sources 5 \
  --max-per-source 10

# APIs searched:
#   1. EUR-Lex (EU legislation)
#   2. OpenAlex (250M+ papers)
#   3. CORE (100M+ open access)
#   4. DOAJ (open access journals)
#   5. HAL (EU research)
#   6. Zenodo (EU projects)
#   7. arXiv (preprints)
#   8. Semantic Scholar (CS papers)

# Output: data/discovered_urls_expanded.txt (typically 50-100 URLs)
```

**Step 3: Prioritize by Relevance**
```bash
# Rank sources using OpenAI embeddings
python prioritize_sources.py

# Computes semantic similarity to research topics
# Output: data/discovered_urls_prioritized.txt
#   - HIGH (≥0.50 similarity)
#   - MEDIUM (0.40-0.49)
#   - LOW (<0.40)
```

**Step 4: Review Prioritized List** 🧑‍🔬 (Manual Checkpoint)
```bash
# Open the prioritized list
notepad data/discovered_urls_prioritized.txt

# Review the top HIGH relevance sources
# Remove any that don't fit your research
# This is an intentional supervision step
```

**Step 5: Auto-Download Papers**
```bash
# Download HIGH relevance papers automatically
python auto_download_papers.py --tier high --limit 10

# Uses Unpaywall API + Crossref for DOI resolution
# Downloads open-access PDFs to data/sources/
# Success rate: ~70% (varies by publisher)
```

**Step 6: Review Downloaded Content** 🧑‍🔬 (Manual Checkpoint)
```bash
# Check downloaded files
ls data/sources/

# Read a few papers to verify relevance
# Remove any that don't fit
# This is an intentional supervision step
```

**Step 7: Import & Rebuild Knowledge Graph**
```bash
# Import remaining URLs (non-downloadable sources)
python import_urls.py data/discovered_urls_prioritized.txt

# Rebuild knowledge graph with new content
python build_graph.py

# Your knowledge graph now includes:
#   - Downloaded papers (PDFs)
#   - Web articles (HTML/Markdown)
#   - Existing sources
```

#### Advanced Options

**Adjust Relevance Thresholds:**
```bash
# More permissive (exploratory research)
python auto_discover_sources.py --domain-similarity 0.25

# Stricter (narrow domain)
python auto_discover_sources.py --domain-similarity 0.40
```

**Download MEDIUM Relevance Sources:**
```bash
python auto_download_papers.py --tier medium --limit 20
```

**Test Single DOI Download:**
```bash
python download_papers.py "10.1038/sdata.2016.18"
```

#### API Coverage Summary

| API | Content Type | Rate Limit | Auth | Coverage |
|-----|--------------|------------|------|----------|
| EUR-Lex | EU legislation | Unlimited | No | EU Data Act ground truth |
| OpenAlex | Academic papers (all fields) | 10 req/sec | No | 250M+ papers |
| CORE | Open access papers | 10 req/sec | No (basic) | 100M+ papers |
| DOAJ | OA journals/articles | Unlimited | No | Quality OA sources |
| HAL | EU research | 100 req/min | No | French/EU academic |
| Zenodo | EU projects/data | 100 req/hour | No | EU-funded projects |
| arXiv | Preprints (CS/physics/math) | Unlimited | No | Preprint papers |
| Semantic Scholar | CS papers | ~100 req/day | No | CS academic papers |

#### Success Metrics

**Expected Results:**
- 50-100 URLs discovered per run
- 60-70% HIGH relevance (similarity ≥0.50)
- 20-30% MEDIUM relevance (similarity 0.40-0.49)
- 10% LOW relevance (similarity <0.40)
- 60-80% download success rate for open-access papers

**Why Manual Checkpoints?**
1. **Step 4 Review:** Prevents importing irrelevant sources that passed automated filters
2. **Step 6 Review:** Validates downloaded content quality before graph integration
3. **Supervision:** Keeps human oversight in the research loop

#### Troubleshooting

**No results found:**
```bash
# Lower domain similarity threshold
python auto_discover_sources.py --domain-similarity 0.25
```

**All sources filtered out:**
```bash
# Check if semantic filtering is too strict
# Disable semantic filtering to test
python auto_discover_sources.py --no-semantic-filter
```

**Download failures:**
```bash
# Check if DOI is behind paywall
python download_papers.py "10.xxxx/xxxxx" --verbose

# Try arXiv alternative if available
python download_papers.py "arXiv:1234.5678"
```

**Rate limiting errors:**
- EUR-Lex: No limits, should not error
- OpenAlex: Wait 10 seconds between runs
- Semantic Scholar: Wait 24 hours if 429 errors
```

---

### Phase 2: QUICKSTART Consolidation ⭐ (High Priority)

**Action:** Merge `QUICKSTART_EXPANDED_DISCOVERY.md` + `QUICKSTART_GRAPH_DISCOVERY.txt` → `QUICKSTART.md`

**Proposed Structure:**

```markdown
# PKM System Quick Start

## Installation (2 minutes)

```bash
# 1. Clone repository
git clone <repo-url>
cd obsidian-control

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set OpenAI API key
# Create .env file with:
OPENAI_API_KEY=sk-your-key-here
```

## Usage Paths (Choose One)

### Path 1: Simple Chat (Recommended for Beginners)
1. Drop files in `data/sources/`
2. Run `python server.py`
3. Open http://localhost:5000
4. Ask questions

### Path 2: Knowledge Graph Research
1. Add sources to `data/sources/`
2. Build graph: `python build_graph.py`
3. Generate article: `python generate_article_from_graph.py data/graphs/knowledge_graph.ttl`
4. Chat with synthesis: `python server.py`

### Path 3: Automated Source Discovery
1. Identify gaps: `python discover_sources.py`
2. Search APIs: `python auto_discover_sources.py --report data/discovery_report.txt`
3. Prioritize: `python prioritize_sources.py`
4. **[REVIEW]** Check `data/discovered_urls_prioritized.txt`
5. Download: `python auto_download_papers.py --tier high --limit 10`
6. **[REVIEW]** Check `data/sources/` for downloaded papers
7. Import: `python import_urls.py data/discovered_urls_prioritized.txt`
8. Rebuild graph: `python build_graph.py`

### Path 4: YouTube Research
1. Add YouTube URLs to `data/sources/youtube_links.txt`
2. Process transcripts: `python process_youtube.py --article`
3. Chat with content: `python server.py`

## Next Steps

See `README.md` for complete feature documentation.
See `RESEARCH_PIPELINE_GUIDE.txt` for advanced workflows.
```

---

### Phase 3: Documentation Cleanup 🗑️ (Medium Priority)

**Create archive/ directory:**
```bash
mkdir archive
```

**Archive legacy documentation:**
```bash
# Move original spec (now superseded by implementation)
mv HANDOUT_SOURCE_DISCOVERY_EXPANSION.md archive/

# Keep implementation docs (authoritative)
# - SOURCE_DISCOVERY_EXPANSION_COMPLETE.md (technical reference)
# - IMPLEMENTATION_STATUS.md (consolidate into README or archive)
```

**Consolidate IMPLEMENTATION_STATUS.md:**

Option A: Add summary to README features section
Option B: Archive if redundant with SOURCE_DISCOVERY_EXPANSION_COMPLETE.md

**Decision:** Archive IMPLEMENTATION_STATUS.md since it's redundant with SOURCE_DISCOVERY_EXPANSION_COMPLETE.md (which has more detail)

```bash
mv IMPLEMENTATION_STATUS.md archive/
```

---

### Phase 4: Test File Cleanup 🧪 (Low Priority)

**Keep These (Core System Tests):**
- `test_chat.py` - End-to-end chat validation
- `test_graph.py` - Graph building validation
- `test_expanded_apis.py` - 8-API integration test
- `test_meta_ontology.py` - Meta-ontology features
- `test_part4_pipeline.py` - Full pipeline test
- `test_youtube.py` - YouTube processing test

**Review These (Potential Archive):**
- `test_discovery.py` - Check if superseded by test_expanded_apis.py
- `test_graph_extraction.py` - Component test, keep if used for debugging
- `test_topic_extraction.py` - Component test, keep if used for debugging
- `test_relationship_extraction.py` - Component test, keep if used for debugging

**Action:** Create `tests/archive/` and move older component tests if not actively used

```bash
mkdir tests
mkdir tests/archive

# After verification, move older tests
mv test_discovery.py tests/archive/
mv test_graph_extraction.py tests/archive/
mv test_topic_extraction.py tests/archive/
mv test_relationship_extraction.py tests/archive/
```

---

### Phase 5: Architecture Diagram Update 📊 (Medium Priority)

**Current README has text-based architecture** (lines ~50-100). Enhance with discovery pipeline:

```markdown
## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Data Sources                             │
├─────────────────────────────────────────────────────────────────┤
│  Manual: data/sources/ (PDF, MD, HTML, TXT)                     │
│  YouTube: process_youtube.py → data/sources/                    │
│  Discovery: auto_discover_sources.py → 8 APIs → data/sources/   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Core Processing Layer                         │
├─────────────────────────────────────────────────────────────────┤
│  core/rag_engine.py:                                            │
│    - Document loading & chunking                                │
│    - Embedding generation (OpenAI text-embedding-3-small)       │
│    - Knowledge graph building (RDF + SPARQL)                    │
│    - Hybrid search (keyword + semantic + graph)                 │
│                                                                  │
│  core/document_processor.py:                                    │
│    - PDF extraction (PyPDF2)                                    │
│    - HTML extraction (BeautifulSoup + html2text)                │
│    - YouTube transcripts (youtube-transcript-api)               │
│                                                                  │
│  core/web_discovery.py:                                         │
│    - 8 API integrations (EUR-Lex, OpenAlex, CORE, etc.)        │
│    - Article extraction (trafilatura)                           │
│    - URL validation                                             │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Knowledge Graph                             │
├─────────────────────────────────────────────────────────────────┤
│  data/graphs/knowledge_graph.ttl (RDF Turtle format)           │
│    - 708 triples from 17 documents (example scale)              │
│    - Domain concepts (106 instances)                            │
│    - Topic nodes (11 clusters)                                  │
│    - Document chunks (22 pieces)                                │
│    - Relationships (mentionsConcept, coversConcept, etc.)       │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Application Layer                           │
├─────────────────────────────────────────────────────────────────┤
│  features/chat.py:                                              │
│    - VaultChat class (conversational interface)                 │
│    - Context window management                                  │
│    - Source citation with relevance scores                      │
│                                                                  │
│  features/research_agent.py:                                    │
│    - Multi-source research workflows                            │
│    - Literature review generation                               │
│                                                                  │
│  features/artifacts.py:                                         │
│    - Article generation from knowledge graph                    │
│    - Synthesis of multiple sources                              │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         User Interfaces                          │
├─────────────────────────────────────────────────────────────────┤
│  Web UI: server.py (Flask) → http://localhost:5000             │
│  Notebooks: notebooks/source_discovery.ipynb                    │
│  CLI: test_chat.py, interactive_chat.py                        │
└─────────────────────────────────────────────────────────────────┘

                    Discovery Pipeline (NEW)
                    ════════════════════════
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│ discover_sources │      │ auto_discover    │      │ prioritize       │
│ .py              │─────▶│ _sources.py      │─────▶│ _sources.py      │
│ (Gap analysis)   │      │ (8 APIs)         │      │ (Embeddings)     │
└──────────────────┘      └──────────────────┘      └──────────────────┘
                                                              │
                                                              ▼
                                                     🧑‍🔬 MANUAL REVIEW
                                                              │
                                                              ▼
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│ build_graph.py   │      │ import_urls.py   │      │ auto_download    │
│ (Rebuild graph)  │◀─────│ (Import sources) │◀─────│ _papers.py       │
└──────────────────┘      └──────────────────┘      │ (Download PDFs)  │
                                 ▲                   └──────────────────┘
                                 │                            │
                                 │                            ▼
                                 │                   🧑‍🔬 MANUAL REVIEW
                                 │                            │
                                 └────────────────────────────┘
```
```

---

### Phase 6: Dependencies Verification ✅ (High Priority)

**Check current requirements.txt:**

```bash
cat requirements.txt
```

**Expected dependencies (verify versions):**
```txt
# Core
openai>=1.0.0
flask>=3.1.2
rdflib>=7.4.0
numpy>=1.24.0
python-dotenv>=1.0.0

# Document Processing
pypdf2>=3.0.0
beautifulsoup4>=4.12.0
html2text>=2024.0.0
youtube-transcript-api>=1.2.3
lxml>=4.9.0
trafilatura>=1.6.0

# Discovery & Prioritization (NEW)
sentence-transformers>=2.2.0
fuzzywuzzy>=0.18.0
python-Levenshtein>=0.21.0

# Optional (if semantic filtering enabled)
# torch>=2.1.0  # Note: PyTorch 2.0.0 incompatible with sentence-transformers
```

**Action:** Verify all dependencies are listed with appropriate version constraints

---

### Phase 7: Update Features List in README 🎯 (Medium Priority)

**Add to Features section** (after line ~50):

```markdown
### 🔍 Automated Source Discovery (NEW)

- **Multi-API Search**: Query 8 research APIs simultaneously (EUR-Lex, OpenAlex, CORE, DOAJ, HAL, Zenodo, arXiv, Semantic Scholar)
- **Intelligent Prioritization**: Rank sources by semantic relevance using OpenAI embeddings
- **Auto-Download**: Fetch open-access papers via DOI using Unpaywall and Crossref APIs
- **Gap Analysis**: Identify coverage gaps in knowledge graph to guide source discovery
- **Manual Supervision**: Built-in checkpoints for human oversight of discovered/downloaded sources
- **Success Rate**: 50-100 URLs discovered per run, 60-70% high relevance, 60-80% download success

### 🧠 Knowledge Graph Intelligence

(existing content...)
```

---

## 📋 Implementation Checklist

### Immediate Actions (Session Complete)

- [x] ✅ Analyze file timestamps and identify legacy files
- [x] ✅ Map complete source discovery workflow with manual checkpoints
- [ ] 🔄 Update README.md with Option E workflow
- [ ] 🔄 Create consolidated QUICKSTART.md
- [ ] 🔄 Archive legacy documentation files
- [ ] 🔄 Update architecture diagram in README
- [ ] 🔄 Verify requirements.txt dependencies
- [ ] 🔄 Update features list in README

### Follow-Up Actions (Next Session)

- [ ] Test complete workflow end-to-end after README updates
- [ ] Review and archive older test files if not actively used
- [ ] Create tests/archive/ directory for component tests
- [ ] Update .github/copilot-instructions.md with new workflow
- [ ] Consider adding workflow diagram visualization (Mermaid or image)

---

## 🎯 Key Design Principles Preserved

### Manual Supervision Checkpoints 🧑‍🔬

**Why they exist:**
1. **After prioritization** (Step 4): Prevent importing irrelevant sources
2. **After download** (Step 6): Validate content quality before graph integration

**Do NOT automate away:**
- Human review of prioritized list
- Content quality verification of downloaded papers
- Manual removal of off-topic sources

### Intentional Workflow Separation

**Scripts are separate by design:**
- `discover_sources.py` - Gap analysis (can run independently)
- `auto_discover_sources.py` - Discovery (can run with custom queries)
- `prioritize_sources.py` - Ranking (can run on any URL list)
- `auto_download_papers.py` - Download (can run on any prioritized list)
- `import_urls.py` - Import (final integration step)

**Benefits:**
- Each step can be debugged independently
- Users can skip/repeat steps as needed
- Manual review between steps preserves control

### Documentation Philosophy

**Keep:**
- `README.md` - Complete feature reference (expand with new workflow)
- `SOURCE_DISCOVERY_EXPANSION_COMPLETE.md` - Technical deep-dive
- `RESEARCH_PIPELINE_GUIDE.txt` - Advanced research workflows
- `QUICKSTART.md` - Quick start for all major workflows

**Archive:**
- `HANDOUT_SOURCE_DISCOVERY_EXPANSION.md` - Original spec (superseded)
- `IMPLEMENTATION_STATUS.md` - Summary (redundant with complete doc)
- `QUICKSTART_EXPANDED_DISCOVERY.md` - Merge into QUICKSTART.md
- `QUICKSTART_GRAPH_DISCOVERY.txt` - Merge into QUICKSTART.md

---

## 📈 Expected Outcomes

### After Integration

**Users will have:**
1. **Clear entry points**: README workflows guide users to correct tool
2. **Consolidated quick start**: Single QUICKSTART.md for all major paths
3. **Clean codebase**: No redundant documentation, archived legacy files
4. **Comprehensive discovery**: Full 7-step automated workflow documented
5. **Manual control**: Clear supervision checkpoints in workflow

### Documentation Structure (Post-Cleanup)

```
📄 README.md                               (Complete feature reference, 600+ lines)
📄 QUICKSTART.md                           (Consolidated quick start, ~200 lines)
📄 RESEARCH_PIPELINE_GUIDE.txt             (Advanced workflows)
📄 SOURCE_DISCOVERY_EXPANSION_COMPLETE.md  (Technical deep-dive for discovery)
📄 requirements.txt                        (All dependencies with versions)

📁 archive/
   📄 HANDOUT_SOURCE_DISCOVERY_EXPANSION.md
   📄 IMPLEMENTATION_STATUS.md
   📄 QUICKSTART_EXPANDED_DISCOVERY.md
   📄 QUICKSTART_GRAPH_DISCOVERY.txt

📁 tests/
   📁 archive/
      📄 test_discovery.py (if superseded)
      📄 test_graph_extraction.py (if not actively used)
      📄 test_topic_extraction.py (if not actively used)
```

---

## 🚀 Next Steps

1. **Review this plan** - Confirm proposed changes align with vision
2. **Execute Phase 1** - Update README with Option E workflow
3. **Execute Phase 2** - Create consolidated QUICKSTART.md
4. **Execute Phase 3** - Archive legacy documentation
5. **Execute Phase 6** - Verify requirements.txt
6. **Execute Phase 7** - Update features list
7. **Execute Phase 4** - Clean up test files (optional)
8. **Execute Phase 5** - Enhance architecture diagram (optional)

**Estimated Time:** 1-2 hours for high-priority phases (1, 2, 3, 6, 7)

---

## ✅ Approval Required

**Questions for User:**

1. **Documentation Consolidation**: Approve archiving HANDOUT and IMPLEMENTATION_STATUS?
2. **QUICKSTART Merge**: Approve merging two quickstart files into one?
3. **Test File Cleanup**: Should we archive older component tests or keep all?
4. **Architecture Diagram**: ASCII art in README or separate image file?
5. **README Length**: Option E section is ~150 lines - too detailed or appropriate?

**After approval, proceed with implementation in order of priority.**

