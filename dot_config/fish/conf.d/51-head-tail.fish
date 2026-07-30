status is-interactive; or return

# Adds abbrs like head20, head100, tail50 etc.
# To keep functionality similar with `head-tail.sh`.

function __head_tail_lines
  string replace --regex '(\d)' ' -n $1' $argv[1]
end

abbr --add head_lines --position command --regex 'head\d+' --function __head_tail_lines
abbr --add tail_lines --position command --regex 'tail\d+' --function __head_tail_lines
