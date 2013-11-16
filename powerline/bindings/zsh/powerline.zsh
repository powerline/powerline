if test -z "${POWERLINE_COMMAND}" ; then
	if which powerline-client &>/dev/null ; then
		export POWERLINE_COMMAND=powerline-client
	elif which powerline &>/dev/null ; then
		export POWERLINE_COMMAND=powerline
	else
		export POWERLINE_COMMAND="$0:A:h:h:h:h/scripts/powerline"
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

_powerline_precmd() {
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
	_powerline_set_true_keymap_name "${${(Q)${${(z)${"$(bindkey -lL main)"}}[3]}}:-.safe}"
}

_powerline_setup_prompt() {
	emulate -L zsh
	for f in "${precmd_functions[@]}"; do
		if [[ "$f" = "_powerline_precmd" ]]; then
			return
		fi
	done
	precmd_functions+=( _powerline_precmd )
	chpwd_functions+=( _powerline_tmux_set_pwd )
	_powerline_set_true_keymap_name "${${(Q)${${(z)${"$(bindkey -lL main)"}}[3]}}:-.safe}"
	if zmodload zsh/zpython &>/dev/null ; then
		zpython 'from powerline.bindings.zsh import setup as powerline_setup'
		zpython 'powerline_setup()'
		zpython 'del powerline_setup'
	else
		local add_args='--last_exit_code=$? --last_pipe_status="$pipestatus"'
		add_args+=' --jobnum=$_POWERLINE_JOBNUM'
		PS1='$($POWERLINE_COMMAND shell left -r zsh_prompt '$add_args')'
		RPS1='$($POWERLINE_COMMAND shell right -r zsh_prompt '$add_args')'
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
		local save_widget="powerline_save_$widget"
		local -i i=0
		while ! test -z "$(zle -l -L $save_widget)" ; do
			save_widget="${save_widget}_$i"
			(( i++ ))
		done
		eval "${old_widget_command/$widget/$save_widget}"
		zle -N $widget $function
		export POWERLINE_SAVE_WIDGET="$save_widget"
	fi
}

_powerline_set_true_keymap_name() {
	export POWERLINE_MODE="${1}"
	local plm_bk="$(bindkey -lL ${POWERLINE_MODE})"
	if [[ $plm_bk = 'bindkey -A'* ]] ; then
		_powerline_set_true_keymap_name ${(Q)${${(z)plm_bk}[3]}}
	fi
}

_powerline_zle_keymap_select() {
	_powerline_set_true_keymap_name $KEYMAP
	zle reset-prompt
	test -z "$POWERLINE_SAVE_WIDGET" || zle $POWERLINE_SAVE_WIDGET
}

_powerline_add_widget zle-keymap-select _powerline_zle_keymap_select
_powerline_precmd

if [[ "$POWERLINE_MODE" != vi* ]] ; then
	export POWERLINE_DEFAULT_MODE="$POWERLINE_MODE"
fi

trap "_powerline_tmux_set_columns" SIGWINCH
_powerline_tmux_set_columns
_powerline_tmux_set_pwd

setopt promptpercent
setopt promptsubst
_powerline_setup_prompt
