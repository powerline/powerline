# http://unix.stackexchange.com/questions/4650/determining-path-to-sourced-shell-script:
# > In tcsh, $_ at the beginning of the script will contain the location if the
# > file was sourced and $0 contains it if it was run.
#
# Guess this relies on `$_` being set as to last argument to previous command 
# which must be `.` or `source` in this case
set POWERLINE_SOURCED=($_)
if ! $?POWERLINE_CONFIG then
	if ( { which powerline-config > /dev/null } ) then
		set POWERLINE_CONFIG="powerline-config"
	else
		set POWERLINE_CONFIG="$POWERLINE_SOURCED[2]:h:h:h:h/scripts/powerline-config"
	endif
else
	if "$POWERLINE_CONFIG" == "" then
		if ( { which powerline-config > /dev/null } ) then
			set POWERLINE_CONFIG="powerline-config"
		else
			set POWERLINE_CONFIG="$POWERLINE_SOURCED[2]:h:h:h:h/scripts/powerline-config"
		endif
	endif
endif
if ( { $POWERLINE_CONFIG shell --shell=tcsh uses tmux } ) then
	alias _powerline_tmux_set_pwd 'if ( $?TMUX && { tmux refresh -S >&/dev/null } ) tmux setenv -g TMUX_PWD_`tmux display -p "#D" | tr -d %` $PWD:q ; if ( $?TMUX ) tmux refresh -S >&/dev/null'
	alias cwdcmd "`alias cwdcmd` ; _powerline_tmux_set_pwd"
endif
if ( { $POWERLINE_CONFIG shell --shell=tcsh uses prompt } ) then
	if ! $?POWERLINE_COMMAND then
		set POWERLINE_COMMAND="`$POWERLINE_CONFIG:q shell command`"
	else
		if "$POWERLINE_COMMAND" == "" then
			set POWERLINE_COMMAND="`$POWERLINE_CONFIG:q shell command`"
		endif
	endif

	if ( $?POWERLINE_NO_TCSH_ABOVE || $?POWERLINE_NO_SHELL_ABOVE ) then
		alias _powerline_above true
	else
		alias _powerline_above '$POWERLINE_COMMAND shell above --renderer_arg=client_id=$$ --last_exit_code=$POWERLINE_STATUS --width=$POWERLINE_COLUMNS'
	endif

	alias _powerline_set_prompt 'set prompt="`$POWERLINE_COMMAND shell left -r .tcsh --renderer_arg=client_id=$$ --last_exit_code=$POWERLINE_STATUS --width=$POWERLINE_COLUMNS`"'
	alias _powerline_set_rprompt 'set rprompt="`$POWERLINE_COMMAND shell right -r .tcsh --renderer_arg=client_id=$$ --last_exit_code=$POWERLINE_STATUS --width=$POWERLINE_COLUMNS` "'
	alias _powerline_set_columns 'set POWERLINE_COLUMNS=`stty size|cut -d" " -f2` ; set POWERLINE_COLUMNS=`expr $POWERLINE_COLUMNS - 2`'

	alias precmd 'set POWERLINE_STATUS=$? ; '"`alias precmd`"' ; _powerline_set_columns ; _powerline_above ; _powerline_set_prompt ; _powerline_set_rprompt'
endif
