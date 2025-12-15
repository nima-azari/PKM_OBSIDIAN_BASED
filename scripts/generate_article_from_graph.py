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
from rdflib import Graph, Namespace, RDF, RDFS
from rdflib.namespace import SKOS
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# Load research priorities if available
try:
    from research_priorities import RESEARCH_PRIORITIES, RESEARCH_STANCE, FOCUS_AREAS, DEEMPHASIZE
    PRIORITIES_AVAILABLE = True
except ImportError:
    RESEARCH_PRIORITIES = []
    RESEARCH_STANCE = {}
    FOCUS_AREAS = []
    DEEMPHASIZE = []
    PRIORITIES_AVAILABLE = False

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
        """Extract concepts, topics, and relationships from the graph."""
        info = {
            'documents': [],
            'concepts': [],
            'topics': [],
            'relationships': [],
            'chunks': []
        }
        
        # Define namespaces
        ONTO = Namespace("http://pkm.local/ontology/")
        
        # Extract documents
        for s, p, o in g.triples((None, RDF.type, ONTO.Document)):
            doc_info = {'uri': str(s), 'properties': {}}
            for pred, obj in g.predicate_objects(s):
                pred_name = str(pred).split('/')[-1].split('#')[-1]
                doc_info['properties'][pred_name] = str(obj)
            info['documents'].append(doc_info)
        
        # Extract DomainConcepts (the actual content!)
        for s, p, o in g.triples((None, RDF.type, ONTO.DomainConcept)):
            concept_info = {'uri': str(s), 'label': None, 'mentions': 0}
            
            # Get prefLabel
            for _, _, label in g.triples((s, SKOS.prefLabel, None)):
                concept_info['label'] = str(label)
                break
            
            # Count how many chunks mention this concept
            concept_info['mentions'] = len(list(g.subjects(ONTO.mentionsConcept, s)))
            
            if concept_info['label']:
                info['concepts'].append(concept_info)
        
        # Extract TopicNodes (not Topic!)
        for s, p, o in g.triples((None, RDF.type, ONTO.TopicNode)):
            topic_info = {'uri': str(s), 'label': None, 'concepts': [], 'description': None}
            
            # Get label (try SKOS.prefLabel first, then RDFS.label)
            for _, _, label in g.triples((s, SKOS.prefLabel, None)):
                topic_info['label'] = str(label)
                break
            if not topic_info['label']:
                for _, _, label in g.triples((s, RDFS.label, None)):
                    topic_info['label'] = str(label)
                    break
            
            # Get description/comment
            for _, _, comment in g.triples((s, RDFS.comment, None)):
                topic_info['description'] = str(comment)
                break
            
            # Get concepts covered by this topic
            for _, _, concept_uri in g.triples((s, ONTO.coversConcept, None)):
                for _, _, concept_label in g.triples((concept_uri, SKOS.prefLabel, None)):
                    topic_info['concepts'].append(str(concept_label))
            
            # Add topic even if no label (use URI as fallback)
            if not topic_info['label']:
                topic_info['label'] = str(s).split('/')[-1].replace('_', ' ').title()
            
            info['topics'].append(topic_info)
        
        # Extract key relationships
        relationship_predicates = ['mentionsConcept', 'coversConcept', 'coversChunk', 'hasChunk']
        for pred_name in relationship_predicates:
            try:
                for s, p, o in g.triples((None, getattr(ONTO, pred_name), None)):
                    info['relationships'].append({
                        'subject': str(s).split('/')[-1],
                        'predicate': pred_name,
                        'object': str(o).split('/')[-1]
                    })
            except:
                pass
        
        if self.verbose:
            print(f"Extracted: {len(info['documents'])} documents, {len(info['concepts'])} concepts, "
                  f"{len(info['topics'])} topics, {len(info['relationships'])} relationships")
        
        return info
    
    def generate_article(self, graph_info):
        """Generate a comprehensive article using OpenAI based on graph data."""
        if self.verbose:
            print("Generating article with AI...")
            if PRIORITIES_AVAILABLE:
                print(f"  Using research priorities: {', '.join(RESEARCH_PRIORITIES[:3])}...")
        
        # Build context from graph info - prioritize by user's research focus
        context_parts = []
        
        # Add research priorities first if available
        if RESEARCH_PRIORITIES:
            context_parts.append("**USER'S RESEARCH PRIORITIES (Focus on these!):**")
            for i, priority in enumerate(RESEARCH_PRIORITIES, 1):
                context_parts.append(f"{i}. {priority}")
            
            # Add stance information
            if RESEARCH_STANCE:
                context_parts.append("\n**Research Stance:**")
                for topic, stance in RESEARCH_STANCE.items():
                    context_parts.append(f"- {topic.replace('_', ' ').title()}: {stance}")
        
        # Filter and sort concepts by priority match
        if graph_info['concepts']:
            priority_concepts = []
            other_concepts = []
            
            for concept in graph_info['concepts']:
                label = concept.get('label', '').lower()
                mentions = concept.get('mentions', 0)
                
                # Check if concept matches priorities
                is_priority = any(p.lower() in label or label in p.lower() 
                                for p in RESEARCH_PRIORITIES)
                
                # Check if should be de-emphasized
                is_deemphasized = any(d.lower() in label 
                                     for d in DEEMPHASIZE)
                
                if is_priority and not is_deemphasized:
                    priority_concepts.append((concept, mentions * 3))  # 3x weight
                elif not is_deemphasized:
                    other_concepts.append((concept, mentions))
            
            # Sort by weighted mentions
            priority_concepts.sort(key=lambda x: x[1], reverse=True)
            other_concepts.sort(key=lambda x: x[1], reverse=True)
            
            # Priority concepts first
            if priority_concepts:
                context_parts.append("\n**Priority Concepts (matching research focus):**")
                for i, (concept, _) in enumerate(priority_concepts[:15], 1):
                    label = concept.get('label', 'Unknown')
                    mentions = concept.get('mentions', 0)
                    context_parts.append(f"{i}. {label} (mentioned {mentions}x) ⭐")
            
            # Other relevant concepts
            if other_concepts:
                context_parts.append("\n**Supporting Concepts:**")
                for i, (concept, _) in enumerate(other_concepts[:15], 1):
                    label = concept.get('label', 'Unknown')
                    mentions = concept.get('mentions', 0)
                    context_parts.append(f"{i}. {label} (mentioned {mentions}x)")
        
        # Topics (for structure)
        if graph_info['topics']:
            context_parts.append("\n**Topics for Structure:**")
            for i, topic in enumerate(graph_info['topics'][:10], 1):
                label = topic.get('label', 'Unknown')
                concepts = topic.get('concepts', [])
                # Check if topic is relevant to priorities
                is_relevant = any(p.lower() in ' '.join(concepts).lower() 
                                for p in RESEARCH_PRIORITIES)
                marker = " ⭐" if is_relevant else ""
                context_parts.append(f"{i}. {label}{marker}")
        
        # Documents (for reference)
        if graph_info['documents']:
            context_parts.append("\n**Source Documents:**")
            for doc in graph_info['documents'][:8]:
                label = doc['properties'].get('label', 'Unknown')
                context_parts.append(f"- {label}")
        
        context = "\n".join(context_parts)
        
        # Create prompt - incorporate research priorities and stance
        if RESEARCH_PRIORITIES:
            stance_guidance = ""
            if RESEARCH_STANCE.get('cloud_platforms') == 'critical':
                stance_guidance += "\n- Critically examine cloud platforms (vendor lock-in, data silos, interoperability issues)"
            if RESEARCH_STANCE.get('linked_data') == 'positive':
                stance_guidance += "\n- Emphasize benefits of Linked Data and semantic web technologies"
            if RESEARCH_STANCE.get('data_silos') == 'critical':
                stance_guidance += "\n- Highlight problems caused by data silos and proprietary systems"
            if RESEARCH_STANCE.get('eu_regulations') == 'positive':
                stance_guidance += "\n- Present EU Data Act as a positive regulatory framework"
            
            system_prompt = f"""You are a technical writer synthesizing knowledge aligned with specific research priorities.

Your task:
1. PRIORITIZE concepts marked with ⭐ - these are the user's main research focus
2. Follow the research stance provided - maintain the user's perspective
3. Create sections around priority concepts, not generic topics
4. Use supporting concepts to provide context and details
5. Write in a clear, analytical style suitable for research synthesis
6. Use proper markdown: # title, ## sections, ### subsections

Research Perspective:{stance_guidance}

CRITICAL: The article should reflect the user's research priorities and stance, not be neutral."""
        else:
            system_prompt = """You are a technical writer synthesizing knowledge from domain concepts and topics.

Your task:
1. Focus on the most-mentioned concepts (they're more important)
2. Create a coherent narrative connecting related concepts
3. Use topics to organize content into sections
4. Write in a clear, professional style
5. Use proper markdown: # title, ## sections, ### subsections"""

        user_prompt = f"""Synthesize this knowledge graph data into a comprehensive research article:

{context}

Create an article that:
- Focuses heavily on PRIORITY concepts (marked with ⭐)
- Maintains the research stance specified above
- Uses priority concepts as main sections (## headings)
- Supports arguments with specific details from the knowledge base
- Provides a coherent narrative aligned with research priorities
- Is 1000-1500 words

Title should reflect the main priority concepts.

Write the article now:"""

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
            print(f"✓ Article saved to: {output_path}")
        
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
    print("✅ Article generation complete!")
    print("="*60)
    print(f"\n📁 OUTPUT: {output_file}")
    print(f"\nNext steps:")
    print(f"1. Review article: {output_file}")
    print(f"2. Rebuild graph: python build_graph.py")
    print(f"3. Chat with sources: python server.py")
    print("\n")


if __name__ == "__main__":
    main()
