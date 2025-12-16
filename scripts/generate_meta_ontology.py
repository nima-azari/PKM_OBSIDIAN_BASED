"""
Generate meta-ontology from sources (Step 1 of pipeline).

This script analyzes all documents in data/sources/ and extracts:
- Top-level domain concepts (classes)
- Key relationships (properties)
- Domain vocabulary

The output is a meta-ontology TTL file that can be manually reviewed/edited
before using it to guide knowledge graph construction.

Usage:
    python generate_meta_ontology.py [output_file]
    
Example:
    python generate_meta_ontology.py
    python generate_meta_ontology.py data/graphs/meta_ontology.ttl
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from core.rag_engine import VaultRAG

# Load environment variables
load_dotenv()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Generate meta-ontology from sources')
    parser.add_argument('output', nargs='?', default='data/graphs/meta_ontology.ttl',
                        help='Output TTL file path (default: data/graphs/meta_ontology.ttl)')
    args = parser.parse_args()
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*60)
    print("Meta-Ontology Generator (Step 1)")
    print("="*60 + "\n")
    
    print("📚 Loading documents from data/sources/...")
    rag = VaultRAG(
        sources_dir="data/sources",
        verbose=True
    )
    
    print(f"\n✓ Loaded {len(rag.documents)} documents")
    
    print("\n🤖 Analyzing documents to extract domain vocabulary...")
    print("   This uses LLM to identify:")
    print("   • Top-level concepts (classes)")
    print("   • Key relationships (properties)")
    print("   • Domain-specific terminology\n")
    
    # Generate meta-ontology from documents
    meta_path = rag.generate_meta_ontology_from_sources(str(output_path))
    
    print("\n" + "="*60)
    print("✅ Meta-ontology generated successfully!")
    print("="*60)
    print(f"\n📁 OUTPUT: {meta_path}")
    
    # Auto-enhance: Run LLM evaluation to connect disconnected nodes
    print(f"\n🔗 Auto-enhancing meta-ontology (connecting isolated nodes)...")
    try:
        import subprocess
        result = subprocess.run(
            ['python', 'scripts/evaluate_meta_ontology.py', str(output_path), '--threshold', '0.6'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        if result.returncode == 0:
            print("   ✅ Auto-enhancement complete")
        else:
            print(f"   ⚠️  Auto-enhancement skipped (no disconnected nodes or error)")
    except Exception as e:
        print(f"   ⚠️  Auto-enhancement failed: {e}")
    
    print(f"\n⚠️  IMPORTANT: Review and edit the meta-ontology before Step 2!")
    print(f"\nNext steps:")
    print(f"1. Review: {meta_path}")
    print(f"2. Visualize: Run cells in data/graphs/visualize_graphs.ipynb")
    print(f"3. Edit: Add/remove/refine concepts and relationships if needed")
    print(f"4. Build graph: python scripts/build_graph_with_meta.py")
    print("\n")


if __name__ == "__main__":
    main()
