status is-interactive; or return

abbr --add l ls
abbr --add ll 'ls -lh'
abbr --add la 'ls -lAh'
abbr --add l. 'ls -d .*'
abbr --add ll. 'ls -lh -d .*'

abbr --add pse 'ps -e'
abbr --add psef 'ps -ef'
abbr --add psme "ps -u '$USER'"
abbr --add psmef "ps -u '$USER' -f"

abbr --add scr 'screen -S'
abbr --add lsscr 'screen -ls'
abbr --add xscr 'screen -x'

abbr --add watch 'watch -e -n1'
abbr --add watchcolor 'watch -e -n1 -c'
abbr --add watchdiff 'watch -e -n1 -c --differences=cumulative'

abbr --add langposix 'langset POSIX POSIX'
abbr --add langzh 'langset zh_CN.UTF-8 zh_CN:zh'
abbr --add langen 'langset en_US.UTF-8 en_US:en'
