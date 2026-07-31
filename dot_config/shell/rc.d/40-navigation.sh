is_interactive || return

if is_bash; then
  alias -- -='cd -'
else
  alias -='cd -'
fi
alias cd-='cd -'
alias cd.='cd .'
alias cd..='cd ..'
alias cd...='cd ../..'
alias cd....='cd ../../..'
alias cd.....='cd ../../../..'
alias cd......='cd ../../../../..'
alias cd.......='cd ../../../../../..'
alias cd........='cd ../../../../../../..'
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias .....='cd ../../../..'
alias ......='cd ../../../../..'
alias .......='cd ../../../../../..'
alias ........='cd ../../../../../../..'

gitroot() {
  cd "$(git rev-parse --show-toplevel)" || return
}
