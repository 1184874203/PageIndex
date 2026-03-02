# Scripts

This folder contains small executable wrappers for convenience.

## markdown_to_kb

A lightweight CLI wrapper around `kb.markdown_to_kb`.

Usage (from project root):

```bash
# make executable once
chmod +x scripts/markdown_to_kb

# run
./scripts/markdown_to_kb path/to/document.md --output-dir ./kb
```

It simply calls `kb.markdown_to_kb.main()` so all same flags are supported.
