"""
Document Processing Pipeline

Handles various document formats (txt, md, PDF) and adds them to the vault.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib

import pypdf
import core.obsidian_api as obs_api


class DocumentProcessor:
    """Process and ingest documents into vault"""
    
    def __init__(self, vault_path: str = "10-Projects/Cloud-vs-KG-Data-Centric/Literature"):
        self.vault_path = vault_path
    
    def process_file(self, file_path: str, tags: Optional[List[str]] = None) -> str:
        """Process file and add to vault"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Extract content based on file type
        if file_path.suffix.lower() == '.pdf':
            content = self._extract_pdf(file_path)
        elif file_path.suffix.lower() in ['.txt', '.md']:
            content = self._extract_text(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")
        
        # Create note in vault
        note_path = self._create_note(
            file_path.stem,
            content,
            source_file=str(file_path),
            tags=tags
        )
        
        return note_path
    
    def _extract_pdf(self, pdf_path: Path) -> str:
        """Extract text from PDF"""
        reader = pypdf.PdfReader(pdf_path)
        
        text_parts = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text.strip():
                text_parts.append(f"## Page {i+1}\n\n{text}")
        
        return "\n\n".join(text_parts)
    
    def _extract_text(self, text_path: Path) -> str:
        """Extract text from txt/md file"""
        with open(text_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _create_note(
        self,
        title: str,
        content: str,
        source_file: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """Create note in vault with frontmatter"""
        
        # Sanitize title
        safe_title = self._sanitize_filename(title)
        
        # Build frontmatter
        frontmatter_lines = ["---"]
        frontmatter_lines.append(f"title: {title}")
        frontmatter_lines.append(f"type: literature")
        frontmatter_lines.append(f"created: {datetime.now().isoformat()}")
        
        if source_file:
            frontmatter_lines.append(f"source_file: {source_file}")
        
        if tags:
            tags_str = ", ".join(tags)
            frontmatter_lines.append(f"tags: [{tags_str}]")
        
        frontmatter_lines.append("---")
        
        # Combine frontmatter and content
        full_content = "\n".join(frontmatter_lines) + "\n\n" + content
        
        # Create file in vault
        note_path = f"{self.vault_path}/{safe_title}.md"
        
        try:
            # Try to create new file
            obs_api.put_file(note_path, full_content)
            print(f"Created note: {note_path}")
        except Exception as e:
            print(f"Warning: Could not create note via API: {e}")
            print("Note content prepared but not uploaded.")
        
        return note_path
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for vault"""
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '')
        
        # Limit length
        if len(filename) > 100:
            filename = filename[:100]
        
        return filename.strip()
    
    def process_directory(
        self,
        directory_path: str,
        tags: Optional[List[str]] = None,
        recursive: bool = False
    ) -> List[str]:
        """Process all supported files in directory"""
        directory = Path(directory_path)
        
        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"Invalid directory: {directory_path}")
        
        supported_extensions = ['.txt', '.md', '.pdf']
        created_notes = []
        
        # Find files
        if recursive:
            files = []
            for ext in supported_extensions:
                files.extend(directory.rglob(f'*{ext}'))
        else:
            files = []
            for ext in supported_extensions:
                files.extend(directory.glob(f'*{ext}'))
        
        # Process each file
        for file_path in files:
            try:
                note_path = self.process_file(file_path, tags=tags)
                created_notes.append(note_path)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
        
        return created_notes
    
    def add_text_note(
        self,
        title: str,
        content: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add text content directly as note"""
        
        # Build frontmatter
        frontmatter_lines = ["---"]
        frontmatter_lines.append(f"title: {title}")
        frontmatter_lines.append(f"type: note")
        frontmatter_lines.append(f"created: {datetime.now().isoformat()}")
        
        if tags:
            tags_str = ", ".join(tags)
            frontmatter_lines.append(f"tags: [{tags_str}]")
        
        if metadata:
            for key, value in metadata.items():
                frontmatter_lines.append(f"{key}: {value}")
        
        frontmatter_lines.append("---")
        
        # Combine
        full_content = "\n".join(frontmatter_lines) + "\n\n" + content
        
        # Create in vault
        safe_title = self._sanitize_filename(title)
        note_path = f"{self.vault_path}/{safe_title}.md"
        
        try:
            obs_api.put_file(note_path, full_content)
            print(f"Created note: {note_path}")
        except Exception as e:
            print(f"Warning: Could not create note: {e}")
        
        return note_path
    
    def get_document_hash(self, file_path: str) -> str:
        """Get hash of document for deduplication"""
        hasher = hashlib.md5()
        
        with open(file_path, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        
        return hasher.hexdigest()


if __name__ == "__main__":
    # Demo
    processor = DocumentProcessor()
    
    print("Document Processor initialized")
    print(f"Target vault path: {processor.vault_path}")
