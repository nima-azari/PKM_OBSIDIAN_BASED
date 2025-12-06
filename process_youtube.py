"""
Process YouTube URLs from youtube_links.txt

Usage:
    python process_youtube.py              # Extract with timestamps
    python process_youtube.py --article    # Convert to article format (AI-powered)

This will:
1. Read URLs from data/sources/youtube_links.txt
2. Extract transcripts for each video
3. Optionally convert to article format (removes timestamps, adds structure)
4. Save them to data/sources/ as markdown files
5. Comment out processed URLs in the file
"""

import sys
from pathlib import Path
from core.document_processor import DocumentProcessor


def process_youtube_links(links_file: str = "data/sources/youtube_links.txt", convert_to_article: bool = False):
    """Process all YouTube links from a text file"""
    
    links_path = Path(links_file)
    
    if not links_path.exists():
        print(f"Creating new links file: {links_file}")
        links_path.parent.mkdir(parents=True, exist_ok=True)
        with open(links_path, 'w', encoding='utf-8') as f:
            f.write("# YouTube Links to Process\n")
            f.write("# Add one URL per line, lines starting with # are ignored\n\n")
        print(f"✓ Created {links_file}")
        print(f"  Add your YouTube URLs (one per line) and run this script again.")
        return
    
    # Read all lines
    with open(links_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find URLs to process
    urls_to_process = []
    for i, line in enumerate(lines):
        line = line.strip()
        if line and not line.startswith('#'):
            if 'youtube.com' in line or 'youtu.be' in line:
                urls_to_process.append((i, line))
    
    if not urls_to_process:
        print("No YouTube URLs found in the file.")
        print(f"Add URLs to {links_file} (one per line)")
        return
    
    print(f"Found {len(urls_to_process)} YouTube URLs to process\n")
    
    if convert_to_article:
        print("🤖 AI Article Mode: Converting transcripts to structured articles")
        print("   This will take longer but produces cleaner content\n")
    else:
        print("📝 Timestamp Mode: Preserving original transcript with timestamps\n")
    
    processor = DocumentProcessor(vault_path="data/sources")
    processed_indices = []
    
    for idx, url in urls_to_process:
        print(f"[{idx + 1}/{len(urls_to_process)}] Processing: {url}")
        try:
            note_path = processor.process_youtube_url(
                url,
                tags=['youtube', 'video', 'transcript'],
                convert_to_article=convert_to_article
            )
            print(f"  ✓ Saved to: {note_path}")
            processed_indices.append(idx)
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    # Comment out processed URLs
    if processed_indices:
        print(f"\n✓ Successfully processed {len(processed_indices)} videos")
        print(f"Commenting out processed URLs in {links_file}...")
        
        for idx in processed_indices:
            if not lines[idx].strip().startswith('#'):
                lines[idx] = '# [PROCESSED] ' + lines[idx]
        
        with open(links_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print("✓ Done! Processed URLs have been commented out.")
    
    print(f"\n📁 Transcript files saved to: data/sources/")
    print(f"💬 You can now chat with your video transcripts!")


if __name__ == "__main__":
    print("=" * 60)
    print("YouTube Transcript Processor")
    print("=" * 60)
    print()
    
    # Check for --article flag
    convert_to_article = '--article' in sys.argv or '-a' in sys.argv
    
    if convert_to_article:
        print("Mode: AI Article Conversion 🤖")
    else:
        print("Mode: Timestamped Transcript 📝")
        print("(Use --article flag for AI-converted article format)")
    print()
    
    process_youtube_links(convert_to_article=convert_to_article)
