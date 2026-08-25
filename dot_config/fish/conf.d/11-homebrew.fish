status is-login; or return

if command -q brew
  set -l brew_prefix (brew --prefix)
  set -l gnubins (command find "$brew_prefix/opt" -type d -path '*/libexec/gnubin' -print -prune 2>/dev/null)
  test (count $gnubins) -eq 0; or fish_add_path --global --path $gnubins
  if command -q manpath
    set -l gnumans (command find "$brew_prefix/opt" -type d -path '*/libexec/gnuman' -print -prune 2>/dev/null)
    set --global --export --path MANPATH $gnumans (manpath)
  end
  set --global --export HOMEBREW_AUTO_UPDATE_SECS 604800
end
