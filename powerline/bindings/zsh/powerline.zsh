_POWERLINE_SOURCED="$0:A"

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

integer _POWERLINE_JOBNUM

_powerline_init_tmux_support() {
	emulate -L zsh
	if test -n "$TMUX" && tmux refresh -S &>/dev/null ; then
		# TMUX variable may be unset to create new tmux session inside this one
		typeset -g _POWERLINE_TMUX="$TMUX"

		function -g _powerline_tmux_setenv() {
			emulate -L zsh
			local -x TMUX="$_POWERLINE_TMUX"
			tmux setenv -g TMUX_"$1"_$(tmux display -p "#D" | tr -d %) "$2"
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

	typeset -ga VS
	VS=( ${(s:.:)ZSH_VERSION} )

	# Mode support requires >=zsh-4.3.11
	if (( VS[1] < 4 || (VS[1] == 4 && (VS[2] < 3 || (VS[2] == 3 && VS[3] < 11))) )) ; then
		return 0
	fi

	function -g _powerline_get_main_keymap_name() {
		REPLY="${${(Q)${${(z)${"$(bindkey -lL main)"}}[3]}}:-.safe}"
	}

	function -g _powerline_set_true_keymap_name() {
		export _POWERLINE_MODE="${1}"
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
		export _POWERLINE_DEFAULT_MODE="$_POWERLINE_MODE"
	fi

	precmd_functions+=( _powerline_set_main_keymap_name )
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
	_POWERLINE_JOBNUM=${(%):-%j}
}

_powerline_update_counter() {
	zpython '_powerline.precmd()'
}

_powerline_setup_prompt() {
	emulate -L zsh

	for f in "${precmd_functions[@]}"; do
		if [[ "$f" = '_powerline_set_jobnum' ]]; then
			return
		fi
	done
	precmd_functions+=( _powerline_set_jobnum )

	VIRTUAL_ENV_DISABLE_PROMPT=1

	if test -z "${POWERLINE_NO_ZSH_ZPYTHON}" && { zmodload libzpython || zmodload zsh/zpython } &>/dev/null ; then
		precmd_functions+=( _powerline_update_counter )
		zpython 'from powerline.bindings.zsh import setup as _powerline_setup'
		zpython '_powerline_setup(globals())'
		zpython 'del _powerline_setup'
		powerline-reload() {
			zpython 'from powerline.bindings.zsh import reload as _powerline_reload'
			zpython '_powerline_reload()'
			zpython 'del _powerline_reload'
		}
	else
		if test -z "${POWERLINE_COMMAND}" ; then
			POWERLINE_COMMAND="$($POWERLINE_CONFIG shell command)"
		fi

		local add_args='-r .zsh'
		add_args+=' --last_exit_code=$?'
		add_args+=' --last_pipe_status="$pipestatus"'
		add_args+=' --renderer_arg="client_id=$$"'
		add_args+=' --renderer_arg="shortened_path=${(%):-%~}"'
		add_args+=' --jobnum=$_POWERLINE_JOBNUM'
		local new_args_2=' --renderer_arg="parser_state=${(%%):-%_}"'
		new_args_2+=' --renderer_arg="local_theme=continuation"'
		local add_args_3=$add_args' --renderer_arg="local_theme=select"'
		local add_args_2=$add_args$new_args_2
		add_args+=' --width=$(( ${COLUMNS:-$(_powerline_columns_fallback)} - 1 ))'
		local add_args_r2=$add_args$new_args_2
		PS1='$($=POWERLINE_COMMAND shell aboveleft '$add_args')'
		RPS1='$($=POWERLINE_COMMAND shell right '$add_args')'
		PS2='$($=POWERLINE_COMMAND shell left '$add_args_2')'
		RPS2='$($=POWERLINE_COMMAND shell right '$add_args_r2')'
		PS3='$($=POWERLINE_COMMAND shell left '$add_args_3')'
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
		export _POWERLINE_SAVE_WIDGET="$save_widget"
	fi
}

if test -z "${POWERLINE_CONFIG}" ; then
	if which powerline-config >/dev/null ; then
		export POWERLINE_CONFIG=powerline-config
	else
		export POWERLINE_CONFIG="$_POWERLINE_SOURCED:h:h:h:h/scripts/powerline-config"
	fi
fi

setopt promptpercent
setopt promptsubst

if ${POWERLINE_CONFIG} shell --shell=zsh uses prompt ; then
	_powerline_setup_prompt
	_powerline_init_modes_support
fi
if ${POWERLINE_CONFIG} shell --shell=zsh uses tmux ; then
	_powerline_init_tmux_support
fi
