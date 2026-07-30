function verbosecmd
  set -l intent $argv[1]
  set --erase argv[1]
  echo
  highlight-echo $intent
  highlight-echo "# $argv" >&2
  command $argv
end
