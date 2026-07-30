status is-interactive; or return

function __print_duration_record_start_time --on-event fish_preexec
  set -g __print_duration_start_time (date '+%m-%d %H:%M:%S')
end

function __print_duration --on-event fish_postexec
  if [ $CMD_DURATION -lt 10000 ]
    return
  end

  set -l end_time (date '+%m-%d %H:%M:%S')
  set -l sec (math "round($CMD_DURATION / 1000) % 60")
  set -l min (math "floor($CMD_DURATION / 60000) % 60")
  set -l hrs (math "floor($CMD_DURATION / 3600000)")
  set -l w (set_color white)
  set -l r (set_color brred)
  set -l y (set_color bryellow)
  set -l g (set_color brgreen)
  set -l b (set_color --bold)
  set -l n (set_color normal)

  printf "$b$r❮$y❮$g❮$w ELAPSED:$n %d:%02d:%02d.$b$w START:$n %s.$b$w END:$n %s. $b$g❯$y❯$r❯$n\n" $hrs $min $sec $__print_duration_start_time $end_time
end
