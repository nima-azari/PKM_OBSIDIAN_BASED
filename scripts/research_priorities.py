"""
Define research priorities for knowledge graph construction and article generation.

This file specifies which concepts are most important for your research,
helping the system focus extraction and synthesis on what matters to you.

Edit this file to reflect YOUR research priorities.
"""

# Top 5 Research Priorities
# These concepts will be weighted higher during graph construction and article generation
RESEARCH_PRIORITIES = [
    "EU Data Act",
    "Linked Data", 
    "Data Silos",
    "Vendor Lock-in",
    "Interoperability"
]

# Research Stance (optional)
# Define your perspective on key topics to guide article generation
RESEARCH_STANCE = {
    "cloud_platforms": "critical",  # Options: "positive", "neutral", "critical"
    "linked_data": "positive",      # Your position on Linked Data
    "data_silos": "critical",       # Your view on data silos
    "eu_regulations": "positive"    # Your stance on EU Data Act
}

# Focus Areas (optional)
# Specify which aspects to emphasize in article synthesis
FOCUS_AREAS = [
    "regulatory_compliance",     # EU Data Act obligations
    "technical_solutions",       # Linked Data, RDF, semantic web
    "problems_to_solve",         # Vendor lock-in, data silos, lack of interoperability
    "benefits_of_standards"      # Why open standards matter
]

# Concepts to De-emphasize (optional)
# These will be downweighted in article generation
DEEMPHASIZE = [
    "cloud advantages",
    "proprietary solutions",
    "vendor-specific features"
]
