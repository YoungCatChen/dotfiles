#!/bin/sh
set -eu

old_command="$HOME/.local/bin/dotfiles"
if [ -f "$old_command" ] &&
  grep -Fq '.config/dotfiles/sources.d' "$old_command" &&
  grep -Fq 'dotfiles: no registered source states found' "$old_command"; then
  rm -f -- "$old_command"
fi
