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
│   ├── generate.py          # generator (downloaded or added by installer)
│   ├── .ai-context.yml      # optional config
│   └── generated/           # outputs (gitignored by installer)
├── scripts/
│   ├── install_context.py   # Python installer
│   └── install_context.sh   # Shell installer
├── src/
└── ...

```

---

## Install

Two ways: automated (recommended) or manual.

### Automated (recommended)

From the **project root**, run either the shell or python installer.

Shell:

```bash
chmod +x scripts/install_context.sh
./scripts/install_context.sh --download-generate "https://github.com/temrb/generate-project-context/main/.context/generate.py"
```

Python:

```bash
python3 scripts/install_context.py --download-generate "https://github.com/temrb/generate-project-context/.context/generate.py"
```

The installers will:

- Ensure `.context/generated/` exists
- Add `.context/generated/` and `**/generated/` to `.gitignore` (if missing)
- Optionally download `generate.py` into `.context/`

### Manual

```bash
mkdir -p .context/generated
# Add a .gitignore entry:
printf ".context/generated/\n**/generated/\n" >> .gitignore
# Place the generator
curl -o .context/generate.py https://github.com/temrb/generate-project-context/.context/generate.py
chmod +x .context/generate.py
```

---

## Optional deps

```bash
pip3 install pyyaml chardet tqdm
```

- `pyyaml`: read `.ai-context.yml`
- `chardet`: better encoding detection
- `tqdm`: progress bars

If you omit them, the generator will still run but with reduced functionality (warnings are shown).

---

## Usage

From your project root:

```bash
# Basic (auto-detect project type)
python .context/generate.py

# Scan specific directories
python .context/generate.py src/ tests/

# Use a preset
python .context/generate.py --preset python

# Output markdown with a custom filename (placed in .context/generated/)
python .context/generate.py --output api_docs.md --format markdown

# Enable experimental minification
python .context/generate.py --minify

# Dry run (list files that would be processed)
python .context/generate.py --dry-run --verbose
```

---

## Configuration

Create `.context/.ai-context.yml` to pin reproducible runs:

```yaml
preset: python
paths:
  - src
  - lib
output: context.md # if just a filename it's written under .context/generated/
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

## CLI flags

- `paths` — directories/files to scan (default: project root)
- `-o, --output` — output file name (default: `.context/generated/context.txt`)
- `--preset` — project preset (auto | python | javascript | java | go | rust | ...)
- `--include` — add include glob patterns
- `--exclude` — add exclude glob patterns
- `--max-file-size-mb` — skip files larger than this (default 1 MB)
- `--format` — `text` (default) | `markdown` | `json`
- `--minify` — experimental comment/whitespace removal
- `--dry-run` — list files that would be processed
- `-v, --verbose` — more logging
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

  ```
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
# generate-project-context
