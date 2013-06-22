function powerline
	if test -z "$POWERLINE_COMMAND"
		if which powerline-client >/dev/null
			set -g -x POWERLINE_COMMAND powerline-client
		else
			set -g -x POWERLINE_COMMAND powerline
		end
	end
	function _powerline_update -v POWERLINE_COMMAND
		eval "
		function fish_prompt
			$POWERLINE_COMMAND shell left --last_exit_code=\$status --last_pipe_status=\$status
		end
		function fish_right_prompt
			$POWERLINE_COMMAND shell right --last_exit_code=\$status --last_pipe_status=\$status
		end
		"
	end
	_powerline_update
end
