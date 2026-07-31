is_interactive || return

setup_head_tail_aliases() {
  local line_count
  for line_count in 20 30 40 50 100 1000 10000; do
    alias "head$line_count=head -n $line_count"
    alias "tail$line_count=tail -n $line_count"
  done
}

setup_head_tail_aliases
unset -f setup_head_tail_aliases
