"""
Test knowledge graph concept and topic extraction for source discovery.
"""

from pathlib import Path
from core.rag_engine import VaultRAG
from core.web_discovery import WebDiscovery

def test_graph_extraction():
    """Test extracting concepts and topics from knowledge graph."""
    
    print("="*80)
    print("Testing Knowledge Graph Extraction for Source Discovery")
    print("="*80)
    print()
    
    # Initialize RAG with existing knowledge graph
    graph_path = Path("data/graphs/knowledge_graph.ttl")
    
    if not graph_path.exists():
        print(f"❌ Knowledge graph not found at: {graph_path}")
        print(f"💡 Run 'python build_graph.py' first to create the graph")
        return
    
    print(f"📂 Loading knowledge graph from: {graph_path}")
    rag = VaultRAG(sources_dir="data/sources", verbose=True)
    
    # Load the existing graph
    try:
        rag.rdf_graph.parse(str(graph_path), format='turtle')
        print(f"✓ Successfully loaded knowledge graph\n")
    except Exception as e:
        print(f"❌ Error loading graph: {e}")
        return
    
    # Get statistics
    print("📊 Graph Statistics:")
    stats = rag.get_graph_stats()
    print(f"  - Domain Concepts: {stats['domain_concepts']}")
    print(f"  - Topic Nodes: {stats['topic_nodes']}")
    print(f"  - Documents: {stats['documents']}")
    print(f"  - Chunks: {stats['chunks']}")
    print(f"  - Total Triples: {stats['total_triples']}")
    print()
    
    # Extract topics
    print("="*80)
    print("🧠 Extracting Topics from Graph:")
    print("="*80)
    topics = rag.get_graph_topics(top_k=5)
    
    if topics:
        print(f"\n✓ Found {len(topics)} topic nodes:\n")
        for i, topic in enumerate(topics, 1):
            print(f"{i}. {topic['label']}")
            if topic.get('description'):
                print(f"   Description: {topic['description']}")
            if topic.get('concepts'):
                print(f"   Concepts ({len(topic['concepts'])}): {', '.join(topic['concepts'][:5])}")
                if len(topic['concepts']) > 5:
                    print(f"              ... and {len(topic['concepts']) - 5} more")
            print()
    else:
        print("⚠️ No topics found in knowledge graph")
    
    # Extract concepts
    print("="*80)
    print("💡 Extracting Domain Concepts from Graph:")
    print("="*80)
    concepts = rag.get_graph_concepts(top_k=20)
    
    if concepts:
        print(f"\n✓ Found {len(concepts)} domain concepts:\n")
        for i in range(0, len(concepts), 5):
            print(f"  {', '.join(concepts[i:i+5])}")
        print()
    else:
        print("⚠️ No domain concepts found in knowledge graph")
    
    # Test query generation from graph
    print("="*80)
    print("🔍 Generating Search Queries from Graph:")
    print("="*80)
    
    discovery = WebDiscovery()
    queries = discovery.generate_queries_from_graph_concepts(
        topics=topics,
        concepts=concepts,
        num_queries=5
    )
    
    if queries:
        print(f"\n✓ Generated {len(queries)} search queries:\n")
        for i, query in enumerate(queries, 1):
            print(f"{i}. {query}")
        print()
    else:
        print("⚠️ No queries generated")
    
    # Compare with document-based approach
    print("="*80)
    print("📊 Comparison with Document-Based Approach:")
    print("="*80)
    
    # Load documents
    rag2 = VaultRAG(sources_dir="data/sources", verbose=False)
    rag2._load_documents()
    
    if rag2.documents:
        # Extract topic from documents
        combined_content = "\n\n---\n\n".join([
            f"{doc.title}\n{doc.content[:2000]}"
            for doc in rag2.documents[:3]
        ])
        
        doc_topic = discovery.extract_research_topic(combined_content, max_words=15)
        doc_queries = discovery._generate_search_queries(doc_topic)
        
        print(f"\nDocument-based topic: {doc_topic}")
        print(f"\nDocument-based queries ({len(doc_queries)}):")
        for i, query in enumerate(doc_queries, 1):
            print(f"{i}. {query}")
    
    print("\n" + "="*80)
    print("✅ Test complete!")
    print("="*80)
    print("\n💡 Key Benefits of Graph-Based Approach:")
    print("   - Uses manually refined concepts and topics")
    print("   - Captures researcher's domain expertise")
    print("   - More targeted and specific queries")
    print("   - Leverages knowledge graph structure")
    print("   - Considers relationships between concepts")
    print()

if __name__ == "__main__":
    test_graph_extraction()
