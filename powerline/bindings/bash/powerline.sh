if test -z "${POWERLINE_COMMAND}" ; then
	if which powerline-client &>/dev/null ; then
		export POWERLINE_COMMAND=powerline-client
	else
		export POWERLINE_COMMAND=powerline
	fi
fi

_powerline_tmux_setenv() {
	if [[ -n "$TMUX" ]]; then
		tmux setenv -g TMUX_"$1"_$(tmux display -p "#D" | tr -d %) "$2"
		tmux refresh -S
	fi
}

POWERLINE_SAVED_PWD=

_powerline_tmux_set_pwd() {
	if test "x$POWERLINE_SAVED_PWD" != "x$PWD" ; then
		POWERLINE_SAVED_PWD="$PWD"
		_powerline_tmux_setenv PWD "$PWD"
	fi
}

_powerline_tmux_set_columns() {
	_powerline_tmux_setenv COLUMNS "$COLUMNS"
}

_powerline_prompt() {
	local last_exit_code=$?
	[[ -z "$POWERLINE_OLD_PROMPT_COMMAND" ]] ||
		eval $POWERLINE_OLD_PROMPT_COMMAND
	PS1="$($POWERLINE_COMMAND shell left -r bash_prompt --last_exit_code=$last_exit_code)"
	_powerline_tmux_set_pwd
	return $last_exit_code
}

trap "_powerline_tmux_set_columns" SIGWINCH
_powerline_tmux_set_columns

[[ "$PROMPT_COMMAND" == "_powerline_prompt" ]] ||
	POWERLINE_OLD_PROMPT_COMMAND="$PROMPT_COMMAND"
export PROMPT_COMMAND="_powerline_prompt"
