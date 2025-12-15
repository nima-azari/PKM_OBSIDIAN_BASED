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
from dotenv import load_dotenv

# Load environment variables (for OpenAI API key)
load_dotenv()

from core.rag_engine import VaultRAG


def main():
    # Parse command-line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Build knowledge graph from sources')
    parser.add_argument('output', nargs='?', default='data/graphs/knowledge_graph.ttl',
                        help='Output TTL file path (default: data/graphs/knowledge_graph.ttl)')
    parser.add_argument('--meta-ontology', dest='meta_ontology',
                        help='Path to meta-ontology TTL file to guide graph construction')
    args = parser.parse_args()
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*60)
    print("Knowledge Graph Builder")
    print("="*60 + "\n")
    
    # Show meta-ontology status
    if args.meta_ontology:
        print(f"🎯 Meta-ontology: {args.meta_ontology}")
        print("   (LLM-guided concept extraction enabled)\n")
    else:
        print("ℹ️  No meta-ontology specified (using heuristic extraction)")
        print("   Tip: Use --meta-ontology to guide graph with your domain model\n")
    
    print("📚 Initializing RAG engine...")
    rag = VaultRAG(
        sources_dir="data/sources",
        verbose=True,
        meta_ontology_path=args.meta_ontology
    )
    
    print("\n🔗 Building knowledge graph...")
    print("  Chunking: enabled")
    print("  Topic extraction: enabled")
    num_triples = rag.build_knowledge_graph(enable_chunking=True, enable_topics=True)
    
    print(f"\n✓ Created {num_triples} triples")
    
    print(f"\n💾 Exporting graphs...")
    
    # Export knowledge graph (instance data)
    saved_path = rag.export_graph_ttl(str(output_path))
    print(f"✓ Knowledge graph saved to: {saved_path}")
    
    # Export meta-ontology separately (if loaded)
    if args.meta_ontology:
        meta_output = output_path.parent / "meta_ontology.ttl"
        meta_saved = rag.export_meta_ontology(str(meta_output))
        if meta_saved:
            print(f"✓ Meta-ontology saved to: {meta_saved}")
    
    print("\n📊 Graph Statistics:")
    stats = rag.get_graph_stats()
    for key, value in stats.items():
        print(f"  • {key}: {value}")
    
    print("\n" + "="*60)
    print("✅ Knowledge graph built successfully!")
    print("="*60)
    print(f"\n📁 OUTPUTS:")
    print(f"   • Knowledge Graph (instances): {saved_path}")
    if args.meta_ontology:
        print(f"   • Meta-Ontology (schema): {meta_output}")
    print(f"\nNext steps:")
    print(f"1. (Optional) Edit the TTL files in: {output_path.parent}")
    print(f"2. Generate article: python generate_article_from_graph.py {saved_path}")
    print(f"3. Launch UI: python server.py")
    print("\n")


if __name__ == "__main__":
    main()
