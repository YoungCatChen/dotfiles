is_interactive || return

__dotfiles_set_bash_prompt() {
  local last_status=$?
  local prompt_mark='\$'

  if [ -t 1 ] && [ "${TERM:-dumb}" != dumb ]; then
    local gray='\[\e[1;30m\]'
    local red='\[\e[0;31m\]'
    local white='\[\e[0;37m\]'
    local yellow='\[\e[0;33m\]'
    local blue='\[\e[0;34m\]'
    local bright='\[\e[1;37m\]'
    local reset='\[\e[0m\]'
    local status_color=$gray
    [ "$last_status" -eq 0 ] || status_color=$red
    PS1="${status_color}?=${last_status} ${red}\u${white}@${yellow}\h ${blue}\w ${bright}${prompt_mark} ${reset}"
    PS1+='\[\e]0;\u@\h \W\a\]'
  else
    PS1="?=${last_status} \u@\h \w ${prompt_mark} "
  fi
}

case ";${PROMPT_COMMAND:-};" in
  *';__dotfiles_set_bash_prompt;'*) ;;
  *) PROMPT_COMMAND="__dotfiles_set_bash_prompt${PROMPT_COMMAND:+;$PROMPT_COMMAND}" ;;
esac
