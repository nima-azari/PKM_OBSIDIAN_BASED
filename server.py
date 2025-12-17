"""
Simple HTTP server for PKM Chat Assistant
Uses Flask for the backend API
"""
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from pathlib import Path
import os
from dotenv import load_dotenv

from features.chat import VaultChat

load_dotenv()

app = Flask(__name__, 
            static_folder='static',
            static_url_path='/static')
CORS(app)

# Initialize chat with verbose mode
chat = VaultChat(verbose=True)

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('static', 'index.html')

@app.route('/api/stats')
def stats():
    """Get statistics about loaded documents"""
    return jsonify({
        'num_documents': len(chat.rag.documents),
        'sources': [{'title': doc.title, 'path': doc.path} for doc in chat.rag.documents]
    })

@app.route('/api/ask', methods=['POST'])
def ask():
    """Process a question and return answer with sources"""
    try:
        data = request.json
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        
        print(f"\n{'='*80}")
        print(f"[API] 📨 Received question: {question}")
        print(f"{'='*80}")
        
        # Measure time
        import time
        start_time = time.time()
        
        print("[ENGINE] 🔍 Starting RAG engine...")
        print("[ENGINE] 📚 Searching through documents...")
        
        # Get response from chat
        result = chat.ask(question)
        
        elapsed_time = time.time() - start_time
        
        print(f"[ENGINE] ✅ Processing complete!")
        print(f"[ENGINE] ⏱️  Time taken: {elapsed_time:.2f}s")
        
        if result.get('sources'):
            print(f"[ENGINE] 📖 Found {len(result['sources'])} relevant sources:")
            for i, src in enumerate(result['sources'], 1):
                print(f"[ENGINE]    [{i}] {src.get('title', 'Unknown')}")
        
        print(f"[ENGINE] 📝 Generated answer length: {len(result.get('answer', ''))} characters")
        print(f"{'='*80}\n")
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 500
        
        return jsonify({
            'answer': result.get('answer', 'No answer generated'),
            'sources': result.get('sources', []),
            'model': result.get('model', 'unknown'),
            'elapsed_time': elapsed_time
        })
    
    except Exception as e:
        print(f"[API] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/source')
def get_source():
    """Serve a source file"""
    path = request.args.get('path')
    if not path:
        return "No path provided", 400
    
    # Security check: ensure path is within data/sources
    # precise implementation depends on how paths are stored. 
    # self.rag.documents stores absolute paths or relative?
    # Let's assume relative to CWD or absolute.
    # We should just try to serve it if it exists and is a file.
    
    if os.path.exists(path) and os.path.isfile(path):
        directory = os.path.dirname(path)
        filename = os.path.basename(path)
        return send_from_directory(directory, filename)
    else:
        # Try relative to cwd
        if os.path.exists(os.path.abspath(path)):
             directory = os.path.dirname(os.path.abspath(path))
             filename = os.path.basename(os.path.abspath(path))
             return send_from_directory(directory, filename)
        
        return "File not found", 404

def main():
    """Start the Flask server"""
    print("=" * 80)
    print("PKM Chat Assistant - HTML/CSS Interface")
    print("=" * 80)
    print(f"\nLoaded {len(chat.rag.documents)} documents from data/sources/")
    print("\nStarting server...")
    print("\n🌐 Open your browser to: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 80)
    
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    main()
