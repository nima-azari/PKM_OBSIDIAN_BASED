# Knowledge Graph-Guided Source Discovery

## Overview

This enhancement integrates Part 4's manually refined knowledge graphs into the source discovery workflow (`notebooks/source_discovery.ipynb`). Instead of relying solely on AI extraction from raw documents, researchers can now leverage their curated knowledge graph structure to generate more targeted and relevant search queries.

## New Features

### 1. Core Methods Added to `VaultRAG` (core/rag_engine.py)

#### `get_graph_topics(top_k=10)`
Extracts topic nodes from the knowledge graph with their covered concepts.

```python
topics = rag.get_graph_topics(top_k=5)
# Returns: [
#   {
#     'label': 'Topic: Knowledge Graphs, Conclusion In',
#     'description': 'Clusters concepts: Knowledge Graphs, Conclusion In, Dynamic Nature',
#     'concepts': ['Conclusion', 'Conclusion In', 'Dynamic Nature', ...]
#   },
#   ...
# ]
```

#### `get_graph_concepts(top_k=20)`
Extracts domain concepts from the knowledge graph, ordered by mention frequency.

```python
concepts = rag.get_graph_concepts(top_k=20)
# Returns: ['Data Act', 'Atanas Kirakov', 'European Commission', ...]
```

### 2. Method Added to `WebDiscovery` (core/web_discovery.py)

#### `generate_queries_from_graph_concepts(topics, concepts, num_queries=5)`
Generates targeted search queries based on knowledge graph structure.

```python
queries = discovery.generate_queries_from_graph_concepts(
    topics=topics,
    concepts=concepts,
    num_queries=5
)
# Returns: [
#   "Atanas Kirakov role in knowledge graphs and their application in data spaces",
#   "Dynamic nature of knowledge graphs in event participation",
#   ...
# ]
```

### 3. Updated Notebook (notebooks/source_discovery.ipynb)

The notebook now offers **three modes** in Step 1:

#### Option 1: Manual Research Topic
```python
research_topic = "EU Data Act and Linked Data governance frameworks"
use_graph_mode = False
```

#### Option 2: Auto-extract from Documents
```python
research_topic = None
use_graph_mode = False
```

#### Option 3: Use Knowledge Graph (⭐ Recommended)
```python
research_topic = None
use_graph_mode = True
graph_path = "../data/graphs/knowledge_graph.ttl"
```

## Workflow Comparison

### Traditional Document-Based Approach

1. Load documents from `data/sources/`
2. AI extracts general research topic (e.g., "Exploring key themes in knowledge graphs")
3. Generate search queries from extracted topic
4. Queries tend to be generic and broad

**Result**: "knowledge graphs information organization retrieval key themes concepts"

### Graph-Guided Approach ⭐

1. Load pre-built knowledge graph from Part 4
2. Extract 11 topic nodes and 107 domain concepts
3. Generate queries based on specific concepts and their relationships
4. Queries are highly targeted and domain-specific

**Result**: "Atanas Kirakov role in knowledge graphs and their application in data spaces"

## Benefits

1. **Researcher Expertise**: Leverages manual curation from Part 4
2. **Specific Queries**: Uses exact concepts from your knowledge graph
3. **Relationship-Aware**: Combines related concepts meaningfully
4. **Avoids Noise**: Prevents irrelevant results (e.g., no more physics papers when researching EU Data Act)
5. **Iterative Refinement**: Edit graph → regenerate queries → discover sources → rebuild graph

## Usage

### Step 1: Build Your Knowledge Graph
```bash
python build_graph.py
```

This creates `data/graphs/knowledge_graph.ttl` with:
- 107 domain concepts
- 11 topic nodes
- 17 documents
- 22 chunks
- 704 triples

### Step 2: (Optional) Manually Refine Graph
Edit `data/graphs/knowledge_graph.ttl` to:
- Adjust topic labels (`skos:prefLabel`)
- Add/remove concept relationships (`onto:coversConcept`)
- Refine concept hierarchies (`skos:broader/narrower`)

### Step 3: Run Source Discovery Notebook
```python
# In notebooks/source_discovery.ipynb, Cell 1:
use_graph_mode = True
graph_path = "../data/graphs/knowledge_graph.ttl"
```

### Step 4: Review Generated Queries
The notebook will display:
- 5 topic nodes with their concepts
- 20 domain concepts
- 5 targeted search queries

### Step 5: Search & Extract
- Copy queries
- Search on Google Scholar, arXiv, etc.
- Paste URLs in next cell
- Articles automatically extracted and saved

### Step 6: Iterate
- New articles added to `data/sources/`
- Rebuild graph: `python build_graph.py`
- Repeat discovery with enriched graph

## Test Results

### Graph Statistics
```
Domain Concepts: 107
Topic Nodes: 11
Documents: 17
Chunks: 22
Total Triples: 704
```

### Sample Topics Extracted
1. **Topic: Key Entities and Their Roles, Key Entities**
   - Concepts: Atanas Kirakov, Entity Relationships, Hierarchical Relationships

2. **Topic: Knowledge Graphs, Conclusion In**
   - Concepts: Knowledge Graphs, Dynamic Nature, Event Participation

3. **Topic: Architectural Specification, Data Spaces**
   - Concepts: Data Spaces, Electrotechnical Standardization, Data Solutions

### Sample Generated Queries
1. "Atanas Kirakov role in knowledge graphs and their application in data spaces"
2. "Dynamic nature of knowledge graphs in event participation and information presentation"
3. "Architectural specification impact on common European data spaces and intellectual property rights"
4. "Comparative analysis of RDF advantages over labeled property graphs in data solutions"
5. "Key entities and their hierarchical relationships in the context of the European Commission's data act"

**vs. Document-Based:**
- "knowledge graphs information organization retrieval key themes concepts"
- "enhanced information retrieval knowledge graphs semantic relationships"

## Technical Details

### SPARQL Queries Used

**Topics Extraction:**
```sparql
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX onto: <http://pkm.local/ontology/>

SELECT ?topic ?label ?description
WHERE {
    ?topic a onto:TopicNode .
    ?topic skos:prefLabel ?label .
    OPTIONAL { ?topic rdfs:comment ?description }
}
```

**Concepts Extraction:**
```sparql
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX onto: <http://pkm.local/ontology/>

SELECT ?label (COUNT(?chunk) as ?mentions)
WHERE {
    ?concept a onto:DomainConcept .
    ?concept skos:prefLabel ?label .
    OPTIONAL { ?chunk onto:mentionsConcept ?concept }
}
GROUP BY ?label
ORDER BY DESC(?mentions)
```

### AI Prompt for Query Generation

The system uses GPT-4o-mini (temperature 0.4) with this system prompt:

```
You are a research search query expert. Generate 5 highly specific 
search queries based on the provided knowledge graph structure.

Guidelines:
- Use the EXACT concepts and topics from the knowledge graph
- Combine multiple concepts to create focused queries
- Target academic papers, technical articles, and industry reports
- Make queries specific enough to avoid irrelevant results
- Focus on relationships between concepts
```

## Files Modified

1. **core/rag_engine.py**
   - Added `get_graph_topics()` method
   - Added `get_graph_concepts()` method
   - Fixed namespace binding for external graph loading

2. **core/web_discovery.py**
   - Added `generate_queries_from_graph_concepts()` method

3. **notebooks/source_discovery.ipynb**
   - Added three-mode selection (manual, document, graph)
   - Integrated graph loading and concept extraction
   - Updated query generation to use graph mode

## Files Created

1. **test_graph_extraction.py** - Comprehensive test of new features
2. **test_sparql_debug.py** - SPARQL query debugging utility
3. **GRAPH_GUIDED_DISCOVERY.md** - This documentation

## Future Enhancements

1. **Interactive Graph Editor**: Visual UI to refine topics/concepts before generating queries
2. **Feedback Loop**: Track which queries find relevant sources, suggest graph improvements
3. **Multi-Graph Support**: Load multiple TTL files for different research projects
4. **Concept Weighting**: Prioritize concepts based on your manual importance ratings
5. **Query Templates**: Save successful query patterns for reuse

## Conclusion

This enhancement bridges Part 4's knowledge graph curation with source discovery, enabling researchers to:
- Leverage their domain expertise embedded in the graph
- Generate highly targeted search queries
- Avoid irrelevant search results
- Create an iterative research workflow: graph → queries → sources → graph

The graph-guided approach produces queries that are **specific, relevant, and actionable**, significantly improving the quality of discovered sources compared to document-based extraction alone.
