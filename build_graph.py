"""
Build a knowledge graph from all sources in data/sources/ directory.

This script loads all documents, builds an RDF knowledge graph with concepts,
entities, and relationships, and exports it to a TTL file.

Usage:
    python build_graph.py [output_file]
    
Example:
    python build_graph.py
    python build_graph.py data/graphs/my_custom_graph.ttl
"""

import sys
from pathlib import Path
from core.rag_engine import VaultRAG


def main():
    # Determine output path
    if len(sys.argv) >= 2:
        output_path = sys.argv[1]
    else:
        output_path = "data/graphs/knowledge_graph.ttl"
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*60)
    print("Knowledge Graph Builder")
    print("="*60 + "\n")
    
    print("📚 Initializing RAG engine...")
    rag = VaultRAG(sources_dir="data/sources", verbose=True)
    
    print("\n🔗 Building knowledge graph...")
    print("  Chunking: enabled")
    print("  Topic extraction: enabled")
    num_triples = rag.build_knowledge_graph(enable_chunking=True, enable_topics=True)
    
    print(f"\n✓ Created {num_triples} triples")
    
    print(f"\n💾 Exporting graph to: {output_path}")
    rag.export_graph_ttl(str(output_path))
    
    print("\n📊 Graph Statistics:")
    stats = rag.get_graph_stats()
    for key, value in stats.items():
        print(f"  • {key}: {value}")
    
    print("\n" + "="*60)
    print("✅ Knowledge graph built successfully!")
    print("="*60)
    print(f"\nNext steps:")
    print(f"1. (Optional) Edit the TTL file: {output_path}")
    print(f"2. Generate article: python generate_article_from_graph.py {output_path}")
    print(f"3. Launch UI: python server.py")
    print("\n")


if __name__ == "__main__":
    main()
