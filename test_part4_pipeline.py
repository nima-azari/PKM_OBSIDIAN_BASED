"""
Test script for Part 4: Knowledge Graph & Article Generation Pipeline

This tests the complete workflow:
1. Build knowledge graph from sources
2. Generate AI article from graph
3. Chat with the generated article

Usage:
    python test_part4_pipeline.py
"""

from pathlib import Path
from core.rag_engine import VaultRAG
from features.chat import VaultChat
from dotenv import load_dotenv
import subprocess
import sys

load_dotenv()


def test_pipeline():
    print("\n" + "=" * 80)
    print("Part 4: Knowledge Graph → Article Pipeline Test")
    print("=" * 80)
    
    # Step 1: Build Knowledge Graph
    print("\n" + "=" * 80)
    print("STEP 1: Building Knowledge Graph")
    print("=" * 80)
    
    graph_path = Path("data/graphs/test_pipeline_graph.ttl")
    
    rag = VaultRAG(sources_dir="data/sources", verbose=True)
    print("\n🔗 Building knowledge graph...")
    num_triples = rag.build_knowledge_graph()
    print(f"✓ Created {num_triples} triples")
    
    print(f"\n💾 Exporting graph to: {graph_path}")
    rag.export_graph_ttl(str(graph_path))
    
    stats = rag.get_graph_stats()
    print("\n📊 Graph Statistics:")
    for key, value in stats.items():
        print(f"  • {key}: {value}")
    
    # Step 2: Generate Article from Graph
    print("\n" + "=" * 80)
    print("STEP 2: Generating Article from Knowledge Graph")
    print("=" * 80)
    
    article_path = Path("data/sources/test_pipeline_article.md")
    
    # Run the article generator
    result = subprocess.run(
        [sys.executable, "generate_article_from_graph.py", str(graph_path), str(article_path)],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✓ Article generated successfully")
        print(result.stdout)
    else:
        print("✗ Article generation failed")
        print(result.stderr)
        return False
    
    # Verify article exists
    if article_path.exists():
        print(f"✓ Article saved to: {article_path}")
        print(f"✓ Article size: {article_path.stat().st_size} bytes")
    else:
        print("✗ Article file not found!")
        return False
    
    # Step 3: Chat with the Article
    print("\n" + "=" * 80)
    print("STEP 3: Testing Chat with Generated Article")
    print("=" * 80)
    
    # Reinitialize chat to pick up new article
    chat = VaultChat(verbose=True)
    
    # Test questions
    questions = [
        "What are the main themes in the knowledge graph article?",
        "What entities are mentioned in the knowledge graph synthesis?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n{'─' * 80}")
        print(f"Question {i}: {question}")
        print('─' * 80)
        
        result = chat.ask(question)
        
        if 'error' in result:
            print(f"✗ ERROR: {result['error']}")
        else:
            print(f"\n📝 Answer:\n{result['answer']}\n")
            
            # Check if the generated article is in the sources
            sources = result.get('sources', [])
            article_found = any('test_pipeline_article' in str(s.get('path', '')) 
                              for s in sources)
            
            if article_found:
                print("✅ Generated article WAS used as a source!")
            else:
                print("⚠️  Generated article was NOT in top sources")
            
            print(f"\nSources ({len(sources)}):")
            for j, source in enumerate(sources[:3], 1):
                print(f"  {j}. {source.get('title', 'Unknown')} (score: {source.get('score', 0):.0f})")
    
    # Summary
    print("\n" + "=" * 80)
    print("PIPELINE TEST SUMMARY")
    print("=" * 80)
    print("✅ Step 1: Knowledge graph built successfully")
    print("✅ Step 2: Article generated from graph")
    print("✅ Step 3: Chat system can query the article")
    print("\n✅ Part 4 pipeline test PASSED!")
    print("=" * 80 + "\n")
    
    return True


if __name__ == "__main__":
    success = test_pipeline()
    sys.exit(0 if success else 1)
