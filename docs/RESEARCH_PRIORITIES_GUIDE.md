# Research Priorities Guide

## Why Research Priorities Matter

Without priorities, AI-generated articles can be generic or even contradict your research goals. For example, researching "problems with cloud platforms" could generate pro-cloud content if the system doesn't understand your stance.

**With priorities**, you define:
- What concepts are most important
- Your perspective on key topics (critical, neutral, positive)
- Which aspects to emphasize vs. de-emphasize

## Quick Start

### 1. Edit `research_priorities.py`

```python
RESEARCH_PRIORITIES = [
    "EU Data Act",
    "Linked Data", 
    "Data Silos",
    "Vendor Lock-in",
    "Interoperability"
]

RESEARCH_STANCE = {
    "cloud_platforms": "critical",  # Critical analysis
    "linked_data": "positive",      # Promote benefits
    "data_silos": "critical",       # Highlight problems
    "eu_regulations": "positive"    # Support framework
}
```

### 2. Generate Article

```bash
python generate_article_from_graph.py data/graphs/knowledge_graph.ttl
```

The article will now:
- Focus on your top 5 priorities
- Maintain your critical/positive stance
- Weight concepts 3x if they match priorities
- De-emphasize concepts you don't want

## How It Works

### Concept Weighting

```
Priority concept + 5 mentions = 15 weight ⭐
Regular concept + 5 mentions = 5 weight
```

Priority concepts appear first and get more coverage in the article.

### Stance Integration

```python
RESEARCH_STANCE = {
    "cloud_platforms": "critical"  # → "critically examine cloud platforms"
}
```

The LLM receives explicit instructions:
- **Critical**: Examine problems, limitations, risks
- **Positive**: Emphasize benefits, solutions, advantages
- **Neutral**: Balanced coverage

### Example Output Difference

**Without Priorities:**
> "Cloud platforms offer many benefits including scalability and flexibility..."

**With Priorities (cloud_platforms: critical):**
> "Vendor lock-in remains a significant concern in cloud platforms, where organizations often find themselves tethered to specific vendors..."

## Use Cases

### Use Case 1: Regulatory Compliance Research

```python
RESEARCH_PRIORITIES = [
    "GDPR",
    "EU Data Act",
    "Data Protection",
    "Compliance Requirements",
    "Member State Obligations"
]

RESEARCH_STANCE = {
    "eu_regulations": "positive",
    "compliance": "positive"
}
```

**Result**: Article emphasizes regulatory frameworks and compliance benefits.

### Use Case 2: Technical Solution Research

```python
RESEARCH_PRIORITIES = [
    "Linked Data",
    "RDF",
    "SPARQL",
    "Semantic Web",
    "Knowledge Graphs"
]

RESEARCH_STANCE = {
    "linked_data": "positive",
    "proprietary_systems": "critical"
}
```

**Result**: Article promotes semantic web technologies and critiques closed systems.

### Use Case 3: Problem Analysis

```python
RESEARCH_PRIORITIES = [
    "Vendor Lock-in",
    "Data Silos",
    "Interoperability Issues",
    "Proprietary Formats",
    "Cloud Migration Challenges"
]

RESEARCH_STANCE = {
    "cloud_platforms": "critical",
    "data_silos": "critical",
    "vendor_lock_in": "critical"
}
```

**Result**: Article critically analyzes problems with current systems.

## Configuration Options

### RESEARCH_PRIORITIES (List)

Top 5 concepts to focus on. These will:
- Get 3x weighting in concept sorting
- Appear in "Priority Concepts" section
- Get more detailed coverage in article
- Influence section structure

**Tips:**
- Keep it to 5-7 concepts (more = dilution)
- Use exact phrases from your documents
- Order by importance (most important first)

### RESEARCH_STANCE (Dict)

Your perspective on key topics:

```python
RESEARCH_STANCE = {
    "topic_name": "stance"  # Options: "positive", "neutral", "critical"
}
```

**Stance Effects:**

| Stance | LLM Instruction | Example Output |
|--------|----------------|----------------|
| `positive` | "Emphasize benefits..." | "X offers significant advantages..." |
| `neutral` | "Provide balanced coverage..." | "X has both strengths and limitations..." |
| `critical` | "Critically examine..." | "X poses challenges including..." |

### FOCUS_AREAS (List)

Aspects to emphasize:

```python
FOCUS_AREAS = [
    "regulatory_compliance",
    "technical_solutions",
    "problems_to_solve",
    "benefits_of_standards"
]
```

### DEEMPHASIZE (List)

Concepts to downweight:

```python
DEEMPHASIZE = [
    "cloud advantages",
    "proprietary solutions",
    "vendor-specific features"
]
```

These won't appear in the priority section even if mentioned frequently.

## Testing Your Priorities

### 1. Generate Without Priorities

```bash
# Rename or remove research_priorities.py temporarily
mv research_priorities.py research_priorities.py.bak
python generate_article_from_graph.py data/graphs/knowledge_graph.ttl
```

### 2. Generate With Priorities

```bash
# Restore priorities
mv research_priorities.py.bak research_priorities.py
python generate_article_from_graph.py data/graphs/knowledge_graph.ttl
```

### 3. Compare

Check:
- Title reflects priorities?
- First sections cover priority concepts?
- Stance is maintained throughout?
- De-emphasized concepts appear less?

## Best Practices

### 1. Align Priorities with Meta-Ontology

If using meta-ontology guided graphs:

```python
# research_priorities.py
RESEARCH_PRIORITIES = [
    "EU Data Act",        # → PolicyFramework
    "Linked Data",        # → DataTechnology
    "Vendor Lock-in"      # → DataLimitation
]

# data/graphs/meta-ont-eu-linkeddata.ttl
:EUDataAct a :PolicyFramework .
:LinkedData a :DataTechnology .
:VendorLockIn a :DataLimitation .
```

Alignment ensures LLM extracts concepts that match your priorities.

### 2. Iterate Based on Output

1. Generate article
2. Review which concepts appear
3. Adjust priorities if needed
4. Regenerate

Example iteration:
```python
# First attempt
RESEARCH_PRIORITIES = ["Data Act", "Linked Data"]

# After review: article mentions "EU Data Act" not "Data Act"
RESEARCH_PRIORITIES = ["EU Data Act", "Linked Data"]  # Fixed
```

### 3. Use Stance Strategically

Don't make everything critical or positive:

```python
# ❌ Too extreme
RESEARCH_STANCE = {
    "cloud": "critical",
    "vendors": "critical",
    "proprietary": "critical",
    "lock_in": "critical"
}

# ✓ Balanced critique
RESEARCH_STANCE = {
    "cloud_platforms": "critical",      # Main problem
    "linked_data": "positive",          # Solution
    "open_standards": "positive",       # Alternative
    "interoperability": "neutral"       # Context
}
```

### 4. Update Priorities as Research Evolves

Your research focus changes over time:

```python
# Week 1: Understanding the problem
RESEARCH_PRIORITIES = ["Vendor Lock-in", "Data Silos", "Interoperability Issues"]

# Week 3: After more sources, focused on solutions
RESEARCH_PRIORITIES = ["Linked Data", "RDF", "Semantic Web", "EU Data Act", "Open Standards"]
```

Regenerate articles as priorities shift.

## Integration with Pipeline

### Full Workflow with Priorities

```bash
# 1. Set priorities
nano research_priorities.py

# 2. Build graph (optionally with meta-ontology)
python build_graph.py --meta-ontology data/graphs/meta-ont-eu-linkeddata.ttl

# 3. Generate priority-aligned article
python generate_article_from_graph.py data/graphs/knowledge_graph.ttl

# 4. Review article
cat data/sources/knowledge_graph_article.md

# 5. Rebuild graph (article now included in knowledge base)
python build_graph.py --meta-ontology data/graphs/meta-ont-eu-linkeddata.ttl

# 6. Chat with everything
python server.py
```

## Troubleshooting

### Problem: Article doesn't reflect priorities

**Solution 1**: Check concept names match
```python
# Bad: "Data Act" (too generic)
# Good: "EU Data Act" (specific phrase from documents)
```

**Solution 2**: Increase concept weight
```python
# In generate_article_from_graph.py, line ~142
priority_concepts.append((concept, mentions * 5))  # Increase from 3x to 5x
```

### Problem: Stance not strong enough

**Solution**: Edit prompt in `generate_article_from_graph.py`:

```python
if RESEARCH_STANCE.get('cloud_platforms') == 'critical':
    stance_guidance += "\n- STRONGLY critique cloud platforms: emphasize lock-in, silos, proprietary issues"
```

### Problem: Wrong concepts still prominent

**Solution**: Add to DEEMPHASIZE:

```python
DEEMPHASIZE = [
    "cloud advantages",
    "scalability",
    "flexibility",
    "convenience"
]
```

## Summary

**Research priorities = User control over AI synthesis**

✅ Focus on what matters to you
✅ Maintain your research perspective
✅ Generate aligned, purposeful articles
✅ Avoid generic or contradictory content

**Quick Checklist:**
- [ ] Edit `research_priorities.py`
- [ ] Set top 5 priorities
- [ ] Define stance (critical/positive/neutral)
- [ ] Regenerate article
- [ ] Review for alignment
- [ ] Iterate as needed

---

**Next Steps:**
- See `META_ONTOLOGY_GUIDE.md` for concept extraction
- See `RESEARCH_PIPELINE_GUIDE.txt` for full workflow
- See `QUICKSTART_GRAPH_DISCOVERY.txt` for quick start
