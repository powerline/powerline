_powerline_columns_fallback() {
	if command -v stty &>/dev/null ; then
		local cols="$(stty size 2>/dev/null)"
		if ! test -z "$cols" ; then
			echo "${cols#* }"
			return 0
		fi
	fi
	echo 0
	return 0
}

_powerline_tmux_pane() {
	echo "${TMUX_PANE:-`TMUX="$_POWERLINE_TMUX" tmux display -p "#D"`}" | \
		tr -d ' %'
}

_powerline_tmux_setenv() {
	TMUX="$_POWERLINE_TMUX" tmux setenv -g TMUX_"$1"_`_powerline_tmux_pane` "$2"
	TMUX="$_POWERLINE_TMUX" tmux refresh -S
}

_powerline_tmux_set_pwd() {
	if test "$_POWERLINE_SAVED_PWD" != "$PWD" ; then
		_POWERLINE_SAVED_PWD="$PWD"
		_powerline_tmux_setenv PWD "$PWD"
	fi
}

_powerline_return() {
	return $1
}

_POWERLINE_HAS_PIPESTATUS="$(
	_powerline_return 0 | _powerline_return 43
	test "${PIPESTATUS[*]}" = "0 43"
	echo "$?"
)"

_powerline_has_pipestatus() {
	return $_POWERLINE_HAS_PIPESTATUS
}

_powerline_status_wrapper() {
	local last_exit_code=$? last_pipe_status=( "${PIPESTATUS[@]}" )

	if ! _powerline_has_pipestatus \
	   || test "${#last_pipe_status[@]}" -eq "0" \
	   || test "$last_exit_code" != "${last_pipe_status[$(( ${#last_pipe_status[@]} - 1 ))]}" ; then
		last_pipe_status=()
	fi
	"$@" $last_exit_code "${last_pipe_status[*]}"
	return $last_exit_code
}

_powerline_add_status_wrapped_command() {
	local action="$1" ; shift
	local cmd="$1" ; shift
	full_cmd="_powerline_status_wrapper $cmd"
	if test "$action" = "append" ; then
		PROMPT_COMMAND="$PROMPT_COMMAND"$'\n'"$full_cmd"
	else
		PROMPT_COMMAND="$full_cmd"$'\n'"$PROMPT_COMMAND"
	fi
}

_powerline_tmux_set_columns() {
	_powerline_tmux_setenv COLUMNS "${COLUMNS:-`_powerline_columns_fallback`}"
}

_powerline_init_tmux_support() {
	if test -n "$TMUX" && tmux refresh -S &>/dev/null ; then
		# TMUX variable may be unset to create new tmux session inside this one
		_POWERLINE_TMUX="$TMUX"

		trap '_powerline_tmux_set_columns' WINCH
		_powerline_tmux_set_columns

		test "$PROMPT_COMMAND" != "${PROMPT_COMMAND/_powerline_tmux_set_pwd}" \
			|| _powerline_add_status_wrapped_command append _powerline_tmux_set_pwd
	fi
}

_powerline_local_prompt() {
	# Arguments:
	# 1: side
	# 2: renderer_module arg
	# 3: last_exit_code
	# 4: last_pipe_status
	# 5: jobnum
	# 6: local theme
	"$POWERLINE_COMMAND" $POWERLINE_COMMAND_ARGS shell $1 \
		$2 \
		--last-exit-code=$3 \
		--last-pipe-status="$4" \
		--jobnum=$5 \
		--renderer-arg="client_id=$$" \
		--renderer-arg="local_theme=$6"
}

_powerline_prompt() {
	# Arguments:
	# 1: side
	# 2: last_exit_code
	# 3: last_pipe_status
	# 4: jobnum
	"$POWERLINE_COMMAND" $POWERLINE_COMMAND_ARGS shell $1 \
		--width="${COLUMNS:-$(_powerline_columns_fallback)}" \
		-r.bash \
		--last-exit-code=$2 \
		--last-pipe-status="$3" \
		--jobnum=$4 \
		--renderer-arg="client_id=$$"
}

_powerline_set_prompt() {
	local last_exit_code=$1 ; shift
	local last_pipe_status=$1 ; shift
	local jobnum="$(jobs -p|wc -l)"
	PS1="$(_powerline_prompt aboveleft $last_exit_code "$last_pipe_status" $jobnum)"
	if test -n "$POWERLINE_SHELL_CONTINUATION$POWERLINE_BASH_CONTINUATION" ; then
		PS2="$(_powerline_local_prompt left -r.bash $last_exit_code "$last_pipe_status" $jobnum continuation)"
	fi
	if test -n "$POWERLINE_SHELL_SELECT$POWERLINE_BASH_SELECT" ; then
		PS3="$(_powerline_local_prompt left '' $last_exit_code "$last_pipe_status" $jobnum select)"
	fi
}

_powerline_setup_prompt() {
	VIRTUAL_ENV_DISABLE_PROMPT=1
	if test -z "${POWERLINE_COMMAND}" ; then
		POWERLINE_COMMAND="$("$POWERLINE_CONFIG_COMMAND" shell command)"
	fi
	test "$PROMPT_COMMAND" != "${PROMPT_COMMAND%_powerline_set_prompt*}" \
		|| _powerline_add_status_wrapped_command prepend _powerline_set_prompt
	PS2="$(_powerline_local_prompt left -r.bash 0 0 0 continuation)"
	PS3="$(_powerline_local_prompt left '' 0 0 0 select)"
}

if test -z "${POWERLINE_CONFIG_COMMAND}" ; then
	if command -v powerline-config >/dev/null ; then
		POWERLINE_CONFIG_COMMAND=powerline-config
	else
		POWERLINE_CONFIG_COMMAND="$(dirname "$BASH_SOURCE")/../../../scripts/powerline-config"
	fi
fi

if "${POWERLINE_CONFIG_COMMAND}" shell --shell=bash uses prompt ; then
	_powerline_setup_prompt
fi
if "${POWERLINE_CONFIG_COMMAND}" shell --shell=bash uses tmux ; then
	_powerline_init_tmux_support
fi
