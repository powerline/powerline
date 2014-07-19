# http://unix.stackexchange.com/questions/4650/determining-path-to-sourced-shell-script:
# > In tcsh, $_ at the beginning of the script will contain the location if the
# > file was sourced and $0 contains it if it was run.
#
# Guess this relies on `$_` being set as to last argument to previous command 
# which must be `.` or `source` in this case
set POWERLINE_SOURCED=($_)
if ! ( $?POWERLINE_NO_TCSH_TMUX_SUPPORT || $?POWERLINE_NO_SHELL_TMUX_SUPPORT ) then
	alias _powerline_tmux_set_pwd 'if ( $?TMUX && { tmux refresh -S >&/dev/null } ) tmux setenv -g TMUX_PWD_`tmux display -p "#D" | tr -d %` $PWD:q ; if ( $?TMUX ) tmux refresh -S >&/dev/null'
	alias cwdcmd "`alias cwdcmd` ; _powerline_tmux_set_pwd"
endif
if ! ( $?POWERLINE_NO_TCSH_PROMPT || $?POWERLINE_NO_SHELL_PROMPT ) then
	if ! $?POWERLINE_COMMAND then
		if ( { which powerline-client > /dev/null } ) then
			setenv POWERLINE_COMMAND powerline-client
		else if ( { which powerline > /dev/null } ) then
			setenv POWERLINE_COMMAND powerline
		else
			setenv POWERLINE_COMMAND $POWERLINE_SOURCED:h:h:h:h:q/scripts/powerline
		endif
	endif

	if ( $?POWERLINE_NO_TCSH_ABOVE || $?POWERLINE_NO_SHELL_ABOVE ) then
		alias _powerline_above true
	else
		alias _powerline_above '$POWERLINE_COMMAND shell above --last_exit_code=$POWERLINE_STATUS --width=$POWERLINE_COLUMNS'
	endif

	alias _powerline_set_prompt 'set prompt="`$POWERLINE_COMMAND shell left -r tcsh_prompt --last_exit_code=$POWERLINE_STATUS --width=$POWERLINE_COLUMNS`"'
	alias _powerline_set_rprompt 'set rprompt="`$POWERLINE_COMMAND shell right -r tcsh_prompt --last_exit_code=$POWERLINE_STATUS --width=$POWERLINE_COLUMNS` "'
	alias _powerline_set_columns 'set POWERLINE_COLUMNS=`stty size|cut -d" " -f2` ; set POWERLINE_COLUMNS=`expr $POWERLINE_COLUMNS - 2`'

	alias precmd 'set POWERLINE_STATUS=$? ; '"`alias precmd`"' ; _powerline_set_columns ; _powerline_above ; _powerline_set_prompt ; _powerline_set_rprompt'
endif
