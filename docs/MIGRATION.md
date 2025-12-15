# Migration Guide: Separating Tool from Development Work

## Overview

The repository is now organized to separate:
- **Tool code** (publishable, in git)
- **Development/example work** (private, gitignored)

## Directory Structure

```
obsidian-control/
├── core/                    # ✅ Tool code (published)
├── features/               # ✅ Tool code (published)
├── static/                 # ✅ Web UI (published)
├── notebooks/              # ✅ Example notebooks (published)
├── data/                   # ✅ Template structure (published)
│   ├── sources/            #    (empty, just .gitkeep)
│   ├── graphs/             #    (empty, just .gitkeep)
│   ├── embeddings/         #    (empty, just .gitkeep)
│   ├── keywords/           #    (empty, just .gitkeep)
│   ├── index/              #    (empty, just .gitkeep)
│   └── processed/          #    (empty, just .gitkeep)
├── examples/               # ❌ YOUR work (gitignored)
│   ├── data/
│   │   ├── sources/        #    Your documents here!
│   │   ├── graphs/         #    Your generated graphs
│   │   ├── embeddings/     #    Cached data
│   │   └── ...
│   ├── notebooks/          #    Your test notebooks
│   └── outputs/            #    Generated articles/posts
├── build_graph.py          # ✅ Tool script (published)
├── generate_article_from_graph.py  # ✅ Tool script (published)
├── server.py               # ✅ Tool script (published)
├── test_*.py               # ✅ Test scripts (published)
└── requirements.txt        # ✅ Dependencies (published)
```

## Migration Steps

### Step 1: Move Your Personal Data

```bash
# Move your documents from data/sources/ to examples/data/sources/
mv data/sources/*.md examples/data/sources/
mv data/sources/*.pdf examples/data/sources/
mv data/sources/*.html examples/data/sources/

# Keep youtube_links.txt in both places (template in data/, yours in examples/)
cp data/sources/youtube_links.txt examples/data/sources/

# Move generated graphs
mv data/graphs/*.ttl examples/data/graphs/

# Move cached data (optional, will be regenerated)
mv data/embeddings/* examples/data/embeddings/ 2>/dev/null || true
mv data/keywords/* examples/data/keywords/ 2>/dev/null || true
```

### Step 2: Update Your Workflow

**Before (old way):**
```bash
# Documents in data/sources/
python build_graph.py
python server.py
```

**After (new way - Option A: Update scripts):**
```bash
# Documents in examples/data/sources/
python build_graph.py examples/data/graphs/my_graph.ttl
python generate_article_from_graph.py examples/data/graphs/my_graph.ttl
# TODO: Update server.py to use examples/data/sources/
```

**After (new way - Option B: Use symlinks):**
```bash
# On Linux/Mac:
ln -s ../examples/data/sources data/sources

# On Windows (PowerShell as Admin):
New-Item -ItemType SymbolicLink -Path "data\sources" -Target "examples\data\sources"
```

### Step 3: Update Configuration Files

Create `examples/.env` for your API keys:
```bash
cp .env examples/.env
```

Update scripts to use examples/ path:
```python
# In test scripts
rag = VaultRAG(sources_dir="examples/data/sources", verbose=True)
```

## What Gets Published vs. Ignored

### ✅ Published to Git

- All Python code (`core/`, `features/`, `*.py`)
- Documentation (`README.md`, `MIGRATION.md`)
- Configuration templates (`.env.example`)
- Empty data structure (`data/*/. gitkeep`)
- Example files (`examples/README.md`, `examples/data/sources/example_document.md`)
- Test scripts (`test_*.py`)

### ❌ Gitignored (Private)

- Your documents (`examples/data/sources/*.pdf`, `*.md`, etc.)
- Generated graphs (`examples/data/graphs/*.ttl`)
- Cached embeddings (`examples/data/embeddings/`)
- Your API keys (`examples/.env`, `.env`)
- Development outputs (`examples/outputs/`)
- Analysis documents (`GENERATED_TTL_ANALYSIS.md`, `km_graphrag_stack_design.md`)
- Social media posts (`socialmediapost/`)

## Verification

Check what will be published:
```bash
# See what git tracks
git status

# See what's ignored
git status --ignored

# Dry-run: see what would be committed
git add -A --dry-run
```

Ensure these are NOT in git:
```bash
git ls-files | grep -E "examples/data/sources/.*\.(pdf|md)" 
# Should return nothing

git ls-files | grep ".env"
# Should return nothing (except .env.example if you create one)
```

## Creating .env.example

For publishing, create a template:
```bash
cat > .env.example << 'EOF'
# Required for RAG and chat
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Obsidian vault integration
OBSIDIAN_API_KEY=your_obsidian_api_key_here
OBSIDIAN_VAULT_NAME=your_vault_name
EOF
```

## Rollback (If Needed)

If you need to go back:
```bash
# Move data back
mv examples/data/sources/* data/sources/
mv examples/data/graphs/* data/graphs/

# Keep using data/ as before
```

## Benefits

1. **Clean repository** - Only tool code is published
2. **Privacy** - Your personal documents stay private
3. **Flexibility** - Work in `examples/` without affecting the tool
4. **Easy updates** - Pull tool updates without conflicts with your data
5. **Professional** - Repository looks clean for GitHub publishing

## Next Steps

1. ✅ Move your data to `examples/`
2. ✅ Test that everything still works
3. ✅ Verify `.gitignore` is working (`git status`)
4. ✅ Commit the new structure
5. ✅ Push to GitHub

```bash
git add .
git commit -m "refactor: separate tool code from development work"
git push origin master
```
