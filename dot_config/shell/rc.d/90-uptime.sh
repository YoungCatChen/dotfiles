is_login || return
is_interactive || return

if command -v uptime >/dev/null 2>&1; then
  printf 'uptime: '
  command uptime
fi
