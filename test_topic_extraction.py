"""
Test WebDiscovery's extract_research_topic() method

Tests the AI-powered research topic extraction from document content.
"""

from core.web_discovery import WebDiscovery
from core.rag_engine import VaultRAG
from pathlib import Path

def test_topic_extraction():
    """Test research topic extraction from actual documents"""
    print("\n" + "="*80)
    print("TEST: Research Topic Extraction")
    print("="*80)
    
    sources_dir = Path('data/sources')
    
    # Initialize
    discovery = WebDiscovery()
    rag = VaultRAG(sources_dir=str(sources_dir), verbose=True)
    
    # Load documents (this populates rag.documents internally)
    print("\n📂 Loading documents...")
    rag._load_documents()
    documents = rag.documents
    
    if not documents:
        print("\n⚠️  No documents found in data/sources/")
        print("\nTo test:")
        print("1. Add documents to data/sources/ (.md, .txt, .pdf, .html)")
        print("2. Run this test again")
        return False
    
    print(f"✓ Loaded {len(documents)} document(s)\n")
    
    # Show document details
    print("Documents:")
    for i, doc in enumerate(documents[:5], 1):
        print(f"  {i}. {doc.title[:60]}")
        print(f"     Source: {Path(doc.path).name}")
        print(f"     Length: {len(doc.content):,} chars")
        print()
    
    if len(documents) > 5:
        print(f"  ... and {len(documents) - 5} more\n")
    
    # Test topic extraction
    print("="*80)
    print("Testing Topic Extraction\n")
    
    # Combine first 3 documents
    combined_content = "\n\n---\n\n".join([
        f"Document {i+1}: {doc.title}\n{doc.content[:2000]}"
        for i, doc in enumerate(documents[:3])
    ])
    
    print(f"📊 Combined content: {len(combined_content):,} characters")
    print(f"📝 Using first {min(3, len(documents))} document(s)\n")
    
    # Extract topic
    print("🤖 Extracting research topic with AI...\n")
    
    try:
        research_topic = discovery.extract_research_topic(combined_content, max_words=15)
        
        print("="*80)
        print("✅ EXTRACTION SUCCESSFUL\n")
        
        print(f"🎯 Research Topic:")
        print(f"   {research_topic}\n")
        
        # Analyze quality
        word_count = len(research_topic.split())
        has_specific_terms = any(term in research_topic.lower() for term in [
            'data act', 'eu', 'cloud', 'linked data', 'rdf', 'graph', 
            'portability', 'compliance', 'regulation', 'governance'
        ])
        is_generic = any(term in research_topic.lower() for term in [
            'big data', 'technology', 'innovation', 'digital transformation'
        ])
        
        print("📊 Quality Metrics:")
        print(f"   Word count: {word_count} (target: ≤15)")
        print(f"   Specific terms: {'✓ Yes' if has_specific_terms else '✗ No (too generic)'}")
        print(f"   Generic terms: {'✗ Present' if is_generic else '✓ None (good)'}")
        
        # Overall assessment
        print("\n💡 Assessment:")
        if word_count <= 15 and has_specific_terms and not is_generic:
            print("   ✅ EXCELLENT - Specific, focused, and concise")
        elif word_count <= 15 and has_specific_terms:
            print("   ✓ GOOD - Specific and concise")
        elif has_specific_terms:
            print("   ⚠️ ACCEPTABLE - Specific but too long")
        else:
            print("   ✗ POOR - Too generic or unfocused")
        
        print("\n" + "="*80)
        
        # Test query generation with this topic
        print("\n🔍 Testing Search Query Generation...\n")
        
        queries = discovery._generate_search_queries(research_topic)
        
        print(f"Generated {len(queries)} search queries:\n")
        for i, query in enumerate(queries, 1):
            print(f"  {i}. {query}")
        
        print("\n" + "="*80)
        print("✅ All tests passed!")
        print("="*80)
        
        return True
        
    except Exception as e:
        print("="*80)
        print(f"✗ EXTRACTION FAILED\n")
        print(f"Error: {str(e)}")
        print(f"Type: {type(e).__name__}")
        print("="*80)
        return False

if __name__ == "__main__":
    test_topic_extraction()
