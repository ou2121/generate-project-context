#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: install_context.sh [--download-generate URL]
Options:
  --download-generate URL   Download generate.py from URL into .context/
  -h, --help                Show this help message
USAGE
}

ROOT="$(cd "$(dirname "$0")/.." && pwd -P)"
CONTEXT_DIR="$ROOT/.context"
GENERATED_DIR="$CONTEXT_DIR/generated"
GITIGNORE_FILE="$ROOT/.gitignore"
GENERATE_DEST="$CONTEXT_DIR/generate.py"
DOWNLOAD_URL=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --download-generate)
      if [[ -z "${2-}" || "${2-}" == --* ]]; then
        echo "Error: --download-generate requires a URL." >&2
        exit 2
      fi
      DOWNLOAD_URL="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Error: Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

printf "Project root: %s\n" "$ROOT"
mkdir -p "$GENERATED_DIR"
printf "Ensured directory: %s\n" "$GENERATED_DIR"

download_file() {
  local url="$1" dest="$2"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$url" -o "$dest"
    return $?
  fi
  if command -v wget >/dev/null 2>&1; then
    wget -qO "$dest" "$url"
    return $?
  fi
  return 127
}

if [[ -n "$DOWNLOAD_URL" ]]; then
  printf "Attempting to download generate.py from: %s\n" "$DOWNLOAD_URL"
  if download_file "$DOWNLOAD_URL" "$GENERATE_DEST"; then
    chmod +x "$GENERATE_DEST" 2>/dev/null || true
    printf "Downloaded and saved to: %s\n" "$GENERATE_DEST"
  else
    echo "Warning: failed to download generate.py (curl/wget unavailable or fetch failed)." >&2
  fi
fi

if [[ ! -f "$GITIGNORE_FILE" ]]; then
  printf "# .gitignore created by install_context.sh\n\n" > "$GITIGNORE_FILE"
  echo "Created $GITIGNORE_FILE"
fi

PATTERNS=(
  ".context/generated/"
  "**/generated/"
)

for p in "${PATTERNS[@]}"; do
  if ! grep -Fqx -- "$p" "$GITIGNORE_FILE"; then
    # Ensure file ends with newline
    if [[ -s "$GITIGNORE_FILE" && "$(tail -c1 "$GITIGNORE_FILE")" != "" ]]; then
      printf "\n" >> "$GITIGNORE_FILE"
    fi
    printf "%s\n" "$p" >> "$GITIGNORE_FILE"
    printf "Added '%s' to %s\n" "$p" "$GITIGNORE_FILE"
  else
    printf "Already present in %s: %s\n" "$GITIGNORE_FILE" "$p"
  fi
done

echo "Installation complete."
