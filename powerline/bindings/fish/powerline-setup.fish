function powerline-setup
	if test -z "$POWERLINE_COMMAND"
		if which powerline-client >/dev/null
			set -g -x POWERLINE_COMMAND powerline-client
		else
			set -g -x POWERLINE_COMMAND powerline
		end
	end
	function --on-variable POWERLINE_COMMAND _powerline_update
		set -l addargs "--last_exit_code=\$status --last_pipe_status=\$status --jobnum=(jobs -p | wc -l)"
		eval "
		function fish_prompt
			$POWERLINE_COMMAND shell left $addargs
		end
		function fish_right_prompt
			$POWERLINE_COMMAND shell right $addargs
		end
		"
	end
	_powerline_update
	function _powerline_tmux_setenv
		if test -n "$TMUX"
			tmux setenv -g TMUX_$argv[1]_(tmux display -p "#D" | tr -d "%") "$argv[2]"
			tmux refresh -S
		end
	end
	function --on-variable PWD _powerline_tmux_set_pwd
		_powerline_tmux_setenv PWD "$PWD"
	end
	function --on-signal WINCH _powerline_tmux_set_columns
		_powerline_tmux_setenv COLUMNS "$COLUMNS"
	end
	_powerline_tmux_set_columns
	_powerline_tmux_set_pwd
end
