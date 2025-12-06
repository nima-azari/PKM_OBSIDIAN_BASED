"""
Test YouTube transcript extraction
"""

from core.document_processor import DocumentProcessor

def test_youtube_extraction():
    """Test extracting YouTube transcripts"""
    processor = DocumentProcessor(vault_path="data/sources")
    
    # Example YouTube URLs
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Example
        "https://youtu.be/dQw4w9WgXcQ",  # Short format
    ]
    
    print("YouTube Transcript Extraction Test")
    print("=" * 50)
    
    for url in test_urls:
        print(f"\nProcessing: {url}")
        try:
            note_path = processor.process_youtube_url(
                url,
                tags=['youtube', 'test']
            )
            print(f"✓ Successfully created: {note_path}")
        except Exception as e:
            print(f"✗ Error: {e}")

if __name__ == "__main__":
    test_youtube_extraction()
