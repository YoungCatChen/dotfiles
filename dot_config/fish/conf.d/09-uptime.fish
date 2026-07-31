status is-login; or return
status is-interactive; or return

if command -q uptime
  printf 'uptime: '
  command uptime
end
