#!/bin/sh
set -eu

force=
for arg do
  case $arg in
    --force) force=1 ;;
    *) echo "usage: $0 [--force]" >&2; exit 2 ;;
  esac
done

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if ! command -v chezmoi >/dev/null 2>&1; then
  mkdir -p "$HOME/.local/bin"
  sh -c "$(curl -fsLS get.chezmoi.io)" -- -b "$HOME/.local/bin"
  PATH="$HOME/.local/bin:$PATH"
fi

chezmoi --source "$repo_dir" apply ${force:+--force}
