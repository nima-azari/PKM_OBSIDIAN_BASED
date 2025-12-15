# Meta-Ontology Guided Graph Construction

## Overview

The meta-ontology feature allows you to guide the LLM during knowledge graph construction using your domain model. Instead of extracting arbitrary concepts, the LLM focuses on concepts that align with your predefined semantic classes and relationships.

## Concept

**Traditional Approach (Heuristic):**
- Extract capitalized phrases
- Extract markdown headings
- No semantic guidance
- Random concept types

**Meta-Ontology Approach (LLM-Guided):**
- Load your domain ontology (TTL file)
- LLM extracts concepts matching ontology classes
- Concepts align with your semantic model
- Interpretable, structured graph

## Benefits

### 1. Semantic Consistency
All extracted concepts fit into predefined categories from your meta-ontology:
- `PolicyFramework` (e.g., EU Data Act, GDPR)
- `DataTechnology` (e.g., Linked Data, RDF, SPARQL)
- `DataSilo` (e.g., Cloud data silos, proprietary systems)
- `DataStandard` (e.g., Interoperability standards)
- `DataBenefit` (e.g., Improved interoperability, data portability)
- `DataLimitation` (e.g., Vendor lock-in, opaque formats)
- `DataEcosystemActor` (e.g., Cloud providers, data holders)

### 2. Guided Vocabulary
The LLM uses your defined relationships:
- `:regulates`, `:imposesObligation`, `:requiresStandard`
- `:createsSilo`, `:hasLimitation`, `:constrainedBy`
- `:mitigatesLimitation`, `:enablesBenefit`, `:addressesObligation`

### 3. Concrete Anchors
Your ontology provides specific instances to extend:
- `:EUDataAct` - policy framework
- `:LinkedData` - technology solution
- `:CloudComputing`, `:CloudDataSilo` - problematic silos

### 4. Pattern-Based Structuring
Meta-patterns guide the LLM:
- **RegulatoryToTechPattern**: Policy → Obligations → Tech/Standards
- **TechToSiloPattern**: Technology → Silos → Limitations
- **BenefitRealisationPattern**: Solution → Mitigates → Yields Benefits

## Usage

### Method 1: Using build_graph.py with --meta-ontology

```bash
python build_graph.py --meta-ontology data/graphs/meta-ont-eu-linkeddata.ttl
```

This builds the graph with LLM-guided extraction using your meta-ontology.

### Method 2: Using dedicated script

```bash
python build_graph_with_meta.py
```

This script uses the default meta-ontology path and creates `knowledge_graph_meta.ttl`.

### Method 3: Programmatic usage

```python
from core.rag_engine import VaultRAG

rag = VaultRAG(
    sources_dir="data/sources",
    verbose=True,
    meta_ontology_path="data/graphs/meta-ont-eu-linkeddata.ttl"
)

rag.build_knowledge_graph(enable_chunking=True, enable_topics=True)
rag.export_graph_ttl("data/graphs/my_guided_graph.ttl")
```

## Creating Your Meta-Ontology

### Step 1: Define Core Classes

```turtle
@prefix :      <http://example.org/meta-kg#> .
@prefix owl:   <http://www.w3.org/2002/07/owl#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .

:MyDomainConcept a owl:Class ;
    rdfs:label "Domain-specific concept type" ;
    rdfs:comment "Description of what concepts fit here." .
```

### Step 2: Define Relationships

```turtle
:myRelation a owl:ObjectProperty ;
    rdfs:label "my relation" ;
    rdfs:domain :ConceptTypeA ;
    rdfs:range :ConceptTypeB ;
    rdfs:comment "Describes how A relates to B." .
```

### Step 3: Create Concrete Instances (Anchors)

```turtle
:MyKeyConceptInstance a :MyDomainConcept ;
    rdfs:label "My Key Concept" ;
    skos:prefLabel "My Key Concept" ;
    rdfs:comment "A specific important concept in my domain." .
```

### Step 4: Add Pattern Nodes (Optional)

```turtle
:MyDomainPattern a :Concept ;
    rdfs:label "Common pattern in my domain" ;
    rdfs:comment "Pattern: ConceptA creates ConceptB which has LimitationC." .
```

## Example: EU Data Act + Linked Data Ontology

See `data/graphs/meta-ont-eu-linkeddata.ttl` for a complete example.

**Key Classes:**
- `PolicyFramework` - Regulatory instruments
- `DataTechnology` - Technical approaches
- `DataSilo` - Isolated environments
- `DataStandard` - Formalized specifications
- `DataObligation` - Regulatory requirements
- `DataBenefit` - Positive outcomes
- `DataLimitation` - Negative properties
- `DataEcosystemActor` - Stakeholders

**Key Relationships:**
- Policy regulates technology
- Technology creates/mitigates silos
- Standards address obligations
- Technologies enable benefits

**Concrete Instances:**
- `:EUDataAct` - The regulation itself
- `:LinkedData` - The solution technology
- `:CloudDataSilo` - The problem space
- `:VendorLockIn`, `:OpaqueDataFormats` - Specific limitations

## How It Works

### 1. Meta-Ontology Loading
```
VaultRAG.__init__() → _load_meta_ontology()
  ↓
Parse TTL → Extract classes and properties → Store in dictionaries
  ↓
Available to LLM as context
```

### 2. Document Processing
```
build_knowledge_graph() → _add_document_with_chunks()
  ↓
Split into chunks → _extract_domain_concepts()
  ↓
If meta-ontology: _llm_extract_concepts()
  ↓
LLM sees meta-ontology classes → Extracts aligned concepts
```

### 3. LLM Prompt Structure
```
System: You are a knowledge engineer.
        Extract concepts matching these classes:
        - PolicyFramework
        - DataTechnology
        - DataSilo
        ...

User: Extract from this text: [chunk content]

LLM: EU Data Act
     Linked Data
     Vendor lock-in
     Interoperability
```

### 4. Graph Construction
```
Extracted concepts → Create DomainConcept nodes
  ↓
Link to chunks via onto:mentionsConcept
  ↓
Group into topics via onto:coversConcept
  ↓
Export as TTL with all triples
```

## Comparison: Heuristic vs Meta-Ontology Extraction

### Example Document Chunk

> "The EU Data Act imposes interoperability obligations on cloud service providers. Linked Data technologies can address these requirements by using RDF and common vocabularies, reducing vendor lock-in and enabling data portability across platforms."

### Heuristic Extraction (No Meta-Ontology)

**Extracted Concepts:**
- "EU Data Act" ✓
- "Linked Data" ✓
- "RDF" (too technical)
- "cloud service" (partial phrase)
- "Data Act" (duplicate partial)

**Issues:**
- Misses abstract concepts ("vendor lock-in", "interoperability")
- No semantic typing
- Random capitalization artifacts

### LLM-Guided Extraction (With Meta-Ontology)

**Extracted Concepts:**
- "EU Data Act" → PolicyFramework
- "Interoperability obligations" → DataObligation
- "Cloud service providers" → DataEcosystemActor
- "Linked Data" → DataTechnology
- "RDF" → DataStandard
- "Vendor lock-in" → DataLimitation
- "Data portability" → DataBenefit

**Benefits:**
- Complete coverage of semantic content
- Typed concepts
- Aligned with domain model
- Abstract concepts captured

## Advanced: Extending Generated Graphs

After LLM-guided extraction, you can:

### 1. Add Meta-Ontology Types
```turtle
# In your TTL file, add meta-ontology types
sources:EU_Data_Act a meta:PolicyFramework ;
    skos:prefLabel "EU Data Act" .

sources:Linked_Data a meta:DataTechnology ;
    skos:prefLabel "Linked Data" .
```

### 2. Add Meta-Ontology Relationships
```turtle
# Use meta-ontology predicates
meta:EUDataAct meta:imposesObligation sources:Interoperability_obligation .
meta:LinkedData meta:enablesBenefit sources:Improved_interoperability .
meta:CloudDataSilo meta:hasLimitation sources:Vendor_lock_in .
```

### 3. Link to Meta-Ontology Patterns
```turtle
# Connect to patterns
sources:EU_Data_Act_Implementation a meta:Concept ;
    meta:relatedToConcept meta:RegulatoryToTechPattern ;
    rdfs:comment "EU Data Act → Interoperability → Linked Data" .
```

## Troubleshooting

### Meta-ontology not loading
**Issue:** `Warning: Could not load meta-ontology`

**Solutions:**
- Check file path is correct
- Verify TTL syntax: `rapper -i turtle -c your-ontology.ttl`
- Ensure file has proper prefixes and namespaces

### LLM extraction fails
**Issue:** `Warning: LLM extraction failed, falling back to heuristics`

**Solutions:**
- Verify `OPENAI_API_KEY` is set
- Check OpenAI API quota/rate limits
- Simplify meta-ontology (too many classes can confuse LLM)

### No concepts extracted
**Issue:** Empty concept lists

**Solutions:**
- Check document content has text (not just frontmatter)
- Reduce `max_concepts` parameter
- Review meta-ontology class labels (make them clear)

### Wrong concept types
**Issue:** LLM extracts concepts but they don't match meta-classes

**Solutions:**
- Add more examples to meta-ontology comments
- Use `skos:example` for each class
- Refine class labels to be more descriptive

## Best Practices

### 1. Start Small
Begin with 5-10 core classes, not 50. The LLM performs better with focused guidance.

### 2. Use Clear Labels
❌ `:DT` - cryptic
✓ `:DataTechnology` - clear

### 3. Add Rich Comments
```turtle
:DataSilo a owl:Class ;
    rdfs:label "Data silo" ;
    rdfs:comment "Isolated data environments that hinder interoperability and portability. Examples: proprietary cloud storage, closed APIs, vendor-specific formats." ;
    skos:example "Proprietary cloud data silo", "Closed vendor ecosystem" .
```

### 4. Provide Concrete Instances
Give the LLM concrete examples to extend:
```turtle
:EUDataAct a :PolicyFramework ;
    rdfs:label "EU Data Act" .

# LLM can then extract similar concepts:
# "GDPR", "Data Governance Act", etc.
```

### 5. Test Incrementally
```bash
# Test with 1-2 documents first
python build_graph_with_meta.py

# Review extracted concepts
# Adjust meta-ontology if needed
# Then process full corpus
```

### 6. Combine with Manual Curation
```
1. LLM extracts → Initial graph
2. You edit TTL → Add meta-ontology types
3. You add relationships → Use meta predicates
4. You rebuild graph → Richer knowledge base
```

## Performance Considerations

### Token Usage
- LLM extraction uses ~200-300 tokens per chunk
- For 100 documents × 20 chunks = ~400K-600K tokens
- Cost: ~$0.30-0.60 (GPT-4o-mini at $0.001/1K tokens)

### Speed
- Heuristic: ~0.01 seconds per chunk
- LLM: ~0.5-1 second per chunk
- For 2000 chunks: Heuristic = 20s, LLM = 20-30 minutes

### Caching
- Embeddings are cached by content hash (unchanged)
- Keywords are cached (unchanged)
- Concept extraction is NOT cached (runs every time)

### Recommendation
- **Development/Testing**: Use meta-ontology for precision
- **Production**: Use meta-ontology for initial build, then iterate manually
- **Large corpora**: Consider batch processing or selective LLM extraction

## Integration with Research Pipeline

### Graph-Guided Discovery + Meta-Ontology

```python
# 1. Build meta-guided graph
rag = VaultRAG(meta_ontology_path="data/graphs/meta-ont-eu-linkeddata.ttl")
rag.build_knowledge_graph(enable_chunking=True, enable_topics=True)
rag.export_graph_ttl("data/graphs/knowledge_graph_meta.ttl")

# 2. Use in source discovery
from core.web_discovery import WebDiscovery

discovery = WebDiscovery(verbose=True)
topics = rag.get_graph_topics(top_k=5)
concepts = rag.get_graph_concepts(top_k=20)

queries = discovery.generate_queries_from_graph_concepts(topics, concepts, num_queries=5)
# → Queries use meta-ontology-aligned concepts
# → "EU Data Act interoperability obligations cloud providers"
```

Result: **Doubly-guided research**
- Meta-ontology guides concept extraction
- Extracted concepts guide source discovery
- New sources enrich graph
- Virtuous cycle of aligned knowledge

## Example Workflow

### Full Pipeline with Meta-Ontology

```bash
# 1. Create/refine your meta-ontology
# Edit: data/graphs/meta-ont-eu-linkeddata.ttl

# 2. Add seed documents
cp eu-data-act-article.pdf data/sources/
cp linked-data-primer.md data/sources/

# 3. Build meta-guided graph
python build_graph.py --meta-ontology data/graphs/meta-ont-eu-linkeddata.ttl

# 4. Review extracted concepts
# Check: data/graphs/knowledge_graph.ttl

# 5. Use for guided discovery
jupyter notebook notebooks/source_discovery.ipynb
# Enable graph mode, generate queries

# 6. Extract new sources (aligned with meta-ontology)
# Discovery uses meta-aligned concepts

# 7. Rebuild graph (now richer)
python build_graph.py --meta-ontology data/graphs/meta-ont-eu-linkeddata.ttl

# 8. Generate synthesis
python generate_article_from_graph.py data/graphs/knowledge_graph.ttl

# 9. Chat with meta-aligned knowledge
python server.py
```

## Summary

**Meta-ontology = Your Domain Model as LLM Guidance**

✅ Semantic consistency
✅ Interpretable graphs
✅ Aligned concepts
✅ Pattern-based structure
✅ Concrete anchors for extension

**Trade-offs:**
- ⏱️ Slower (LLM calls)
- 💰 Cost (API tokens)
- 🎯 Precision over recall

**Best for:**
- Domain-specific knowledge management
- Regulatory/compliance research
- Structured knowledge synthesis
- Multi-source integration with semantic consistency

---

**Quick Start:**
```bash
python build_graph_with_meta.py
```

**Full Documentation:**
- This file: META_ONTOLOGY_GUIDE.md
- Research pipeline: RESEARCH_PIPELINE_GUIDE.txt
- Graph-guided discovery: GRAPH_GUIDED_DISCOVERY.md
