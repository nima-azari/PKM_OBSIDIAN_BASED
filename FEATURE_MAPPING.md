## This is the key:
Web UI - Browser interface (current) -> 1
CLI - Command line scripts -> 2
Python API - Import in code/notebooks -> 3
Obsidian Plugin - Native integration -> 4
Services - Background processes -> 5
Jupyter - Interactive notebooks -> 6
VS Code IDE and Windows Directory Structure -> 7


# Feature Mapping - Where to Manage Each Feature

## Current System Features

### 1. Source Management
- **Upload documents** (PDF, txt, md) -> 7 (to put in a specific folder)
- **Extract from web URLs** (article scraping) -> 6 (as a variable with named prompt and then reply of the servers of the sources it found)
- **Web discovery** (AI-generated search queries) -> 6 (as a variable with named prompt and then reply of the servers of the sources it found)
- **Source list display** -> 6 
- **Add/remove sources** -> 7 (by the end of adding sources from web we will add it to the same source folder and manage all other modifications from there)

**Current Location:** UI (Left Column)
**Your Decision:** a combination of 6 and 7

---

### 2. Chat & Q&A
- **Ask questions** to knowledge base -> 1 (a simple ui with just a chat site like chatgpt)
- **Get answers with citations** -> same as above
- **Conversation history** -> 1 same as above
- **Smart action chips** (Ask notes, Audio overview, Drafting help) -> not needed
- **Suggested questions** (pre-built prompts) -> integrated in the same simple ui

**Current Location:** UI (Middle Column + Right Column suggestions)
**Your Decision:** 1 with simple chat ui

---

### 3. Notebook Guides / Artifacts
- **Generate FAQ**
- **Generate Study Guide**
- **Generate Timeline**
- **Generate Briefing**

**Current Location:** UI (Right Column)
**Your Decision:** NOT NEEDED

---

### 4. RAG Engine - > all from specific directory in the code base in including Keyword files, graph files, and JSON dicts
- **Keyword search** (TF-IDF)
- **Semantic search** (embeddings)
- **Document loading** from vault
- **Context retrieval**
- **Source ranking**

**Current Location:** Backend (core/rag_engine.py)
**Your Decision:** all from specific directory in the code base in including Keyword files, graph files, and JSON dicts

---

### 5. Graph RAG / Knowledge Graph
- **Build RDF graph** from vault
- **SPARQL queries**
- **Export to TTL**
- **Create ontologies** (OWL)
- **Find related notes** (graph traversal)
- **Graph statistics**

**Current Location:** Backend (core/graph_rag.py)
**Your Decision:** Integrated with RAG engine above

---

### 6. Document Processing
- **PDF text extraction** -> Backend (core/document_processor.py)
- **Frontmatter generation**
- **Tag management**
- **Create vault notes**
- **Batch import**

**Current Location:** Backend (core/document_processor.py)
**Your Decision:** Backend (core/document_processor.py)

---

### 7. Web Discovery
- **Generate search queries** (AI)
- **Extract articles** (Trafilatura)
- **Quality assessment** (AI)
- **Save to vault**

**Current Location:** Backend (core/web_discovery.py) + UI
**Your Decision:** Backend (core/web_discovery.py) + Jupyter Notebooks for interaction (as mentioned in the first part)

---

### 8. Deep Research
- **Scrape multiple URLs**
- **Quality filtering**
- **Source synthesis**
- **Literature note creation**

**Current Location:** Backend (features/research_agent.py)
**Your Decision:** Backend (core/web_discovery.py) + Jupyter Notebooks for interaction (as mentioned in the first part) using the module in features/research_agent.py

---

### 9. Obsidian API Integration
- **Get file content**
- **Create/update files**
- **Search vault**
- **List directories**
- **Delete files**

**Current Location:** Backend (core/obsidian_api.py)
**Your Decision:** Backend (core/obsidian_api.py)

---

### 10. Vault Management
- **Project structure** creation
- **Concept notes** creation
- **Wikilink management**
- **Bulk operations**
- **Export vault graph**

**Current Location:** CLI scripts
**Your Decision:** CLI scripts

---

