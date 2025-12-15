"""
Evaluate and connect isolated nodes in meta-ontology using LLM.

This script:
1. Loads meta-ontology
2. Identifies disconnected nodes (degree = 0)
3. Uses LLM to evaluate potential connections
4. Adds edges where relevance > 0.6
5. Saves updated meta-ontology

Usage:
    python scripts/evaluate_meta_ontology.py
    python scripts/evaluate_meta_ontology.py data/graphs/meta_ontology.ttl
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from openai import OpenAI
from rdflib import Graph, Namespace, RDF, RDFS, OWL, Literal, URIRef
import json

# Load environment variables
load_dotenv()

# Namespaces
META = Namespace("http://pkm.local/meta-ontology/")
ONTO_NS = Namespace("http://pkm.local/meta-ontology/")

def load_meta_ontology(file_path):
    """Load meta-ontology from TTL file"""
    g = Graph()
    g.parse(file_path, format='turtle')
    
    # Bind namespaces for clean serialization
    g.bind('', ONTO_NS)
    g.bind('owl', OWL)
    g.bind('rdfs', RDFS)
    
    return g

def get_classes_and_properties(g):
    """Extract all classes and existing properties"""
    classes = {}
    properties = []
    
    # Get classes
    for s, p, o in g.triples((None, RDF.type, OWL.Class)):
        label = str(g.value(s, RDFS.label) or s.split('/')[-1])
        comment = str(g.value(s, RDFS.comment) or "")
        classes[str(s)] = {
            'label': label,
            'comment': comment,
            'connections': 0
        }
    
    # Count connections for each class
    for s, p, o in g.triples((None, RDF.type, OWL.ObjectProperty)):
        domain = g.value(s, RDFS.domain)
        range_val = g.value(s, RDFS.range)
        
        if domain and str(domain) in classes:
            classes[str(domain)]['connections'] += 1
        if range_val and str(range_val) in classes:
            classes[str(range_val)]['connections'] += 1
        
        prop_label = str(g.value(s, RDFS.label) or s.split('/')[-1])
        properties.append({
            'uri': str(s),
            'label': prop_label,
            'domain': str(domain) if domain else None,
            'range': str(range_val) if range_val else None
        })
    
    return classes, properties

def find_disconnected_nodes(classes):
    """Find nodes with 0 connections"""
    return {uri: data for uri, data in classes.items() if data['connections'] == 0}

def evaluate_connection_with_llm(source_class, target_class, existing_properties, client):
    """Use LLM to evaluate if two classes should be connected"""
    
    prompt = f"""You are an ontology expert. Evaluate if these two domain concepts should be connected with a relationship.

Source Concept:
- Name: {source_class['label']}
- Description: {source_class['comment']}

Target Concept:
- Name: {target_class['label']}
- Description: {target_class['comment']}

Existing relationship types in the ontology:
{', '.join([p['label'] for p in existing_properties[:10]])}

Task:
1. Determine if there is a meaningful semantic relationship between these concepts
2. If yes, suggest an appropriate relationship type (can be from existing or new)
3. Provide a relevance score (0.0 to 1.0)

Return ONLY a JSON object with this format:
{{
    "should_connect": true/false,
    "relevance_score": 0.0-1.0,
    "relationship_label": "relationship name",
    "relationship_direction": "source_to_target" or "target_to_source",
    "reasoning": "brief explanation"
}}

Be strict: only suggest connections with clear semantic relationships."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an ontology expert that evaluates semantic relationships between concepts."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
        
    except Exception as e:
        print(f"  ⚠️ LLM evaluation failed: {e}")
        return {
            "should_connect": False,
            "relevance_score": 0.0,
            "reasoning": f"Error: {str(e)}"
        }

def add_property_to_graph(g, source_uri, target_uri, relationship_label, direction):
    """Add new property to the graph"""
    
    # Create property URI
    prop_name = relationship_label.replace(' ', '_').replace('-', '_')
    prop_uri = META[prop_name]
    
    # Check if property already exists
    existing = list(g.triples((prop_uri, RDF.type, OWL.ObjectProperty)))
    if not existing:
        # Add property definition
        g.add((prop_uri, RDF.type, OWL.ObjectProperty))
        g.add((prop_uri, RDFS.label, Literal(relationship_label)))
    
    # Convert string URIs to URIRef objects if needed
    source_uri_ref = URIRef(source_uri) if isinstance(source_uri, str) else source_uri
    target_uri_ref = URIRef(target_uri) if isinstance(target_uri, str) else target_uri
    
    # Add domain and range
    if direction == "source_to_target":
        g.add((prop_uri, RDFS.domain, source_uri_ref))
        g.add((prop_uri, RDFS.range, target_uri_ref))
    else:  # target_to_source
        g.add((prop_uri, RDFS.domain, target_uri_ref))
        g.add((prop_uri, RDFS.range, source_uri_ref))
    
    return prop_uri

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Evaluate and connect isolated nodes in meta-ontology')
    parser.add_argument('input', nargs='?', default='data/graphs/meta_ontology.ttl',
                        help='Input meta-ontology TTL file (default: data/graphs/meta_ontology.ttl)')
    parser.add_argument('--threshold', type=float, default=0.6,
                        help='Minimum relevance score to add connection (default: 0.6)')
    parser.add_argument('--output', default=None,
                        help='Output file path (default: overwrites input)')
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path
    threshold = args.threshold
    
    print("\n" + "="*70)
    print("META-ONTOLOGY CONNECTION EVALUATOR")
    print("="*70)
    print(f"Input: {input_path}")
    print(f"Threshold: {threshold}")
    print(f"Output: {output_path}")
    
    # Load meta-ontology
    print("\n📖 Loading meta-ontology...")
    g = load_meta_ontology(input_path)
    original_triple_count = len(g)
    print(f"   Loaded {original_triple_count} triples")
    
    # Extract classes and properties
    print("\n🔍 Analyzing structure...")
    classes, properties = get_classes_and_properties(g)
    print(f"   Found {len(classes)} classes")
    print(f"   Found {len(properties)} properties")
    
    # Find disconnected nodes
    disconnected = find_disconnected_nodes(classes)
    print(f"\n⚠️  Found {len(disconnected)} disconnected nodes:")
    for uri, data in disconnected.items():
        print(f"   - {data['label']}")
    
    if not disconnected:
        print("\n✅ No disconnected nodes! Meta-ontology is fully connected.")
        return
    
    # Initialize OpenAI client
    print("\n🤖 Initializing LLM evaluator...")
    client = OpenAI()
    
    # Evaluate connections for each disconnected node
    print(f"\n🔗 Evaluating potential connections (threshold: {threshold})...")
    connections_added = 0
    
    for disconnected_uri, disconnected_data in disconnected.items():
        print(f"\n  Evaluating: {disconnected_data['label']}")
        
        # Try connecting to each connected node
        connected_classes = {uri: data for uri, data in classes.items() 
                           if data['connections'] > 0 and uri != disconnected_uri}
        
        for target_uri, target_data in connected_classes.items():
            print(f"    vs {target_data['label']}...", end=" ")
            
            # Evaluate with LLM
            result = evaluate_connection_with_llm(
                disconnected_data,
                target_data,
                properties,
                client
            )
            
            relevance = result.get('relevance_score', 0.0)
            should_connect = result.get('should_connect', False)
            
            print(f"score: {relevance:.2f}", end="")
            
            if should_connect and relevance >= threshold:
                # Add connection
                relationship = result.get('relationship_label', 'relatesTo')
                direction = result.get('relationship_direction', 'source_to_target')
                reasoning = result.get('reasoning', '')
                
                prop_uri = add_property_to_graph(
                    g, 
                    disconnected_uri if direction == 'source_to_target' else target_uri,
                    target_uri if direction == 'source_to_target' else disconnected_uri,
                    relationship,
                    direction
                )
                
                connections_added += 1
                print(f" ✅ ADDED: {relationship}")
                print(f"      → {reasoning}")
            else:
                print(f" ❌ skip")
    
    # Save updated ontology
    if connections_added > 0:
        print(f"\n💾 Saving updated meta-ontology...")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Re-bind namespaces before serialization to ensure clean output
        g.bind('', ONTO_NS)
        g.bind('owl', OWL)
        g.bind('rdfs', RDFS)
        
        g.serialize(destination=str(output_path), format='turtle')
        
        new_triple_count = len(g)
        print(f"   Triples: {original_triple_count} → {new_triple_count} (+{new_triple_count - original_triple_count})")
        print(f"   New connections: {connections_added}")
        print(f"\n✅ Updated meta-ontology saved to: {output_path}")
        print("\n⚠️  NEXT STEPS:")
        print("   1. Review the new connections (open TTL file)")
        print("   2. Visualize updated ontology (Jupyter notebook)")
        print("   3. Rebuild knowledge graph with updated meta-ontology")
    else:
        print(f"\n⚠️  No connections met the threshold ({threshold})")
        print("   Consider lowering threshold or manually adding relationships")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()
