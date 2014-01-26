# http://unix.stackexchange.com/questions/4650/determining-path-to-sourced-shell-script:
# > In tcsh, $_ at the beginning of the script will contain the location if the
# > file was sourced and $0 contains it if it was run.
#
# Guess this relies on `$_` being set as to last argument to previous command 
# which must be `.` or `source` in this case
set POWERLINE_SOURCED=($_)
if ! $?POWERLINE_COMMAND then
	if ( { which powerline-client > /dev/null } ) then
		setenv POWERLINE_COMMAND powerline-client
	else if ( { which powerline > /dev/null } ) then
		setenv POWERLINE_COMMAND powerline
	else
		setenv POWERLINE_COMMAND $POWERLINE_SOURCED:h:h:h:h:q/scripts/powerline
	endif
endif
alias _powerline_tmux_set_pwd 'if $?TMUX tmux setenv -g TMUX_PWD_`tmux display -p "#D" | tr -d %` $PWD:q ; if $?TMUX tmux refresh -S'
alias _powerline_set_prompt 'set prompt="`$POWERLINE_COMMAND shell left -r tcsh_prompt --last_exit_code=$?`"'
alias _powerline_set_rprompt 'set rprompt="`$POWERLINE_COMMAND shell right -r tcsh_prompt --last_exit_code=$?` "'
alias cwdcmd "`alias cwdcmd` ; _powerline_tmux_set_pwd"
alias precmd "`alias precmd` ; _powerline_set_prompt ; _powerline_set_rprompt"
