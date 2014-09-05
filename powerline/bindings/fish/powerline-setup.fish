function powerline-setup
	function _powerline_columns_fallback
		if which stty >/dev/null
			if stty size >/dev/null
				stty size | cut -d' ' -f2
				return 0
			end
		end
		echo 0
		return 0
	end

	function _powerline_columns
		# Hack: `test "" -eq 0` is true, as well as `test 0 -eq 0`
		# Note: at fish startup `$COLUMNS` is equal to zero, meaning that it may 
		# not be used.
		if test "$COLUMNS" -eq 0
			_powerline_columns_fallback
		else
			echo "$COLUMNS"
		end
	end

	if test -z "$POWERLINE_CONFIG"
		if which powerline-config >/dev/null
			set -g POWERLINE_CONFIG powerline-config
		else
			set -g POWERLINE_CONFIG (dirname (status -f))/../../../scripts/powerline-config
		end
	end

	if eval $POWERLINE_CONFIG shell --shell=fish uses prompt
		if test -z "$POWERLINE_COMMAND"
			set -g POWERLINE_COMMAND (eval $POWERLINE_CONFIG shell command)
		end
		function --on-variable fish_bind_mode _powerline_bind_mode
			set -g -x _POWERLINE_MODE $fish_bind_mode
		end
		function --on-variable fish_key_bindings _powerline_set_default_mode
			if test x$fish_key_bindings != xfish_vi_key_bindings
				set -g -x _POWERLINE_DEFAULT_MODE default
			else
				set -g -e _POWERLINE_DEFAULT_MODE
			end
		end
		function --on-variable POWERLINE_COMMAND _powerline_update
			set -l addargs "--last_exit_code=\$status"
			set -l addargs "$addargs --last_pipe_status=\$status"
			set -l addargs "$addargs --jobnum=(jobs -p | wc -l)"
			# One random value has an 1/32767 = 0.0031% probability of having 
			# the same value in two shells
			set -l addargs "$addargs --renderer_arg=client_id="(random)
			set -l addargs "$addargs --width=\$_POWERLINE_COLUMNS"
			set -l promptside
			set -l rpromptpast
			set -l columnsexpr
			if test -z "$POWERLINE_NO_FISH_ABOVE$POWERLINE_NO_SHELL_ABOVE"
				set promptside aboveleft
				set rpromptpast 'echo -n " "'
				set columnsexpr '(math (_powerline_columns) - 1)'
			else
				set promptside left
				set rpromptpast
				set columnsexpr '(_powerline_columns)'
			end
			eval "
			function fish_prompt
				$POWERLINE_COMMAND shell $promptside $addargs
			end
			function fish_right_prompt
				$POWERLINE_COMMAND shell right $addargs
				$rpromptpast
			end
			function --on-signal WINCH _powerline_set_columns
				set -g _POWERLINE_COLUMNS $columnsexpr
			end
			"
			_powerline_set_columns
		end
		_powerline_bind_mode
		_powerline_set_default_mode
		_powerline_update
	end
	if eval $POWERLINE_CONFIG shell --shell=fish uses tmux
		if test -n "$TMUX"
			if tmux refresh -S ^/dev/null
				function _powerline_tmux_setenv
					tmux setenv -g TMUX_$argv[1]_(tmux display -p "#D" | tr -d "%") "$argv[2]"
					tmux refresh -S
				end
				function --on-variable PWD _powerline_tmux_set_pwd
					_powerline_tmux_setenv PWD "$PWD"
				end
				function --on-signal WINCH _powerline_tmux_set_columns
					_powerline_tmux_setenv COLUMNS (_powerline_columns)
				end
				_powerline_tmux_set_columns
				_powerline_tmux_set_pwd
			end
		end
	end
end
# vim: ft=fish
