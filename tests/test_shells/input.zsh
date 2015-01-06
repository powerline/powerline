unset HOME
unsetopt promptsp notransientrprompt
setopt interactivecomments
setopt autonamedirs
if test -z "$POWERLINE_NO_ZSH_ZPYTHON" ; then
	function set_theme_option() {
		POWERLINE_THEME_OVERRIDES[$1]=$2
		powerline-reload-config
	}
	function set_theme() {
		typeset -A POWERLINE_CONFIG_OVERRIDES
		POWERLINE_CONFIG_OVERRIDES=(
			ext.shell.theme $1
		)
		powerline-reload-config
	}
else
	function set_theme_option() {
		POWERLINE_COMMAND="$POWERLINE_COMMAND -t $1=$2"
	}
	function set_theme() {
		POWERLINE_COMMAND="$POWERLINE_COMMAND -c ext.shell.theme=$1"
	}
fi
source powerline/bindings/zsh/powerline.zsh
typeset -gA POWERLINE_CONFIG_OVERRIDES POWERLINE_THEME_OVERRIDES
set_theme_option default_leftonly.segment_data.hostname.args.only_if_ssh false
set_theme_option default.segment_data.hostname.args.only_if_ssh false
set_theme default_leftonly
export VIRTUAL_ENV=
cd tests/shell/3rd
cd .git
cd ..
VIRTUAL_ENV="/home/USER/.virtenvs/some-virtual-environment"
VIRTUAL_ENV=
bgscript.sh & waitpid.sh
false
kill `cat pid` ; sleep 1s
cd "$DIR1"
cd ../"$DIR2"
cd ../'\[\]'
cd ../'%%'
cd ../'#[bold]'
cd ../'(echo)'
cd ../'$(echo)'
cd ../'`echo`'
cd ../'«Unicode!»'
cd ..
bindkey -v ; set_theme default


echo abc
false
set_theme_option default.segment_data.hostname.display false
set_theme_option default.segment_data.user.display false
select abc in def ghi jkl
do
	echo $abc
	break
done
1
cd .
cd .
hash -d foo=$PWD:h ; cd .
set_theme_option default.dividers.left.hard \$ABC
true
true is the last line
exit
