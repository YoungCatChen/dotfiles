# Shared dispatcher for Bash, Dash, and BusyBox ash.

if [ "${DOTFILES_SHELL_INITIALIZED:-}" = 1 ]; then
  return
fi

case ${DOTFILES_SHELL_LOGIN:-0} in
  1) DOTFILES_MODE_LOGIN=1 ;;
  *) DOTFILES_MODE_LOGIN=0 ;;
esac
case $- in
  *i*) DOTFILES_MODE_INTERACTIVE=1 ;;
  *) DOTFILES_MODE_INTERACTIVE=0 ;;
esac
if [ -n "${BASH_VERSION:-}" ]; then
  DOTFILES_MODE_BASH=1
else
  DOTFILES_MODE_BASH=0
fi

is_login() {
  [ "$DOTFILES_MODE_LOGIN" = 1 ]
}

is_interactive() {
  [ "$DOTFILES_MODE_INTERACTIVE" = 1 ]
}

is_bash() {
  [ "$DOTFILES_MODE_BASH" = 1 ]
}

DOTFILES_SHELL_INITIALIZED=1

if ! is_login && ! is_interactive; then
  return
fi

load_shell_fragments() {
  local dir file
  dir="$HOME/.config/shell/rc.d"
  for file in "$dir"/*; do
    [ -r "$file" ] || continue
    case $file in
      *.sh) . "$file" ;;
      *.bash) is_bash && . "$file" ;;
    esac
  done
}

load_shell_fragments
unset -f load_shell_fragments
