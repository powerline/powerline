function powerline-setup
	function _powerline_columns
		if which stty >/dev/null
			if stty size >/dev/null
				stty size | cut -d' ' -f2
				return 0
			end
		end
		echo 0
		return 0
	end

	if not set -q POWERLINE_CONFIG_COMMAND
		if which powerline-config >/dev/null
			set -g POWERLINE_CONFIG_COMMAND powerline-config
		else
			set -g POWERLINE_CONFIG_COMMAND (dirname (status -f))/../../../scripts/powerline-config
		end
	end

	if eval $POWERLINE_CONFIG_COMMAND shell --shell=fish uses prompt
		if not set -q POWERLINE_COMMAND
			set -g POWERLINE_COMMAND (eval $POWERLINE_CONFIG_COMMAND shell command)
		end
		function _powerline_set_default_mode --on-variable fish_key_bindings
			if test $fish_key_bindings != fish_vi_key_bindings
				set -g _POWERLINE_DEFAULT_MODE default
			else
				set -g -e _POWERLINE_DEFAULT_MODE
			end
		end
		function _powerline_update --on-variable POWERLINE_COMMAND
			set -l addargs "--last-exit-code=\$status"
			if set -q pipestatus
				set addargs "$addargs --last-pipe-status=\"\$pipestatus\""
			else
				set addargs "$addargs --last-pipe-status=\$status"
			end
			set -l addargs "$addargs --jobnum=(jobs -p | wc -l)"
			if set -q fish_pid
				set addargs "$addargs --renderer-arg=client_id=\$fish_pid"
			else
				# One random value has an 1/32767 = 0.0031% probability of having
				# the same value in two shells
				set addargs "$addargs --renderer-arg=client_id="(random)
			end
			set -l addargs "$addargs --width=\$_POWERLINE_COLUMNS"
			set -l addargs "$addargs --renderer-arg=mode=\$fish_bind_mode"
			set -l addargs "$addargs --renderer-arg=default_mode=\$_POWERLINE_DEFAULT_MODE"
			set -l promptside
			set -l rpromptpast
			set -l columnsexpr
			if begin set -q POWERLINE_NO_FISH_ABOVE; or set -q POWERLINE_NO_SHELL_ABOVE; end
				set promptside left
				set rpromptpast
				set columnsexpr '(_powerline_columns)'
			else
				set promptside aboveleft
				set rpromptpast 'echo -n " "'
				set columnsexpr '(math (_powerline_columns) - 1)'
			end
			echo "
			function fish_prompt
				eval \$POWERLINE_COMMAND $POWERLINE_COMMAND_ARGS shell $promptside $addargs
			end
			function fish_right_prompt
				eval \$POWERLINE_COMMAND $POWERLINE_COMMAND_ARGS shell right $addargs
				$rpromptpast
			end
			function fish_mode_prompt
			end
			function _powerline_set_columns --on-signal WINCH
				set -g _POWERLINE_COLUMNS $columnsexpr
			end
			" | source
			_powerline_set_columns
		end
		_powerline_set_default_mode
		_powerline_update
	end
	if eval $POWERLINE_CONFIG_COMMAND shell --shell=fish uses tmux
		if set -q TMUX
			if tmux refresh -S ^/dev/null
				set -g _POWERLINE_TMUX "$TMUX"
				function _powerline_tmux_pane
					if set -q TMUX_PANE
						echo "$TMUX_PANE" | tr -d ' %'
					else
						env TMUX="$_POWERLINE_TMUX" tmux display -p "#D" | tr -d ' %'
					end
				end
				function _powerline_tmux_setenv
					env TMUX="$_POWERLINE_TMUX" tmux setenv -g TMUX_$argv[1]_(_powerline_tmux_pane) "$argv[2]"
					env TMUX="$_POWERLINE_TMUX" tmux refresh -S
				end
				function _powerline_tmux_set_pwd --on-variable PWD
					_powerline_tmux_setenv PWD "$PWD"
				end
				function _powerline_tmux_set_columns --on-signal WINCH
					_powerline_tmux_setenv COLUMNS (_powerline_columns)
				end
				_powerline_tmux_set_columns
				_powerline_tmux_set_pwd
			end
		end
	end

	return 0
end
# vim: ft=fish
