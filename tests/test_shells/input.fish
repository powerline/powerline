function set_theme_option
	set -g -x POWERLINE_THEME_OVERRIDES "$POWERLINE_THEME_OVERRIDES;$argv[1]=$argv[2]"
end
function set_theme
	set -g -x POWERLINE_CONFIG_OVERRIDES "ext.shell.theme=$argv"
end
set -g -x POWERLINE_
set -g ABOVE_LEFT '[{
	"left": [
		{
			"function": "powerline.segments.common.env.environment",
			"args": {"variable": "DISPLAYED_ENV_VAR"}
		}
	]
}]'
set -g ABOVE_FULL '[{
	"left": [
		{
			"type": "string",
			"name": "background",
			"draw_hard_divider": false,
			"width": "auto"
		}
	],
	"right": [
		{
			"function": "powerline.segments.common.env.environment",
			"args": {"variable": "DISPLAYED_ENV_VAR"}
		}
	]
}]'
set_theme_option default_leftonly.segment_data.hostname.args.only_if_ssh false
set_theme default_leftonly
set fish_function_path "$PWD/powerline/bindings/fish" $fish_function_path
while jobs | grep fish_update_completions
	sleep 1
end
powerline-setup
setenv VIRTUAL_ENV
cd tests/shell/3rd
cd .git
cd ..
setenv VIRTUAL_ENV "$HOME/.virtenvs/some-virtual-environment"
setenv VIRTUAL_ENV
bgscript.sh & waitpid.sh
false
kill (cat pid) ; sleep 1s
cd "$DIR1"
cd ../"$DIR2"
cd ../'\[\]'
cd ../'%%'
cd ../'#[bold]'
cd ../'(echo)'
cd ../'$(echo)'
cd ../'`echo`'
cd ../'«Unicode!»'
set_theme default
set_theme_option default.segments.above "$ABOVE_LEFT"
set -g -x DISPLAYED_ENV_VAR foo
set -g -x -e DISPLAYED_ENV_VAR
set_theme_option default.segments.above "$ABOVE_FULL"
set -g -x DISPLAYED_ENV_VAR foo
set -g -x -e DISPLAYED_ENV_VAR
set_theme_option default.segments.above ''
set -g fish_key_bindings fish_vi_key_bindings
ii
false
true is the last line
exit
