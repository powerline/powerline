unset HOME
unsetopt promptsp notransientrprompt
setopt interactivecomments
setopt autonamedirs
# POWERLINE_CONFIG_PATH=$PWD/powerline/config_files
# POWERLINE_THEME_CONFIG=( default_leftonly.segment_data.hostname.args.only_if_ssh=false )
# POWERLINE_CONFIG=( ext.shell.theme=default_leftonly )
POWERLINE_NO_ZSH_ZPYTHON=1  # TODO: make tests work with zsh/zpython
source powerline/bindings/zsh/powerline.zsh
POWERLINE_COMMAND="$POWERLINE_COMMAND -t default_leftonly.segment_data.hostname.args.only_if_ssh=false"
POWERLINE_COMMAND="$POWERLINE_COMMAND -c ext.shell.theme=default_leftonly"
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
cd ..
POWERLINE_COMMAND="${POWERLINE_COMMAND//_leftonly}" ; bindkey -v


echo abc
false
POWERLINE_COMMAND="$POWERLINE_COMMAND -t default.segment_data.hostname.display=false"
POWERLINE_COMMAND="$POWERLINE_COMMAND -t default.segment_data.user.display=false"
select abc in def ghi jkl
do
	echo $abc
	break
done
1
cd .
cd .
hash -d foo=$PWD:h ; cd .
POWERLINE_COMMAND="$POWERLINE_COMMAND -t default.dividers.left.hard=\$ABC"
true
true is the last line
exit
