#!/usr/bin/env python3
"""
Source Importance Annotator

Allows researcher to assign importance ratings (1-5) to sources.
These ratings guide graph construction weighting and retrieval prioritization.

Usage:
    python annotate_sources.py                    # Annotate all sources
    python annotate_sources.py --new-only         # Only unannotated sources
    python annotate_sources.py --update SOURCE    # Update specific source
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional
import yaml
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))


class SourceAnnotator:
    """Manage source importance annotations."""
    
    IMPORTANCE_LEVELS = {
        1: "REFERENCE - Background context only",
        2: "SUPPORTING - Provides supporting evidence",
        3: "RELEVANT - Directly relevant to research",
        4: "KEY - Key contribution to domain",
        5: "CRITICAL - Essential primary source"
    }
    
    def __init__(self, sources_dir: str = "data/sources", annotations_file: str = "data/source_annotations.yaml", verbose: bool = False):
        self.sources_dir = Path(sources_dir)
        self.annotations_file = Path(annotations_file)
        self.annotations = self._load_annotations()
        self.verbose = verbose
    
    def _load_annotations(self) -> Dict[str, Dict]:
        """Load existing annotations."""
        if self.annotations_file.exists():
            with open(self.annotations_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {}
    
    def _save_annotations(self):
        """Save annotations to file."""
        self.annotations_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.annotations_file, 'w', encoding='utf-8') as f:
            yaml.dump(self.annotations, f, default_flow_style=False, sort_keys=False)
        print(f"\n✓ Saved annotations to: {self.annotations_file}")
    
    def _extract_title_from_file(self, filepath: Path) -> str:
        """Extract title from file (from frontmatter or filename)."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try to extract from YAML frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    if isinstance(frontmatter, dict) and 'title' in frontmatter:
                        return frontmatter['title']
            
            # Fallback to filename
            return filepath.stem
        except:
            return filepath.stem
    
    def get_unannotated_sources(self) -> List[Path]:
        """Get list of sources without annotations."""
        all_sources = list(self.sources_dir.glob('**/*.md')) + \
                     list(self.sources_dir.glob('**/*.txt')) + \
                     list(self.sources_dir.glob('**/*.pdf')) + \
                     list(self.sources_dir.glob('**/*.html'))
        
        unannotated = []
        for source in all_sources:
            if source.name not in self.annotations:
                unannotated.append(source)
        
        return unannotated
    
    def get_annotated_sources(self) -> List[tuple]:
        """Get list of annotated sources with their ratings."""
        annotated = []
        for filename, data in self.annotations.items():
            filepath = self.sources_dir / filename
            if filepath.exists():
                annotated.append((filepath, data))
        return annotated
    
    def annotate_source(self, filepath: Path, interactive: bool = True) -> Dict:
        """Annotate a single source with importance rating."""
        
        title = self._extract_title_from_file(filepath)
        
        print("\n" + "="*70)
        print(f"📄 Source: {filepath.name}")
        print(f"📝 Title: {title}")
        print("="*70)
        
        # Show existing annotation if available
        existing = self.annotations.get(filepath.name, {})
        if existing:
            print(f"\n⚠️  Existing annotation:")
            print(f"   Importance: {existing['importance']}/5 - {self.IMPORTANCE_LEVELS[existing['importance']]}")
            print(f"   Note: {existing.get('note', 'N/A')}")
            print(f"   Annotated: {existing.get('annotated_date', 'N/A')}")
        
        if not interactive:
            # Return existing or default
            return existing if existing else {'importance': 3, 'note': 'Auto-assigned'}
        
        # Show first 500 chars of content as preview
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(1000)
                # Skip frontmatter if present
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        content = parts[2][:500]
                else:
                    content = content[:500]
                
                print(f"\n📖 Preview:")
                print("   " + content[:300].replace('\n', '\n   ') + "...")
        except:
            pass
        
        # Display importance levels
        print("\n🎯 Importance Levels:")
        for level, description in self.IMPORTANCE_LEVELS.items():
            print(f"   {level} - {description}")
        
        # Get rating
        while True:
            try:
                rating_input = input("\n⭐ Enter importance (1-5, 's' to skip/delete, 'q' to quit): ").strip().lower()
                
                if rating_input == 'q':
                    print("   ⏹️  Quitting annotation process")
                    return 'QUIT'
                
                if rating_input == 's':
                    # Skip means delete the file (bad source)
                    confirm = input("   ⚠️  Delete this file? (y/n): ").strip().lower()
                    if confirm == 'y':
                        try:
                            filepath.unlink()
                            # Remove from annotations if it was there
                            if filepath.name in self.annotations:
                                del self.annotations[filepath.name]
                            print(f"   🗑️  Deleted: {filepath.name}")
                            return 'DELETED'
                        except Exception as e:
                            print(f"   ❌ Error deleting file: {e}")
                            return None
                    else:
                        print("   Skipped (file kept)")
                        return existing if existing else None
                
                rating = int(rating_input)
                if 1 <= rating <= 5:
                    break
                else:
                    print("   ⚠️  Please enter a number between 1 and 5")
            except ValueError:
                print("   ⚠️  Please enter a valid number, 's' to skip/delete, or 'q' to quit")
        
        # Get optional note
        note = input("\n📝 Add note (optional, press Enter to skip): ").strip()
        
        # Create annotation
        annotation = {
            'importance': rating,
            'title': title,
            'note': note if note else None,
            'annotated_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'annotator': 'researcher'
        }
        
        # Save annotation
        self.annotations[filepath.name] = annotation
        
        print(f"\n✓ Annotated: {rating}/5 - {self.IMPORTANCE_LEVELS[rating]}")
        
        return annotation
    
    def batch_annotate(self, new_only: bool = False):
        """Batch annotate multiple sources."""
        
        if new_only:
            sources = self.get_unannotated_sources()
            print(f"\n📚 Found {len(sources)} unannotated sources")
        else:
            all_sources = list(self.sources_dir.glob('**/*.md')) + \
                         list(self.sources_dir.glob('**/*.txt')) + \
                         list(self.sources_dir.glob('**/*.pdf')) + \
                         list(self.sources_dir.glob('**/*.html'))
            sources = all_sources
            print(f"\n📚 Found {len(sources)} total sources")
        
        if not sources:
            print("✓ No sources to annotate")
            return
        
        print(f"\n🎯 Starting annotation process...")
        print("   (Press 's' to delete bad sources, 'q' to quit)\n")
        
        annotated_count = 0
        skipped_count = 0
        deleted_count = 0
        already_annotated_count = 0
        
        for i, source in enumerate(sources, 1):
            # Skip if already annotated (unless new_only=False which means re-annotate)
            if not new_only and source.name in self.annotations:
                already_annotated_count += 1
                if self.verbose:
                    existing = self.annotations[source.name]
                    print(f"\n[{i}/{len(sources)}] ✓ Already annotated: {source.name} ({existing['importance']}/5)")
                continue
            
            print(f"\n{'='*70}")
            print(f"Progress: [{i}/{len(sources)}]")
            
            result = self.annotate_source(source, interactive=True)
            
            # Check for quit signal
            if result == 'QUIT':
                print("\n⚠️  Annotation process stopped by user")
                break
            
            if result == 'DELETED':
                deleted_count += 1
            elif result:
                annotated_count += 1
            else:
                skipped_count += 1
            
            # Save after each annotation (in case of interruption)
            self._save_annotations()
        
        print(f"\n{'='*70}")
        print(f"✅ Annotation Complete!")
        print(f"   Newly annotated: {annotated_count}")
        print(f"   Skipped: {skipped_count}")
        print(f"   Deleted (bad sources): {deleted_count}")
        if already_annotated_count > 0:
            print(f"   Already annotated (skipped): {already_annotated_count}")
        print(f"   Total in database: {len(self.annotations)} sources")
        print(f"{'='*70}\n")
    
    def show_statistics(self):
        """Display annotation statistics."""
        
        if not self.annotations:
            print("\n⚠️  No annotations found")
            return
        
        print("\n" + "="*70)
        print("📊 Source Annotation Statistics")
        print("="*70)
        
        # Count by importance
        by_importance = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for data in self.annotations.values():
            importance = data.get('importance', 3)
            by_importance[importance] += 1
        
        print(f"\n📚 Total Annotated: {len(self.annotations)} sources\n")
        print("🎯 By Importance Level:")
        for level in sorted(by_importance.keys(), reverse=True):
            count = by_importance[level]
            percentage = (count / len(self.annotations)) * 100
            bar = "█" * int(percentage / 5)
            print(f"   {level} - {self.IMPORTANCE_LEVELS[level]}")
            print(f"       {count:3d} sources ({percentage:5.1f}%) {bar}")
        
        # Show critical and key sources
        critical = [(name, data) for name, data in self.annotations.items() if data['importance'] >= 4]
        if critical:
            print(f"\n🔥 Critical & Key Sources ({len(critical)}):")
            for name, data in sorted(critical, key=lambda x: x[1]['importance'], reverse=True):
                print(f"   [{data['importance']}/5] {data.get('title', name)}")
                if data.get('note'):
                    print(f"           Note: {data['note']}")
        
        print("\n" + "="*70 + "\n")
    
    def export_weighted_list(self, output_file: str = "data/weighted_sources.txt"):
        """Export source list ordered by importance."""
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Group by importance
        by_importance = {5: [], 4: [], 3: [], 2: [], 1: []}
        for name, data in self.annotations.items():
            importance = data.get('importance', 3)
            by_importance[importance].append((name, data))
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Weighted Source List\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"# Total Sources: {len(self.annotations)}\n\n")
            
            for level in sorted(by_importance.keys(), reverse=True):
                sources = by_importance[level]
                if sources:
                    f.write(f"\n## IMPORTANCE {level}/5 - {self.IMPORTANCE_LEVELS[level]}\n")
                    f.write(f"## Count: {len(sources)}\n\n")
                    
                    for name, data in sorted(sources, key=lambda x: x[1].get('title', x[0])):
                        f.write(f"### {data.get('title', name)}\n")
                        f.write(f"File: {name}\n")
                        if data.get('note'):
                            f.write(f"Note: {data['note']}\n")
                        f.write(f"Annotated: {data.get('annotated_date', 'N/A')}\n\n")
        
        print(f"✓ Exported weighted list to: {output_path}")
        return output_path


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Annotate sources with importance ratings')
    parser.add_argument('--new-only', action='store_true',
                       help='Only annotate unannotated sources')
    parser.add_argument('--update', type=str, metavar='SOURCE',
                       help='Update annotation for specific source')
    parser.add_argument('--stats', action='store_true',
                       help='Show annotation statistics')
    parser.add_argument('--export', type=str, metavar='FILE',
                       help='Export weighted source list')
    parser.add_argument('--sources-dir', default='data/sources',
                       help='Directory containing source files')
    
    args = parser.parse_args()
    
    annotator = SourceAnnotator(sources_dir=args.sources_dir)
    
    if args.stats:
        annotator.show_statistics()
    elif args.export:
        annotator.export_weighted_list(args.export)
    elif args.update:
        source_path = Path(args.sources_dir) / args.update
        if not source_path.exists():
            print(f"❌ Source not found: {source_path}")
            return 1
        annotator.annotate_source(source_path, interactive=True)
        annotator._save_annotations()
    else:
        # Default: batch annotate
        annotator.batch_annotate(new_only=args.new_only)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
