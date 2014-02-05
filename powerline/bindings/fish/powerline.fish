if test -z $POWERLINE_COMMAND
    if which powerline-client >/dev/null ^&1
        set -x POWERLINE_COMMAND powerline-client
    else if which powerline >/dev/null ^&1
        set -x POWERLINE_COMMAND powerline
    else
        set -x POWERLINE_COMMAND (dirname (status -f))"/../../../scripts/powerline"
    end
end

function _powerline_tmux_setenv
    if test -n $TMUX
        tmux setenv -g "TMUX_$1_"(tmux display -p "#D" ^/dev/null | tr -d %) "$2" ^/dev/null
        tmux refresh -S ^/dev/null
    end
end

set POWERLINE_SAVED_PWD ""

function _powerline_tmux_set_pwd
    if test "x$POWERLINE_SAVED_PWD" != "x$PWD"
        set POWERLINE_SAVED_PWD "$PWD"
        _powerline_tmux_setenv PWD "$PWD"
    end
end

function -s WINCH _powerline_tmux_set_columns
    _powerline_tmux_setenv COLUMNS "$COLUMNS"
end

function fish_prompt
    set -l last_exit_code $status
    eval $POWERLINE_COMMAND shell left -r fish_prompt --last_exit_code=$last_exit_code --jobnum=(jobs -p|wc -l)
    _powerline_tmux_set_pwd
    return $last_exit_code
end

_powerline_tmux_set_columns
