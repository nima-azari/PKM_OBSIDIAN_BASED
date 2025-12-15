# Researcher-in-the-Loop Pipeline Guide

**Complete Iterative Research Workflow with Human Supervision**

---

## 🎯 Philosophy

This pipeline places **YOU, the researcher**, at the center of knowledge curation. The system assists but never replaces human judgment. At each critical stage, you provide guidance through:

1. **Importance ratings** (1-5) - Weight sources by relevance
2. **Meta-ontology supervision** - Define your domain model
3. **Discovery curation** - Approve new sources before integration

---

## 📊 Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────┐
│              RESEARCHER-IN-THE-LOOP PIPELINE                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Phase 1: INITIALIZATION                                       │
│  ├─ 1.1 Annotate Initial Sources (1-5 importance)              │
│  ├─ 1.2 Build/Refine Meta-Ontology (researcher supervised)     │
│  └─ 1.3 Build Weighted Knowledge Graph                         │
│                                                                 │
│  Phase 2: DISCOVERY                                            │
│  ├─ 2.1 Gap Analysis (meta-ontology guided)                    │
│  ├─ 2.2 Multi-API Search (24+ APIs, semantic filtering)        │
│  └─ 2.3 Generate Prioritized Discovery List                    │
│                                                                 │
│  Phase 3: INTEGRATION (Feedback Loop)                          │
│  ├─ 3.1 Researcher Reviews Discovery List (manual curation)    │
│  ├─ 3.2 Download Papers (DOI auto-download)                    │
│  ├─ 3.3 Import Web Sources                                     │
│  ├─ 3.4 Annotate New Sources (1-5 importance)                  │
│  ├─ 3.5 Refine Meta-Ontology (with new insights)               │
│  └─ 3.6 Rebuild Weighted Knowledge Graph                       │
│                                                                 │
│  Phase 4: RESEARCH                                             │
│  └─ 4.1 Graph-Guided Chat (importance-weighted retrieval)      │
│                                                                 │
│  ↻ Iterate: Phase 2 → Phase 3 → Phase 4 (continuous)          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Getting Started

### Prerequisites

```bash
# Ensure you have sources in data/sources/
ls data/sources/

# If empty, add your initial research documents
cp my_paper.pdf data/sources/
cp article.md data/sources/
```

### Check Pipeline Status

```bash
python scripts/research_pipeline.py --status
```

**Output:**
```
📊 RESEARCH PIPELINE STATUS
═══════════════════════════════════════════════════════════════

🎯 Current Phase: UNINITIALIZED
🔄 Iterations: 0
⏱️  Last Update: Never

📚 Resources:
   Sources: 15 files
   Annotations: 0/15 ⚠️
   Meta-Ontology: ✗ Not built
   Knowledge Graph: ✗ Not built

🎯 Next Steps:
   1. Run: python scripts/research_pipeline.py --init
```

---

## 📝 PHASE 1: INITIALIZATION

### What Happens

1. **Interactive annotation** - You rate each source 1-5
2. **Meta-ontology generation** - AI builds domain model from your description
3. **Weighted graph construction** - Graph built with importance weights

### Run Phase 1

```bash
python scripts/research_pipeline.py --init
```

### Step 1.1: Annotate Sources

**You will see:**

```
═══════════════════════════════════════════════════════════════
📄 Source: EU_Data_Act_Overview.pdf
📝 Title: The EU Data Act Explained
═══════════════════════════════════════════════════════════════

📖 Preview:
   The European Union's Data Act represents a landmark piece
   of legislation aimed at ensuring fair access to and use...

🎯 Importance Levels:
   1 - REFERENCE - Background context only
   2 - SUPPORTING - Provides supporting evidence
   3 - RELEVANT - Directly relevant to research
   4 - KEY - Key contribution to domain
   5 - CRITICAL - Essential primary source

⭐ Enter importance (1-5, or 's' to skip): 
```

**Your Action:**
- Read preview
- Enter rating 1-5 based on:
  - **5 (CRITICAL)**: Essential primary source, cite frequently
  - **4 (KEY)**: Major contribution, core to research
  - **3 (RELEVANT)**: Directly relevant, good supporting material
  - **2 (SUPPORTING)**: Provides context/evidence, referenced occasionally
  - **1 (REFERENCE)**: Background only, rarely cited

**Tips:**
- Rate honestly - this guides retrieval prioritization
- Press 's' to skip and annotate later
- You can update ratings anytime with:
  ```bash
  python scripts/annotate_sources.py --update SOURCE_FILE.pdf
  ```

### Step 1.2: Meta-Ontology Generation

**You will be asked:**

```
Please describe your research domain:
   Example: 'EU Data Act, semantic web, knowledge graphs, data portability'

🔍 Domain: 
```

**Your Action:**
- Describe your research focus in one sentence
- Include key concepts, technologies, regulations
- Example: *"EU Data Act implementation using semantic web technologies, knowledge graphs, and RDF for data portability and interoperability"*

**What Happens:**
- GPT-4 analyzes your description
- Generates ontology classes (DataPortability, SemanticWeb, etc.)
- Defines relationships between concepts
- Saves to `data/graphs/meta_ontology.ttl`

**Review Output:**
```bash
# View generated ontology
cat data/graphs/meta_ontology.ttl | Select-Object -First 100
```

### Step 1.3: Build Weighted Graph

**Automatic - No Action Required**

The system:
- Loads all annotated sources
- Weights chunks by source importance
- Aligns concepts to meta-ontology
- Builds 3-layer graph (Info → Domain → Topic)
- Exports to `data/graphs/knowledge_graph.ttl`

**Output:**
```
✅ INITIALIZATION COMPLETE

📋 What was created:
   ✓ Source annotations: data/source_annotations.yaml
   ✓ Meta-ontology: data/graphs/meta_ontology.ttl
   ✓ Knowledge graph: data/graphs/knowledge_graph.ttl

🎯 Next Steps:
   1. Review meta-ontology (optional refinement)
   2. Run discovery: python scripts/research_pipeline.py --discover
   3. Or start chat: python scripts/interactive_chat.py
```

---

## 🔍 PHASE 2: DISCOVERY

### What Happens

1. **Gap analysis** - Identifies low-coverage areas in your knowledge
2. **Multi-API search** - Searches 24+ APIs with semantic filtering
3. **Priority ranking** - Organizes results by relevance (HIGH/MEDIUM/LOW)

### Run Phase 2

```bash
python scripts/research_pipeline.py --discover
```

### Step 2.1: Gap Analysis

**Automatic - Shows Results:**

```
📊 Analyzing knowledge gaps...

Coverage Analysis:
  Data Portability: 38/100 (1 instance, 4 chunks, 2 relations) ⚠️
  Data Governance: 67/100 (2 instances, 11 chunks, 5 relations)
  Semantic Web: 82/100 (3 instances, 15 chunks, 7 relations) ✓

Gaps Identified: 1 class below 50%

Generated Queries:
  1. EU Data Act data portability implementation case studies
  2. Cloud provider data portability technical standards
  3. Data portability regulatory compliance frameworks
```

### Step 2.2: Multi-API Search

**Automatic - 24+ APIs Searched:**

```
🌐 Searching 24+ APIs for relevant sources...

  Scientific:
    ✓ Crossref: 5 results
    ✓ OpenAlex: 7 results
    ⚠️ Semantic Scholar: Rate limited
  
  Scholarly:
    ✓ CORE: 4 results
    ✓ arXiv: 6 results
    ✓ DOAJ: 3 results
  
  News:
    ✓ GDELT: 2 results
  
  Total: 27 candidate sources
  After deduplication: 18 sources
  After semantic filtering: 12 sources
```

### Step 2.3: Prioritized List Generated

**Output File:** `data/discovered_urls.txt`

```
# Discovered Sources - 2025-12-15
# Total: 12 sources
# Semantic filtering: ✓ (domain similarity > 0.35)

## HIGH RELEVANCE (6 sources)

### Data Portability in the EU Data Act: Technical Implementation
URL: https://doi.org/10.1234/example1
Source: Crossref
Domain Similarity: 0.82
Reason: Directly addresses data portability implementation

### Cloud Data Portability Standards and Best Practices
URL: https://arxiv.org/abs/2401.12345
Source: arXiv
Domain Similarity: 0.78
Reason: Technical standards for cloud portability

## MEDIUM RELEVANCE (4 sources)

### Semantic Web Technologies for Data Interoperability
URL: https://doi.org/10.5678/example2
Source: OpenAlex
Domain Similarity: 0.65

## LOW RELEVANCE (2 sources)

### General Data Management Frameworks
URL: https://core.ac.uk/...
Source: CORE
Domain Similarity: 0.42
```

**🎯 RESEARCHER ACTION REQUIRED:**

```
✅ DISCOVERY COMPLETE

📝 Discovery list saved to: data/discovered_urls.txt

🎯 RESEARCHER ACTION REQUIRED:
   1. Open and review: data/discovered_urls.txt
   2. Remove any unwanted sources (manual curation)
   3. Save the file with your final selections
   4. Run: python scripts/research_pipeline.py --integrate
```

---

## 🔄 PHASE 3: INTEGRATION (Critical Feedback Loop!)

### Your Manual Curation Task

**Before running Phase 3:**

1. **Open:** `data/discovered_urls.txt`
2. **Review:** Each discovered source
3. **Edit:** Remove unwanted sources (delete entire section)
4. **Save:** File with your final selections
5. **Proceed:** Run integration

**Example Edits:**

```
## HIGH RELEVANCE (6 sources)

### Data Portability in the EU Data Act: Technical Implementation
URL: https://doi.org/10.1234/example1
Source: Crossref
Domain Similarity: 0.82
✓ KEEP - Perfect match

### Cloud Data Portability Standards and Best Practices
URL: https://arxiv.org/abs/2401.12345
Source: arXiv
Domain Similarity: 0.78
✓ KEEP - Highly relevant

### Some Tangentially Related Paper
❌ DELETE THIS ENTIRE SECTION - Not relevant enough
```

**After Editing:**
```
## HIGH RELEVANCE (2 sources)

### Data Portability in the EU Data Act: Technical Implementation
URL: https://doi.org/10.1234/example1

### Cloud Data Portability Standards and Best Practices
URL: https://arxiv.org/abs/2401.12345
```

### Run Phase 3

```bash
python scripts/research_pipeline.py --integrate
```

### Step 3.1: Auto-Download Papers

**Automatic - Processes DOIs:**

```
📥 Step 1: Download Papers from DOIs

Found 2 DOI links in discovery list

[1/2] Downloading: 10.1234/example1
  ✓ Downloaded from Unpaywall (open access)
  ✓ Saved to: data/sources/Data_Portability_EU_Data_Act.pdf

[2/2] Downloading: arxiv:2401.12345
  ✓ Downloaded from arXiv
  ✓ Saved to: data/sources/Cloud_Data_Portability_Standards.pdf

✅ Downloaded 2/2 papers successfully
```

### Step 3.2: Import Web Sources

**Automatic - Imports Non-DOI URLs:**

```
📥 Step 2: Import Web Sources

Processing 0 web URLs
(All sources were DOIs, downloaded in Step 1)
```

### Step 3.3: Annotate New Sources

**Interactive - Rate New Sources:**

```
📝 Step 3: Annotate New Sources
   Rate the importance of newly added sources

Press Enter to start annotation...

═══════════════════════════════════════════════════════════════
Progress: [1/2]
📄 Source: Data_Portability_EU_Data_Act.pdf
📝 Title: Data Portability in the EU Data Act: Technical Implementation
═══════════════════════════════════════════════════════════════

📖 Preview:
   This paper analyzes the technical requirements for implementing
   data portability provisions under the EU Data Act...

🎯 Importance Levels:
   1 - REFERENCE - Background context only
   2 - SUPPORTING - Provides supporting evidence
   3 - RELEVANT - Directly relevant to research
   4 - KEY - Key contribution to domain
   5 - CRITICAL - Essential primary source

⭐ Enter importance (1-5, or 's' to skip): 5
📝 Add note (optional): Critical analysis of portability implementation

✓ Annotated: 5/5 - CRITICAL - Essential primary source
```

### Step 3.4: Refine Meta-Ontology

**Interactive - Update Domain Model:**

```
🔄 Step 4: Refine Meta-Ontology
   Updating domain model with new concepts...

Refine meta-ontology with new sources? (y/n, default: y): y

   ✓ Backed up to: data/graphs/meta_ontology.ttl.backup

   Current domain focus + new insights?
   🔍 Domain (or Enter to skip): EU Data Act, semantic web, knowledge graphs, data portability, technical implementation standards, cloud interoperability

Generating refined meta-ontology...
✓ Updated meta-ontology with:
   - 3 new classes (TechnicalStandards, CloudInteroperability, ImplementationFrameworks)
   - 5 new relationships
```

### Step 3.5: Rebuild Knowledge Graph

**Automatic - Integrates Everything:**

```
🕸️  Step 5: Rebuild Knowledge Graph
   Integrating new sources with updated weights...

Building knowledge graph from 17 documents...
  Chunking: enabled
  Topic extraction: enabled
  Meta-ontology alignment: enabled
  
Graph built: 1043 triples
  Documents: 17 (+2)
  Chunks: 35 (+5)
  Domain Concepts: 231 (+22)
  Topic Nodes: 12 (+1)

✓ Built graph with 1043 triples
```

**Output:**

```
✅ INTEGRATION COMPLETE

🔄 Iteration 2 finished

📊 Updated Statistics:
   Sources: 17 files (+2)
   Annotations: 17/17 (100%) ✓
   Critical sources: 3
   Key sources: 7
   Relevant sources: 5
   Supporting sources: 2

🎯 Next Steps:
   1. Start research chat:
      python scripts/interactive_chat.py

   2. Or discover more sources:
      python scripts/research_pipeline.py --discover
```

---

## 💬 PHASE 4: RESEARCH (Graph-Guided Chat)

### Start Interactive Chat

```bash
python scripts/interactive_chat.py
```

### How Importance Weights Are Used

The chat system **prioritizes retrieval** based on your annotations:

1. **Critical sources (5)** - Retrieved first, highest weight
2. **Key sources (4)** - High priority
3. **Relevant sources (3)** - Standard priority
4. **Supporting sources (2)** - Lower priority
5. **Reference sources (1)** - Retrieved only if needed

**Example Chat Session:**

```
Knowledge Graph Chat Interface
═══════════════════════════════════════════════════════════════
Loaded 17 documents, 1043 triples, 231 concepts

You: What are the technical implementation requirements for EU Data Act data portability?

🔍 Retrieving relevant sources...
  Graph-guided retrieval with importance weighting...
  Found 8 relevant sources

📖 Generating answer...

The EU Data Act establishes several technical implementation requirements
for data portability:

1. **Standardized Data Formats** [5]
   - Use of RDF/RDFS/OWL for semantic interoperability
   - JSON-LD for web-based data exchange
   - Support for DCAT vocabularies for data cataloging

2. **API Requirements** [5]
   - RESTful APIs with OpenAPI specifications
   - OAuth 2.0 for secure authorization
   - Rate limiting and bulk export capabilities

3. **Cloud Provider Obligations** [4]
   - 30-day data export window
   - Machine-readable formats required
   - No fees for standard exports

Sources:
  [5] 📌 Data_Portability_EU_Data_Act.pdf (CRITICAL)
      📄 Chunk 3, Relevance: 0.94
  
  [5] 📌 Cloud_Data_Portability_Standards.pdf (CRITICAL)
      📄 Chunk 2, Relevance: 0.89
  
  [4] 🔑 EU_Data_Act_Technical_Standards.pdf (KEY)
      📄 Chunk 5, Relevance: 0.82
```

**Notice:**
- Critical sources [5] appear first
- Importance level shown in sources (📌 CRITICAL, 🔑 KEY, ✓ RELEVANT)
- Retrieval prioritizes high-importance sources

---

## 🔄 ITERATIVE WORKFLOW

### Iteration Pattern

```
Phase 1: Initialize (once)
   ↓
Phase 2: Discover → Phase 3: Integrate → Phase 4: Research
   ↑                                            ↓
   └──────────── Repeat as needed ──────────────┘
```

### Example Multi-Iteration Research

**Iteration 1:**
```bash
# Initial setup
python scripts/research_pipeline.py --init       # 15 sources annotated
python scripts/research_pipeline.py --discover   # Found 12 new sources
# Edit data/discovered_urls.txt (keep 5)
python scripts/research_pipeline.py --integrate  # Now 20 sources
```

**Iteration 2:**
```bash
# Focus on specific gap
python scripts/research_pipeline.py --discover   # Found 8 sources on portability
# Edit data/discovered_urls.txt (keep 3)
python scripts/research_pipeline.py --integrate  # Now 23 sources
```

**Iteration 3:**
```bash
# Deep dive into technical standards
python scripts/research_pipeline.py --discover   # Found 15 sources on standards
# Edit data/discovered_urls.txt (keep 7)
python scripts/research_pipeline.py --integrate  # Now 30 sources
```

### Check Progress

```bash
python scripts/research_pipeline.py --status
```

**Output After 3 Iterations:**
```
📊 RESEARCH PIPELINE STATUS

🎯 Current Phase: READY_FOR_CHAT
🔄 Iterations: 3
⏱️  Last Update: 2025-12-15 14:30

📚 Resources:
   Sources: 30 files
   Annotations: 30/30 (100%) ✓
   Meta-Ontology: ✓ Built (refined 2 times)
   Knowledge Graph: ✓ Built (1847 triples)

📊 Coverage Improvement:
   Iteration 1: Data Portability 38/100 ⚠️
   Iteration 2: Data Portability 64/100 ↑
   Iteration 3: Data Portability 89/100 ✓
```

---

## 📋 Quick Command Reference

### Pipeline Commands

```bash
# Check status
python scripts/research_pipeline.py --status

# Initialize (first time only)
python scripts/research_pipeline.py --init

# Discover new sources
python scripts/research_pipeline.py --discover

# Integrate after manual curation
python scripts/research_pipeline.py --integrate

# Reset pipeline state
python scripts/research_pipeline.py --reset
```

### Annotation Commands

```bash
# Annotate all sources
python scripts/annotate_sources.py

# Annotate only new sources
python scripts/annotate_sources.py --new-only

# Update specific source
python scripts/annotate_sources.py --update SOURCE_FILE.pdf

# Show statistics
python scripts/annotate_sources.py --stats

# Export weighted list
python scripts/annotate_sources.py --export data/weighted_sources.txt
```

### Chat & Research

```bash
# Start interactive chat
python scripts/interactive_chat.py

# Generate synthesis article
python scripts/generate_article_from_graph.py data/graphs/knowledge_graph.ttl
```

---

## 💡 Best Practices

### Annotation Guidelines

1. **Be Consistent:**
   - Define your own criteria for each level
   - Document your rating rationale in notes
   - Re-rate if research focus shifts

2. **Use Full Range:**
   - Don't rate everything 3-4
   - Be honest about source quality
   - Critical (5) should be <20% of sources

3. **Add Notes:**
   - Explain why a source is critical
   - Note specific sections of interest
   - Link related sources in notes

### Discovery Curation

1. **Review Carefully:**
   - Don't auto-accept all discovered sources
   - Check HIGH relevance sources manually
   - Remove duplicates or outdated sources

2. **Quality Over Quantity:**
   - 5 high-quality sources > 20 mediocre ones
   - Focus on filling specific gaps
   - Prefer recent publications (unless historical context)

3. **Balance Coverage:**
   - Ensure diverse perspectives
   - Mix academic and practical sources
   - Include specifications/standards

### Meta-Ontology Refinement

1. **Start Broad, Refine Iteratively:**
   - Initial: General domain description
   - Iteration 2+: Add specific concepts discovered

2. **Align with Research Questions:**
   - Ontology should reflect what you're investigating
   - Add classes for emerging themes
   - Remove obsolete concepts

3. **Review Generated Ontology:**
   - Check `data/graphs/meta_ontology.ttl`
   - Verify classes make sense
   - Manual editing supported (TTL is human-readable)

---

## 🐛 Troubleshooting

### "No sources found to annotate"

```bash
# Check sources directory
ls data/sources/

# Add sources first
cp my_research/*.pdf data/sources/
```

### "Discovery returns no results"

```bash
# Check if OpenAI API key is set
echo $env:OPENAI_API_KEY

# Try with lower domain similarity
python scripts/auto_discover_sources.py --domain-similarity 0.25
```

### "Downloaded papers are corrupted"

```bash
# Some DOIs may be paywalled
# Check data/sources/FAILED_DOWNLOADS.txt for list

# Alternative: Manual download then import
python scripts/import_urls.py manual_urls.txt
```

### "Annotation file is corrupt"

```bash
# Backup exists
cp data/source_annotations.yaml.backup data/source_annotations.yaml

# Or reset annotations (careful!)
rm data/source_annotations.yaml
python scripts/annotate_sources.py
```

---

## 📚 Advanced Features

### Manual Meta-Ontology Editing

```bash
# Edit directly (TTL format)
code data/graphs/meta_ontology.ttl

# After editing, rebuild graph
python scripts/build_graph.py --meta-ontology data/graphs/meta_ontology.ttl
```

### Custom Importance Weighting in Retrieval

Edit `core/rag_engine.py` to customize weight formula:

```python
# Default: Linear scaling
weight = annotation['importance'] / 5.0

# Alternative: Exponential (favors critical sources more)
weight = (annotation['importance'] ** 2) / 25.0

# Alternative: Threshold (only 4-5 rated)
weight = 1.0 if annotation['importance'] >= 4 else 0.3
```

### Batch Discovery for Multiple Topics

```bash
# Create custom discovery queries
cat > custom_queries.txt << EOF
Data portability technical implementation
Cloud provider compliance frameworks
Semantic web interoperability standards
EOF

# Run discovery with custom queries
python scripts/auto_discover_sources.py --queries custom_queries.txt
```

---

## ✅ Success Criteria

You've successfully set up the pipeline when:

- ✓ All sources annotated (100% coverage)
- ✓ Meta-ontology reflects your research domain
- ✓ Knowledge graph built with 500+ triples
- ✓ At least 1 discovery→integration cycle completed
- ✓ Chat returns relevant, well-cited answers

**You're ready to research! 🎉**

---

## 📖 Related Documentation

- **COMPLETE_PIPELINE_WALKTHROUGH.md** - Technical details
- **API_EXPANSION_COMPLETE.md** - API integration guide
- **README.md** - Project overview

---

**Generated:** 2025-12-15  
**Pipeline Version:** 2.0 (Researcher-in-the-Loop)
