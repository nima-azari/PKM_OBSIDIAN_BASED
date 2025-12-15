#!/usr/bin/env python3
"""
Researcher-in-the-Loop Pipeline

Complete iterative research workflow with human feedback at each stage:
1. Annotate initial sources with importance ratings (1-5)
2. Build/refine meta-ontology with researcher supervision
3. Build weighted knowledge graph using annotations
4. Discover new sources (with priorities)
5. Researcher reviews and finalizes discovery list
6. Auto-download papers from DOIs
7. Annotate new sources
8. Refine meta-ontology and knowledge graph
9. Ready for graph-guided chat

Usage:
    python research_pipeline.py --init          # Initialize pipeline
    python research_pipeline.py --discover      # Run discovery phase
    python research_pipeline.py --integrate     # Integrate discovered sources
    python research_pipeline.py --status        # Show pipeline status
"""

import sys
from pathlib import Path
from typing import Dict, List
import yaml
from datetime import datetime
import subprocess

sys.path.insert(0, str(Path(__file__).parent.parent))


class ResearchPipeline:
    """Orchestrate researcher-in-the-loop workflow."""
    
    def __init__(self, workspace_dir: str = "."):
        self.workspace = Path(workspace_dir)
        self.sources_dir = self.workspace / "data" / "sources"
        self.graphs_dir = self.workspace / "data" / "graphs"
        self.annotations_file = self.workspace / "data" / "source_annotations.yaml"
        self.meta_ontology_file = self.graphs_dir / "meta_ontology.ttl"
        self.knowledge_graph_file = self.graphs_dir / "knowledge_graph.ttl"
        self.discovery_file = self.workspace / "data" / "discovered_urls.txt"
        self.pipeline_state_file = self.workspace / "data" / "pipeline_state.yaml"
        
        self.state = self._load_state()
    
    def _load_state(self) -> Dict:
        """Load pipeline state."""
        if self.pipeline_state_file.exists():
            with open(self.pipeline_state_file, 'r') as f:
                return yaml.safe_load(f) or {}
        return {
            'phase': 'uninitialized',
            'iterations': 0,
            'last_update': None,
            'sources_count': 0,
            'annotations_count': 0
        }
    
    def _save_state(self):
        """Save pipeline state."""
        self.pipeline_state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        with open(self.pipeline_state_file, 'w') as f:
            yaml.dump(self.state, f, default_flow_style=False)
    
    def _run_command(self, cmd: List[str], description: str) -> bool:
        """Run command and handle errors."""
        print(f"\n🔧 {description}...")
        print(f"   Command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            if result.stdout:
                print(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error: {e}")
            if e.stderr:
                print(e.stderr)
            return False
    
    def show_status(self):
        """Display current pipeline status."""
        
        print("\n" + "="*70)
        print("📊 RESEARCH PIPELINE STATUS")
        print("="*70)
        
        # Current phase
        phase = self.state.get('phase', 'uninitialized')
        iterations = self.state.get('iterations', 0)
        last_update = self.state.get('last_update', 'Never')
        
        print(f"\n🎯 Current Phase: {phase.upper()}")
        print(f"🔄 Iterations: {iterations}")
        print(f"⏱️  Last Update: {last_update}")
        
        # Count resources
        sources_count = len(list(self.sources_dir.glob('*.md'))) + \
                       len(list(self.sources_dir.glob('*.pdf'))) + \
                       len(list(self.sources_dir.glob('*.html'))) + \
                       len(list(self.sources_dir.glob('*.txt')))
        
        annotations_count = 0
        if self.annotations_file.exists():
            with open(self.annotations_file, 'r') as f:
                annotations = yaml.safe_load(f) or {}
                annotations_count = len(annotations)
        
        meta_exists = self.meta_ontology_file.exists()
        graph_exists = self.knowledge_graph_file.exists()
        discovery_exists = self.discovery_file.exists()
        
        print(f"\n📚 Resources:")
        print(f"   Sources: {sources_count} files")
        print(f"   Annotations: {annotations_count}/{sources_count} " + 
              ("✓" if annotations_count == sources_count else "⚠️"))
        print(f"   Meta-Ontology: {'✓ Built' if meta_exists else '✗ Not built'}")
        print(f"   Knowledge Graph: {'✓ Built' if graph_exists else '✗ Not built'}")
        print(f"   Discovery List: {'✓ Available' if discovery_exists else '✗ Not available'}")
        
        # Show next steps
        print(f"\n🎯 Next Steps:")
        
        if phase == 'uninitialized':
            print("   1. Run: python scripts/research_pipeline.py --init")
            print("      → Annotate initial sources and build foundation")
        
        elif phase == 'initialized':
            print("   1. Review meta-ontology: data/graphs/meta_ontology.ttl")
            print("   2. Refine if needed, then:")
            print("      python scripts/research_pipeline.py --discover")
        
        elif phase == 'discovery_pending':
            print("   1. Review discovery list: data/discovered_urls.txt")
            print("   2. Edit file to finalize sources (remove unwanted)")
            print("   3. Run: python scripts/research_pipeline.py --integrate")
        
        elif phase == 'ready_for_chat':
            print("   ✓ Pipeline ready!")
            print("   1. Start chat: python scripts/interactive_chat.py")
            print("   2. Or discover more: python scripts/research_pipeline.py --discover")
        
        print("\n" + "="*70 + "\n")
    
    def phase_1_initialize(self):
        """Phase 1: Annotate initial sources and build foundation."""
        
        print("\n" + "="*70)
        print("🎯 PHASE 1: INITIALIZATION")
        print("="*70)
        
        print("\n📝 Step 1: Annotate Initial Sources")
        print("   You will rate each source's importance (1-5)")
        print("   This guides graph weighting and retrieval priorities\n")
        
        input("Press Enter to start annotation process (Ctrl+C to cancel)...")
        
        # Run annotation script
        success = self._run_command(
            ['python', 'scripts/annotate_sources.py'],
            "Annotating sources"
        )
        
        if not success:
            print("\n❌ Annotation failed. Please run manually:")
            print("   python scripts/annotate_sources.py")
            return False
        
        # Show annotation statistics
        self._run_command(
            ['python', 'scripts/annotate_sources.py', '--stats'],
            "Showing annotation statistics"
        )
        
        print("\n📊 Step 2: Generate Meta-Ontology")
        print("   Creating domain model from your research focus...\n")
        
        # Ask for domain description
        print("Please describe your research domain:")
        print("   Example: 'EU Data Act, semantic web, knowledge graphs, data portability'")
        domain = input("\n🔍 Domain: ").strip()
        
        if not domain:
            domain = "knowledge management, semantic web, knowledge graphs"
            print(f"   Using default: {domain}")
        
        # Generate meta-ontology
        success = self._run_command(
            ['python', 'scripts/generate_meta_ontology.py', 
             '--domain', domain,
             '--output', str(self.meta_ontology_file)],
            "Generating meta-ontology"
        )
        
        if not success:
            print("\n⚠️  Meta-ontology generation had issues")
            print("   You can create it manually or continue without it")
        
        print("\n🕸️  Step 3: Build Weighted Knowledge Graph")
        print("   Building graph with importance-weighted sources...\n")
        
        # Build knowledge graph with meta-ontology and weights
        cmd = ['python', 'scripts/build_graph.py']
        if self.meta_ontology_file.exists():
            cmd.extend(['--meta-ontology', str(self.meta_ontology_file)])
        
        success = self._run_command(cmd, "Building knowledge graph")
        
        if not success:
            print("\n❌ Graph building failed")
            return False
        
        # Update state
        self.state['phase'] = 'initialized'
        self.state['iterations'] = 1
        self._save_state()
        
        print("\n" + "="*70)
        print("✅ INITIALIZATION COMPLETE")
        print("="*70)
        print("\n📋 What was created:")
        print(f"   ✓ Source annotations: {self.annotations_file}")
        print(f"   ✓ Meta-ontology: {self.meta_ontology_file}")
        print(f"   ✓ Knowledge graph: {self.knowledge_graph_file}")
        
        print("\n🎯 Next Steps:")
        print("   1. Review meta-ontology (optional refinement)")
        print("   2. Run discovery: python scripts/research_pipeline.py --discover")
        print("   3. Or start chat: python scripts/interactive_chat.py")
        print("\n" + "="*70 + "\n")
        
        return True
    
    def phase_2_discover(self):
        """Phase 2: Discover new sources with priorities."""
        
        print("\n" + "="*70)
        print("🔍 PHASE 2: SOURCE DISCOVERY")
        print("="*70)
        
        print("\n📊 Analyzing knowledge gaps...")
        
        # Run gap analysis (if discover_sources.py exists)
        discover_script = self.workspace / "scripts" / "discover_sources.py"
        if discover_script.exists():
            self._run_command(
                ['python', str(discover_script)],
                "Running gap analysis"
            )
            report_file = self.workspace / "data" / "discovery_report.txt"
        else:
            print("   ⚠️  Gap analysis script not found, using direct discovery")
            report_file = None
        
        print("\n🌐 Searching 24+ APIs for relevant sources...")
        print("   (Using semantic filtering for quality)")
        
        # Run automated discovery with semantic filtering
        cmd = ['python', 'scripts/auto_discover_sources.py', 
               '--semantic-filter',
               '--min-new-sources', '10',
               '--output', str(self.discovery_file)]
        
        if report_file and report_file.exists():
            cmd.extend(['--report', str(report_file)])
        
        success = self._run_command(cmd, "Running automated discovery")
        
        if not success or not self.discovery_file.exists():
            print("\n❌ Discovery failed or produced no results")
            return False
        
        # Update state
        self.state['phase'] = 'discovery_pending'
        self._save_state()
        
        print("\n" + "="*70)
        print("✅ DISCOVERY COMPLETE")
        print("="*70)
        
        print(f"\n📝 Discovery list saved to: {self.discovery_file}")
        print("\n🎯 RESEARCHER ACTION REQUIRED:")
        print("   1. Open and review: data/discovered_urls.txt")
        print("   2. Remove any unwanted sources (manual curation)")
        print("   3. Save the file with your final selections")
        print("   4. Run: python scripts/research_pipeline.py --integrate")
        
        print("\n💡 TIP: The file is organized by priority (HIGH/MEDIUM/LOW)")
        print("   You can keep only HIGH priority sources if desired")
        
        print("\n" + "="*70 + "\n")
        
        return True
    
    def phase_3_integrate(self):
        """Phase 3: Integrate discovered sources with feedback loop."""
        
        print("\n" + "="*70)
        print("🔄 PHASE 3: INTEGRATE DISCOVERED SOURCES")
        print("="*70)
        
        if not self.discovery_file.exists():
            print("\n❌ Discovery file not found: data/discovered_urls.txt")
            print("   Run: python scripts/research_pipeline.py --discover")
            return False
        
        print("\n📥 Step 1: Download Papers from DOIs")
        
        # Auto-download papers
        success = self._run_command(
            ['python', 'scripts/auto_download_papers.py', str(self.discovery_file)],
            "Downloading papers"
        )
        
        # Also import URLs (for non-DOI sources)
        print("\n📥 Step 2: Import Web Sources")
        self._run_command(
            ['python', 'scripts/import_urls.py', str(self.discovery_file)],
            "Importing web sources"
        )
        
        print("\n📝 Step 3: Annotate New Sources")
        print("   Rate the importance of newly added sources\n")
        
        input("Press Enter to start annotation (Ctrl+C to cancel)...")
        
        # Annotate only new sources
        success = self._run_command(
            ['python', 'scripts/annotate_sources.py', '--new-only'],
            "Annotating new sources"
        )
        
        if not success:
            print("\n⚠️  Some sources may not be annotated")
            print("   You can annotate manually later with:")
            print("   python scripts/annotate_sources.py --new-only")
        
        print("\n🔄 Step 4: Refine Meta-Ontology")
        print("   Updating domain model with new concepts...\n")
        
        # Ask if researcher wants to refine meta-ontology
        refine = input("Refine meta-ontology with new sources? (y/n, default: y): ").strip().lower()
        
        if refine != 'n':
            # Backup existing meta-ontology
            if self.meta_ontology_file.exists():
                backup = self.meta_ontology_file.with_suffix('.ttl.backup')
                import shutil
                shutil.copy(self.meta_ontology_file, backup)
                print(f"   ✓ Backed up to: {backup}")
            
            # Ask for updated domain description
            print("\n   Current domain focus + new insights?")
            domain = input("   🔍 Domain (or Enter to skip): ").strip()
            
            if domain:
                self._run_command(
                    ['python', 'scripts/generate_meta_ontology.py',
                     '--domain', domain,
                     '--output', str(self.meta_ontology_file)],
                    "Refining meta-ontology"
                )
        
        print("\n🕸️  Step 5: Rebuild Knowledge Graph")
        print("   Integrating new sources with updated weights...\n")
        
        # Rebuild knowledge graph
        cmd = ['python', 'scripts/build_graph.py']
        if self.meta_ontology_file.exists():
            cmd.extend(['--meta-ontology', str(self.meta_ontology_file)])
        
        success = self._run_command(cmd, "Rebuilding knowledge graph")
        
        if not success:
            print("\n❌ Graph rebuild failed")
            return False
        
        # Update state
        self.state['phase'] = 'ready_for_chat'
        self.state['iterations'] += 1
        self._save_state()
        
        print("\n" + "="*70)
        print("✅ INTEGRATION COMPLETE")
        print("="*70)
        
        print(f"\n🔄 Iteration {self.state['iterations']} finished")
        
        # Show statistics
        self._run_command(
            ['python', 'scripts/annotate_sources.py', '--stats'],
            "Showing updated statistics"
        )
        
        print("\n🎯 Next Steps:")
        print("   1. Start research chat:")
        print("      python scripts/interactive_chat.py")
        print("\n   2. Or discover more sources:")
        print("      python scripts/research_pipeline.py --discover")
        
        print("\n" + "="*70 + "\n")
        
        return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Researcher-in-the-loop pipeline')
    parser.add_argument('--init', action='store_true',
                       help='Initialize pipeline (Phase 1)')
    parser.add_argument('--discover', action='store_true',
                       help='Run source discovery (Phase 2)')
    parser.add_argument('--integrate', action='store_true',
                       help='Integrate discovered sources (Phase 3)')
    parser.add_argument('--status', action='store_true',
                       help='Show pipeline status')
    parser.add_argument('--reset', action='store_true',
                       help='Reset pipeline state (careful!)')
    
    args = parser.parse_args()
    
    pipeline = ResearchPipeline()
    
    if args.reset:
        confirm = input("⚠️  Reset pipeline state? (type 'yes'): ").strip()
        if confirm.lower() == 'yes':
            pipeline.state = {
                'phase': 'uninitialized',
                'iterations': 0,
                'last_update': None
            }
            pipeline._save_state()
            print("✓ Pipeline state reset")
        return 0
    
    if args.status or (not args.init and not args.discover and not args.integrate):
        pipeline.show_status()
        return 0
    
    if args.init:
        success = pipeline.phase_1_initialize()
        return 0 if success else 1
    
    if args.discover:
        success = pipeline.phase_2_discover()
        return 0 if success else 1
    
    if args.integrate:
        success = pipeline.phase_3_integrate()
        return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
