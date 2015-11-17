set_theme_option() {
	export POWERLINE_THEME_OVERRIDES="${POWERLINE_THEME_OVERRIDES};$1=$2"
}
set_theme() {
	export POWERLINE_CONFIG_OVERRIDES="ext.shell.theme=$1"
}
set_theme_option default_leftonly.segment_data.hostname.args.only_if_ssh false
ABOVE_LEFT='[{
    "left": [
        {
            "function": "powerline.segments.common.env.environment",
            "args": {"variable": "DISPLAYED_ENV_VAR"}
        }
    ]
}]'
ABOVE_FULL='[{
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
set_theme default_leftonly
export VIRTUAL_ENV=
source powerline/bindings/bash/powerline.sh
cd tests/shell/3rd
cd .git
cd ..
VIRTUAL_ENV="$HOME/.virtenvs/some-virtual-environment"
VIRTUAL_ENV=
bgscript.sh & waitpid.sh
false
kill `cat pid` ; sleep 1s
set_theme_option default_leftonly.segment_data.hostname.display false
set_theme_option default_leftonly.segment_data.user.display false
echo '
abc
def
'
cd "$DIR1"
cd ../"$DIR2"
cd ../'\[\]'
cd ../'%%'
cd ../'#[bold]'
cd ../'(echo)'
cd ../'$(echo)'
cd ../'`echo`'
cd ../'«Unicode!»'
set_theme_option default_leftonly.segments.above "$ABOVE_LEFT"
export DISPLAYED_ENV_VAR=foo
unset DISPLAYED_ENV_VAR
set_theme_option default_leftonly.segments.above "$ABOVE_FULL"
export DISPLAYED_ENV_VAR=foo
unset DISPLAYED_ENV_VAR
set_theme_option default_leftonly.segments.above
set_theme_option default_leftonly.dividers.left.hard \$ABC
false
true is the last line
exit
