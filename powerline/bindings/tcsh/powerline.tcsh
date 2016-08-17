# http://unix.stackexchange.com/questions/4650/determining-path-to-sourced-shell-script:
# > In tcsh, $_ at the beginning of the script will contain the location if the
# > file was sourced and $0 contains it if it was run.
#
# Guess this relies on `$_` being set as to last argument to previous command 
# which must be `.` or `source` in this case
set POWERLINE_SOURCED=($_)
if ! $?POWERLINE_CONFIG_COMMAND then
	if ( { which powerline-config > /dev/null } ) then
		set POWERLINE_CONFIG_COMMAND="powerline-config"
	else
		set POWERLINE_CONFIG_COMMAND="$POWERLINE_SOURCED[2]:h:h:h:h/scripts/powerline-config"
	endif
else
	if "$POWERLINE_CONFIG_COMMAND" == "" then
		if ( { which powerline-config > /dev/null } ) then
			set POWERLINE_CONFIG_COMMAND="powerline-config"
		else
			set POWERLINE_CONFIG_COMMAND="$POWERLINE_SOURCED[2]:h:h:h:h/scripts/powerline-config"
		endif
	endif
endif
if ( { $POWERLINE_CONFIG_COMMAND shell --shell=tcsh uses tmux } ) then
	if ( $?TMUX_PANE ) then
		if ( "$TMUX_PANE" == "" ) then
			set _POWERLINE_TMUX_PANE="`tmux display -p '#D'`"
		else
			set _POWERLINE_TMUX_PANE="$TMUX_PANE"
		endif
	else
		set _POWERLINE_TMUX_PANE="`tmux display -p '#D'`"
	endif
	set _POWERLINE_TMUX_PANE="`echo $_POWERLINE_TMUX_PANE:q | tr -d '% '`"
	alias _powerline_tmux_set_pwd 'if ( $?TMUX && { tmux refresh -S >&/dev/null } ) tmux setenv -g TMUX_PWD_$_POWERLINE_TMUX_PANE $PWD:q ; if ( $?TMUX ) tmux refresh -S >&/dev/null'
	alias cwdcmd "`alias cwdcmd` ; _powerline_tmux_set_pwd"
endif
if ( { $POWERLINE_CONFIG_COMMAND shell --shell=tcsh uses prompt } ) then
	if ! $?POWERLINE_COMMAND then
		set POWERLINE_COMMAND="`$POWERLINE_CONFIG_COMMAND:q shell command`"
	else
		if "$POWERLINE_COMMAND" == "" then
			set POWERLINE_COMMAND="`$POWERLINE_CONFIG_COMMAND:q shell command`"
		endif
	endif
	if ! $?POWERLINE_COMMAND_ARGS then
		set POWERLINE_COMMAND_ARGS=""
	endif

	if ( $?POWERLINE_NO_TCSH_ABOVE || $?POWERLINE_NO_SHELL_ABOVE ) then
		alias _powerline_above true
	else
		alias _powerline_above '$POWERLINE_COMMAND:q $POWERLINE_COMMAND_ARGS shell above --renderer-arg=client_id=$$ --last-exit-code=$POWERLINE_STATUS --width=$POWERLINE_COLUMNS'
	endif

	alias _powerline_set_prompt 'set prompt="`$POWERLINE_COMMAND:q $POWERLINE_COMMAND_ARGS shell left -r .tcsh --renderer-arg=client_id=$$ --last-exit-code=$POWERLINE_STATUS --width=$POWERLINE_COLUMNS`"'
	alias _powerline_set_rprompt 'set rprompt="`$POWERLINE_COMMAND:q $POWERLINE_COMMAND_ARGS shell right -r .tcsh --renderer-arg=client_id=$$ --last-exit-code=$POWERLINE_STATUS --width=$POWERLINE_COLUMNS`"'
	alias _powerline_set_columns 'set POWERLINE_COLUMNS=`stty size|cut -d" " -f2` ; set POWERLINE_COLUMNS=`expr $POWERLINE_COLUMNS - 2`'

	alias precmd 'set POWERLINE_STATUS=$? ; '"`alias precmd`"' ; _powerline_set_columns ; _powerline_above ; _powerline_set_prompt ; _powerline_set_rprompt'
endif
