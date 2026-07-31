is_interactive || return

: "${CD_HISTORY_SIZE:=50}"

__dotfiles_cd_remove_current_duplicates() {
  local index
  for ((index = ${#DIRSTACK[@]} - 1; index >= 1; index--)); do
    if [ "${DIRSTACK[$index]}" = "$PWD" ]; then
      builtin popd -n +"$index" >/dev/null || break
    fi
  done
}

cd() {
  local old_pwd=$PWD
  builtin cd "$@" || return
  [ "$PWD" != "$old_pwd" ] || return 0

  builtin pushd -n "$old_pwd" >/dev/null || return
  __dotfiles_cd_remove_current_duplicates

  case $CD_HISTORY_SIZE in
    ''|*[!0-9]*) CD_HISTORY_SIZE=50 ;;
  esac
  if [ "$CD_HISTORY_SIZE" -gt 0 ]; then
    while [ "${#DIRSTACK[@]}" -gt "$CD_HISTORY_SIZE" ]; do
      builtin popd -n -0 >/dev/null || break
    done
  fi
}

cdh() {
  builtin dirs -l -v
}
