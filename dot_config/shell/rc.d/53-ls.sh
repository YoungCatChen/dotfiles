is_login || is_interactive || return

if command -v dircolors >/dev/null 2>&1; then
  eval "$(dircolors -b 2>/dev/null)"
elif [ -z "${LS_COLORS+x}" ]; then
  LS_COLORS='di=01;34:ln=01;36:so=01;35:pi=33:ex=01;32:bd=01;33:cd=01;33'
  export LS_COLORS
fi
case ":${LS_COLORS:-}:" in
  *':*.img=01;31:'*) ;;
  *) LS_COLORS="${LS_COLORS:+$LS_COLORS:}*.img=01;31:*.iso=01;31" ;;
esac
export LS_COLORS

is_interactive || return

setup_ls_alias() {
  local options os
  options=

  if command ls --group-directories-first / >/dev/null 2>&1; then
    options="$options --group-directories-first"
  fi
  if command ls --color=auto / >/dev/null 2>&1; then
    options="$options --color=auto"
  else
    os=$(uname -s 2>/dev/null)
    case $os in
      Darwin|FreeBSD)
        if command ls -G / >/dev/null 2>&1; then
          options="$options -G"
          CLICOLOR=1
          export CLICOLOR
        fi
        ;;
    esac
  fi
  if command ls -F / >/dev/null 2>&1; then
    options="$options -F"
  fi

  alias "ls=ls$options"
}

setup_ls_alias
unset -f setup_ls_alias
