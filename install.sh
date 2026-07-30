#!/bin/sh
set -eu

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if ! command -v chezmoi >/dev/null 2>&1; then
  mkdir -p "$HOME/.local/bin"
  sh -c "$(curl -fsLS get.chezmoi.io)" -- -b "$HOME/.local/bin"
  PATH="$HOME/.local/bin:$PATH"
fi

chezmoi --source "$repo_dir" apply
