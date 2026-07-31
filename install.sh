#!/bin/sh
set -eu

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if ! command -v chezmoi >/dev/null 2>&1; then
  mkdir -p "$HOME/.local/bin"
  sh -c "$(curl -fsLS get.chezmoi.io)" -- -b "$HOME/.local/bin"
  PATH="$HOME/.local/bin:$PATH"
fi

config_file=$(chezmoi execute-template '{{ .chezmoi.configFile }}')
if [ -f "$config_file" ]; then
  chezmoi --source "$repo_dir" init --apply
elif [ -n "${DOTFILES_MACHINE_ROLES:-}" ] && [ -n "${DOTFILES_MACHINE_TRAITS:-}" ]; then
  chezmoi --source "$repo_dir" init --apply --promptDefaults \
    --promptMultichoice "Machine roles=$DOTFILES_MACHINE_ROLES,Machine traits=$DOTFILES_MACHINE_TRAITS"
elif [ -n "${DOTFILES_MACHINE_ROLES:-}" ]; then
  chezmoi --source "$repo_dir" init --apply --promptDefaults \
    --promptMultichoice "Machine roles=$DOTFILES_MACHINE_ROLES"
else
  chezmoi --source "$repo_dir" init --apply
fi
