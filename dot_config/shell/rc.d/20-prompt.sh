# Portable prompt. Bash replaces this with a richer prompt in 21-prompt.bash.
is_interactive || return

setup_prompt() {
  local user host mark esc bel begin end exe
  local gray red white yellow blue bright reset title

  user=${USER:-$(id -un 2>/dev/null || printf '?')}
  host=$(hostname 2>/dev/null || printf '?')
  host=${host%%.*}
  if [ "$(id -u 2>/dev/null)" = 0 ]; then
    mark='#'
  else
    mark='$'
  fi

  if [ -t 1 ] && [ "${TERM:-dumb}" != dumb ]; then
    esc=$(printf '\033')
    bel=$(printf '\007')
    begin=
    end=
    exe=$(readlink "/proc/$$/exe" 2>/dev/null || :)
    case $exe in
      */busybox)
        begin='\['
        end='\]'
        ;;
    esac
    gray="${begin}${esc}[1;30m${end}"
    red="${begin}${esc}[0;31m${end}"
    white="${begin}${esc}[0;37m${end}"
    yellow="${begin}${esc}[0;33m${end}"
    blue="${begin}${esc}[0;34m${end}"
    bright="${begin}${esc}[1;37m${end}"
    reset="${begin}${esc}[0m${end}"
    title="${begin}${esc}]0;${user}@${host} \${PWD##*/}${bel}${end}"
    PS1="${gray}"'?=$?'" ${red}${user}${white}@${yellow}${host} ${blue}"'$PWD '"${bright}${mark} ${reset}${title}"
  else
    PS1='?=$?'" ${user}@${host}"' $PWD '"${mark} "
  fi
}

setup_prompt
unset -f setup_prompt
