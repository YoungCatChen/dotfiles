if command -q dircolors
  dircolors -c | source
else if not set --query LS_COLORS
  set --global --export LS_COLORS 'di=01;34:ln=01;36:so=01;35:pi=33:ex=01;32:bd=01;33:cd=01;33'
end
if not string match --quiet -- '*:*.img=01;31:*' ":$LS_COLORS:"
  set --global --export LS_COLORS "$LS_COLORS:*.img=01;31:*.iso=01;31"
end

status is-interactive; or return

function setup_ls_alias
  set --local ls_command ls
  set --local options
  if command -q gls
    set ls_command gls
  end

  if command $ls_command --group-directories-first / &>/dev/null
    set --append options --group-directories-first
  end
  if command $ls_command --color=auto / &>/dev/null
    set --append options --color=auto
  else if contains -- (uname -s 2>/dev/null) Darwin FreeBSD
    if command $ls_command -G / &>/dev/null
      set --append options -G
      set --global --export CLICOLOR 1
    end
  end
  if command $ls_command -F / &>/dev/null
    set --append options -F
  end

  set --local definition \
    (string join -- ' ' command $ls_command (string escape -- $options))
  alias ls $definition
end

setup_ls_alias
functions --erase setup_ls_alias
