"""
Test script for Graph RAG functionality
"""
from core.rag_engine import VaultRAG
from dotenv import load_dotenv

load_dotenv()

def test_graph_rag():
    print("=" * 80)
    print("Testing Graph RAG Integration")
    print("=" * 80)
    
    # Initialize RAG with verbose mode
    rag = VaultRAG(verbose=True)
    
    print("\n" + "=" * 80)
    print("Building Knowledge Graph...")
    print("=" * 80)
    
    # Build graph
    triples = rag.build_knowledge_graph()
    
    print(f"\n✓ Built graph with {triples} triples")
    
    # Get graph stats
    print("\n" + "=" * 80)
    print("Graph Statistics:")
    print("=" * 80)
    
    stats = rag.get_graph_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Export to TTL
    print("\n" + "=" * 80)
    print("Exporting Graph...")
    print("=" * 80)
    
    ttl_path = rag.export_graph_ttl("test_graph.ttl")
    print(f"\n✓ Exported to: {ttl_path}")
    
    # Create ontology
    print("\n" + "=" * 80)
    print("Creating Ontology...")
    print("=" * 80)
    
    onto_path = rag.create_ontology("test_ontology.ttl")
    print(f"\n✓ Created ontology: {onto_path}")
    
    # Example SPARQL query
    print("\n" + "=" * 80)
    print("Testing SPARQL Query...")
    print("=" * 80)
    
    query = f"""
    PREFIX onto: <{rag.ONTO}>
    
    SELECT ?label
    WHERE {{
        ?doc a onto:Document .
        ?doc rdfs:label ?label .
    }}
    """
    
    results = rag.query_sparql(query)
    print(f"\nFound {len(results)} documents:")
    for r in results:
        print(f"  - {r.get('label', 'Unknown')}")
    
    print("\n" + "=" * 80)
    print("Graph RAG Test Complete!")
    print("=" * 80)

if __name__ == "__main__":
    test_graph_rag()
