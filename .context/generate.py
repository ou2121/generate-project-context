#!/usr/bin/env python3
# generate.py
"""AI Context Generator - A structured tool to package project files for LLMs.

This script collects text files from a project, applies smart filtering, and
generates a single context file for use with Large Language Models.

Directory Structure:
  .context/                     # Main context generation directory
    ├── generate.py # This script
    ├── .ai-context.yml        # Configuration file (optional)
    └── generated/             # Output directory for generated files
        └── context.txt        # Generated context file

Core Principles:
- Structured Organization: All context-related files in .context/ directory
- Convention over Configuration: Smart defaults that work for most projects
- Simplicity: Easy to use with minimal and intuitive CLI
- Performance: Fast, streaming processing with low memory usage
- Universal: Works for any programming language or project type

Usage Examples:
  # Basic usage (auto-detects project type, outputs to .context/generated/context.txt)
  python .context/generate.py

  # Specify a directory to scan
  python .context/generate.py ../src/

  # Use a preset and enable minification
  python .context/generate.py --preset python --minify

  # Custom output name (still in .context/generated/)
  python .context/generate.py --output my_context.md

  # Provide custom patterns (added to preset)
  python .context/generate.py --preset python --include "*.toml" --exclude "tests/*"
"""

from __future__ import annotations

import argparse
import fnmatch
import io
import json
import logging
import os
import re
import sys
import tempfile
import time
import tokenize
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set

# Optional libs with graceful fallback
try:
    import chardet

    HAS_CHARDET = True
except ImportError:
    HAS_CHARDET = False

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    from tqdm import tqdm

    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

__version__ = "5.0.0"

# --- Constants and Defaults ---
CONTEXT_DIR_NAME = ".context"
GENERATED_DIR_NAME = "generated"
CONFIG_FILE_NAME = ".ai-context.yml"
DEFAULT_OUTPUT_NAME = "context.txt"
DEFAULT_EXCLUDE_PATTERNS = [
    "*/.*",
    "dist",
    "build",
    "node_modules",
    "__pycache__",
    f"{CONTEXT_DIR_NAME}/*",  # Always exclude the .context directory itself
]
BINARY_FILE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".ico",
    ".svg",
    ".webp",
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".7z",
    ".rar",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".o",
    ".a",
    ".lib",
    ".mp3",
    ".wav",
    ".flac",
    ".aac",
    ".ogg",
    ".wma",
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".webm",
    ".flv",
    ".class",
    ".jar",
    ".pyc",
    ".pyo",
    ".pyd",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".ttf",
    ".otf",
    ".woff",
    ".woff2",
    ".eot",
}
ENCODING_SAMPLE_SIZE = 8192
DEFAULT_MAX_FILE_SIZE_MB = 1

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stderr)
logger = logging.getLogger(__name__)


# --- Path Management ---
class PathManager:
    """Manages paths relative to project structure."""

    @staticmethod
    def get_project_root() -> Path:
        """Get the project root (parent of .context directory)."""
        # If we're running from within .context, go up one level
        current = Path.cwd()
        if current.name == CONTEXT_DIR_NAME:
            return current.parent
        # Otherwise check if .context exists in current directory
        if (current / CONTEXT_DIR_NAME).exists():
            return current
        # Otherwise assume current directory is project root
        return current

    @staticmethod
    def get_context_dir() -> Path:
        """Get the .context directory path."""
        project_root = PathManager.get_project_root()
        return project_root / CONTEXT_DIR_NAME

    @staticmethod
    def get_generated_dir() -> Path:
        """Get the .context/generated directory path."""
        return PathManager.get_context_dir() / GENERATED_DIR_NAME

    @staticmethod
    def get_config_path() -> Path:
        """Get the path to .ai-context.yml in .context directory."""
        return PathManager.get_context_dir() / CONFIG_FILE_NAME

    @staticmethod
    def ensure_generated_dir() -> Path:
        """Ensure the generated directory exists."""
        generated_dir = PathManager.get_generated_dir()
        generated_dir.mkdir(parents=True, exist_ok=True)
        return generated_dir

    @staticmethod
    def resolve_project_path(path: Path) -> Path:
        """Resolve a path relative to the project root."""
        project_root = PathManager.get_project_root()
        if path.is_absolute():
            return path
        return (project_root / path).resolve()

    @staticmethod
    def rel_to_project_root(path: Path) -> str:
        """Get path relative to project root for display."""
        try:
            project_root = PathManager.get_project_root()
            return str(path.relative_to(project_root))
        except Exception:
            return str(path)


# --- Core Data Structures ---
class OutputFormat(Enum):
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"


@dataclass
class Config:
    """Configuration with structure-aware defaults."""

    paths: List[Path] = field(default_factory=lambda: [PathManager.get_project_root()])
    output: Path = field(
        default_factory=lambda: PathManager.get_generated_dir() / DEFAULT_OUTPUT_NAME
    )
    preset: str = "auto"
    include: List[str] = field(default_factory=list)
    exclude: List[str] = field(default_factory=list)
    exclude_common: bool = True
    max_file_size_mb: float = DEFAULT_MAX_FILE_SIZE_MB
    output_format: OutputFormat = OutputFormat.TEXT
    minify: bool = False
    verbose: bool = False
    dry_run: bool = False

    @property
    def max_file_size_bytes(self) -> int:
        if self.max_file_size_mb <= 0:
            return float("inf")
        return int(self.max_file_size_mb * 1024 * 1024)


@dataclass
class ProcessedFile:
    """Represents a file that has been processed."""

    path: Path
    content: Optional[str] = None
    skipped: bool = False
    reason: Optional[str] = None
    size: int = 0
    encoding: str = "unknown"


# --- Project Intelligence ---
class ProjectDetector:
    """Auto-detects project type to apply smart configuration presets."""

    PRESETS = {
        "python": {
            "include": [
                "*.py",
                "requirements*.txt",
                "pyproject.toml",
                "setup.py",
                "*.pyx",
                "*.pyi",
            ],
            "exclude": [
                "*.pyc",
                "*.pyo",
                "*.pyd",
                "*.egg-info/*",
                "venv/*",
                ".venv/*",
                "__pycache__/*",
            ],
        },
        "javascript": {
            "include": [
                "*.js",
                "*.jsx",
                "*.ts",
                "*.tsx",
                "*.mjs",
                "*.cjs",
                "package.json",
                "tsconfig.json",
                "*.vue",
                "*.svelte",
                "*.html",
                "*.css",
                "*.scss",
                "*.less",
            ],
            "exclude": [
                "*.log",
                "package-lock.json",
                "yarn.lock",
                "pnpm-lock.yaml",
                "*.map",
            ],
        },
        "java": {
            "include": [
                "*.java",
                "*.xml",
                "*.properties",
                "pom.xml",
                "build.gradle*",
                "*.kt",
            ],
            "exclude": ["*.class", "*.jar", "target/*", "build/*"],
        },
        "csharp": {
            "include": ["*.cs", "*.csproj", "*.sln", "*.xaml", "*.config", "*.resx"],
            "exclude": ["bin/*", "obj/*", "*.dll", "*.exe"],
        },
        "ruby": {
            "include": ["*.rb", "*.erb", "*.rake", "Gemfile", "Rakefile", "*.ru"],
            "exclude": ["Gemfile.lock", "vendor/*"],
        },
        "go": {
            "include": ["*.go", "go.mod", "go.sum", "*.proto"],
            "exclude": ["vendor/*"],
        },
        "rust": {
            "include": ["*.rs", "Cargo.toml", "Cargo.lock"],
            "exclude": ["target/*"],
        },
        "php": {
            "include": ["*.php", "composer.json", "*.blade.php"],
            "exclude": ["vendor/*", "composer.lock"],
        },
        "cpp": {
            "include": [
                "*.cpp",
                "*.cc",
                "*.cxx",
                "*.h",
                "*.hpp",
                "*.hxx",
                "CMakeLists.txt",
                "*.cmake",
            ],
            "exclude": ["*.o", "*.obj", "build/*", "cmake-build-*/*"],
        },
        "swift": {
            "include": ["*.swift", "Package.swift", "*.xcodeproj/*", "*.xcworkspace/*"],
            "exclude": ["*.xcuserdata/*", "build/*", "DerivedData/*"],
        },
    }

    INDICATORS = {
        "python": [
            "requirements.txt",
            "requirements-dev.txt",
            "pyproject.toml",
            "setup.py",
            "Pipfile",
        ],
        "javascript": ["package.json", "node_modules"],
        "java": ["pom.xml", "build.gradle", "build.gradle.kts"],
        "csharp": ["*.csproj", "*.sln"],
        "ruby": ["Gemfile", "Rakefile"],
        "go": ["go.mod"],
        "rust": ["Cargo.toml"],
        "php": ["composer.json"],
        "cpp": ["CMakeLists.txt", "Makefile"],
        "swift": ["Package.swift", "*.xcodeproj"],
    }

    @classmethod
    def detect(cls, path: Path) -> str:
        """Detects the project type by looking for key indicator files."""
        for name, indicators in cls.INDICATORS.items():
            for indicator in indicators:
                if "*" in indicator:
                    # Handle glob patterns
                    if list(path.glob(indicator)):
                        logger.info(f"✓ Detected {name.capitalize()} project.")
                        return name
                else:
                    if (path / indicator).exists():
                        logger.info(f"✓ Detected {name.capitalize()} project.")
                        return name

        logger.info("✓ Could not auto-detect project type, using generic settings.")
        return "generic"

    @classmethod
    def get_preset_config(cls, name: str) -> Dict:
        """Returns the configuration for a given preset name."""
        return cls.PRESETS.get(name, {})


# --- File Filtering and Collection ---
class SmartFilter:
    """Intelligent file filtering with caching and fast-path excludes."""

    def __init__(self, config: Config):
        self.exclude_common = config.exclude_common
        self.include_patterns = [self._compile_glob(p) for p in config.include]
        self.exclude_patterns = [self._compile_glob(p) for p in config.exclude]
        self.base_exclude = [self._compile_glob(p) for p in DEFAULT_EXCLUDE_PATTERNS]
        self._cache: Dict[Path, bool] = {}

    @staticmethod
    def _compile_glob(pattern: str) -> re.Pattern:
        """Compiles a glob pattern into a regex."""
        return re.compile(fnmatch.translate(pattern))

    def _matches(self, path_str: str, patterns: List[re.Pattern]) -> bool:
        """Checks if a string matches any of the compiled patterns."""
        return any(p.match(path_str) for p in patterns)

    def should_process(self, path: Path) -> bool:
        """Determines if a file or directory should be processed."""

        key = path.resolve()
        if key in self._cache:
            return self._cache[key]

        # Always exclude .context directory
        try:
            rel_path = PathManager.rel_to_project_root(path)
            if rel_path.startswith(CONTEXT_DIR_NAME):
                self._cache[key] = False
                return False
        except Exception:
            pass

        # Use posix path for consistent pattern matching
        path_str = str(path.as_posix())

        # Fast path for common binary extensions
        if path.suffix.lower() in BINARY_FILE_EXTENSIONS:
            self._cache[key] = False
            return False

        # Fast path for common excluded directories
        if self.exclude_common:
            if path.name.startswith(".") or self._matches(path_str, self.base_exclude):
                self._cache[key] = False
                return False

        # Custom exclude patterns
        if self._matches(path_str, self.exclude_patterns):
            self._cache[key] = False
            return False

        # If include patterns are specified, a file must match at least one
        if (
            self.include_patterns
            and path.is_file()
            and not self._matches(path.name, self.include_patterns)
        ):
            self._cache[key] = False
            return False

        self._cache[key] = True
        return True


class FileCollector:
    """Walks directories and collects files based on filter criteria."""

    def __init__(self, config: Config, file_filter: SmartFilter):
        self.config = config
        self.filter = file_filter

    def collect(self) -> Iterable[Path]:
        """Collects all files that should be processed."""
        seen_paths: Set[Path] = set()

        for start_path in self.config.paths:
            # Resolve paths relative to project root
            start_path = PathManager.resolve_project_path(start_path)

            if not start_path.exists():
                logger.warning(
                    f"Warning: Path does not exist and will be skipped: {start_path}"
                )
                continue

            if start_path.is_file():
                if self.filter.should_process(start_path):
                    resolved_path = start_path.resolve()
                    if resolved_path not in seen_paths:
                        seen_paths.add(resolved_path)
                        yield resolved_path
            else:
                for root, dirs, files in os.walk(
                    start_path, topdown=True, followlinks=False
                ):
                    root_path = Path(root)
                    # Filter directories in-place
                    dirs[:] = [
                        d for d in dirs if self.filter.should_process(root_path / d)
                    ]

                    for name in files:
                        file_path = root_path / name
                        if self.filter.should_process(file_path):
                            resolved_path = file_path.resolve()
                            if resolved_path not in seen_paths:
                                seen_paths.add(resolved_path)
                                yield resolved_path


# --- File Processing and Minification ---
class Minifier:
    """Language-aware minification logic."""

    @staticmethod
    def minify(content: str, path: Path) -> str:
        """Removes comments and extraneous whitespace based on file type."""
        ext = path.suffix.lower()
        if ext in {".py"}:
            return Minifier._minify_python(content)
        elif ext in {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}:
            return Minifier._minify_javascript(content)
        elif ext in {".css", ".scss", ".less"}:
            return Minifier._minify_css(content)
        return Minifier._minify_generic(content)

    @staticmethod
    def _minify_generic(content: str) -> str:
        """A simple generic minifier for comments and empty lines."""
        lines = content.splitlines()
        res = []

        for i, line in enumerate(lines):
            if i == 0 and line.startswith("#!"):
                res.append(line)
                continue

            # Remove single line comments (naive but safer)
            newline = re.sub(r"//.*$", "", line)
            newline = re.sub(r"#(?!!).*$", "", newline)

            if newline.strip():
                res.append(newline.rstrip())

        # Simple block comment removal
        result = "\n".join(res)
        result = re.sub(r"/\*.*?\*/", "", result, flags=re.DOTALL)

        return result

    @staticmethod
    def _minify_python(content: str) -> str:
        """Safely removes only comments from Python code using the tokenize module."""
        try:
            tokens = tokenize.generate_tokens(io.StringIO(content).readline)
            return tokenize.untokenize(
                tok for tok in tokens if tok.type != tokenize.COMMENT
            )
        except (tokenize.TokenError, IndentationError):
            return Minifier._minify_generic(content)

    @staticmethod
    def _minify_javascript(content: str) -> str:
        """Minify JavaScript/TypeScript code."""
        # Remove single-line comments
        content = re.sub(r"//.*$", "", content, flags=re.MULTILINE)
        # Remove multi-line comments
        content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
        # Remove empty lines
        lines = [line.rstrip() for line in content.splitlines() if line.strip()]
        return "\n".join(lines)

    @staticmethod
    def _minify_css(content: str) -> str:
        """Minify CSS code."""
        # Remove comments
        content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
        # Remove unnecessary whitespace
        content = re.sub(r"\s+", " ", content)
        content = re.sub(r"\s*([{}:;,])\s*", r"\1", content)
        return content.strip()


class FileProcessor:
    """Handles reading, decoding, and processing a single file."""

    def __init__(self, config: Config):
        self.config = config

    def process_file(self, path: Path) -> ProcessedFile:
        """Processes a single file."""
        try:
            size = path.stat().st_size
            if (
                self.config.max_file_size_bytes != float("inf")
                and size > self.config.max_file_size_bytes
            ):
                return ProcessedFile(
                    path,
                    skipped=True,
                    reason=f"Exceeds max size ({size} > {self.config.max_file_size_bytes})",
                    size=size,
                )

            with path.open("rb") as f:
                # Read a small chunk to detect binary content and encoding
                chunk = f.read(ENCODING_SAMPLE_SIZE)
                if b"\x00" in chunk:
                    return ProcessedFile(
                        path, skipped=True, reason="Binary file detected", size=size
                    )

                encoding = self._detect_encoding(chunk)

                # Read the full content
                f.seek(0)
                try:
                    content = f.read().decode(encoding, errors="replace")
                except Exception as e:
                    return ProcessedFile(
                        path,
                        skipped=True,
                        reason=f"Could not decode with {encoding}: {e}",
                        size=size,
                    )

            # Apply minification if requested
            if self.config.minify:
                content = Minifier.minify(content, path)

            if not content.strip():
                reason = (
                    "Empty after minification"
                    if self.config.minify
                    else "Empty or whitespace-only file"
                )
                return ProcessedFile(path, skipped=True, reason=reason, size=size)

            return ProcessedFile(path, content=content, size=size, encoding=encoding)

        except Exception as e:
            return ProcessedFile(path, skipped=True, reason=f"Error reading file: {e}")

    @staticmethod
    def _detect_encoding(chunk: bytes) -> str:
        """Detects file encoding from a sample chunk."""
        # First try UTF-8
        try:
            chunk.decode("utf-8")
            return "utf-8"
        except UnicodeDecodeError:
            pass

        # Then try chardet if available
        if HAS_CHARDET:
            result = chardet.detect(chunk)
            if result.get("encoding") and result["confidence"] > 0.7:
                return result["encoding"]

        # Fallback to latin-1
        return "latin-1"


# --- Output Formatting and Writing ---
class Formatter:
    """Base class for output formatters."""

    def __init__(self, config: Config):
        self.config = config

    def write_header(self, file_stream, file_count: int):
        pass

    def write_file(self, file_stream, processed_file: ProcessedFile):
        raise NotImplementedError

    def write_footer(self, file_stream):
        pass


class TextFormatter(Formatter):
    """Formats output as a simple, human-readable text file."""

    def write_header(self, file_stream, file_count: int):
        project_root = PathManager.get_project_root()
        header = (
            f"AI Context Report (v{__version__})\n"
            f"{'=' * 50}\n"
            f"Project Root: {project_root.resolve()}\n"
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Files discovered: {file_count}\n"
            f"{'=' * 50}\n\n"
        )
        file_stream.write(header)

    def write_file(self, file_stream, processed_file: ProcessedFile):
        rel_path = PathManager.rel_to_project_root(processed_file.path)
        separator = f"\n\n{'=' * 20} File: {rel_path} {'=' * 20}\n\n"
        file_stream.write(separator)
        file_stream.write(processed_file.content)


class MarkdownFormatter(Formatter):
    """Formats output as a structured Markdown file."""

    def write_header(self, file_stream, file_count: int):
        project_root = PathManager.get_project_root()
        header = (
            f"# AI Context Report\n\n"
            f"- **Version**: `{__version__}`\n"
            f"- **Project Root**: `{project_root.resolve()}`\n"
            f"- **Generated**: `{time.strftime('%Y-%m-%d %H:%M:%S')}`\n"
            f"- **Files discovered**: `{file_count}`\n\n"
            f"---\n\n"
        )
        file_stream.write(header)

    def write_file(self, file_stream, processed_file: ProcessedFile):
        rel_path = PathManager.rel_to_project_root(processed_file.path)
        ext = processed_file.path.suffix.lstrip(".").lower() or "text"

        file_header = f"## `{rel_path}`\n\n"
        code_block = f"```{ext}\n{processed_file.content}\n```\n\n---\n\n"
        file_stream.write(file_header)
        file_stream.write(code_block)


class JsonFormatter(Formatter):
    """Formats output as a JSON object."""

    def __init__(self, config: Config):
        super().__init__(config)
        self._is_first_file = True

    def write_header(self, file_stream, file_count: int):
        project_root = PathManager.get_project_root()
        file_stream.write("{\n")
        file_stream.write('  "metadata": {\n')
        file_stream.write(f'    "version": "{__version__}",\n')
        project_root_str = json.dumps(str(project_root.resolve()))
        file_stream.write(f'    "project_root": {project_root_str},\n')
        file_stream.write(
            f'    "generated_at": "{time.strftime("%Y-%m-%d %H:%M:%S")}",\n'
        )
        file_stream.write(f'    "file_count": {file_count}\n')
        file_stream.write("  },\n")
        file_stream.write('  "files": [\n')

    def write_file(self, file_stream, processed_file: ProcessedFile):
        rel_path = PathManager.rel_to_project_root(processed_file.path)
        file_data = {
            "path": rel_path,
            "size": processed_file.size,
            "encoding": processed_file.encoding,
            "content": processed_file.content,
        }
        if not self._is_first_file:
            file_stream.write(",\n")

        json_string = json.dumps(file_data, indent=4)
        indented_json = "    " + json_string.replace("\n", "\n    ")
        file_stream.write(indented_json)
        self._is_first_file = False

    def write_footer(self, file_stream):
        file_stream.write("\n  ]\n}\n")


class StreamingWriter:
    """Writes processed files to the output stream."""

    def __init__(self, config: Config):
        self.config = config
        self.formatter = self._get_formatter()

    def _get_formatter(self) -> Formatter:
        if self.config.output_format == OutputFormat.MARKDOWN:
            return MarkdownFormatter(self.config)
        if self.config.output_format == OutputFormat.JSON:
            return JsonFormatter(self.config)
        return TextFormatter(self.config)

    def write(self, files: Iterable[Path]):
        """Processes and writes files in a streaming fashion."""
        processor = FileProcessor(self.config)

        # Collect and sort paths
        file_paths = sorted(list(files))

        # Exclude the output file itself
        try:
            out_resolved = self.config.output.resolve()
            file_paths = [p for p in file_paths if p.resolve() != out_resolved]
        except (OSError, RuntimeError, ValueError):
            pass

        total_files = len(file_paths)

        if self.config.dry_run:
            logger.info(
                f"DRY RUN: Would process {total_files} files and write to {self.config.output}"
            )
            for path in file_paths:
                logger.info(f"  - {PathManager.rel_to_project_root(path)}")
            return

        # Ensure output directory exists
        PathManager.ensure_generated_dir()

        processed_count = 0
        skipped_count = 0

        progress_bar = None
        if HAS_TQDM and sys.stderr.isatty():
            progress_bar = tqdm(total=total_files, desc="Processing files", unit="file")

        try:
            out_suffix = self.config.output.suffix or ".txt"
            with tempfile.NamedTemporaryFile(
                "w",
                delete=False,
                encoding="utf-8",
                dir=self.config.output.parent,
                prefix=".tmp_",
                suffix=out_suffix,
            ) as tmp:
                tmp_path = Path(tmp.name)

                self.formatter.write_header(tmp, total_files)

                for path in file_paths:
                    if progress_bar:
                        progress_bar.update(1)

                    result = processor.process_file(path)

                    if result.skipped:
                        skipped_count += 1
                        if self.config.verbose:
                            logger.info(
                                f"Skipped: {PathManager.rel_to_project_root(path)} (Reason: {result.reason})"
                            )
                        continue

                    self.formatter.write_file(tmp, result)
                    processed_count += 1

                self.formatter.write_footer(tmp)

            # Atomically move temp file to final destination
            os.replace(tmp_path, self.config.output)

        except Exception as e:
            if "tmp_path" in locals() and tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
            raise e
        finally:
            if progress_bar:
                progress_bar.close()

        logger.info("✓ Generation complete.")
        logger.info(f"  - Output file: {self.config.output.resolve()}")
        logger.info(f"  - Files processed: {processed_count}")
        logger.info(f"  - Files skipped: {skipped_count}")


# --- Main Orchestrator ---
class Generator:
    """Orchestrates the context generation process."""

    def __init__(self, config: Config):
        self.config = self._resolve_config(config)

    def _resolve_config(self, cli_config: Config) -> Config:
        """Merges CLI config, file config, and presets."""
        file_conf = self._load_config_from_file()

        # Priority: CLI > File > Preset > Default
        final_config = Config()

        # Apply preset
        preset_name = cli_config.preset or file_conf.get("preset", "auto")
        if preset_name == "auto":
            project_root = PathManager.get_project_root()
            preset_name = ProjectDetector.detect(project_root)

        preset_conf = ProjectDetector.get_preset_config(preset_name)

        # Combine includes and excludes
        includes = preset_conf.get("include", [])
        includes.extend(file_conf.get("include", []))
        includes.extend(cli_config.include)

        excludes = preset_conf.get("exclude", [])
        excludes.extend(file_conf.get("exclude", []))
        excludes.extend(cli_config.exclude)

        final_config.include = list(dict.fromkeys(includes))
        final_config.exclude = list(dict.fromkeys(excludes))

        # Handle paths - resolve relative to project root
        if cli_config.paths != [PathManager.get_project_root()]:
            final_config.paths = cli_config.paths
        else:
            config_paths = file_conf.get("paths", ["."])
            final_config.paths = [Path(p) for p in config_paths]

        # Handle output
        default_output = PathManager.get_generated_dir() / DEFAULT_OUTPUT_NAME
        if cli_config.output != default_output:
            # CLI specified output
            if cli_config.output.parent == Path("."):
                # Just a filename, put it in generated dir
                final_config.output = (
                    PathManager.get_generated_dir() / cli_config.output.name
                )
            else:
                final_config.output = cli_config.output
        else:
            # Use file config or default
            config_output = file_conf.get("output", DEFAULT_OUTPUT_NAME)
            if Path(config_output).parent == Path("."):
                final_config.output = PathManager.get_generated_dir() / config_output
            else:
                final_config.output = Path(config_output)

        # Other settings
        final_config.max_file_size_mb = (
            cli_config.max_file_size_mb
            if cli_config.max_file_size_mb != DEFAULT_MAX_FILE_SIZE_MB
            else file_conf.get("max_file_size_mb", DEFAULT_MAX_FILE_SIZE_MB)
        )
        final_config.output_format = (
            cli_config.output_format
            if cli_config.output_format != OutputFormat.TEXT
            else OutputFormat(file_conf.get("format", OutputFormat.TEXT.value))
        )
        final_config.minify = cli_config.minify or file_conf.get("minify", False)
        final_config.verbose = cli_config.verbose or file_conf.get("verbose", False)
        final_config.dry_run = cli_config.dry_run

        return final_config

    def _load_config_from_file(self) -> Dict:
        """Loads configuration from .context/.ai-context.yml if it exists."""
        config_path = PathManager.get_config_path()

        if config_path.exists():
            if not HAS_YAML:
                logger.warning(
                    f"Warning: Config file {config_path} exists but PyYAML is not installed. "
                    "Install it with: pip install pyyaml"
                )
                return {}
            try:
                with config_path.open("r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data and isinstance(data, dict):
                        logger.info(
                            f"✓ Loaded configuration from {PathManager.rel_to_project_root(config_path)}"
                        )
                        return data
                    return {}
            except Exception as e:
                logger.warning(
                    f"Warning: Could not read config file {config_path}: {e}"
                )
        return {}

    def run(self):
        """Executes the file collection, processing, and writing pipeline."""
        start_time = time.monotonic()

        if self.config.verbose:
            logger.setLevel(logging.DEBUG)
            logger.info("Verbose mode enabled.")
            logger.debug(f"Resolved config: {self.config}")

        logger.info(f"Starting AI Context Generator (v{__version__})...")
        logger.info(f"Project root: {PathManager.get_project_root()}")

        if self.config.minify:
            logger.info(
                "Note: Minification is experimental and may not work perfectly for all languages."
            )

        smart_filter = SmartFilter(self.config)
        collector = FileCollector(self.config, smart_filter)
        files_to_process = collector.collect()

        writer = StreamingWriter(self.config)
        writer.write(files_to_process)

        duration = time.monotonic() - start_time
        logger.info(f"Finished in {duration:.2f} seconds.")


# --- Command-Line Interface ---
def create_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AI Context Generator: A structured tool to package project files for LLMs.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Directory Structure:
  .context/                     # Main directory for context generation
    ├── generate.py # This script
    ├── .ai-context.yml        # Configuration file (optional)
    └── generated/             # Output directory
        └── context.txt        # Generated context file

Examples:
  python .context/generate.py                    # Auto-detect and generate
  python .context/generate.py ../src/            # Scan specific directory
  python .context/generate.py --preset python    # Use Python preset
  python .context/generate.py --output api.md    # Custom output name
        """,
    )

    parser.add_argument(
        "paths",
        nargs="*",
        help="Directories or files to include (default: project root)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help=f"Output file name (default: {DEFAULT_OUTPUT_NAME} in .context/generated/)",
    )
    parser.add_argument(
        "--preset",
        choices=["auto"] + list(ProjectDetector.PRESETS.keys()),
        default=None,
        help="Use a preset configuration for a specific project type",
    )
    parser.add_argument(
        "--include",
        nargs="+",
        help="Glob patterns for files to include (adds to presets)",
    )
    parser.add_argument(
        "--exclude",
        nargs="+",
        help="Glob patterns for files/directories to exclude (adds to presets)",
    )
    parser.add_argument(
        "--max-file-size-mb",
        type=float,
        default=DEFAULT_MAX_FILE_SIZE_MB,
        help=f"Maximum size for a single file in MB (default: {DEFAULT_MAX_FILE_SIZE_MB}MB)",
    )
    parser.add_argument(
        "--format",
        choices=[f.value for f in OutputFormat],
        default=None,
        help="The output format (default: text)",
    )
    parser.add_argument(
        "--minify",
        action="store_true",
        help="[EXPERIMENTAL] Remove comments and whitespace from code",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List files that would be processed without creating output",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    return parser


def main():
    parser = create_arg_parser()
    args = parser.parse_args()

    try:
        # Parse paths
        if args.paths:
            paths = [Path(p) for p in args.paths]
        else:
            paths = [PathManager.get_project_root()]

        # Parse output
        if args.output:
            output_path = Path(args.output)
            # If just a filename, put it in generated directory
            if output_path.parent == Path("."):
                output_path = PathManager.get_generated_dir() / output_path
        else:
            output_path = PathManager.get_generated_dir() / DEFAULT_OUTPUT_NAME

        # Parse format
        output_format = OutputFormat(args.format) if args.format else OutputFormat.TEXT

        config = Config(
            paths=paths,
            output=output_path,
            preset=args.preset,
            include=args.include or [],
            exclude=args.exclude or [],
            max_file_size_mb=args.max_file_size_mb,
            output_format=output_format,
            minify=args.minify,
            verbose=args.verbose,
            dry_run=args.dry_run,
        )

        generator = Generator(config)
        generator.run()

    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        # Avoid referencing args if an exception happens before args is defined.
        verbose_flag = False
        if "args" in locals():
            try:
                verbose_flag = bool(getattr(args, "verbose", False))
            except Exception:
                verbose_flag = False
        logger.error(f"An unexpected error occurred: {e}", exc_info=verbose_flag)
        sys.exit(1)


if __name__ == "__main__":
    main()
