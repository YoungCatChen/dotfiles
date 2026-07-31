is_login || return

setup_login_environment() {
  local dir
  for dir in \
    /sbin \
    /usr/sbin \
    /bin \
    /usr/bin \
    /usr/local/sbin \
    /usr/local/bin \
    /opt/homebrew/sbin \
    /opt/homebrew/bin \
    "$HOME/go/bin" \
    "$HOME/.local/bin" \
    "$HOME/usr/sbin" \
    "$HOME/usr/bin" \
    "$HOME/bin"; do
    case ":$PATH:" in
      *":$dir:"*) ;;
      *) PATH="$dir${PATH:+:$PATH}" ;;
    esac
  done
  export PATH

  : "${LANG:=en_US.UTF-8}"
  : "${LANGUAGE:=en_US:en}"
  : "${TIME_STYLE:=iso}"
  export LANG LANGUAGE TIME_STYLE

  if command -v nvim >/dev/null 2>&1; then
    EDITOR=nvim
  else
    EDITOR=vim
  fi
  export EDITOR

  if command -v lesspipe.sh >/dev/null 2>&1; then
    LESSOPEN='|lesspipe.sh %s'
    export LESSOPEN
  fi
}

setup_login_environment
unset -f setup_login_environment
