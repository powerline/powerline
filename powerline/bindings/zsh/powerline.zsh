if test -z "${POWERLINE_COMMAND}" ; then
	if which powerline-client &>/dev/null ; then
		export POWERLINE_COMMAND=powerline-client
	elif which powerline &>/dev/null ; then
		export POWERLINE_COMMAND=powerline
	else
		export POWERLINE_COMMAND="$0:A:h:h:h:h/scripts/powerline"
	fi
fi

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
			_powerline_tmux_setenv COLUMNS "$COLUMNS"
		}

		chpwd_functions+=( _powerline_tmux_set_pwd )
		trap "_powerline_tmux_set_columns" SIGWINCH
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

_powerline_setup_prompt() {
	emulate -L zsh
	for f in "${precmd_functions[@]}"; do
		if [[ "$f" = "_powerline_set_jobnum" ]]; then
			return
		fi
	done
	precmd_functions+=( _powerline_set_jobnum )
	if zmodload zsh/zpython &>/dev/null ; then
		zpython 'from powerline.bindings.zsh import setup as _powerline_setup'
		zpython '_powerline_setup()'
		zpython 'del _powerline_setup'
	else
		local add_args='--last_exit_code=$? --last_pipe_status="$pipestatus"'
		add_args+=' --renderer_arg="client_id=$$"'
		add_args+=' --jobnum=$_POWERLINE_JOBNUM'
		local add_args_2=$add_args' -R parser_state=${(%%):-%_} -R local_theme=continuation'
		PS1='$($POWERLINE_COMMAND shell left -r zsh_prompt '$add_args')'
		RPS1='$($POWERLINE_COMMAND shell right -r zsh_prompt '$add_args')'
		PS2='$($POWERLINE_COMMAND shell left -r zsh_prompt '$add_args_2')'
		RPS2='$($POWERLINE_COMMAND shell right -r zsh_prompt '$add_args_2')'
		PS3='$($POWERLINE_COMMAND shell left -r zsh_prompt -R local_theme=select '$add_args')'
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

setopt promptpercent
setopt promptsubst
_powerline_setup_prompt
_powerline_init_tmux_support
_powerline_init_modes_support
