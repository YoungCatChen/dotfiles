alias -- -='cd -'
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias l='ls'
alias ll='ls -lh'
alias la='ls -lAh'
alias watch='watch -e -n1'

gitroot() {
  cd "$(git rev-parse --show-toplevel)" || return
}

for line_count in 20 30 40 50 100 1000 10000; do
  alias "head$line_count=head -n $line_count"
  alias "tail$line_count=tail -n $line_count"
done
unset line_count
