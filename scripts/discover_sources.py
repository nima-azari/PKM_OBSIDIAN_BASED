#!/usr/bin/env python3
"""
Source Discovery Workflow
Uses meta-ontology and knowledge graph to identify knowledge gaps and discover new sources.
"""

import sys
from pathlib import Path
from rdflib import Graph, Namespace, RDF, RDFS, OWL
from rdflib.namespace import SKOS
from typing import Dict, List, Set, Tuple
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.web_discovery import WebDiscovery
from openai import OpenAI

class SourceDiscovery:
    """Analyze knowledge graph gaps and discover new sources."""
    
    def __init__(self, meta_ontology_path: str, knowledge_graph_path: str, verbose: bool = True):
        self.verbose = verbose
        self.meta_ontology_path = meta_ontology_path
        self.knowledge_graph_path = knowledge_graph_path
        
        # Load graphs
        self.meta = Graph()
        self.meta.parse(meta_ontology_path, format='turtle')
        
        self.kg = Graph()
        self.kg.parse(knowledge_graph_path, format='turtle')
        
        # Namespaces
        self.META_NS = Namespace('http://pkm.local/meta-ontology/')
        self.ONTO_NS = Namespace('http://pkm.local/ontology/')
        
        # OpenAI client for query generation
        self.client = OpenAI()
        
        if self.verbose:
            print(f"✓ Loaded meta-ontology: {meta_ontology_path}")
            print(f"✓ Loaded knowledge graph: {knowledge_graph_path}")
    
    def analyze_coverage(self) -> Dict[str, any]:
        """Analyze which meta-ontology concepts have rich vs sparse coverage."""
        
        if self.verbose:
            print("\n" + "="*60)
            print("KNOWLEDGE COVERAGE ANALYSIS")
            print("="*60)
        
        # Get all meta-ontology classes
        meta_classes = {}
        for cls in self.meta.subjects(RDF.type, OWL.Class):
            label = self.meta.value(cls, RDFS.label)
            if label:
                meta_classes[str(label)] = cls
        
        coverage = {}
        
        for class_label, class_uri in meta_classes.items():
            # Find matching domain concepts
            matching_concepts = []
            for concept in self.kg.subjects(RDF.type, self.ONTO_NS.DomainConcept):
                concept_label = self.kg.value(concept, SKOS.prefLabel)
                if concept_label and class_label.lower() in str(concept_label).lower():
                    matching_concepts.append(concept)
            
            # Count related chunks
            chunk_count = 0
            for concept in matching_concepts:
                chunks = list(self.kg.subjects(self.ONTO_NS.mentionsConcept, concept))
                chunk_count += len(chunks)
            
            # Count relationships involving these concepts
            relationship_count = 0
            for concept in matching_concepts:
                # Outgoing relationships
                outgoing = list(self.kg.triples((concept, None, None)))
                # Filter to only meta-ontology properties
                for s, p, o in outgoing:
                    if str(p).startswith(str(self.META_NS)):
                        relationship_count += 1
                
                # Incoming relationships
                incoming = list(self.kg.triples((None, None, concept)))
                for s, p, o in incoming:
                    if str(p).startswith(str(self.META_NS)):
                        relationship_count += 1
            
            coverage[class_label] = {
                'instances': len(matching_concepts),
                'chunks': chunk_count,
                'relationships': relationship_count,
                'score': self._calculate_coverage_score(len(matching_concepts), chunk_count, relationship_count)
            }
        
        # Sort by score
        sorted_coverage = dict(sorted(coverage.items(), key=lambda x: x[1]['score']))
        
        if self.verbose:
            print("\n📊 Coverage by Meta-Ontology Class:")
            print(f"{'Class':<30} {'Instances':<12} {'Chunks':<10} {'Relations':<12} {'Score':<8}")
            print("-" * 80)
            for class_label, stats in sorted_coverage.items():
                score_indicator = "🔴" if stats['score'] < 30 else "🟡" if stats['score'] < 60 else "🟢"
                print(f"{class_label:<30} {stats['instances']:<12} {stats['chunks']:<10} {stats['relationships']:<12} {score_indicator} {stats['score']:<6.0f}")
        
        return sorted_coverage
    
    def _calculate_coverage_score(self, instances: int, chunks: int, relationships: int) -> float:
        """Calculate coverage score (0-100) based on instances, chunks, and relationships."""
        # Weights: instances (30%), chunks (40%), relationships (30%)
        instance_score = min(instances * 10, 30)  # Cap at 30
        chunk_score = min(chunks * 4, 40)         # Cap at 40
        rel_score = min(relationships * 6, 30)    # Cap at 30
        return instance_score + chunk_score + rel_score
    
    def identify_gaps(self, coverage: Dict[str, any], threshold: float = 50.0) -> List[str]:
        """Identify under-covered topics (score below threshold)."""
        gaps = []
        
        if self.verbose:
            print(f"\n🔍 Identifying Gaps (threshold: {threshold}):")
        
        for class_label, stats in coverage.items():
            if stats['score'] < threshold:
                gaps.append(class_label)
                if self.verbose:
                    print(f"   ⚠️  {class_label}: Score {stats['score']:.0f}/100")
                    if stats['instances'] == 0:
                        print(f"       - No instances found")
                    if stats['chunks'] < 5:
                        print(f"       - Only {stats['chunks']} chunk(s) mention this concept")
                    if stats['relationships'] < 3:
                        print(f"       - Only {stats['relationships']} relationship(s)")
        
        return gaps
    
    def analyze_relationship_gaps(self) -> Dict[str, List[str]]:
        """Identify which meta-ontology relationships are under-utilized."""
        
        if self.verbose:
            print("\n🔗 Relationship Gap Analysis:")
        
        # Get all meta-ontology properties
        meta_props = {}
        for prop in self.meta.subjects(RDF.type, OWL.ObjectProperty):
            label = self.meta.value(prop, RDFS.label)
            if label:
                meta_props[str(label)] = prop
        
        relationship_gaps = {}
        
        for prop_label, prop_uri in meta_props.items():
            # Count usage in knowledge graph
            triples = list(self.kg.triples((None, prop_uri, None)))
            
            # Get domain and range
            domain = self.meta.value(prop_uri, RDFS.domain)
            range_val = self.meta.value(prop_uri, RDFS.range)
            domain_label = self.meta.value(domain, RDFS.label) if domain else "Any"
            range_label = self.meta.value(range_val, RDFS.label) if range_val else "Any"
            
            if len(triples) < 3:  # Under-utilized threshold
                relationship_gaps[prop_label] = {
                    'count': len(triples),
                    'domain': str(domain_label),
                    'range': str(range_label)
                }
                
                if self.verbose:
                    print(f"   ⚠️  '{prop_label}': Only {len(triples)} triple(s)")
                    print(f"       Expected: {domain_label} → {range_label}")
        
        return relationship_gaps
    
    def generate_search_queries(self, gaps: List[str], relationship_gaps: Dict[str, any], max_queries: int = 5) -> List[str]:
        """Use LLM to generate targeted search queries for knowledge gaps."""
        
        if self.verbose:
            print(f"\n🤖 Generating Search Queries (max: {max_queries})...")
        
        # Build context from gaps
        gap_context = "\n".join([f"  - {gap}" for gap in gaps[:5]])
        
        # Build relationship context
        rel_context = "\n".join([
            f"  - {prop}: {info['domain']} → {info['range']} (only {info['count']} examples)"
            for prop, info in list(relationship_gaps.items())[:5]
        ])
        
        prompt = f"""You are a research assistant helping discover sources to fill knowledge gaps.

Current Knowledge Gaps (under-covered topics):
{gap_context}

Under-utilized Relationships:
{rel_context}

Generate {max_queries} targeted search queries to find sources that would:
1. Provide more depth on under-covered topics
2. Explain relationships between these concepts
3. Include practical examples and case studies

Return queries as a JSON array: ["query1", "query2", ...]
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a research assistant. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=500
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            queries = result.get('queries', [])
            
            if self.verbose:
                print("\n📝 Generated Search Queries:")
                for i, query in enumerate(queries, 1):
                    print(f"   {i}. {query}")
            
            return queries
        
        except Exception as e:
            if self.verbose:
                print(f"   ✗ Error generating queries: {e}")
            
            # Fallback: generate simple queries
            fallback_queries = [f"{gap} overview examples" for gap in gaps[:max_queries]]
            return fallback_queries
    
    def suggest_focus_areas(self, coverage: Dict[str, any], top_k: int = 3) -> List[Tuple[str, str]]:
        """Suggest specific focus areas for research."""
        
        if self.verbose:
            print(f"\n💡 Top {top_k} Focus Areas for Research:")
        
        # Sort by lowest score
        sorted_gaps = sorted(coverage.items(), key=lambda x: x[1]['score'])
        
        focus_areas = []
        for i, (class_label, stats) in enumerate(sorted_gaps[:top_k], 1):
            reason = []
            if stats['instances'] == 0:
                reason.append("no instances found")
            elif stats['instances'] < 2:
                reason.append("only 1 instance")
            
            if stats['chunks'] < 3:
                reason.append(f"only {stats['chunks']} mentions")
            
            if stats['relationships'] < 2:
                reason.append(f"only {stats['relationships']} relationships")
            
            reason_text = ", ".join(reason)
            focus_areas.append((class_label, reason_text))
            
            if self.verbose:
                print(f"   {i}. {class_label}")
                print(f"      Why: {reason_text}")
                print(f"      Score: {stats['score']:.0f}/100")
        
        return focus_areas
    
    def generate_discovery_report(self, output_path: str = "data/discovery_report.txt"):
        """Generate a comprehensive discovery report."""
        
        # Run analysis
        coverage = self.analyze_coverage()
        gaps = self.identify_gaps(coverage)
        relationship_gaps = self.analyze_relationship_gaps()
        focus_areas = self.suggest_focus_areas(coverage)
        queries = self.generate_search_queries(gaps, relationship_gaps)
        
        # Generate report
        report = []
        report.append("="*60)
        report.append("SOURCE DISCOVERY REPORT")
        report.append(f"Generated: {Path(self.knowledge_graph_path).name}")
        report.append("="*60)
        report.append("")
        
        report.append("## Coverage Summary")
        report.append("")
        for class_label, stats in coverage.items():
            indicator = "LOW" if stats['score'] < 30 else "MEDIUM" if stats['score'] < 60 else "HIGH"
            report.append(f"  {class_label}: {indicator} ({stats['score']:.0f}/100)")
            report.append(f"    - {stats['instances']} instances, {stats['chunks']} chunks, {stats['relationships']} relationships")
        report.append("")
        
        report.append("## Top Focus Areas")
        report.append("")
        for i, (area, reason) in enumerate(focus_areas, 1):
            report.append(f"  {i}. {area}")
            report.append(f"     Reason: {reason}")
        report.append("")
        
        report.append("## Relationship Gaps")
        report.append("")
        for prop, info in relationship_gaps.items():
            report.append(f"  - {prop}: {info['domain']} → {info['range']}")
            report.append(f"    Current usage: {info['count']} triple(s)")
        report.append("")
        
        report.append("## Recommended Search Queries")
        report.append("")
        for i, query in enumerate(queries, 1):
            report.append(f"  {i}. {query}")
        report.append("")
        
        report.append("## Next Steps")
        report.append("")
        report.append("  1. Use the search queries above to find relevant articles/papers")
        report.append("  2. Add discovered sources to data/sources/")
        report.append("  3. Rebuild knowledge graph: python build_graph.py --meta-ontology data/graphs/meta_ontology.ttl")
        report.append("  4. Re-run discovery to assess improvement")
        report.append("")
        
        # Save report
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(report))
        
        if self.verbose:
            print(f"\n✅ Discovery report saved: {output_path}")
        
        return "\n".join(report)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Discover sources based on knowledge graph gaps')
    parser.add_argument('--meta-ontology', default='data/graphs/meta_ontology.ttl',
                        help='Path to meta-ontology TTL file')
    parser.add_argument('--knowledge-graph', default='data/graphs/knowledge_graph.ttl',
                        help='Path to knowledge graph TTL file')
    parser.add_argument('--output', default='data/discovery_report.txt',
                        help='Path to save discovery report')
    parser.add_argument('--threshold', type=float, default=50.0,
                        help='Coverage score threshold for identifying gaps (default: 50)')
    parser.add_argument('--queries', type=int, default=5,
                        help='Number of search queries to generate (default: 5)')
    
    args = parser.parse_args()
    
    # Create discovery engine
    discovery = SourceDiscovery(
        meta_ontology_path=args.meta_ontology,
        knowledge_graph_path=args.knowledge_graph,
        verbose=True
    )
    
    # Generate report
    report = discovery.generate_discovery_report(output_path=args.output)
    
    print(f"\n{'='*60}")
    print("Discovery workflow complete!")
    print(f"Review the report: {args.output}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
