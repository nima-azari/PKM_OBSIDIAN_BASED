# PKM GraphRAG v2: Complete Workflow Guide

## Quick Start: From Sources to Research

### Phase 1: Initialize (First Time Setup)

#### Step 1: Add Your Sources
```powershell
# Drop your research files into data/sources/
cp your_paper.pdf data/sources/
cp research_notes.md data/sources/
cp article.html data/sources/

# Verify files loaded
ls data/sources/
```

#### Step 2: Annotate Source Importance
```powershell
# Launch interactive annotation tool
python scripts/annotate_sources.py

# For each source:
# - Rate importance: 1-5 (5 = CRITICAL, 1 = REFERENCE)
# - Add category: theory/regulation/industry/etc.
# - Add tags: [linked-data, eu-data-act, etc.]
# - Add notes (optional)

# Output: data/source_annotations.yaml
```

**Rating Guide:**
- **5 (CRITICAL)**: Core papers, main regulations, foundational texts
- **4 (KEY)**: Important supporting evidence, major case studies
- **3 (USEFUL)**: Relevant context, related research
- **2 (REFERENCE)**: Background information, definitions
- **1 (MINIMAL)**: Tangential content, low relevance

#### Step 3: Generate Meta-Ontology
```powershell
# Define your research domain structure
python scripts/generate_meta_ontology.py

# Prompt: Describe your research focus
# Example: "EU Data Act compliance, Linked Data technologies, 
#          data portability, vendor lock-in prevention"

# Output: data/graphs/meta_ontology.ttl
```

#### Step 4: Visualize Meta-Ontology (SUPERVISION ASSISTANT)
```powershell
# Launch interactive visualization notebook
jupyter notebook data/graphs/visualize_graphs.ipynb

# Run the notebook cells (Shift+Enter) to:
# - Visualize meta-ontology as interactive network graph
# - See classes and their relationships
# - Identify missing concepts or connections
# - View statistics (concept counts, top connections)
# - Export to HTML for sharing

# The visualization helps you understand:
# - Which concepts are central (high connections)
# - Which concepts are isolated (need more relationships)
# - Overall domain structure completeness
```

**What to look for in the visualization:**
- **Isolated nodes**: Classes with no relationships (add properties)
- **Central hubs**: Over-connected concepts (might need splitting)
- **Missing links**: Expected relationships that aren't present
- **Naming issues**: Labels that need clarification

#### Step 5: Auto-Connect Isolated Nodes (LLM-POWERED)
```powershell
# Use LLM to evaluate and connect disconnected nodes
python scripts/evaluate_meta_ontology.py

# What it does:
# - Identifies nodes with 0 connections
# - For each isolated node, LLM evaluates connection to other nodes
# - Adds relationship if relevance score > 0.6
# - Suggests appropriate relationship types
# - Saves updated meta-ontology

# Customize threshold (default: 0.6)
python scripts/evaluate_meta_ontology.py --threshold 0.7

# Output: Updated data/graphs/meta_ontology.ttl
```

**How it works:**
- LLM compares each isolated node with all connected nodes
- Evaluates semantic relationship relevance (0.0-1.0)
- Suggests relationship type (uses existing or creates new)
- Only adds connections above threshold (prevents noise)

#### Step 6: Review & Edit Meta-Ontology (MANUAL CHECKPOINT)
```powershell
# Open in your editor
code data/graphs/meta_ontology.ttl

# Add/modify based on visualization insights:
# - Add missing domain concepts (new classes)
# - Define relationships between concepts (properties)
# - Refine class hierarchies (rdfs:subClassOf)
# - Improve labels and descriptions

# Save when ready
```

#### Step 7: Build Knowledge Graph
```powershell
# Build graph with meta-ontology supervision
python scripts/build_graph_with_meta.py

# What it does:
# - Loads sources weighted by importance ratings
# - Extracts concepts guided by meta-ontology
# - Creates relationships based on ontology properties
# - Builds topic clusters

# Output: data/graphs/knowledge_graph.ttl
```

#### Step 8: Visualize Knowledge Graph (OPTIONAL)
```powershell
# Return to visualization notebook
jupyter notebook data/graphs/visualize_graphs.ipynb

# Scroll down to "Knowledge Graph Visualization" section
# Run those cells to see:
# - Documents (blue nodes)
# - Concepts (green nodes)
# - Topics (orange nodes)
# - Chunk groups (gray nodes)
# - How everything connects

# Useful for quality checking:
# - Are concepts properly linked to documents?
# - Do topics cover relevant concepts?
# - Are there orphaned nodes?
```

---

### Phase 2: Discover (Find Knowledge Gaps)

#### Step 9: Analyze Coverage Gaps
```powershell
python scripts/discover_sources.py

# Outputs:
# - Coverage score per meta-ontology class (0-100)
# - Identifies classes with <50% coverage
# - Generates 5 targeted search queries
# - Saves to: data/discovery_report.txt
```

**Review the report:**
```powershell
cat data/discovery_report.txt
```

Look for:
- **0% coverage classes**: Critical - need manual seeding! ⚠️
- **<30% coverage**: High priority for discovery
- **30-60% coverage**: Medium priority
- **>60% coverage**: Good, but can be improved

#### Step 9.5: Seed 0% Coverage Domains (CRITICAL IF NEEDED)

⚠️ **IMPORTANT:** If any domains have **0% coverage**, DO NOT run auto-discovery yet!

**Why?** Semantic filtering uses embeddings from existing sources. With 0% coverage, the domain embedding is too weak → accepts off-topic papers (machine learning, astrophysics instead of EU policy).

**Solution: Manual Seeding**

1. **Identify 0% domains from discovery report:**
   ```
   Coverage Analysis:
     Cloud Computing: 0/100 ⚠️
     Data Quality: 0/100 ⚠️
     EU Data Act: 0/100 ⚠️
   ```

2. **Download 1-2 authoritative seed sources per domain:**
   
   **For EU Data Act:**
   - Official EU Data Act text: https://eur-lex.europa.eu/
   - EU Commission impact assessment
   
   **For Cloud Computing:**
   - NIST Cloud Computing standards
   - ISO/IEC frameworks
   
   **For Data Quality:**
   - W3C Data Quality Vocabulary (DQV)
   - Academic survey papers

3. **Add to sources:**
   ```powershell
   cp ~/Downloads/EU_Data_Act_Official.pdf data/sources/
   cp ~/Downloads/NIST_Cloud_Computing.pdf data/sources/
   ```

4. **Rebuild knowledge graph:**
   ```powershell
   python scripts/build_graph_with_meta.py
   ```

5. **Re-analyze gaps:**
   ```powershell
   python scripts/discover_sources.py
   ```

6. **Verify domains no longer at 0%:**
   ```
   Coverage Analysis:
     Cloud Computing: 25/100 ✓ (now seeded)
     Data Quality: 18/100 ✓ (now seeded)
   ```

**See full guide:** [docs/SEED_SOURCES_GUIDE.md](docs/SEED_SOURCES_GUIDE.md)

#### Step 10: Auto-Discover Sources
```powershell
# Run gap analysis
python scripts/discover_sources.py

# What it does:
# - Compares knowledge graph vs meta-ontology
# - Identifies low-coverage areas (<75%)
# - Generates targeted search queries

# Output: data/discovery_report.txt
```

#### Step 10: Automated Source Discovery
```powershell
# Run intelligent discovery with semantic filtering
python scripts/auto_discover_sources.py `
  --report data/discovery_report.txt `
  --semantic-filter `
  --domain-similarity 0.35 `
  --min-new-sources 5 `
  --max-iterations 3

# What it does:
# - Searches 24+ APIs (arXiv, OpenAlex, EUR-Lex, etc.)
# - Ranks by priority + closeness scores
# - Auto-downloads DOI papers
# - Semantic filtering (90% accuracy)
# - Fuzzy deduplication

# Output: data/discovered_urls.txt
```

#### Step 11: Curate Discovered Sources (MANUAL CHECKPOINT)
```powershell
# Open and review
code data/discovered_urls.txt

# Edit the file:
# - Keep HIGH relevance sources (score ≥ 0.50)
# - Review MEDIUM sources (score 0.40-0.49)
# - Delete LOW relevance sources (score < 0.40)
# - Add your own URLs manually if needed

# Save when ready
```

---

### Phase 3: Integrate (Add New Sources)

#### Step 12: Import Curated Sources
```powershell
# Download and import approved URLs
python scripts/import_urls.py data/discovered_urls.txt

# What it does:
# - Downloads web pages as markdown
# - Saves to data/sources/
# - Preserves metadata (URL, date, author)

# Output: New files in data/sources/
```

#### Step 13: Annotate New Sources
```powershell
# Re-run annotation for new sources only
python scripts/annotate_sources.py

# Rate the new sources (1-5 scale)
# Skip already-annotated sources (press Enter)

# Output: Updated data/source_annotations.yaml
```

#### Step 14: Refine Meta-Ontology (OPTIONAL WITH VISUALIZATION)
```powershell
# Optional: Update ontology based on new insights

# First, visualize current state
jupyter notebook data/graphs/visualize_graphs.ipynb
# Check if new concepts are needed

# Then edit
code data/graphs/meta_ontology.ttl

# Add new concepts discovered in new sources
# Refine relationships
# Save when ready
```

#### Step 15: Rebuild Knowledge Graph
```powershell
# Rebuild with ALL sources (old + new)
python scripts/build_graph_with_meta.py

# What changes:
# - Includes new sources with importance weighting
# - Extracts concepts from expanded corpus
# - Updates topic clusters
# - Increases coverage scores

# Output: Updated data/graphs/knowledge_graph.ttl
```

#### Step 16: Assess Improvement
```powershell
# Re-run gap analysis to measure progress
python scripts/discover_sources.py

# Compare coverage scores:
# - Expect 10-20 point improvement in targeted areas
# - Identify remaining gaps

# Output: Updated data/discovery_report.txt
```

---

### Phase 4: Research (Use the System)

#### Step 17: Interactive Chat
```powershell
# Start research session
python scripts/interactive_chat.py

# Ask questions like:
# - "How does Linked Data address data portability?"
# - "What are the key requirements of EU Data Act Article 6?"
# - "Compare RDF and property graphs for vendor lock-in"

# Features:
# - Retrieves top 5 sources (prioritized by importance)
# - Shows retrieval path (topic → concept → chunk)
# - Cites sources with relevance scores
# - Importance-weighted answers
```

#### Step 18: Generate Synthesis Article
```powershell
# Create AI-generated synthesis from knowledge graph
python scripts/generate_article_from_graph.py data/graphs/knowledge_graph.ttl

# What it does:
# - Reads knowledge graph structure
# - Generates coherent narrative
# - Integrates concepts and relationships
# - Saves as markdown with frontmatter

# Output: data/sources/knowledge_graph_article.md
```

---

### Iteration: Continuous Improvement

**Repeat Phases 2-3 until coverage is satisfactory:**

```
Cycle 1: Broad discovery (10-20 new sources)
   ↓
Cycle 2: Targeted gaps (5-10 new sources)
   ↓
Cycle 3: Final refinement (2-5 new sources)
```

**Expected progress per cycle:**
- Coverage improvement: +10-20 points
- Answer relevance: +5-10%
- Source count: +5-20 documents

---

## Quick Reference Commands

### Check Status
```powershell
# View current pipeline state
python scripts/research_pipeline.py --status

# Shows:
# - Current phase (UNINITIALIZED/READY_FOR_DISCOVERY/READY_FOR_CHAT)
# - Source count
# - Annotations complete
# - Graphs present
# - Iteration count
```

### Full Pipeline (Automated)
```powershell
# Run all phases in one go
python scripts/research_pipeline.py --init      # Phase 1
python scripts/research_pipeline.py --discover  # Phase 2
python scripts/research_pipeline.py --integrate # Phase 3

# Note: Still requires manual checkpoints:
# - Meta-ontology review (after --init)
# - URL curation (after --discover)
# - New source annotation (during --integrate)
```

### Batch Operations
```powershell
# Annotate multiple sources at once
python scripts/annotate_sources.py --batch

# Export annotations to CSV
python scripts/annotate_sources.py --export annotations.csv

# View annotation statistics
python scripts/annotate_sources.py --stats
```

---

## Troubleshooting

### Issue: No sources found
```powershell
# Check directory
ls data/sources/
# Should show: *.md, *.pdf, *.html, *.txt files
```

### Issue: Meta-ontology not loading
```powershell
# Verify TTL file exists and is valid
cat data/graphs/meta_ontology.ttl | Select-String "@prefix"
```

### Issue: Discovery returns no results
```powershell
# Lower domain similarity threshold
python scripts/auto_discover_sources.py --domain-similarity 0.25

# Or increase results per API
python scripts/auto_discover_sources.py --max-per-source 20
```

### Issue: Graph build fails
```powershell
# Check for file encoding issues
python scripts/build_graph_with_meta.py --verbose

# Look for "Error loading" messages
```

---

## Best Practices

1. **Start Small**: Begin with 10-15 core sources
2. **Rate Honestly**: Use full 1-5 scale (not just 4-5)
3. **Curate Strictly**: Reject low-relevance discoveries early
4. **Review Meta-Ontology**: Take time to refine domain structure
5. **Iterate Regularly**: 3-4 cycles is optimal for most projects
6. **Document Decisions**: Add notes to annotations explaining ratings

---

## File Locations

```
data/
├── sources/                 # Your research files (add here)
├── source_annotations.yaml  # Importance ratings (1-5)
├── discovered_urls.txt      # Curated discovery results
├── discovery_report.txt     # Gap analysis output
├── pipeline_state.yaml      # Current workflow state
└── graphs/
    ├── meta_ontology.ttl    # YOUR domain structure
    └── knowledge_graph.ttl  # Generated knowledge graph
```

---

## Next Steps

After completing the workflow:

1. **Publish Research**: Use generated synthesis articles
2. **Share Graph**: Export TTL for collaboration
3. **Expand Domain**: Add new meta-ontology classes
4. **Automate**: Schedule discovery runs weekly/monthly
5. **Integrate Tools**: Connect to Obsidian, Zotero, etc.

**Questions?** See `RESEARCHER_PIPELINE_GUIDE.md` for detailed explanations.
