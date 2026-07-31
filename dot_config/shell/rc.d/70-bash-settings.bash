is_interactive || return

shopt -s cdspell checkwinsize cmdhist histappend interactive_comments
HISTCONTROL=ignoredups:ignorespace
HISTSIZE=100000
HISTFILESIZE=200000
HISTTIMEFORMAT='%Y-%m-%d %H:%M:%S  '

load_bash_completions() {
  local file
  for file in \
    /etc/bash_completion \
    /usr/local/etc/bash_completion \
    "$HOME/usr/etc/bash_completion"; do
    [ -r "$file" ] && . "$file"
  done
}

load_bash_completions
unset -f load_bash_completions

if command -v direnv >/dev/null 2>&1; then
  eval "$(direnv hook bash)"
fi

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
