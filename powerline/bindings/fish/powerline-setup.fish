function powerline-setup
	function _powerline_columns_fallback
		if which stty ^/dev/null
			if stty size ^/dev/null
				stty size | cut -d' ' -f2
				return 0
			end
		end
		echo 0
		return 0
	end

	function _powerline_columns
		if test -z "$COLUMNS"
			_powerline_columns_fallback
		else
			echo "$COLUMNS"
		end
	end

	if test -z "$POWERLINE_NO_FISH_PROMPT$POWERLINE_NO_SHELL_PROMPT"
		if test -z "$POWERLINE_COMMAND"
			if false ;and which powerline-config >/dev/null
				set -g -x POWERLINE_COMMAND (powerline-config shell command)
			else
				set -l powerline_dir (dirname (status -f))/../../..
				set -g -x POWERLINE_COMMAND (eval $powerline_dir/scripts/powerline-config shell command)
			end
		end
		function --on-variable fish_bind_mode _powerline_bind_mode
			set -g -x _POWERLINE_MODE $fish_bind_mode
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
		_powerline_update
	end
	if test -z "$POWERLINE_NO_FISH_TMUX_SUPPORT$POWERLINE_NO_SHELL_TMUX_SUPPORT"
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
