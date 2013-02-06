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

trap "_powerline_tmux_set_columns" SIGWINCH
kill -SIGWINCH "$$"

export PROMPT_COMMAND="_powerline_tmux_set_pwd"
export PS1='$(powerline shell left --last_exit_code=$?)'
