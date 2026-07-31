is_interactive || return

setup_grep_alias() {
  local options
  options=

  if printf 'dotfiles-grep-test\n' | command grep -I -q dotfiles-grep-test >/dev/null 2>&1; then
    options="$options -I"
  fi
  if printf 'dotfiles-grep-test\n' | command grep --color=auto -q dotfiles-grep-test >/dev/null 2>&1; then
    options="$options --color=auto"
  fi
  if printf 'dotfiles-grep-test\n' | command grep --exclude=tags -q dotfiles-grep-test >/dev/null 2>&1; then
    options="$options --exclude=tags"
  fi
  if printf 'dotfiles-grep-test\n' | command grep '--exclude=*~' -q dotfiles-grep-test >/dev/null 2>&1; then
    options="$options --exclude='*~'"
  fi
  if printf 'dotfiles-grep-test\n' | command grep '--exclude-dir=.[^.]*' -q dotfiles-grep-test >/dev/null 2>&1; then
    options="$options --exclude-dir='.[^.]*'"
  fi

  alias "grep=grep$options"
}

setup_grep_alias
unset -f setup_grep_alias
