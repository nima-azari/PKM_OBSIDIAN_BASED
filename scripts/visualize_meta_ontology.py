"""
Visualize meta-ontology as an interactive HTML graph.
Shows classes, properties, and their relationships.
"""

import sys
from pathlib import Path
from rdflib import Graph, RDF, RDFS, OWL, Namespace
import networkx as nx
from pyvis.network import Network

def visualize_meta_ontology(meta_path: str = "data/graphs/meta_ontology.ttl", output_path: str = "data/graphs/meta_ontology_viz.html"):
    """
    Create interactive visualization of meta-ontology.
    
    Args:
        meta_path: Path to meta-ontology TTL file
        output_path: Path to save HTML visualization
    """
    print("\n" + "="*60)
    print("Meta-Ontology Visualizer")
    print("="*60)
    
    # Load meta-ontology
    print(f"\n📖 Loading meta-ontology: {meta_path}")
    g = Graph()
    g.parse(meta_path, format='turtle')
    
    # Get all classes and properties
    classes = list(g.subjects(RDF.type, OWL.Class))
    properties = list(g.subjects(RDF.type, OWL.ObjectProperty))
    
    print(f"✓ Found {len(classes)} classes, {len(properties)} properties")
    
    # Create NetworkX graph
    G = nx.DiGraph()
    
    # Add class nodes
    for cls in classes:
        label = g.value(cls, RDFS.label)
        if not label:
            label = str(cls).split('#')[-1].split('/')[-1]
        
        G.add_node(str(cls), label=str(label), type='class', title=f"Class: {label}")
    
    # Add property edges
    edge_count = 0
    for prop in properties:
        prop_label = g.value(prop, RDFS.label)
        if not prop_label:
            prop_label = str(prop).split('#')[-1].split('/')[-1]
        
        # Get ALL domains and ranges (properties can have multiple)
        domains = list(g.objects(prop, RDFS.domain))
        ranges = list(g.objects(prop, RDFS.range))
        
        # Create edges for all domain-range combinations
        for domain in domains:
            for range_val in ranges:
                if domain and range_val:
                    G.add_edge(
                        str(domain), 
                        str(range_val), 
                        label=str(prop_label),
                        title=f"{prop_label}"
                    )
                    edge_count += 1
    
    print(f"✓ Created graph: {len(G.nodes())} nodes, {len(G.edges())} edges")
    
    # Check for isolated nodes
    isolated = list(nx.isolates(G))
    if isolated:
        print(f"\n⚠️  Found {len(isolated)} isolated nodes (no connections):")
        for node in isolated:
            label = G.nodes[node].get('label', node)
            print(f"   - {label}")
        print(f"\n💡 Run: python scripts/evaluate_meta_ontology.py")
        print(f"   to auto-connect isolated nodes using LLM")
    else:
        print(f"\n✓ No isolated nodes - all concepts connected!")
    
    # Create interactive visualization
    print(f"\n🎨 Creating interactive visualization...")
    net = Network(height="750px", width="100%", directed=True)
    net.from_nx(G)
    
    # Customize appearance with visible labels
    for node in net.nodes:
        # Get the label from the node data
        node_label = G.nodes[node['id']].get('label', node['id'].split('/')[-1])
        node['label'] = node_label  # Make sure label is set
        node['color'] = '#4A90E2'  # Blue for classes
        node['font'] = {'size': 18, 'color': '#333', 'face': 'arial', 'background': 'rgba(255,255,255,0.9)', 'strokeWidth': 3, 'strokeColor': '#fff'}
        node['borderWidth'] = 3
        node['borderWidthSelected'] = 5
        node['size'] = 30
        node['shape'] = 'box'  # Box shape shows labels better
        node['margin'] = 10
    
    for edge in net.edges:
        edge['arrows'] = 'to'
        edge['color'] = {'color': '#666', 'highlight': '#000'}
        edge['width'] = 3
        edge['font'] = {'size': 14, 'align': 'middle', 'color': '#000', 'background': 'rgba(255,255,255,0.8)', 'strokeWidth': 2, 'strokeColor': '#fff'}
    
    # Physics settings for better layout
    net.set_options("""
    {
        "physics": {
            "barnesHut": {
                "gravitationalConstant": -8000,
                "centralGravity": 0.3,
                "springLength": 200,
                "springConstant": 0.04,
                "damping": 0.09
            },
            "minVelocity": 0.75
        },
        "interaction": {
            "hover": true,
            "navigationButtons": true,
            "keyboard": true
        }
    }
    """)
    
    # Save visualization
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    net.save_graph(str(output_path))
    
    print(f"✓ Saved visualization: {output_path}")
    print(f"\n📊 Statistics:")
    print(f"   Classes: {len(classes)}")
    print(f"   Properties: {len(properties)}")
    print(f"   Relationships: {edge_count}")
    print(f"   Isolated nodes: {len(isolated)}")
    
    if G.number_of_nodes() > 0:
        avg_degree = sum(dict(G.degree()).values()) / G.number_of_nodes()
        print(f"   Average connections per class: {avg_degree:.1f}")
    
    print(f"\n{'='*60}")
    print(f"✅ Visualization complete!")
    print(f"{'='*60}")
    print(f"\n📁 Open in browser: {output_path.absolute()}")
    print(f"\nNext steps:")
    if isolated:
        print(f"1. Review isolated nodes in visualization")
        print(f"2. Auto-connect: python scripts/evaluate_meta_ontology.py")
        print(f"3. Or manually edit: data/graphs/meta_ontology.ttl")
    else:
        print(f"1. Review relationships in visualization")
        print(f"2. Manually refine if needed: data/graphs/meta_ontology.ttl")
    print(f"3. Build knowledge graph: python scripts/build_graph_with_meta.py")
    
    # Collect researcher feedback
    return collect_feedback(isolated, G, meta_path)

def collect_feedback(isolated, G, meta_path):
    """
    Collect researcher feedback about meta-ontology structure.
    Saves feedback to data/meta_feedback.txt for enhancement script.
    """
    print(f"\n{'='*60}")
    print(f"📝 RESEARCHER FEEDBACK")
    print(f"{'='*60}")
    print(f"\nPlease review the visualization and provide feedback:")
    print(f"(This will help the auto-enhancement script)")
    print()
    
    feedback = {
        'isolated_nodes': [G.nodes[node].get('label', node) for node in isolated],
        'suggestions': [],
        'missing_concepts': [],
        'missing_relationships': []
    }
    
    # Ask about isolated nodes
    if isolated:
        print(f"⚠️  Found {len(isolated)} isolated node(s):")
        for node in isolated:
            label = G.nodes[node].get('label', node)
            print(f"   - {label}")
        print()
        
        response = input(f"Should these be auto-connected? (y/n/skip): ").strip().lower()
        feedback['auto_connect_isolated'] = response in ['y', 'yes']
        
        if response not in ['y', 'yes', 'n', 'no']:
            print("   Skipping auto-enhancement")
            feedback['auto_connect_isolated'] = False
    else:
        feedback['auto_connect_isolated'] = False
    
    # Ask about missing concepts
    print(f"\n💡 Are there any MISSING CONCEPTS in your domain?")
    print(f"   (e.g., 'Data Governance', 'Vendor Lock-in', 'API Standards')")
    missing = input(f"Enter concepts separated by commas (or press Enter to skip): ").strip()
    if missing:
        feedback['missing_concepts'] = [c.strip() for c in missing.split(',') if c.strip()]
        print(f"   ✓ Recorded {len(feedback['missing_concepts'])} missing concepts")
    
    # Ask about missing relationships
    print(f"\n🔗 Are there any MISSING RELATIONSHIPS?")
    print(f"   (e.g., 'Data Quality -> improves -> Data Access')")
    rel = input(f"Enter relationships (format: ClassA -> relation -> ClassB) or press Enter to skip: ").strip()
    if rel:
        feedback['missing_relationships'] = [r.strip() for r in rel.split(';') if r.strip()]
        print(f"   ✓ Recorded {len(feedback['missing_relationships'])} missing relationships")
    
    # General feedback
    print(f"\n✍️  Any other observations or suggestions?")
    general = input(f"Enter notes (or press Enter to skip): ").strip()
    if general:
        feedback['suggestions'].append(general)
    
    # Save feedback
    feedback_path = Path("data/meta_feedback.txt")
    feedback_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(feedback_path, 'w', encoding='utf-8') as f:
        f.write("# Meta-Ontology Feedback\n")
        f.write(f"# Generated: {Path(meta_path).name}\n\n")
        
        f.write(f"AUTO_CONNECT_ISOLATED: {feedback['auto_connect_isolated']}\n\n")
        
        if feedback['isolated_nodes']:
            f.write(f"ISOLATED_NODES:\n")
            for node in feedback['isolated_nodes']:
                f.write(f"  - {node}\n")
            f.write("\n")
        
        if feedback['missing_concepts']:
            f.write(f"MISSING_CONCEPTS:\n")
            for concept in feedback['missing_concepts']:
                f.write(f"  - {concept}\n")
            f.write("\n")
        
        if feedback['missing_relationships']:
            f.write(f"MISSING_RELATIONSHIPS:\n")
            for rel in feedback['missing_relationships']:
                f.write(f"  - {rel}\n")
            f.write("\n")
        
        if feedback['suggestions']:
            f.write(f"SUGGESTIONS:\n")
            for sug in feedback['suggestions']:
                f.write(f"  - {sug}\n")
    
    print(f"\n✓ Feedback saved to: {feedback_path}")
    print(f"\n{'='*60}")
    print(f"Next step:")
    if feedback['auto_connect_isolated']:
        print(f"✅ Run: python scripts/evaluate_meta_ontology.py")
        print(f"   (Will auto-connect isolated nodes using LLM)")
    else:
        print(f"📝 Manually edit: {meta_path}")
        print(f"   (Add missing concepts/relationships)")
    print(f"{'='*60}\n")
    
    return feedback

if __name__ == '__main__':
    visualize_meta_ontology()
