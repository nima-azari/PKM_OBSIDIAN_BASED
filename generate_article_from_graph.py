"""
Generate a comprehensive article from a knowledge graph TTL file.

This script reads a TTL (Turtle) knowledge graph, extracts concepts and relationships,
and uses AI to generate a structured markdown article.

Usage:
    python generate_article_from_graph.py <ttl_file> [output_file]
    
Example:
    python generate_article_from_graph.py data/graphs/my_graph.ttl
    python generate_article_from_graph.py data/graphs/my_graph.ttl my_article.md
"""

import sys
from pathlib import Path
from datetime import datetime
from rdflib import Graph, Namespace
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

class GraphArticleGenerator:
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.client = OpenAI()
        
    def load_graph(self, ttl_path):
        """Load RDF graph from TTL file."""
        if self.verbose:
            print(f"Loading graph from: {ttl_path}")
        
        g = Graph()
        g.parse(ttl_path, format='turtle')
        
        if self.verbose:
            print(f"Loaded {len(g)} triples")
        
        return g
    
    def extract_graph_info(self, g):
        """Extract concepts, entities, and relationships from the graph."""
        info = {
            'documents': [],
            'entities': [],
            'topics': [],
            'relationships': []
        }
        
        # Define namespaces
        ONTO = Namespace("http://pkm.local/ontology/")
        
        # Extract documents
        for s, p, o in g.triples((None, None, ONTO.Document)):
            doc_info = {'uri': str(s), 'properties': {}}
            for pred, obj in g.predicate_objects(s):
                doc_info['properties'][str(pred).split('/')[-1]] = str(obj)
            info['documents'].append(doc_info)
        
        # Extract entities (Person, Organization, Location)
        for entity_type in ['Person', 'Organization', 'Location']:
            for s, p, o in g.triples((None, None, getattr(ONTO, entity_type))):
                entity_info = {'type': entity_type, 'uri': str(s), 'properties': {}}
                for pred, obj in g.predicate_objects(s):
                    entity_info['properties'][str(pred).split('/')[-1]] = str(obj)
                info['entities'].append(entity_info)
        
        # Extract topics
        for s, p, o in g.triples((None, None, ONTO.Topic)):
            topic_info = {'uri': str(s), 'properties': {}}
            for pred, obj in g.predicate_objects(s):
                topic_info['properties'][str(pred).split('/')[-1]] = str(obj)
            info['topics'].append(topic_info)
        
        # Extract relationships
        relationship_predicates = ['mentions', 'relatedTo', 'hasEntity', 'hasTopic']
        for pred_name in relationship_predicates:
            for s, p, o in g.triples((None, getattr(ONTO, pred_name), None)):
                info['relationships'].append({
                    'subject': str(s).split('/')[-1],
                    'predicate': pred_name,
                    'object': str(o).split('/')[-1]
                })
        
        if self.verbose:
            print(f"Extracted: {len(info['documents'])} documents, {len(info['entities'])} entities, "
                  f"{len(info['topics'])} topics, {len(info['relationships'])} relationships")
        
        return info
    
    def generate_article(self, graph_info):
        """Generate a comprehensive article using OpenAI based on graph data."""
        if self.verbose:
            print("Generating article with AI...")
        
        # Build context from graph info
        context_parts = []
        
        if graph_info['documents']:
            context_parts.append("**Documents in the knowledge base:**")
            for doc in graph_info['documents'][:10]:  # Limit to avoid token overflow
                label = doc['properties'].get('label', 'Unknown')
                context_parts.append(f"- {label}")
        
        if graph_info['entities']:
            context_parts.append("\n**Key entities:**")
            entities_by_type = {}
            for entity in graph_info['entities']:
                etype = entity['type']
                if etype not in entities_by_type:
                    entities_by_type[etype] = []
                label = entity['properties'].get('label', 'Unknown')
                entities_by_type[etype].append(label)
            
            for etype, labels in entities_by_type.items():
                context_parts.append(f"- {etype}s: {', '.join(labels[:20])}")
        
        if graph_info['topics']:
            context_parts.append("\n**Topics:**")
            for topic in graph_info['topics'][:20]:
                label = topic['properties'].get('label', 'Unknown')
                context_parts.append(f"- {label}")
        
        if graph_info['relationships']:
            context_parts.append("\n**Key relationships:**")
            for rel in graph_info['relationships'][:30]:
                context_parts.append(f"- {rel['subject']} → {rel['predicate']} → {rel['object']}")
        
        context = "\n".join(context_parts)
        
        # Create prompt
        system_prompt = """You are a technical writer creating comprehensive articles from knowledge graph data.

Your task is to:
1. Analyze the concepts, entities, topics, and relationships in the knowledge graph
2. Create a well-structured, coherent article that explains the key themes and connections
3. Use proper markdown formatting with headings, lists, and emphasis
4. Write in a clear, professional style
5. Include an introduction, main sections for each major theme, and a conclusion
6. Highlight important connections and insights from the relationships

The article should be informative, well-organized, and readable."""

        user_prompt = f"""Based on the following knowledge graph data, write a comprehensive article:

{context}

Create a detailed article that:
- Explains the main themes and concepts
- Describes key entities and their roles
- Explores important relationships and connections
- Provides insights and synthesis
- Uses proper markdown formatting with ## headings and **bold** for emphasis

Generate the article now:"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        
        article = response.choices[0].message.content
        
        if self.verbose:
            print(f"Generated article ({len(article)} characters)")
        
        return article
    
    def save_article(self, article, output_path, ttl_path):
        """Save article with frontmatter to markdown file."""
        # Add frontmatter
        frontmatter = f"""---
title: Knowledge Graph Article
source_graph: {ttl_path}
date_generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
generated_by: AI from Knowledge Graph
tags: [knowledge-graph, synthesis, ai-generated]
---

"""
        
        full_content = frontmatter + article
        
        # Save to file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        if self.verbose:
            print(f"Article saved to: {output_path}")
        
        return output_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_article_from_graph.py <ttl_file> [output_file]")
        print("\nExample:")
        print("  python generate_article_from_graph.py data/graphs/my_graph.ttl")
        print("  python generate_article_from_graph.py data/graphs/my_graph.ttl my_article.md")
        sys.exit(1)
    
    ttl_path = sys.argv[1]
    
    if not Path(ttl_path).exists():
        print(f"❌ Error: File not found: {ttl_path}")
        sys.exit(1)
    
    # Determine output path
    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        # Auto-generate output filename
        ttl_stem = Path(ttl_path).stem
        output_path = f"data/sources/{ttl_stem}_article.md"
    
    # Generate article
    generator = GraphArticleGenerator(verbose=True)
    
    print("\n" + "="*60)
    print("Knowledge Graph to Article Generator")
    print("="*60 + "\n")
    
    # Load graph
    graph = generator.load_graph(ttl_path)
    
    # Extract information
    graph_info = generator.extract_graph_info(graph)
    
    # Generate article
    article = generator.generate_article(graph_info)
    
    # Save article
    output_file = generator.save_article(article, output_path, ttl_path)
    
    print("\n" + "="*60)
    print(f"Complete! Article saved to: {output_file}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
