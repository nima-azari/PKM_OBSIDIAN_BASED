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
        
        print(f"\n[API] Received question: {question}")
        
        # Get response from chat
        result = chat.ask(question)
        
        print(f"[API] Response: {result.get('answer', 'No answer')[:100]}...")
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 500
        
        return jsonify({
            'answer': result.get('answer', 'No answer generated'),
            'sources': result.get('sources', []),
            'model': result.get('model', 'unknown')
        })
    
    except Exception as e:
        print(f"[API] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

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
