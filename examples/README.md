# Examples Directory

This directory contains example data, test outputs, and development work that is **not published** to the repository.

## Structure

```
examples/
├── data/
│   ├── sources/          # Your personal documents (ignored by git)
│   ├── graphs/           # Generated graphs from your work (ignored)
│   ├── embeddings/       # Cached embeddings (ignored)
│   └── keywords/         # Cached keywords (ignored)
├── notebooks/            # Your Jupyter notebooks for testing (ignored)
├── outputs/              # Generated articles, posts (ignored)
└── README.md             # This file (published)
```

## Usage

### For Development

1. **Add your documents:**
   ```bash
   cp your-document.pdf examples/data/sources/
   ```

2. **Build knowledge graph:**
   ```bash
   python build_graph.py examples/data/graphs/my_graph.ttl
   ```

3. **Generate article:**
   ```bash
   python generate_article_from_graph.py examples/data/graphs/my_graph.ttl
   ```

4. **Test chat:**
   ```bash
   # Update test scripts to use examples/data/sources/
   python test_chat.py
   ```

### For Publishing

Everything in `examples/` is gitignored except:
- This README.md
- Example configuration files (if added)

Your personal documents and generated outputs stay private.

## Moving from `data/` to `examples/data/`

If you have existing files in `data/`:

```bash
# Move your sources
mv data/sources/* examples/data/sources/

# Move your graphs
mv data/graphs/*.ttl examples/data/graphs/

# Keep the example structure in data/ for tool distribution
```

The main `data/` directory will contain only example/template files for users.
