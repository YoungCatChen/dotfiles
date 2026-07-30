# Fixes the global screen completions.

source $__fish_data_dir/completions/screen.fish

# -x can attach to detached screens too.
complete -c screen -o x -d 'Multi attach' -a '(__fish_complete_screen)' -x

# Should use /usr/bin/stat to avoid using Homebrow stat.
function __fish_complete_screen_general_list_mac -d "Get the socket list on mac"
    pushd $__fish_screen_socket_dir >/dev/null
    set -l sockets (ls)
    if test (count $sockets) -ne 0
        switch $argv
            case Detached
                /usr/bin/stat -f "%Lp %SB %N" -t "%D %T" $sockets | string match -r '^6\d{2} .*$' | string replace -r '^6\d{2} (\S+ \S+) (\S+)' '$2\t$1 Detached'
            case Attached
                /usr/bin/stat -f "%Lp %SB %N" -t "%D %T" $sockets | string match -r '^7\d{2} .*$' | string replace -r '^7\d{2} (\S+ \S+) (\S+)' '$2\t$1 Attached'
        end
    end
    popd >/dev/null
end
