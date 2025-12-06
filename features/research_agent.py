"""
Deep Research Agent - NotebookLM-style web discovery.
Finds and synthesizes external sources.
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from urllib.parse import urlparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class ResearchAgent:
    """Web research agent that discovers and synthesizes sources."""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY')) if os.getenv('OPENAI_API_KEY') else None
    
    def scrape_url(self, url: str, max_chars: int = 10000) -> Dict:
        """Scrape text content from a URL."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get title
            title = soup.title.string if soup.title else urlparse(url).netloc
            
            # Get main content
            # Try to find main content areas
            main_content = soup.find('main') or soup.find('article') or soup.find('body')
            
            if main_content:
                text = main_content.get_text(separator='\n', strip=True)
            else:
                text = soup.get_text(separator='\n', strip=True)
            
            # Clean up whitespace
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            text = '\n'.join(lines)
            
            # Limit length
            if len(text) > max_chars:
                text = text[:max_chars] + "\n\n[Content truncated...]"
            
            return {
                "url": url,
                "title": title.strip() if isinstance(title, str) else str(title),
                "content": text,
                "success": True,
                "error": None
            }
        
        except Exception as e:
            return {
                "url": url,
                "title": None,
                "content": None,
                "success": False,
                "error": str(e)
            }
    
    def assess_quality(self, source: Dict) -> Dict:
        """Assess the quality and relevance of a scraped source."""
        if not self.client or not source['success']:
            return {
                "is_quality": False,
                "score": 0,
                "reason": "Failed to scrape or no API key"
            }
        
        content_preview = source['content'][:2000] if source['content'] else ""
        
        prompt = f"""Assess the quality of this web source for research purposes.

Title: {source['title']}
URL: {source['url']}
Content Preview:
{content_preview}

Evaluate:
1. Is this a credible source (academic, professional, reputable)?
2. Does it contain substantive information (not just ads/links)?
3. Is it well-written and informative?

Respond with JSON:
{{
    "is_quality": true/false,
    "score": 0-10,
    "reason": "brief explanation",
    "content_type": "academic paper / blog post / documentation / news / other"
}}"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a research quality assessor. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            import json
            assessment = json.loads(response.choices[0].message.content)
            return assessment
        
        except Exception as e:
            return {
                "is_quality": False,
                "score": 0,
                "reason": f"Error: {str(e)}"
            }
    
    def synthesize_sources(self, sources: List[Dict], topic: str) -> str:
        """Synthesize multiple sources into a coherent summary."""
        if not self.client:
            return "Error: OpenAI API key not configured"
        
        # Build context from sources
        context_parts = []
        for i, source in enumerate(sources, 1):
            if source['success']:
                context_parts.append(f"\n[Source {i}: {source['title']}]")
                context_parts.append(f"URL: {source['url']}")
                context_parts.append(f"\n{source['content'][:3000]}\n")
                context_parts.append("-" * 80)
        
        context = "\n".join(context_parts)
        
        prompt = f"""Synthesize the following web sources about {topic} into a comprehensive research summary.

Sources:
{context}

Create a synthesis that:
1. Identifies key themes across sources
2. Highlights important findings and insights
3. Notes any contradictions or different perspectives
4. Includes citations [1], [2], etc. for specific claims
5. Organizes information logically

Format as a well-structured markdown document with headings."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a research synthesizer creating comprehensive summaries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            return f"Error synthesizing sources: {str(e)}"
    
    def create_literature_note(self, topic: str, synthesis: str, sources: List[Dict]) -> str:
        """Format synthesis as an Obsidian literature note."""
        
        source_list = []
        for i, source in enumerate(sources, 1):
            if source['success']:
                source_list.append(f"{i}. [{source['title']}]({source['url']})")
        
        sources_section = "\n".join(source_list)
        
        note = f"""---
type: literature-note
project: Cloud-vs-KG-Data-Centric
topic: {topic}
source: "Web Research"
generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d')}
tags: [literature, web-research, {topic.lower().replace(' ', '-')}]
---

# Web Research: {topic}

{synthesis}

## Sources

{sources_section}

## Related Concepts

- (Add links to relevant concept notes)

## Notes

- This note was generated from web research
- Review and enhance with additional connections to vault concepts
"""
        
        return note
    
    def deep_research(self, topic: str, urls: List[str] = None, auto_save: bool = False) -> Dict:
        """
        Perform deep research on a topic.
        
        Args:
            topic: Research topic
            urls: Optional list of specific URLs to research
            auto_save: Whether to auto-save as literature note
        
        Returns:
            Dict with synthesis, sources, and optional saved note path
        """
        print(f"\n🔬 Deep Research: {topic}")
        print("=" * 80)
        
        if urls is None:
            print("\n⚠️  No URLs provided. In a full implementation, this would:")
            print("  1. Search the web for relevant sources")
            print("  2. Filter results by relevance and quality")
            print("  3. Scrape top N sources")
            print("\nFor now, please provide URLs manually.\n")
            return {
                "error": "URL list required (web search not yet implemented)",
                "synthesis": None,
                "sources": []
            }
        
        # Scrape URLs
        print(f"\n📥 Scraping {len(urls)} sources...")
        scraped_sources = []
        
        for url in urls:
            print(f"  • {url}...", end=" ")
            source = self.scrape_url(url)
            
            if source['success']:
                print("✓")
                # Assess quality
                assessment = self.assess_quality(source)
                source['quality'] = assessment
                
                if assessment.get('is_quality', False):
                    scraped_sources.append(source)
                    print(f"    Quality score: {assessment.get('score', 0)}/10 - {assessment.get('reason', '')}")
                else:
                    print(f"    Skipped (low quality): {assessment.get('reason', '')}")
            else:
                print(f"✗ Error: {source['error']}")
        
        if not scraped_sources:
            return {
                "error": "No quality sources found",
                "synthesis": None,
                "sources": scraped_sources
            }
        
        # Synthesize
        print(f"\n🧠 Synthesizing {len(scraped_sources)} sources...")
        synthesis = self.synthesize_sources(scraped_sources, topic)
        
        result = {
            "topic": topic,
            "synthesis": synthesis,
            "sources": scraped_sources,
            "num_sources": len(scraped_sources)
        }
        
        # Optionally save as literature note
        if auto_save:
            note = self.create_literature_note(topic, synthesis, scraped_sources)
            filename = f"web_research_{topic.lower().replace(' ', '_')}.md"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(note)
            
            result['saved_note'] = filename
            print(f"\n💾 Saved literature note: {filename}")
        
        return result


def main():
    """Demo the research agent."""
    print("=" * 80)
    print("🔬 Deep Research Agent - NotebookLM Style")
    print("=" * 80)
    
    agent = ResearchAgent()
    
    # Example usage
    topic = input("\nResearch topic: ").strip() or "Knowledge Graphs"
    
    print("\nEnter URLs to research (one per line, empty line to finish):")
    urls = []
    while True:
        url = input("  URL: ").strip()
        if not url:
            break
        urls.append(url)
    
    if not urls:
        print("\nNo URLs provided. Exiting.")
        return
    
    # Perform research
    result = agent.deep_research(topic, urls=urls, auto_save=True)
    
    if result.get('error'):
        print(f"\n❌ Error: {result['error']}")
        return
    
    print("\n" + "=" * 80)
    print("📄 SYNTHESIS")
    print("=" * 80)
    print(result['synthesis'])
    
    print("\n" + "=" * 80)
    print(f"✅ Research complete! Processed {result['num_sources']} sources.")
    if result.get('saved_note'):
        print(f"📝 Literature note saved: {result['saved_note']}")


if __name__ == "__main__":
    main()
