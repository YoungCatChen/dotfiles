status is-interactive; or return

# Vim related shortcuts.
# To be in sync with `vim.sh`.

command -q vim || return

abbr -a vi     vim
abbr -a vidiff vimdiff
abbr -a viless vimless
abbr -a viin   vimin
abbr -a vihead vimhead
abbr -a vitail vimtail

function vimhead; head -n 10000 $argv 2>&1 | vimless; end
function vimtail; tail -n 10000 $argv 2>&1 | vimless; end

function view
  if test (count $argv) = 0
    vim -R -c 'set mouse= | let no_plugin_maps=1' \
      $POSITION -
  else
    vim -R -c 'set mouse= | let no_plugin_maps=1' \
      $POSITION $argv
  end
end

function vimless
  # Shell script to start Vim with less.vim.
  # Read stdin if no arguments were given.

  if test (count $argv) = 0
    vim -c 'set mouse= | let no_plugin_maps=1 | runtime! macros/less.vim' \
      $POSITION -
  else
    vim -c 'set mouse= | let no_plugin_maps=1 | runtime! macros/less.vim' \
      $POSITION $argv
  end
end
