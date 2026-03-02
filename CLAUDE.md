# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PageIndex is a vectorless, reasoning-based RAG (Retrieval-Augmented Generation) system that builds hierarchical tree indexes from long documents. Instead of using vector databases and semantic similarity, it uses LLM reasoning to navigate document structures like human experts do.

**Core Concept**: The system creates a "Table-of-Contents" tree structure from documents (PDF or Markdown) and performs reasoning-based retrieval through tree search, achieving state-of-the-art accuracy on professional document analysis tasks.

## Environment Setup

1. **Python Environment**: Uses Python 3.12 with virtual environment at `.venv/`
2. **Activate virtual environment**:
   ```bash
   source .venv/bin/activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Environment variables**: Configure `.env` file with:
   - `CHATGPT_API_KEY`: OpenAI API key
   - `BASE_URL`: API base URL (defaults to OpenAI, but can use custom endpoints)

## Running PageIndex

### Process PDF Documents
```bash
python run_pageindex.py --pdf_path <path_to_pdf> \
  --model gpt-4o-2024-11-20 \
  --toc-check-pages 20 \
  --max-pages-per-node 10 \
  --max-tokens-per-node 20000 \
  --if-add-node-summary yes \
  --if-add-node-id yes
```

### Process Markdown Documents
```bash
python run_pageindex.py --md_path <path_to_markdown> \
  --model gpt-4o-2024-11-20 \
  --if-thinning no \
  --thinning-threshold 5000 \
  --summary-token-threshold 200 \
  --if-add-node-summary yes
```

**Output**: Results are saved to `./results/<filename>_structure.json`

## Architecture

### Core Modules

**pageindex/page_index.py** (1,200+ lines)
- Main PDF processing logic
- `page_index_main()`: Entry point for PDF document processing
- `check_title_appearance()`: Validates section titles against page content using LLM
- Handles TOC extraction, page number verification, and tree structure generation
- Uses async operations for parallel LLM calls

**pageindex/page_index_md.py** (300+ lines)
- Markdown document processing
- `md_to_tree()`: Entry point for markdown processing
- `extract_nodes_from_markdown()`: Parses markdown headers into hierarchical nodes
- Supports tree thinning for large documents
- Async summary generation for nodes

**pageindex/utils.py** (600+ lines)
- Shared utilities across the codebase
- `ChatGPT_API()` and `ChatGPT_API_async()`: LLM API wrappers with retry logic
- `ConfigLoader`: Loads configuration from `config.yaml`
- `count_tokens()`: Token counting using tiktoken
- `extract_json()`: Robust JSON extraction from LLM responses
- PDF utilities: `extract_text_from_pdf()`, `extract_images_from_pdf()`
- Tree manipulation: `structure_to_list()`, `list_to_structure()`

**pageindex/config.yaml**
- Default configuration for document processing
- Model selection, token limits, page limits
- Feature flags for node summaries, IDs, descriptions

### Key Workflows

**PDF Processing Flow**:
1. Extract text and images from PDF pages
2. Check for existing TOC in first N pages
3. If no TOC, generate structure using LLM reasoning
4. Verify section titles appear on claimed pages
5. Build hierarchical tree with page ranges
6. Optionally add summaries, IDs, and descriptions

**Markdown Processing Flow**:
1. Parse markdown headers (# through ######) into flat list
2. Extract text content for each section
3. Build hierarchical tree based on header levels
4. Optionally apply tree thinning for large documents
5. Generate summaries for nodes above token threshold
6. Add metadata (IDs, descriptions) as configured

### Important Patterns

**Async Operations**: Both PDF and markdown processing use asyncio extensively for parallel LLM calls. When modifying code that calls LLMs, maintain async/await patterns.

**Configuration Management**: The `ConfigLoader` class merges user options with defaults from `config.yaml`. Always use this pattern rather than hardcoding defaults.

**Error Handling**: LLM API calls include retry logic (max 10 retries with 1-second delays). Maintain this pattern for reliability.

**JSON Extraction**: LLM responses are parsed with `extract_json()` which handles various response formats. Use this utility rather than raw `json.loads()`.

## Additional Components

**kb/** directory: Knowledge base utilities for generating lightweight indexes from markdown documents
- `markdown_to_kb.py`: Converts markdown to knowledge base format
- `generate_lite_index.py`: Creates compact indexes for retrieval

**cookbook/** directory: Jupyter notebooks demonstrating usage
- `pageindex_RAG_simple.ipynb`: Basic RAG implementation
- `agentic_retrieval.ipynb`: Advanced agentic retrieval patterns
- `vision_RAG_pageindex.ipynb`: Vision-based RAG without OCR

**scripts/** directory: Utility scripts
- `markdown_to_kb`: Shell script for batch markdown processing

**tests/** directory: Contains test PDFs and expected results for validation

## Configuration Options

Key parameters in `config.yaml` and command-line args:
- `model`: LLM model to use (default: gpt-4o-2024-11-20)
- `toc_check_page_num`: Pages to scan for existing TOC (PDF only)
- `max_page_num_each_node`: Max pages per tree node (PDF only)
- `max_token_num_each_node`: Max tokens per tree node (PDF only)
- `if_add_node_summary`: Generate summaries for nodes ("yes"/"no")
- `if_add_node_id`: Add unique IDs to nodes ("yes"/"no")
- `if_add_doc_description`: Add document-level description ("yes"/"no")
- `if_add_node_text`: Include full text in nodes ("yes"/"no")

## Development Notes

- The codebase uses OpenAI's API but supports custom base URLs via environment variables
- Token counting uses tiktoken library matched to the model
- Tree structures use nested dictionaries with 'nodes' arrays for children
- Page numbers in PDFs are "physical_index" (actual page position) vs "logical_index" (printed page number)
- Markdown processing preserves code blocks and doesn't treat headers inside them as sections
