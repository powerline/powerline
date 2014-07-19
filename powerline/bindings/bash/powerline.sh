_powerline_columns_fallback() {
	if which stty &>/dev/null ; then
		local cols="$(stty size 2>/dev/null)"
		if ! test -z "$cols" ; then
			echo "${cols#* }"
			return 0
		fi
	fi
	echo 0
	return 0
}

_powerline_tmux_setenv() {
	TMUX="$_POWERLINE_TMUX" tmux setenv -g TMUX_"$1"_`tmux display -p "#D" | tr -d %` "$2"
	TMUX="$_POWERLINE_TMUX" tmux refresh -S
}

_powerline_tmux_set_pwd() {
	if test "x$_POWERLINE_SAVED_PWD" != "x$PWD" ; then
		_POWERLINE_SAVED_PWD="$PWD"
		_powerline_tmux_setenv PWD "$PWD"
	fi
}

_powerline_tmux_set_columns() {
	_powerline_tmux_setenv COLUMNS "${COLUMNS:-$(_powerline_columns_fallback)}"
}

_powerline_init_tmux_support() {
	if test -n "$TMUX" && tmux refresh -S &>/dev/null ; then
		# TMUX variable may be unset to create new tmux session inside this one
		_POWERLINE_TMUX="$TMUX"

		trap "_powerline_tmux_set_columns" WINCH
		_powerline_tmux_set_columns

		test "x$PROMPT_COMMAND" != "x${PROMPT_COMMAND/_powerline_tmux_set_pwd}" ||
			export PROMPT_COMMAND="${PROMPT_COMMAND}"$'\n_powerline_tmux_set_pwd'
	fi
}

_powerline_prompt() {
	# Arguments: side, last_exit_code, jobnum
	$POWERLINE_COMMAND shell $1 -w "${COLUMNS:-$(_powerline_columns_fallback)}" -r bash_prompt --last_exit_code=$2 --jobnum=$3
}

_powerline_set_prompt() {
	local last_exit_code=$?
	local jobnum="$(jobs -p|wc -l)"
	PS1="$(_powerline_prompt aboveleft $last_exit_code $jobnum)"
	return $last_exit_code
}

_powerline_setup_prompt() {
	VIRTUAL_ENV_DISABLE_PROMPT=1
	if test -z "${POWERLINE_COMMAND}" ; then
		if which powerline-client &>/dev/null ; then
			export POWERLINE_COMMAND=powerline-client
		elif which powerline &>/dev/null ; then
			export POWERLINE_COMMAND=powerline
		else
			# `$0` is set to `-bash` when using SSH so that won't work
			export POWERLINE_COMMAND="$(dirname "$BASH_SOURCE")/../../../scripts/powerline"
		fi
	fi
	test "x$PROMPT_COMMAND" != "x${PROMPT_COMMAND%_powerline_set_prompt*}" ||
		export PROMPT_COMMAND=$'_powerline_set_prompt\n'"${PROMPT_COMMAND}"
}

if test -z "$POWERLINE_NO_BASH_PROMPT$POWERLINE_NO_SHELL_PROMPT" ; then
	_powerline_setup_prompt
fi
if test -z "$POWERLINE_NO_BASH_TMUX_SUPPORT$POWERLINE_NO_SHELL_TMUX_SUPPORT" ; then
	_powerline_init_tmux_support
fi
