#!/usr/bin/env python3
"""
scripts/install_context.py

Create .context/ and .context/generated/, optionally download generate.py,
and safely add .context/generated/ and **/generated/ to .gitignore.

Usage:
    python scripts/install_context.py [--download-generate URL]
"""

import argparse
import stat
import sys
import urllib.error
import urllib.request
from pathlib import Path


def append_if_missing(file: Path, line: str) -> bool:
    """Append a single line to file if it's not already present."""
    text = file.read_text(encoding="utf-8") if file.exists() else ""
    lines = set(l.strip() for l in text.splitlines())
    if line not in lines:
        with file.open("a", encoding="utf-8") as fh:
            if text and not text.endswith("\n"):
                fh.write("\n")
            fh.write(line + "\n")
        return True
    return False


def download_file(url: str, dest: Path) -> bool:
    """Download url -> dest and try to make it executable."""
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(url) as r:
            data = r.read()
        dest.write_bytes(data)
        try:
            mode = dest.stat().st_mode
            dest.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        except Exception:
            pass
        return True
    except urllib.error.HTTPError as e:
        print(f"HTTP error downloading {url}: {e.code} {e.reason}", file=sys.stderr)
    except urllib.error.URLError as e:
        print(f"URL error downloading {url}: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Error downloading {url}: {e}", file=sys.stderr)
    return False


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Install .context/ structure and update .gitignore"
    )
    parser.add_argument(
        "--download-generate",
        metavar="URL",
        help="URL to download generate.py into .context/",
    )
    args = parser.parse_args(argv)

    # Resolve script path robustly (works when __file__ is not present)
    script_path = None
    if "__file__" in globals():
        script_path = Path(__file__).resolve()
    else:
        # fallback to sys.argv[0] (works when running via `python scripts/install_context.py`)
        try:
            if sys.argv and sys.argv[0]:
                script_path = Path(sys.argv[0]).resolve()
        except Exception:
            script_path = None

    if not script_path:
        print(
            "Error: cannot determine script path (are you running interactively?)",
            file=sys.stderr,
        )
        sys.exit(1)

    project_root = script_path.parent.parent

    context_dir = project_root / ".context"
    generated_dir = context_dir / "generated"
    gitignore_file = project_root / ".gitignore"

    generated_dir.mkdir(parents=True, exist_ok=True)
    print(f"Ensured directory: {generated_dir}")

    if args.download_generate:
        dest = context_dir / "generate.py"
        print(f"Attempting download: {args.download_generate}")
        ok = download_file(args.download_generate, dest)
        print(f"Downloaded generate.py: {ok} -> {dest if ok else 'failed'}")

    if not gitignore_file.exists():
        gitignore_file.write_text(
            "# .gitignore created by install_context.py\n\n", encoding="utf-8"
        )
        print(f"Created {gitignore_file}")

    patterns = [".context/generated/", "**/generated/"]
    for p in patterns:
        added = append_if_missing(gitignore_file, p)
        print(f"{'Added' if added else 'Already present'}: {p}")

    print("Installation complete.")


if __name__ == "__main__":
    main()
