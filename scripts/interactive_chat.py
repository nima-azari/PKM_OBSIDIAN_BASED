"""
Interactive Chat Session with Graph-Guided Retrieval
Quick launcher for research sessions
"""
from features.chat import VaultChat
from dotenv import load_dotenv

load_dotenv()

def main():
    print("=" * 80)
    print("🚀 Starting Interactive Research Session")
    print("=" * 80)
    print()
    
    # Initialize chat
    print("📚 Initializing chat system...")
    chat = VaultChat(verbose=True)
    
    # Build knowledge graph
    print("\n🔗 Building knowledge graph...")
    triples = chat.rag.build_knowledge_graph(enable_chunking=True, enable_topics=True)
    
    if triples > 0:
        print(f"✓ Knowledge graph loaded: {triples} triples")
        
        # Get graph stats
        stats = chat.rag.get_graph_stats()
        print(f"  • Documents: {stats.get('documents', 0)}")
        print(f"  • Chunks: {stats.get('chunks', 0)}")
        print(f"  • Concepts: {stats.get('domain_concepts', 0)}")
        print(f"  • Topics: {stats.get('topic_nodes', 0)}")
    else:
        print("⚠️  No graph data found. Add documents to data/sources/ and try again.")
        return
    
    print("\n" + "=" * 80)
    print()
    
    # Start interactive session
    chat.interactive_session()

if __name__ == "__main__":
    main()
