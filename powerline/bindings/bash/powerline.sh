_powerline_tmux_setenv() {
	if [[ -n "$TMUX" ]]; then
		tmux setenv TMUX_"$1"_$(tmux display -p "#D" | tr -d %) "$2"
	fi
}

_powerline_tmux_set_pwd() {
	_powerline_tmux_setenv PWD "$PWD"
}

_powerline_tmux_set_columns() {
	_powerline_tmux_setenv COLUMNS "$COLUMNS"
}

_powerline_prompt() {
	[[ -z "$POWERLINE_OLD_PROMPT_COMMAND" ]] ||
		eval $POWERLINE_OLD_PROMPT_COMMAND
	PS1="$(powerline shell left -r bash_prompt --last_exit_code=$?)"
	_powerline_tmux_set_pwd
}

trap "_powerline_tmux_set_columns" SIGWINCH
_powerline_tmux_set_columns

[[ "$PROMPT_COMMAND" == "_powerline_prompt" ]] ||
	POWERLINE_OLD_PROMPT_COMMAND="$PROMPT_COMMAND"
export PROMPT_COMMAND="_powerline_prompt"
