# Attaches helpful flags to `pstree`, when supported.
# To keep functionality in sync with `pstree.sh`.

function helpdoc_contains
  string match -q '* '"$argv[1]"' *' $helpdoc
end

set -g helpdoc (command pstree --help 2>&1)

set -l hide       # hide threads, show only processes
set -l highlight  # highlight current process and its ancestors
set -l thisproc   # show only current process and its ancestors
set -l uid        # show uid transitions

helpdoc_contains --hide-threads  && set hide --hide-threads
helpdoc_contains --highlight-all && set highlight --highlight-all
helpdoc_contains '-p pid'        && set thisproc -p '$fish_pid'
helpdoc_contains --uid-changes   && set uid --uid-changes

set -l unicode  # use graphics chars for tree drawing characters
if helpdoc_contains '-g n'
  set unicode -g3
else if helpdoc_contains --unicode
  set unicode --unicode
end

set -l user  # show only branches containing processes of <user>
if helpdoc_contains '-u user'
  set user "-u $USER"
else if helpdoc_contains 'PID | USER'
  set user $USER
end

functions --erase helpdoc_contains
set --erase helpdoc

alias pstree="pstree $hide $highlight $uid $unicode"
alias pstreeme="pstree $user"
alias pstreethis="pstree $thisproc"
