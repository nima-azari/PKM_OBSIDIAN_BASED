"""
Test script to replicate user's chat interaction with graph-guided retrieval
"""
from features.chat import VaultChat
from dotenv import load_dotenv

load_dotenv()

def test_chat():
    print("=" * 80)
    print("Testing Chat Interface with Graph-Guided Retrieval")
    print("=" * 80)
    
    # Initialize chat with verbose mode
    chat = VaultChat(verbose=True)
    
    # Load the knowledge graph
    print("\n📊 Loading knowledge graph...")
    triples = chat.rag.build_knowledge_graph(enable_chunking=True, enable_topics=True)
    print(f"✓ Loaded graph with {triples} triples\n")
    
    # Test question from user
    question = "what is the project about?"
    
    print(f"\nTesting question: '{question}'\n")
    print("-" * 80)
    
    # Ask question with graph retrieval
    result = chat.ask(question)
    
    print("\n" + "=" * 80)
    print("RESULT:")
    print("=" * 80)
    
    # Use the chat's print method to show retrieval path
    chat.print_response(result)
    
    print("=" * 80)

if __name__ == "__main__":
    test_chat()
