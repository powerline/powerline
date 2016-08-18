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

	if test -z "$POWERLINE_CONFIG_COMMAND"
		if which powerline-config >/dev/null
			set -g POWERLINE_CONFIG_COMMAND powerline-config
		else
			set -g POWERLINE_CONFIG_COMMAND (dirname (status -f))/../../../scripts/powerline-config
		end
	end

	if env $POWERLINE_CONFIG_COMMAND shell --shell=fish uses prompt
		if test -z "$POWERLINE_COMMAND"
			set -g POWERLINE_COMMAND (env $POWERLINE_CONFIG_COMMAND shell command)
		end
		function --on-variable fish_key_bindings _powerline_set_default_mode
			if test x$fish_key_bindings != xfish_vi_key_bindings
				set -g _POWERLINE_DEFAULT_MODE default
			else
				set -g -e _POWERLINE_DEFAULT_MODE
			end
		end
		function --on-variable POWERLINE_COMMAND _powerline_update
			set -l addargs "--last-exit-code=\$status"
			set -l addargs "$addargs --last-pipe-status=\$status"
			set -l addargs "$addargs --jobnum=(jobs -p | wc -l)"
			# One random value has an 1/32767 = 0.0031% probability of having 
			# the same value in two shells
			set -l addargs "$addargs --renderer-arg=client_id="(random)
			set -l addargs "$addargs --width=\$_POWERLINE_COLUMNS"
			set -l addargs "$addargs --renderer-arg=mode=\$fish_bind_mode"
			set -l addargs "$addargs --renderer-arg=default_mode=\$_POWERLINE_DEFAULT_MODE"
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
				env \$POWERLINE_COMMAND $POWERLINE_COMMAND_ARGS shell $promptside $addargs
			end
			function fish_right_prompt
				env \$POWERLINE_COMMAND $POWERLINE_COMMAND_ARGS shell right $addargs
				$rpromptpast
			end
			function --on-signal WINCH _powerline_set_columns
				set -g _POWERLINE_COLUMNS $columnsexpr
			end
			"
			_powerline_set_columns
		end
		_powerline_set_default_mode
		_powerline_update
	end
	if env $POWERLINE_CONFIG_COMMAND shell --shell=fish uses tmux
		if test -n "$TMUX"
			if tmux refresh -S ^/dev/null
				set -g _POWERLINE_TMUX "$TMUX"
				function _powerline_tmux_pane
					if test -z "$TMUX_PANE"
						env TMUX="$_POWERLINE_TMUX" tmux display -p "#D" | tr -d ' %'
					else
						echo "$TMUX_PANE" | tr -d ' %'
					end
				end
				function _powerline_tmux_setenv
					env TMUX="$_POWERLINE_TMUX" tmux setenv -g TMUX_$argv[1]_(_powerline_tmux_pane) "$argv[2]"
					env TMUX="$_POWERLINE_TMUX" tmux refresh -S
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
