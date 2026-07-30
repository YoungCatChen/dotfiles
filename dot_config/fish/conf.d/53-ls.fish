status is-interactive; or return

if command ls --group-directories-first / &> /dev/null
  functions --copy ls __fish_ls
  function ls
    __fish_ls --group-directories-first $argv
  end
end
