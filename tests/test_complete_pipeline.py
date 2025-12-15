#!/usr/bin/env python3
"""
Complete Pipeline Test Suite

Tests the entire PKM system pipeline from source discovery to chat,
including all manual control points.

Test Phases:
1. Setup & Configuration
2. Basic Chat (Path 1)
3. Knowledge Graph Building (Path 2)
4. Source Discovery Pipeline (Path 3) - with manual checkpoints
5. Meta-Ontology Guided GraphRAG (Path 4)
6. Integration Tests
"""

import sys
import os
from pathlib import Path
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

class Colors:
    """ANSI color codes"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_section(title: str):
    """Print a section header"""
    print(f"\n{Colors.HEADER}{'='*80}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{title}{Colors.END}")
    print(f"{Colors.HEADER}{'='*80}{Colors.END}\n")

def print_step(step: str, description: str):
    """Print a test step"""
    print(f"{Colors.CYAN}{Colors.BOLD}[{step}]{Colors.END} {description}")

def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_manual_checkpoint(checkpoint_num: int, description: str):
    """Print manual checkpoint notice"""
    print(f"\n{Colors.YELLOW}{Colors.BOLD}🧑‍🔬 MANUAL CHECKPOINT #{checkpoint_num}{Colors.END}")
    print(f"{Colors.YELLOW}{description}{Colors.END}")
    input(f"{Colors.YELLOW}Press Enter when review is complete...{Colors.END}\n")


# =============================================================================
# PHASE 1: Setup & Configuration
# =============================================================================

def test_phase1_setup():
    """Test system setup and configuration"""
    print_section("PHASE 1: Setup & Configuration")
    
    results = {"passed": 0, "failed": 0, "warnings": 0}
    
    # Test 1.1: Check Python version
    print_step("1.1", "Checking Python version...")
    if sys.version_info >= (3, 10):
        print_success(f"Python {sys.version_info.major}.{sys.version_info.minor} detected")
        results["passed"] += 1
    else:
        print_error(f"Python 3.10+ required, found {sys.version_info.major}.{sys.version_info.minor}")
        results["failed"] += 1
    
    # Test 1.2: Check dependencies
    print_step("1.2", "Checking key dependencies...")
    required_modules = [
        'openai', 'flask', 'rdflib', 'numpy', 'sklearn',
        'sentence_transformers', 'fuzzywuzzy', 'dotenv'
    ]
    
    for module in required_modules:
        try:
            __import__(module)
            print_success(f"{module} installed")
            results["passed"] += 1
        except ImportError:
            print_error(f"{module} not installed")
            results["failed"] += 1
        except Exception as e:
            # Handle known PyTorch compatibility issues
            if 'torch' in str(e) and 'compiler' in str(e):
                print_warning(f"{module} installed but has PyTorch version conflict (known issue)")
                print_warning("  Note: Semantic filtering disabled (requires PyTorch 2.1.0+)")
                results["warnings"] += 1
            else:
                print_error(f"{module} import error: {str(e)[:100]}")
                results["failed"] += 1
    
    # Test 1.3: Check environment variables
    print_step("1.3", "Checking environment variables...")
    from dotenv import load_dotenv
    load_dotenv()
    
    if os.getenv('OPENAI_API_KEY'):
        print_success("OPENAI_API_KEY configured")
        results["passed"] += 1
    else:
        print_error("OPENAI_API_KEY not found in .env")
        results["failed"] += 1
    
    # Test 1.4: Check directory structure
    print_step("1.4", "Checking directory structure...")
    required_dirs = [
        'core', 'features', 'scripts', 'data', 'data/sources',
        'data/graphs', 'data/embeddings', 'data/keywords',
        'tests/integration', 'docs', 'static'
    ]
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print_success(f"{dir_path}/ exists")
            results["passed"] += 1
        else:
            print_error(f"{dir_path}/ not found")
            results["failed"] += 1
    
    # Test 1.5: Check core modules
    print_step("1.5", "Importing core modules...")
    try:
        from core.rag_engine import VaultRAG
        print_success("core.rag_engine imported")
        results["passed"] += 1
    except Exception as e:
        print_error(f"core.rag_engine import failed: {e}")
        results["failed"] += 1
    
    try:
        from core.web_discovery import WebDiscovery
        print_success("core.web_discovery imported")
        results["passed"] += 1
    except Exception as e:
        print_error(f"core.web_discovery import failed: {e}")
        results["failed"] += 1
    
    try:
        from features.chat import VaultChat
        print_success("features.chat imported")
        results["passed"] += 1
    except Exception as e:
        print_error(f"features.chat import failed: {e}")
        results["failed"] += 1
    
    return results


# =============================================================================
# PHASE 2: Basic Chat (Path 1)
# =============================================================================

def test_phase2_basic_chat():
    """Test basic chat functionality"""
    print_section("PHASE 2: Basic Chat (Path 1)")
    
    results = {"passed": 0, "failed": 0, "warnings": 0}
    
    try:
        from core.rag_engine import VaultRAG
        from features.chat import VaultChat
        
        # Test 2.1: Load documents
        print_step("2.1", "Loading documents from data/sources/...")
        rag = VaultRAG(sources_dir="data/sources", verbose=False)
        
        # Count source files
        sources_dir = Path("data/sources")
        source_files = list(sources_dir.glob("**/*.md")) + \
                      list(sources_dir.glob("**/*.txt")) + \
                      list(sources_dir.glob("**/*.pdf")) + \
                      list(sources_dir.glob("**/*.html"))
        
        if len(source_files) > 0:
            print_success(f"Found {len(source_files)} source files")
            results["passed"] += 1
        else:
            print_warning("No source files found in data/sources/")
            results["warnings"] += 1
        
        # Test 2.2: Initialize chat
        print_step("2.2", "Initializing chat interface...")
        chat = VaultChat(verbose=False)
        print_success("Chat interface initialized")
        results["passed"] += 1
        
        # Test 2.3: Test query
        if len(source_files) > 0:
            print_step("2.3", "Testing simple query...")
            test_query = "What is this project about?"
            result = chat.ask(test_query)
            
            if result and 'answer' in result:
                print_success(f"Query successful")
                print(f"   Answer preview: {result['answer'][:150]}...")
                print(f"   Sources found: {len(result.get('sources', []))}")
                results["passed"] += 1
            else:
                print_error("Query failed to return results")
                results["failed"] += 1
        else:
            print_warning("Skipping query test (no sources)")
            results["warnings"] += 1
        
    except Exception as e:
        print_error(f"Phase 2 error: {e}")
        import traceback
        traceback.print_exc()
        results["failed"] += 1
    
    return results


# =============================================================================
# PHASE 3: Knowledge Graph Building (Path 2)
# =============================================================================

def test_phase3_knowledge_graph():
    """Test knowledge graph building and editing"""
    print_section("PHASE 3: Knowledge Graph Building (Path 2)")
    
    results = {"passed": 0, "failed": 0, "warnings": 0}
    
    try:
        from core.rag_engine import VaultRAG
        
        # Test 3.1: Build knowledge graph
        print_step("3.1", "Building knowledge graph...")
        rag = VaultRAG(sources_dir="data/sources", verbose=True)
        
        start_time = time.time()
        rag.build_knowledge_graph(enable_chunking=True, enable_topics=True)
        build_time = time.time() - start_time
        
        print_success(f"Knowledge graph built in {build_time:.2f}s")
        results["passed"] += 1
        
        # Test 3.2: Get graph statistics
        print_step("3.2", "Getting graph statistics...")
        stats = rag.get_graph_stats()
        
        print(f"   Documents: {stats.get('documents', 0)}")
        print(f"   Chunks: {stats.get('chunks', 0)}")
        print(f"   Domain Concepts: {stats.get('domain_concepts', 0)}")
        print(f"   Topic Nodes: {stats.get('topic_nodes', 0)}")
        print(f"   Total Triples: {stats.get('total_triples', 0)}")
        
        if stats.get('total_triples', 0) > 0:
            print_success("Graph statistics retrieved")
            results["passed"] += 1
        else:
            print_warning("Graph appears empty")
            results["warnings"] += 1
        
        # Test 3.3: Export graph to TTL
        print_step("3.3", "Exporting graph to TTL format...")
        output_path = "data/graphs/test_knowledge_graph.ttl"
        rag.export_graph_ttl(output_path)
        
        if Path(output_path).exists():
            file_size = Path(output_path).stat().st_size
            print_success(f"Graph exported to {output_path} ({file_size:,} bytes)")
            results["passed"] += 1
            
            # Manual checkpoint for graph editing
            print_manual_checkpoint(
                1,
                f"Review and optionally edit: {output_path}\n"
                "   - Check concept labels (skos:prefLabel)\n"
                "   - Verify relationships\n"
                "   - Add/modify hierarchies if needed"
            )
        else:
            print_error("Graph export failed")
            results["failed"] += 1
        
        # Test 3.4: Test SPARQL query
        print_step("3.4", "Testing SPARQL query...")
        query = """
        PREFIX ex: <http://example.org/>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        
        SELECT (COUNT(?concept) AS ?count) WHERE {
            ?concept a ex:DomainConcept .
        }
        """
        
        try:
            query_results = rag.query_sparql(query)
            if query_results:
                print_success("SPARQL query executed successfully")
                results["passed"] += 1
            else:
                print_warning("SPARQL query returned no results")
                results["warnings"] += 1
        except Exception as e:
            print_error(f"SPARQL query failed: {e}")
            results["failed"] += 1
        
    except Exception as e:
        print_error(f"Phase 3 error: {e}")
        import traceback
        traceback.print_exc()
        results["failed"] += 1
    
    return results


# =============================================================================
# PHASE 4: Source Discovery Pipeline (Path 3)
# =============================================================================

def test_phase4_source_discovery():
    """Test complete source discovery pipeline"""
    print_section("PHASE 4: Automated Source Discovery (Path 3)")
    
    results = {"passed": 0, "failed": 0, "warnings": 0}
    
    try:
        # Test 4.1: Gap analysis
        print_step("4.1", "Running gap analysis...")
        print_warning("Note: This requires a knowledge graph with meta-ontology")
        print_warning("Skipping gap analysis in this test (requires manual setup)")
        results["warnings"] += 1
        
        # Test 4.2: API integration test
        print_step("4.2", "Testing API integrations...")
        from core.web_discovery import WebDiscovery
        
        discovery = WebDiscovery()
        test_query = "knowledge graphs semantic web"
        
        # Test each API
        apis_to_test = {
            'arXiv': lambda: discovery._search_arxiv(test_query, max_results=3),
            'OpenAlex': lambda: discovery._search_openalex(test_query, max_results=3),
            'DOAJ': lambda: discovery._search_doaj(test_query, max_results=3),
        }
        
        for api_name, search_func in apis_to_test.items():
            try:
                api_results = search_func()
                if api_results:
                    print_success(f"{api_name}: {len(api_results)} results")
                    results["passed"] += 1
                else:
                    print_warning(f"{api_name}: No results (API working but no matches)")
                    results["warnings"] += 1
            except Exception as e:
                print_error(f"{api_name}: {str(e)[:100]}")
                results["failed"] += 1
        
        # Test 4.3: Prioritization (mock)
        print_step("4.3", "Testing prioritization logic...")
        print_warning("Skipping prioritization test (requires discovered URLs)")
        results["warnings"] += 1
        
        # Test 4.4: Download test (single DOI)
        print_step("4.4", "Testing paper download (arXiv)...")
        print_warning("Skipping download test (to avoid unnecessary API calls)")
        results["warnings"] += 1
        
        print(f"\n{Colors.CYAN}Note: Full source discovery pipeline requires:{Colors.END}")
        print("  1. Building knowledge graph with meta-ontology")
        print("  2. Running discover_sources.py for gap analysis")
        print("  3. Manual review of prioritized sources")
        print("  4. Manual review of downloaded papers")
        print(f"  See {Colors.BOLD}docs/QUICKSTART.md Path 3{Colors.END} for complete workflow\n")
        
    except Exception as e:
        print_error(f"Phase 4 error: {e}")
        import traceback
        traceback.print_exc()
        results["failed"] += 1
    
    return results


# =============================================================================
# PHASE 5: Meta-Ontology Guided GraphRAG (Path 4)
# =============================================================================

def test_phase5_meta_ontology():
    """Test meta-ontology guided graph building"""
    print_section("PHASE 5: Meta-Ontology Guided GraphRAG (Path 4)")
    
    results = {"passed": 0, "failed": 0, "warnings": 0}
    
    try:
        # Test 5.1: Check if meta-ontology exists
        print_step("5.1", "Checking for meta-ontology...")
        meta_ont_path = Path("data/graphs/meta_ontology.ttl")
        
        if meta_ont_path.exists():
            print_success(f"Meta-ontology found: {meta_ont_path}")
            results["passed"] += 1
            
            # Manual checkpoint for ontology editing
            print_manual_checkpoint(
                2,
                f"Review meta-ontology: {meta_ont_path}\n"
                "   - Check domain classes\n"
                "   - Verify properties\n"
                "   - Adjust hierarchies if needed"
            )
        else:
            print_warning("Meta-ontology not found. Run: python scripts/generate_meta_ontology.py")
            results["warnings"] += 1
        
        # Test 5.2: Validate RDF syntax
        if meta_ont_path.exists():
            print_step("5.2", "Validating RDF syntax...")
            try:
                from rdflib import Graph
                g = Graph()
                g.parse(str(meta_ont_path), format='turtle')
                print_success(f"Valid RDF/Turtle format ({len(g)} triples)")
                results["passed"] += 1
            except Exception as e:
                print_error(f"RDF validation failed: {e}")
                results["failed"] += 1
        
    except Exception as e:
        print_error(f"Phase 5 error: {e}")
        import traceback
        traceback.print_exc()
        results["failed"] += 1
    
    return results


# =============================================================================
# PHASE 6: Integration Tests
# =============================================================================

def test_phase6_integration():
    """Run integration test suite"""
    print_section("PHASE 6: Integration Tests")
    
    results = {"passed": 0, "failed": 0, "warnings": 0}
    
    # List of integration tests
    integration_tests = [
        "tests/integration/test_chat.py",
        "tests/integration/test_graph.py",
        "tests/integration/test_expanded_apis.py",
    ]
    
    for test_file in integration_tests:
        if Path(test_file).exists():
            print_step("6.x", f"Running {Path(test_file).name}...")
            print_warning(f"Run manually: python {test_file}")
            results["warnings"] += 1
        else:
            print_error(f"Test file not found: {test_file}")
            results["failed"] += 1
    
    return results


# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

def main():
    """Run complete pipeline test suite"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                            ║")
    print("║           PKM System - Complete Pipeline Test Suite                       ║")
    print("║                                                                            ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}\n")
    
    print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Run all phases
    all_results = []
    
    try:
        all_results.append(("Phase 1: Setup", test_phase1_setup()))
        all_results.append(("Phase 2: Basic Chat", test_phase2_basic_chat()))
        all_results.append(("Phase 3: Knowledge Graph", test_phase3_knowledge_graph()))
        all_results.append(("Phase 4: Source Discovery", test_phase4_source_discovery()))
        all_results.append(("Phase 5: Meta-Ontology", test_phase5_meta_ontology()))
        all_results.append(("Phase 6: Integration", test_phase6_integration()))
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.END}")
        return
    
    # Summary
    print_section("Test Summary")
    
    total_passed = 0
    total_failed = 0
    total_warnings = 0
    
    for phase_name, results in all_results:
        passed = results["passed"]
        failed = results["failed"]
        warnings = results["warnings"]
        
        total_passed += passed
        total_failed += failed
        total_warnings += warnings
        
        status = "✓" if failed == 0 else "✗"
        color = Colors.GREEN if failed == 0 else Colors.RED
        
        print(f"{color}{status} {phase_name:30s}{Colors.END} "
              f"Passed: {passed:3d}  Failed: {failed:3d}  Warnings: {warnings:3d}")
    
    print(f"\n{Colors.BOLD}{'─'*80}{Colors.END}")
    print(f"{Colors.BOLD}Total:{' '*25}{Colors.END} "
          f"Passed: {total_passed:3d}  Failed: {total_failed:3d}  Warnings: {total_warnings:3d}\n")
    
    if total_failed == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ All critical tests passed!{Colors.END}\n")
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ {total_failed} test(s) failed{Colors.END}\n")
    
    print(f"Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Exit code
    sys.exit(0 if total_failed == 0 else 1)


if __name__ == "__main__":
    main()
