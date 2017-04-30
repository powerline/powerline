_POWERLINE_SOURCED="$_"
_powerline_columns_fallback() {
	if which stty >/dev/null ; then
		# Ksh does not have “local” built-in
		_powerline_cols="$(stty size 2>/dev/null)"
		if ! test -z "$_powerline_cols" ; then
			echo "${_powerline_cols#* }"
			return 0
		fi
	fi
	echo 0
	return 0
}

_powerline_has_jobs_in_subshell() {
	if test -n "$_POWERLINE_HAS_JOBS_IN_SUBSHELL" ; then
		return $_POWERLINE_HAS_JOBS_IN_SUBSHELL
	elif test -z "$1" ; then
		sleep 1 &
		# Check whether shell outputs anything in a subshell when using jobs 
		# built-in. Shells like dash will not output anything meaning that 
		# I have to bother with temporary files.
		test "$(jobs -p|wc -l)" -gt 0
	else
		case "$1" in
			dash|bb|ash) return 1 ;;
			mksh|ksh|bash) return 0 ;;
			*) _powerline_has_jobs_in_subshell ;;
		esac
	fi
	_POWERLINE_HAS_JOBS_IN_SUBSHELL=$?
	return $_POWERLINE_HAS_JOBS_IN_SUBSHELL
}

_powerline_set_append_trap() {
	if _powerline_has_jobs_in_subshell "$@" ; then
		_powerline_append_trap() {
			# Arguments: command, signal
			# Ksh does not have “local” built-in
			_powerline_traps="$(trap)"
			if echo "$_powerline_traps" | grep -cm1 $2'$' >/dev/null ; then
				_powerline_traps="$(echo "$_powerline_traps" | sed "s/ $2/'\\n$1' $2/")"
				eval "$_powerline_traps"
			else
				trap "$1" $2
			fi
		}
	else
		_powerline_append_trap() {
			# Arguments: command, signal
			_powerline_create_temp
			trap > $_POWERLINE_TEMP
			if grep -cm1 $2'$' $_POWERLINE_TEMP >/dev/null ; then
				sed -i -e "s/ $2/'\\n$1' $2/"
				. $_POWERLINE_TEMP
			else
				trap "$1" $2
			fi
			echo -n > $_POWERLINE_TEMP
		}
	fi
	_powerline_set_append_trap() {
		return 0
	}
}

_powerline_create_temp() {
	if test -z "$_POWERLINE_TEMP" || ! test -e "$_POWERLINE_TEMP" ; then
		_POWERLINE_TEMP="$(mktemp "${TMPDIR:-/tmp}/powerline.XXXXXXXX")"
		_powerline_append_trap 'rm $_POWERLINE_TEMP' EXIT
	fi
}

_powerline_set_set_jobs() {
	if _powerline_has_jobs_in_subshell "$@" ; then
		_powerline_set_jobs() {
			_POWERLINE_JOBS="$(jobs -p|wc -l|tr -d ' ')"
		}
	else
		_powerline_set_append_trap "$@"
		_POWERLINE_PID=$$
		_powerline_append_trap '_powerline_do_set_jobs' USR1
		_powerline_do_set_jobs() {
			_powerline_create_temp
			jobs -p > $_POWERLINE_TEMP
		}
		# This command will always be launched from a subshell, thus a hack is 
		# needed to run `jobs -p` outside of the subshell.
		_powerline_set_jobs() {
			kill -USR1 $_POWERLINE_PID
			# Note: most likely this will read data from the previous run. Tests 
			# show that it is OK for some reasons.
			_POWERLINE_JOBS="$(wc -l < $_POWERLINE_TEMP | tr -d ' ')"
		}
	fi
	_powerline_set_set_jobs() {
		return 0
	}
}

_powerline_set_command() {
	if test -z "${POWERLINE_COMMAND}" ; then
		POWERLINE_COMMAND="$("$POWERLINE_CONFIG_COMMAND" shell command)"
	fi
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

_powerline_tmux_set_columns() {
	_powerline_tmux_setenv COLUMNS "${COLUMNS:-$(_powerline_columns_fallback)}"
}

_powerline_set_renderer_arg() {
	case "$1" in
		bb|ash) _POWERLINE_RENDERER_ARG="-r .bash" ;;
		mksh|ksh) _POWERLINE_RENDERER_ARG="-r .ksh" ;;
		bash|dash) _POWERLINE_RENDERER_ARG= ;;
	esac
}

_powerline_set_jobs() {
	_powerline_set_set_jobs
	_powerline_set_jobs
}

_powerline_local_prompt() {
	# Arguments: side, exit_code, local theme
	_powerline_set_jobs
	"$POWERLINE_COMMAND" $POWERLINE_COMMAND_ARGS shell $1 \
		$_POWERLINE_RENDERER_ARG \
		--renderer-arg="client_id=$$" \
		--last-exit-code=$2 \
		--jobnum=$_POWERLINE_JOBS \
		--renderer-arg="local_theme=$3"
}

_powerline_prompt() {
	# Arguments: side, exit_code
	_powerline_set_jobs
	"$POWERLINE_COMMAND" $POWERLINE_COMMAND_ARGS shell $1 \
		--width="${COLUMNS:-$(_powerline_columns_fallback)}" \
		$_POWERLINE_RENDERER_ARG \
		--renderer-arg="client_id=$$" \
		--last-exit-code=$2 \
		--jobnum=$_POWERLINE_JOBS
	_powerline_update_psN
}

_powerline_setup_psN() {
	case "$1" in
		mksh|ksh|bash)
			_POWERLINE_PID=$$
			_powerline_update_psN() {
				kill -USR1 $_POWERLINE_PID
			}
			# No command substitution in PS2 and PS3
			_powerline_set_psN() {
				if test -n "$POWERLINE_SHELL_CONTINUATION" ; then
					PS2="$(_powerline_local_prompt left $? continuation)"
				fi
				if test -n "$POWERLINE_SHELL_SELECT" ; then
					PS3="$(_powerline_local_prompt left $? select)"
				fi
			}
			_powerline_append_trap '_powerline_set_psN' USR1
			_powerline_set_psN
			;;
		bb|ash|dash)
			_powerline_update_psN() {
				# Do nothing
				return
			}
			PS2='$(_powerline_local_prompt left $? continuation)'
			# No select support
			;;
	esac
}

_powerline_setup_prompt() {
	VIRTUAL_ENV_DISABLE_PROMPT=1
	_powerline_set_append_trap "$@"
	_powerline_set_set_jobs "$@"
	_powerline_set_command "$@"
	_powerline_set_renderer_arg "$@"
	PS1='$(_powerline_prompt aboveleft $?)'
	PS2="$(_powerline_local_prompt left 0 continuation)"
	PS3="$(_powerline_local_prompt left 0 select)"
	_powerline_setup_psN "$@"
}

_powerline_init_tmux_support() {
	# Dash does not have &>/dev/null
	if test -n "$TMUX" && tmux refresh -S >/dev/null 2>/dev/null ; then
		# TMUX variable may be unset to create new tmux session inside this one
		_POWERLINE_TMUX="$TMUX"

		_powerline_set_append_trap "$@"

		# If _powerline_tmux_set_pwd is used before _powerline_prompt it sets $? 
		# to zero in ksh.
		PS1="$PS1"'$(_powerline_tmux_set_pwd)'
		_powerline_append_trap '_powerline_tmux_set_columns' WINCH
		_powerline_tmux_set_columns
	fi
}

if test -z "${POWERLINE_CONFIG_COMMAND}" ; then
	if which powerline-config >/dev/null ; then
		POWERLINE_CONFIG_COMMAND=powerline-config
	else
		POWERLINE_CONFIG_COMMAND="$(dirname "$_POWERLINE_SOURCED")/../../../scripts/powerline-config"
	fi
fi

# Strips the leading `-`: it may be present when shell is a login shell
_POWERLINE_USED_SHELL=${0#-}
_POWERLINE_USED_SHELL=${_POWERLINE_USED_SHELL##*/}

if "${POWERLINE_CONFIG_COMMAND}" shell uses tmux ; then
	_powerline_init_tmux_support $_POWERLINE_USED_SHELL
fi
if "${POWERLINE_CONFIG_COMMAND}" shell --shell=bash uses prompt ; then
	_powerline_setup_prompt $_POWERLINE_USED_SHELL
fi
