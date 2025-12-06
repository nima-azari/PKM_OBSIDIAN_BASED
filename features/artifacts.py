"""
Artifact Generators - NotebookLM-style outputs.
FAQ, Study Guides, Timelines, Briefing Docs.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.rag_engine import VaultRAG
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class ArtifactGenerator:
    """Generate structured artifacts from vault content."""
    
    def __init__(self, rag_engine: VaultRAG, model: str = "gpt-4o-mini"):
        self.rag = rag_engine
        self.model = model
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY')) if os.getenv('OPENAI_API_KEY') else None
    
    def generate_faq(self, topic: str, num_questions: int = 10) -> str:
        """Generate FAQ list from vault content about a topic."""
        
        if not self.client:
            return "Error: OpenAI API key not configured"
        
        print(f"Generating FAQ for: {topic}")
        print(f"Searching vault for relevant content...")
        
        # Get relevant documents
        results = self.rag.keyword_search(topic, top_k=10)
        
        if not results:
            return f"No content found about '{topic}' in the vault."
        
        # Build context
        context_parts = []
        for i, (score, doc) in enumerate(results, 1):
            context_parts.append(f"[Source {i}: {doc.title}]")
            context_parts.append(doc.content[:3000])  # Limit per doc
            context_parts.append("-" * 40)
        
        context = "\n".join(context_parts)
        
        print(f"Using {len(results)} sources. Generating FAQ...")
        
        prompt = f"""Based on the provided vault content about {topic}, generate a comprehensive FAQ with {num_questions} questions and detailed answers.

Context from vault:
{context}

Generate an FAQ in this format:

# Frequently Asked Questions: {topic}

## Q1: [Question]
**A:** [Detailed answer with specific information from the sources]

## Q2: [Question]
**A:** [Detailed answer]

...and so on.

Make the questions practical and the answers informative. Include specific details from the sources."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a technical writer creating FAQs from research content."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            return f"Error generating FAQ: {str(e)}"
    
    def generate_study_guide(self, topic: str) -> str:
        """Create a study guide with summaries, key concepts, and quiz questions."""
        
        if not self.client:
            return "Error: OpenAI API key not configured"
        
        print(f"Generating study guide for: {topic}")
        
        # Get relevant documents
        results = self.rag.keyword_search(topic, top_k=10)
        
        if not results:
            return f"No content found about '{topic}' in the vault."
        
        # Build context
        context_parts = []
        for score, doc in results:
            context_parts.append(f"# {doc.title}\n{doc.content[:3000]}\n")
        
        context = "\n".join(context_parts)
        
        print(f"Using {len(results)} sources. Creating study guide...")
        
        prompt = f"""Create a comprehensive study guide for {topic} based on the vault content below.

Content:
{context}

Structure the study guide as follows:

# Study Guide: {topic}

## Overview
[Brief overview of the topic]

## Key Concepts

### Concept 1: [Name]
- **Definition:** ...
- **Key Points:** ...
- **Why It Matters:** ...

[Continue for main concepts]

## Important Relationships
[How concepts connect to each other]

## Summary Points
- [Bullet point summary of main takeaways]

## Self-Test Questions

1. [Question about concept]
2. [Question about relationship]
3. [Application question]
[5-10 questions total]

## Answer Key
1. [Brief answer]
2. [Brief answer]
...

Make it comprehensive but clear and well-organized."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an educational content creator making study materials."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            return f"Error generating study guide: {str(e)}"
    
    def generate_timeline(self, topic: str) -> str:
        """Extract chronological events and create a timeline."""
        
        if not self.client:
            return "Error: OpenAI API key not configured"
        
        print(f"Generating timeline for: {topic}")
        
        # Get all documents (timeline might need broader context)
        all_content = []
        for doc in self.rag.documents:
            all_content.append(f"# {doc.title}\n{doc.content[:2000]}")
        
        context = "\n\n".join(all_content)
        
        print(f"Analyzing {len(self.rag.documents)} documents for chronological events...")
        
        prompt = f"""Extract all chronological events, dates, and temporal information from the content below related to {topic}.

Content:
{context}

Create a timeline in this format:

# Timeline: {topic}

## [Time Period / Date]
**Event:** [What happened]
**Significance:** [Why it matters]
**Source:** [Which document mentioned it]

[Continue chronologically]

If exact dates aren't available, organize by general time periods (e.g., "Early 2000s", "Recent developments").
Focus on historically significant events, technology releases, or conceptual developments."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a researcher extracting chronological information."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            return f"Error generating timeline: {str(e)}"
    
    def generate_briefing(self, topic: str) -> str:
        """Create an executive briefing document."""
        
        if not self.client:
            return "Error: OpenAI API key not configured"
        
        print(f"Generating briefing doc for: {topic}")
        
        # Get relevant documents
        results = self.rag.keyword_search(topic, top_k=8)
        
        if not results:
            return f"No content found about '{topic}' in the vault."
        
        # Build context
        context_parts = []
        for score, doc in results:
            context_parts.append(f"# {doc.title}\n{doc.content[:3000]}\n")
        
        context = "\n".join(context_parts)
        
        print(f"Using {len(results)} sources. Creating briefing...")
        
        prompt = f"""Create an executive briefing document about {topic} based on the vault content.

Content:
{context}

Structure:

# Executive Briefing: {topic}

## Executive Summary
[2-3 paragraph high-level overview for executives]

## Key Findings
1. [Major finding with supporting detail]
2. [Major finding with supporting detail]
3. [Major finding with supporting detail]

## Background & Context
[Necessary context to understand the topic]

## Analysis
[Deeper analysis of the key aspects]

## Implications
[What this means for decision-making]

## Recommendations
[If applicable, what actions to consider]

## References
[Key sources from the vault]

Keep it concise, professional, and action-oriented. Aim for clarity over technical detail."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a strategic analyst creating executive briefings."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            return f"Error generating briefing: {str(e)}"


def main():
    """Demo artifact generation."""
    print("=" * 80)
    print("Artifact Generator - NotebookLM Style")
    print("=" * 80)
    print()
    
    # Initialize RAG engine
    rag = VaultRAG(project_path="10-Projects/Cloud-vs-KG-Data-Centric")
    generator = ArtifactGenerator(rag)
    
    # Menu
    print("\nAvailable Artifacts:")
    print("1. FAQ")
    print("2. Study Guide")
    print("3. Timeline")
    print("4. Executive Briefing")
    print()
    
    choice = input("Select artifact type (1-4): ").strip()
    topic = input("Enter topic (or press Enter for 'knowledge graphs'): ").strip() or "knowledge graphs"
    
    print("\n" + "=" * 80 + "\n")
    
    if choice == "1":
        artifact = generator.generate_faq(topic, num_questions=8)
    elif choice == "2":
        artifact = generator.generate_study_guide(topic)
    elif choice == "3":
        artifact = generator.generate_timeline(topic)
    elif choice == "4":
        artifact = generator.generate_briefing(topic)
    else:
        print("Invalid choice")
        return
    
    print(artifact)
    
    # Offer to save
    print("\n" + "=" * 80)
    save = input("\nSave to file? (y/n): ").strip().lower()
    if save == 'y':
        filename = input("Filename (e.g., faq_knowledge_graphs.md): ").strip()
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(artifact)
        print(f"Saved to {filename}")


if __name__ == "__main__":
    main()
