_powerline_precmd() {
	_powerline_tmux_set_pwd
}

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

_powerline_install_precmd() {
	for f in "${precmd_functions[@]}"; do
		if [[ "$f" = "_powerline_precmd" ]]; then
			return
		fi
	done
	precmd_functions+=(_powerline_precmd)
	setopt promptpercent
	setopt promptsubst
	PS1='$(powerline shell left -r zsh_prompt --last_exit_code=$? --last_pipe_status="$pipestatus")'
	RPS1='$(powerline shell right -r zsh_prompt --last_exit_code=$? --last_pipe_status="$pipestatus")'
}

trap "_powerline_tmux_set_columns" SIGWINCH
kill -SIGWINCH $$

_powerline_install_precmd
