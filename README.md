# AI Context Generator

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
[![Version](https://img.shields.io/badge/version-5.0.0-brightgreen.svg)]()

A small, opinionated CLI tool that packages project source files into a single context file suitable for use with Large Language Models (LLMs). It auto-detects common project types, applies smart include/exclude filters, and can output text, Markdown, or JSON.

---

## Quick overview

- Scans your project files and writes a single, easy-to-read context file.
- Keeps all generator tooling in `.context/` and writes outputs to `.context/generated/`.
- Supports presets (Python, JavaScript, Go, Rust, etc.), custom include/exclude patterns, file-size limits, and experimental minification.

---

## Repo layout (convention)

```

your-project/
├── .context/
│   ├── generate.py          # generator (downloaded or copied)
│   ├── .ai-context.yml      # optional config
│   └── generated/           # outputs (gitignored by installer)
├── src/
└── ...

```

## Install

Two simple options: copy the `.context` folder from the repo (recommended) or manually download the generator. Run from your **project root**:

#### MacOS / Linux / WSL / Git Bash

```bash
git clone --depth=1 https://github.com/temrb/generate-project-context.git tmp_repo \
  && rm -rf .context \
  && mv tmp_repo/.context ./ \
  && rm -rf tmp_repo \
  && chmod +x .context/generate.py || true
```

- `rm -rf .context` ensures any existing `.context` is replaced cleanly.
- `chmod +x` may fail silently on filesystems that don’t support execute bits — you can always run with `python3 .context/generate.py`.

#### Windows PowerShell

```powershell
git clone --depth=1 https://github.com/temrb/generate-project-context.git tmp_repo
Remove-Item -Recurse -Force .context -ErrorAction SilentlyContinue
Move-Item tmp_repo/.context . -Force
Remove-Item tmp_repo -Recurse -Force
```

- Existing `.context` is removed before copying to avoid merge/nesting issues.

Both commands copy the `.context` folder (including `generate.py`) into your project. PowerShell doesn’t require `chmod`, but if you later run the generator from a Unix-like shell you can add execute permissions with `chmod +x .context/generate.py`.

**Tip:** Add generated outputs directory to `.gitignore` if not already ignored:

```bash
echo ".context/generated/" >> .gitignore
```

## Optional deps

```bash
pip3 install pyyaml chardet tqdm
```

- `pyyaml` — read `.ai-context.yml` configs
- `chardet` — improve encoding detection
- `tqdm` — progress bars

The generator runs without them but with reduced functionality (you’ll see warnings).

---

## Usage

From your project root:

```bash
# Basic (auto-detect project type)
python3 .context/generate.py

# Scan specific directories
python3 .context/generate.py src/ tests/

# Use a preset
python3 .context/generate.py --preset python

# Output markdown with a custom filename (placed in .context/generated/)
python3 .context/generate.py --output api_docs.md --format markdown

# Enable experimental minification
python3 .context/generate.py --minify

# Dry run (list files that would be processed)
python3 .context/generate.py --dry-run --verbose
```

---

## Configuration

Create `.context/.ai-context.yml` to pin reproducible runs:

```yaml
preset: python
paths:
  - src
  - lib
output: context.md # written to .context/generated/
include:
  - '*.md'
  - 'Dockerfile'
exclude:
  - '*_test.py'
  - 'experiments/*'
max_file_size_mb: 2
format: markdown # text, markdown, json
minify: false
verbose: false
```

**Priority:** CLI options > config file > presets > built-in defaults

---

## CLI flags (summary)

- `paths` — directories/files to scan (default: project root)
- `-o, --output` — output filename (default: `.context/generated/context.txt`)
- `--preset` — project preset (auto | python | javascript | java | go | rust | ...)
- `--include` / `--exclude` — glob patterns
- `--max-file-size-mb` — skip large files (default: 1 MB)
- `--format` — `text` | `markdown` | `json`
- `--minify` — experimental comment/whitespace removal
- `--dry-run` — list files without generating
- `-v, --verbose` — verbose logging
- `--version` — show version

---

## Output formats

- **Text**: plain, human-readable sections with file separators.
- **Markdown**: syntax-highlighted fenced code blocks per file.
- **JSON**: `metadata` + `files[]` with `path`, `size`, `encoding`, `content`.

Outputs are placed in `.context/generated/` by default.

---

## Behavior notes & edge cases

- Skips common binary extensions (images, archives, compiled artifacts).
- Encoding attempts: UTF-8 → chardet (if installed) → latin-1.
- Skips empty/whitespace-only files.
- Always excludes `.context/` (self-exclusion).
- Minification is experimental — use with caution for production code review.

---

## Troubleshooting

- **Config present but not loaded**

  ```text
  Warning: Config file .context/.ai-context.yml exists but PyYAML is not installed
  ```

  Fix: `pip install pyyaml`

- **Garbled text in output**
  Fix: `pip install chardet`

- **No progress bar**
  Fix: `pip install tqdm`

- **Output missing expected files**

  - Ensure include/exclude patterns are correct and relative to the project root.
  - Check `--max-file-size-mb` (defaults to 1 MB).

---

## Contributing

PRs welcome. Ideas:

- More accurate language-specific minifiers
- Additional presets and smarter detection
- Improved binary detection and performance tweaks

---

## License

MIT
