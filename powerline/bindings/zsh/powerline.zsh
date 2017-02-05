local _POWERLINE_SOURCED="$0:A"

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

_powerline_append_precmd_function() {
	if test -z "${precmd_functions[(re)$1]}" ; then
		precmd_functions+=( $1 )
	fi
}

integer -g _POWERLINE_JOBNUM=0

_powerline_tmux_pane() {
	local -x TMUX="$_POWERLINE_TMUX"
	echo "${TMUX_PANE:-`tmux display -p "#D"`}" | tr -d ' %'
}

_powerline_init_tmux_support() {
	emulate -L zsh
	if test -n "$TMUX" && tmux refresh -S &>/dev/null ; then
		# TMUX variable may be unset to create new tmux session inside this one
		typeset -g _POWERLINE_TMUX="$TMUX"

		function -g _powerline_tmux_setenv() {
			emulate -L zsh
			local -x TMUX="$_POWERLINE_TMUX"
			tmux setenv -g TMUX_"$1"_$(_powerline_tmux_pane) "$2"
			tmux refresh -S
		}

		function -g _powerline_tmux_set_pwd() {
			_powerline_tmux_setenv PWD "$PWD"
		}

		function -g _powerline_tmux_set_columns() {
			_powerline_tmux_setenv COLUMNS "${COLUMNS:-$(_powerline_columns_fallback)}"
		}

		chpwd_functions+=( _powerline_tmux_set_pwd )
		trap '_powerline_tmux_set_columns' SIGWINCH
		_powerline_tmux_set_columns
		_powerline_tmux_set_pwd
	fi
}

_powerline_init_modes_support() {
	emulate -L zsh

	test -z "$ZSH_VERSION" && return 0

	local -a vs
	vs=( ${(s:.:)ZSH_VERSION} )

	# Mode support requires >=zsh-4.3.11
	if (( vs[1] < 4 || (vs[1] == 4 && (vs[2] < 3 || (vs[2] == 3 && vs[3] < 11))) )) ; then
		return 0
	fi

	function -g _powerline_get_main_keymap_name() {
		REPLY="${${(Q)${${(z)${"$(bindkey -lL main)"}}[3]}}:-.safe}"
	}

	function -g _powerline_set_true_keymap_name() {
		typeset -g _POWERLINE_MODE="${1}"
		local plm_bk="$(bindkey -lL ${_POWERLINE_MODE})"
		if [[ $plm_bk = 'bindkey -A'* ]] ; then
			_powerline_set_true_keymap_name ${(Q)${${(z)plm_bk}[3]}}
		fi
	}

	function -g _powerline_zle_keymap_select() {
		_powerline_set_true_keymap_name $KEYMAP
		zle reset-prompt
		test -z "$_POWERLINE_SAVE_WIDGET" || zle $_POWERLINE_SAVE_WIDGET
	}

	function -g _powerline_set_main_keymap_name() {
		local REPLY
		_powerline_get_main_keymap_name
		_powerline_set_true_keymap_name "$REPLY"
	}

	_powerline_add_widget zle-keymap-select _powerline_zle_keymap_select
	_powerline_set_main_keymap_name

	if [[ "$_POWERLINE_MODE" != vi* ]] ; then
		typeset -g _POWERLINE_DEFAULT_MODE="$_POWERLINE_MODE"
	fi

	_powerline_append_precmd_function _powerline_set_main_keymap_name
}

_powerline_set_jobnum() {
	# If you are wondering why I am not using the same code as I use for bash 
	# ($(jobs|wc -l)): consider the following test:
	#     echo abc | less
	#     <C-z>
	# . This way jobs will print
	#     [1]  + done       echo abc |
	#            suspended  less -M
	# ([ is in first column). You see: any line counting thingie will return 
	# wrong number of jobs. You need to filter the lines first. Or not use 
	# jobs built-in at all.
	integer -g _POWERLINE_JOBNUM=${(%):-%j}
}

_powerline_update_counter() {
	zpython '_powerline.precmd()'
}

_powerline_setup_prompt() {
	emulate -L zsh

	_powerline_append_precmd_function _powerline_set_jobnum

	typeset -g VIRTUAL_ENV_DISABLE_PROMPT=1

	if test -z "${POWERLINE_NO_ZSH_ZPYTHON}" && { zmodload libzpython || zmodload zsh/zpython } &>/dev/null ; then
		_powerline_append_precmd_function _powerline_update_counter
		zpython 'from powerline.bindings.zsh import setup as _powerline_setup'
		zpython '_powerline_setup(globals())'
		zpython 'del _powerline_setup'
		powerline-reload() {
			zpython 'from powerline.bindings.zsh import reload as _powerline_reload'
			zpython '_powerline_reload()'
			zpython 'del _powerline_reload'
		}
		powerline-reload-config() {
			zpython 'from powerline.bindings.zsh import reload_config as _powerline_reload_config'
			zpython '_powerline_reload_config()'
			zpython 'del _powerline_reload_config'
		}
	else
		if test -z "${POWERLINE_COMMAND}" ; then
			typeset -g POWERLINE_COMMAND="$($POWERLINE_CONFIG_COMMAND shell command)"
		fi

		local add_args='-r .zsh'
		add_args+=' --last-exit-code=$?'
		add_args+=' --last-pipe-status="$pipestatus"'
		add_args+=' --renderer-arg="client_id=$$"'
		add_args+=' --renderer-arg="shortened_path=${(%):-%~}"'
		add_args+=' --jobnum=$_POWERLINE_JOBNUM'
		add_args+=' --renderer-arg="mode=$_POWERLINE_MODE"'
		add_args+=' --renderer-arg="default_mode=$_POWERLINE_DEFAULT_MODE"'
		local new_args_2=' --renderer-arg="parser_state=${(%%):-%_}"'
		new_args_2+=' --renderer-arg="local_theme=continuation"'
		local add_args_3=$add_args' --renderer-arg="local_theme=select"'
		local add_args_2=$add_args$new_args_2
		add_args+=' --width=$(( ${COLUMNS:-$(_powerline_columns_fallback)} - ${ZLE_RPROMPT_INDENT:-1} ))'
		local add_args_r2=$add_args$new_args_2
		typeset -g PS1='$("$POWERLINE_COMMAND" $=POWERLINE_COMMAND_ARGS shell aboveleft '$add_args')'
		typeset -g RPS1='$("$POWERLINE_COMMAND" $=POWERLINE_COMMAND_ARGS shell right '$add_args')'
		typeset -g PS2='$("$POWERLINE_COMMAND" $=POWERLINE_COMMAND_ARGS shell left '$add_args_2')'
		typeset -g RPS2='$("$POWERLINE_COMMAND" $=POWERLINE_COMMAND_ARGS shell right '$add_args_r2')'
		typeset -g PS3='$("$POWERLINE_COMMAND" $=POWERLINE_COMMAND_ARGS shell left '$add_args_3')'
	fi
}

_powerline_add_widget() {
	local widget="$1"
	local function="$2"
	local old_widget_command="$(zle -l -L $widget)"
	if [[ "$old_widget_command" = "zle -N $widget $function" ]] ; then
		return 0
	elif [[ -z "$old_widget_command" ]] ; then
		zle -N $widget $function
	else
		local save_widget="_powerline_save_$widget"
		local -i i=0
		while ! test -z "$(zle -l -L $save_widget)" ; do
			save_widget="${save_widget}_$i"
			(( i++ ))
		done
		# If widget was defined with `zle -N widget` (without `function` 
		# argument) then this function will be handy.
		eval "function $save_widget() { emulate -L zsh; $widget \$@ }"
		eval "${old_widget_command/$widget/$save_widget}"
		zle -N $widget $function
		typeset -g _POWERLINE_SAVE_WIDGET="$save_widget"
	fi
}

if test -z "${POWERLINE_CONFIG_COMMAND}" ; then
	if which powerline-config >/dev/null ; then
		typeset -g POWERLINE_CONFIG_COMMAND=powerline-config
	else
		typeset -g POWERLINE_CONFIG_COMMAND="${_POWERLINE_SOURCED:h:h:h:h}/scripts/powerline-config"
	fi
fi

setopt promptpercent
setopt promptsubst

if "${POWERLINE_CONFIG_COMMAND}" shell --shell=zsh uses prompt ; then
	_powerline_setup_prompt
	_powerline_init_modes_support
fi
if "${POWERLINE_CONFIG_COMMAND}" shell --shell=zsh uses tmux ; then
	_powerline_init_tmux_support
fi
