"""
Test script to replicate user's chat interaction
"""
from features.chat import VaultChat
from dotenv import load_dotenv

load_dotenv()

def test_chat():
    print("=" * 80)
    print("Testing Chat Interface")
    print("=" * 80)
    
    # Initialize chat with verbose mode
    chat = VaultChat(verbose=True)
    
    # Test question from user
    question = "what is the project about?"
    
    print(f"\n\nTesting question: '{question}'\n")
    print("-" * 80)
    
    # Ask question
    result = chat.ask(question)
    
    print("\n" + "=" * 80)
    print("RESULT:")
    print("=" * 80)
    
    if 'error' in result:
        print(f"ERROR: {result['error']}")
    else:
        print(f"\nAnswer:\n{result['answer']}\n")
        
        print(f"\nSources ({len(result.get('sources', []))}):")
        for i, source in enumerate(result.get('sources', []), 1):
            print(f"  {i}. {source}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_chat()
