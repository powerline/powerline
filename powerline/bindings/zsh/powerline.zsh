if test -z "${POWERLINE_COMMAND}" ; then
	if which powerline-client &>/dev/null ; then
		export POWERLINE_COMMAND=powerline-client
	else
		export POWERLINE_COMMAND=powerline
	fi
fi

_powerline_tmux_setenv() {
	emulate -L zsh
	if [[ -n "$TMUX" ]]; then
		tmux setenv -g TMUX_"$1"_$(tmux display -p "#D" | tr -d %) "$2"
		tmux refresh -S
	fi
}

_powerline_tmux_set_pwd() {
	_powerline_tmux_setenv PWD "$PWD"
}

_powerline_tmux_set_columns() {
	_powerline_tmux_setenv COLUMNS "$COLUMNS"
}

_powerline_install_precmd() {
	emulate -L zsh
	for f in "${precmd_functions[@]}"; do
		if [[ "$f" = "_powerline_precmd" ]]; then
			return
		fi
	done
	chpwd_functions+=( _powerline_tmux_set_pwd )
	if zmodload zsh/zpython &>/dev/null ; then
		zpython 'from powerline.bindings.zsh import setup as powerline_setup'
		zpython 'powerline_setup()'
		zpython 'del powerline_setup'
	else
		PS1='$($POWERLINE_COMMAND shell left -r zsh_prompt --last_exit_code=$? --last_pipe_status="$pipestatus")'
		RPS1='$($POWERLINE_COMMAND shell right -r zsh_prompt --last_exit_code=$? --last_pipe_status="$pipestatus")'
	fi
}

trap "_powerline_tmux_set_columns" SIGWINCH
_powerline_tmux_set_columns

setopt promptpercent
setopt promptsubst
_powerline_install_precmd
