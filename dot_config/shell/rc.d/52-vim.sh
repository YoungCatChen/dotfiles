is_interactive || return

if command -v vim >/dev/null 2>&1; then
  vi() { command vim "$@"; }
  vidiff() { command vimdiff "$@"; }
  viless() { vimless "$@"; }
  viin() { command vimin "$@"; }
  vihead() { vimhead "$@"; }
  vitail() { vimtail "$@"; }
  vimhead() { head -n 10000 "$@" 2>&1 | vimless; }
  vimtail() { tail -n 10000 "$@" 2>&1 | vimless; }

  view() {
    if [ "$#" -eq 0 ]; then
      set -- -
    fi
    command vim -R -c 'set mouse= | let no_plugin_maps=1' \
      ${POSITION:+"$POSITION"} "$@"
  }

  vimless() {
    if [ "$#" -eq 0 ]; then
      set -- -
    fi
    command vim -c 'set mouse= | let no_plugin_maps=1 | runtime! macros/less.vim' \
      ${POSITION:+"$POSITION"} "$@"
  }
fi
