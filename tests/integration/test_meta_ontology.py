"""
Test meta-ontology guided graph construction.

This script tests:
1. Meta-ontology loading
2. LLM-guided concept extraction
3. Meta-ontology class/property extraction
4. Comparison with heuristic extraction
"""

from core.rag_engine import VaultRAG
from pathlib import Path


def test_meta_ontology_loading():
    """Test meta-ontology file loading."""
    print("\n" + "="*60)
    print("TEST 1: Meta-Ontology Loading")
    print("="*60)
    
    meta_path = "data/graphs/meta-ont-eu-linkeddata.ttl"
    
    if not Path(meta_path).exists():
        print(f"❌ Meta-ontology file not found: {meta_path}")
        print("   Please create the meta-ontology file first.")
        return False
    
    print(f"Loading meta-ontology from: {meta_path}")
    
    rag = VaultRAG(
        sources_dir="data/sources",
        verbose=True,
        meta_ontology_path=meta_path
    )
    
    if rag.meta_ontology is None:
        print("❌ Meta-ontology failed to load")
        return False
    
    print(f"\n✓ Meta-ontology loaded successfully")
    print(f"  Classes found: {len(rag.meta_classes)}")
    print(f"  Properties found: {len(rag.meta_properties)}")
    
    if rag.meta_classes:
        print(f"\n  Sample classes:")
        for i, (label, uri) in enumerate(list(rag.meta_classes.items())[:5]):
            print(f"    - {label}: {uri}")
    
    if rag.meta_properties:
        print(f"\n  Sample properties:")
        for i, (label, uri) in enumerate(list(rag.meta_properties.items())[:5]):
            print(f"    - {label}: {uri}")
    
    return True


def test_llm_extraction():
    """Test LLM-guided concept extraction with meta-ontology."""
    print("\n" + "="*60)
    print("TEST 2: LLM-Guided Concept Extraction")
    print("="*60)
    
    meta_path = "data/graphs/meta-ont-eu-linkeddata.ttl"
    
    if not Path(meta_path).exists():
        print(f"❌ Meta-ontology file not found: {meta_path}")
        return False
    
    rag = VaultRAG(
        sources_dir="data/sources",
        verbose=False,  # Reduce output for test
        meta_ontology_path=meta_path
    )
    
    # Test text
    test_text = """
    # EU Data Act and Linked Data
    
    The EU Data Act imposes interoperability obligations on cloud service providers.
    Linked Data technologies can address these requirements by using RDF and common
    vocabularies, reducing vendor lock-in and enabling data portability across platforms.
    
    Data silos created by proprietary cloud solutions hinder cross-domain integration.
    By adopting open standards and semantic web technologies, organizations can achieve
    improved interoperability and semantic consistency.
    """
    
    print("Test text:")
    print(test_text[:200] + "...")
    
    print("\nExtracting concepts with LLM (meta-ontology guided)...")
    try:
        concepts = rag._llm_extract_concepts(test_text, max_concepts=10)
        
        print(f"\n✓ Extracted {len(concepts)} concepts:")
        for i, concept in enumerate(concepts, 1):
            print(f"  {i}. {concept}")
        
        # Check for expected concepts
        expected = ["EU Data Act", "Linked Data", "vendor lock-in", "interoperability"]
        found = sum(1 for exp in expected if any(exp.lower() in c.lower() for c in concepts))
        
        print(f"\n✓ Found {found}/{len(expected)} expected concepts")
        
        return len(concepts) > 0
    
    except Exception as e:
        print(f"❌ LLM extraction failed: {e}")
        return False


def test_heuristic_vs_llm():
    """Compare heuristic vs LLM-guided extraction."""
    print("\n" + "="*60)
    print("TEST 3: Heuristic vs LLM Comparison")
    print("="*60)
    
    meta_path = "data/graphs/meta-ont-eu-linkeddata.ttl"
    
    # Test text
    test_text = """
    ## European Data Governance
    
    The EU Data Act introduces new obligations for Data Holders and Cloud Service Providers.
    These obligations aim to reduce Vendor Lock-In and improve Data Portability.
    
    Linked Data technologies offer a solution by providing Semantic Consistency
    and Cross-Domain Integration capabilities.
    """
    
    print("Test text:")
    print(test_text)
    
    # Heuristic extraction
    print("\n1. HEURISTIC EXTRACTION (no meta-ontology):")
    rag_heuristic = VaultRAG(sources_dir="data/sources", verbose=False)
    concepts_heuristic = rag_heuristic._extract_domain_concepts(test_text)
    print(f"   Extracted {len(concepts_heuristic)} concepts:")
    for c in concepts_heuristic:
        print(f"   - {c}")
    
    # LLM-guided extraction
    if not Path(meta_path).exists():
        print("\n❌ Cannot test LLM extraction: meta-ontology not found")
        return False
    
    print("\n2. LLM-GUIDED EXTRACTION (with meta-ontology):")
    rag_llm = VaultRAG(sources_dir="data/sources", verbose=False, meta_ontology_path=meta_path)
    
    try:
        concepts_llm = rag_llm._llm_extract_concepts(test_text, max_concepts=10)
        print(f"   Extracted {len(concepts_llm)} concepts:")
        for c in concepts_llm:
            print(f"   - {c}")
        
        print("\n3. COMPARISON:")
        print(f"   Heuristic: {len(concepts_heuristic)} concepts")
        print(f"   LLM-guided: {len(concepts_llm)} concepts")
        
        # Check for semantic concepts (abstract concepts LLM should catch)
        semantic_concepts = ["vendor lock-in", "data portability", "semantic consistency"]
        heuristic_catches = sum(1 for sc in semantic_concepts if any(sc.lower() in c.lower() for c in concepts_heuristic))
        llm_catches = sum(1 for sc in semantic_concepts if any(sc.lower() in c.lower() for c in concepts_llm))
        
        print(f"\n   Semantic concepts captured:")
        print(f"   Heuristic: {heuristic_catches}/{len(semantic_concepts)}")
        print(f"   LLM-guided: {llm_catches}/{len(semantic_concepts)}")
        
        if llm_catches > heuristic_catches:
            print("\n   ✓ LLM-guided extraction captures more semantic concepts")
        
        return True
    
    except Exception as e:
        print(f"   ❌ LLM extraction failed: {e}")
        return False


def test_graph_building():
    """Test full graph building with meta-ontology."""
    print("\n" + "="*60)
    print("TEST 4: Full Graph Building with Meta-Ontology")
    print("="*60)
    
    meta_path = "data/graphs/meta-ont-eu-linkeddata.ttl"
    
    if not Path(meta_path).exists():
        print(f"❌ Meta-ontology file not found: {meta_path}")
        return False
    
    print("Building knowledge graph with meta-ontology...")
    
    rag = VaultRAG(
        sources_dir="data/sources",
        verbose=True,
        meta_ontology_path=meta_path
    )
    
    num_triples = rag.build_knowledge_graph(enable_chunking=True, enable_topics=True)
    
    print(f"\n✓ Graph built: {num_triples} triples")
    
    # Export test graph
    test_output = "data/graphs/test_meta_graph.ttl"
    saved_path = rag.export_graph_ttl(test_output)
    
    print(f"✓ Graph exported to: {saved_path}")
    
    # Get statistics
    stats = rag.get_graph_stats()
    print("\nGraph statistics:")
    for key, value in stats.items():
        print(f"  • {key}: {value}")
    
    return num_triples > 0


def main():
    print("\n" + "="*70)
    print(" META-ONTOLOGY GUIDED GRAPH CONSTRUCTION - TEST SUITE")
    print("="*70)
    
    results = []
    
    # Test 1: Loading
    results.append(("Meta-Ontology Loading", test_meta_ontology_loading()))
    
    # Test 2: LLM Extraction
    results.append(("LLM-Guided Extraction", test_llm_extraction()))
    
    # Test 3: Comparison
    results.append(("Heuristic vs LLM", test_heuristic_vs_llm()))
    
    # Test 4: Full graph building
    results.append(("Full Graph Building", test_graph_building()))
    
    # Summary
    print("\n" + "="*70)
    print(" TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status:8} {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Meta-ontology system is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review errors above.")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
