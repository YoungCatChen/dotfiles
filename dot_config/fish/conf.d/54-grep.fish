status is-interactive; or return

function setup_grep_alias
  set --local options
  for option in -I --color=auto --exclude=tags '--exclude=*~' '--exclude-dir=.[^.]*'
    if printf 'dotfiles-grep-test\n' |
        command grep $option -q dotfiles-grep-test &>/dev/null
      set --append options $option
    end
  end

  set --local definition \
    (string join -- ' ' command grep (string escape -- $options))

  # No `--wraps`, to avoid infinite recursion on command completion.
  # Can't use `alias` because it always includes `--wraps`.
  echo "function grep; $definition \$argv; end" | source
end

setup_grep_alias
functions --erase setup_grep_alias
