"""
Interactive chat interface for vault Q&A.
NotebookLM-style grounded conversations.
"""

import os
import sys
import json
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.rag_engine import VaultRAG
from dotenv import load_dotenv

load_dotenv()


class VaultChat:
    """Interactive chat interface with conversation history."""
    
    def __init__(self, sources_dir: str = "data/sources", model: str = "gpt-4o-mini", verbose: bool = False):
        self.rag = VaultRAG(sources_dir=sources_dir, verbose=verbose)
        self.model = model
        self.verbose = verbose
        self.conversation_history = []
        self.session_start = datetime.now()
    
    def ask(self, question: str, use_semantic: bool = False) -> dict:
        """Ask a question and get grounded response."""
        if self.verbose:
            print(f"[VaultChat] Processing question: {question}")
        
        result = self.rag.ask(question, model=self.model, use_semantic=use_semantic)
        
        if self.verbose:
            print(f"[VaultChat] Result keys: {result.keys()}")
            print(f"[VaultChat] Sources: {result.get('sources', [])}")
        
        # Add to history
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "answer": result.get("answer"),
            "sources": result.get("sources", [])
        })
        
        return result
    
    def save_conversation(self, filename: str = None):
        """Save conversation history to JSON."""
        if filename is None:
            timestamp = self.session_start.strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_{timestamp}.json"
        
        data = {
            "session_start": self.session_start.isoformat(),
            "model": self.model,
            "project_path": self.rag.project_path,
            "num_documents": len(self.rag.documents),
            "conversation": self.conversation_history
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Conversation saved to: {filename}")
    
    def print_response(self, result: dict):
        """Pretty print a response."""
        if result.get('error'):
            print(f"\n❌ {result['error']}\n")
            return
        
        print(f"\n{result['answer']}\n")
        
        if result.get('sources'):
            print("📚 Sources:")
            for src in result['sources']:
                print(f"  [{src['number']}] {src['title']}")
                print(f"      📄 {src['path']}")
                if 'relevance_score' in src:
                    print(f"      📊 Relevance: {src['relevance_score']:.2f}")
            print()
    
    def interactive_session(self):
        """Run interactive chat session."""
        print("=" * 80)
        print("🤖 Obsidian Vault Chat - NotebookLM Style")
        print("=" * 80)
        print()
        print(f"📁 Project: {self.rag.project_path}")
        print(f"📚 Documents loaded: {len(self.rag.documents)}")
        print(f"🤖 Model: {self.model}")
        print()
        print("Commands:")
        print("  • Type your question and press Enter")
        print("  • 'save' - Save conversation")
        print("  • 'stats' - Show vault statistics")
        print("  • 'sources' - List all loaded sources")
        print("  • 'exit' or 'quit' - End session")
        print()
        print("=" * 80)
        
        while True:
            try:
                user_input = input("\n💭 You: ").strip()
                
                if not user_input:
                    continue
                
                # Commands
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("\n👋 Ending session...")
                    save = input("Save conversation? (y/n): ").strip().lower()
                    if save == 'y':
                        self.save_conversation()
                    break
                
                elif user_input.lower() == 'save':
                    self.save_conversation()
                    continue
                
                elif user_input.lower() == 'stats':
                    stats = self.rag.get_stats()
                    print(f"\n📊 Vault Statistics:")
                    print(f"  Documents: {stats['num_documents']}")
                    print(f"  Characters: {stats['total_characters']:,}")
                    print(f"  Sections: {stats['total_sections']}")
                    print(f"  Avg doc length: {stats['avg_doc_length']:,} chars")
                    continue
                
                elif user_input.lower() == 'sources':
                    print(f"\n📚 Loaded Sources ({len(self.rag.documents)}):")
                    for i, doc in enumerate(self.rag.documents, 1):
                        print(f"  {i}. {doc.title}")
                        print(f"     📄 {doc.path}")
                    continue
                
                # Ask question
                print("\n🔍 Searching vault...")
                result = self.ask(user_input)
                
                print("\n🤖 Assistant:")
                self.print_response(result)
                
            except KeyboardInterrupt:
                print("\n\n👋 Session interrupted")
                save = input("Save conversation? (y/n): ").strip().lower()
                if save == 'y':
                    self.save_conversation()
                break
            
            except Exception as e:
                print(f"\n❌ Error: {str(e)}\n")


def main():
    """Run interactive chat."""
    chat = VaultChat()
    chat.interactive_session()


if __name__ == "__main__":
    main()
