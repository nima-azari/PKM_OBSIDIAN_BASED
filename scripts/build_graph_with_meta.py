"""
Build knowledge graph using meta-ontology for guided LLM extraction.

This script demonstrates how to use a meta-ontology to guide the LLM
during concept extraction, ensuring extracted concepts align with your
domain model.

Usage:
    python build_graph_with_meta.py

The script will:
1. Load the meta-ontology from data/graphs/meta-ont-eu-linkeddata.ttl
2. Use LLM to extract concepts guided by the meta-ontology classes
3. Build a knowledge graph with meta-ontology-aligned concepts
4. Export to data/graphs/knowledge_graph_meta.ttl
"""

from pathlib import Path
from core.rag_engine import VaultRAG


def main():
    meta_ontology_path = "data/graphs/meta-ont-eu-linkeddata.ttl"
    output_path = "data/graphs/knowledge_graph_meta.ttl"
    
    # Check if meta-ontology exists
    if not Path(meta_ontology_path).exists():
        print(f"❌ Meta-ontology not found: {meta_ontology_path}")
        print("\nPlease ensure your meta-ontology TTL file exists.")
        print("Example: data/graphs/meta-ont-eu-linkeddata.ttl")
        return
    
    print("\n" + "="*60)
    print("Knowledge Graph Builder with Meta-Ontology")
    print("="*60 + "\n")
    
    print(f"🎯 Meta-ontology: {meta_ontology_path}")
    print("   LLM-guided extraction: ENABLED\n")
    
    print("📚 Initializing RAG engine with meta-ontology...")
    rag = VaultRAG(
        sources_dir="data/sources",
        verbose=True,
        meta_ontology_path=meta_ontology_path
    )
    
    print("\n🔗 Building knowledge graph with LLM-guided extraction...")
    print("  Chunking: enabled")
    print("  Topic extraction: enabled")
    print("  Meta-ontology guidance: enabled")
    num_triples = rag.build_knowledge_graph(enable_chunking=True, enable_topics=True)
    
    print(f"\n✓ Created {num_triples} triples")
    
    print(f"\n💾 Exporting graph...")
    saved_path = rag.export_graph_ttl(output_path)
    print(f"✓ Graph saved to: {saved_path}")
    
    print("\n📊 Graph Statistics:")
    stats = rag.get_graph_stats()
    for key, value in stats.items():
        print(f"  • {key}: {value}")
    
    print("\n" + "="*60)
    print("✅ Meta-ontology-guided graph built successfully!")
    print("="*60)
    print(f"\n📁 OUTPUT: {saved_path}")
    print(f"\nKey Features:")
    print(f"  • Concepts extracted align with meta-ontology classes")
    print(f"  • LLM understands your domain model structure")
    print(f"  • Graph uses meta-ontology vocabulary")
    print(f"\nNext steps:")
    print(f"1. Review graph: {saved_path}")
    print(f"2. Compare with standard build: data/graphs/knowledge_graph.ttl")
    print(f"3. Generate article: python generate_article_from_graph.py {saved_path}")
    print(f"4. Chat with sources: python server.py")
    print("\n")


if __name__ == "__main__":
    main()
