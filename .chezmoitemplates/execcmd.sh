execcmd() {
  local color arg

  if [ "$#" -eq 0 ]; then
    printf 'usage: execcmd command [argument ...]\n' >&2
    return 2
  fi

  color=false
  if [ -t 2 ] && [ "${TERM:-dumb}" != dumb ]; then
    printf '\033[1;33m' >&2
    color=true
  fi

  printf '#' >&2
  for arg do
    printf " '" >&2
    printf '%s' "$arg" | sed "s/'/'\\\\''/g" >&2
    printf "'" >&2
  done

  if [ "$color" = true ]; then
    printf '\033[0m' >&2
  fi
  printf '\n' >&2
  command "$@"
}
