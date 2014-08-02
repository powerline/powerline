unsetopt promptsp notransientrprompt
setopt interactivecomments
# POWERLINE_CONFIG_PATH=$PWD/powerline/config_files
# POWERLINE_THEME_CONFIG=( default_leftonly.segment_data.hostname.args.only_if_ssh=false )
# POWERLINE_CONFIG=( ext.shell.theme=default_leftonly )
POWERLINE_NO_ZSH_ZPYTHON=1  # TODO: make tests work with zsh/zpython
source powerline/bindings/zsh/powerline.zsh
POWERLINE_COMMAND=( $POWERLINE_COMMAND -p $PWD/powerline/config_files )
POWERLINE_COMMAND=( $POWERLINE_COMMAND -t default_leftonly.segment_data.hostname.args.only_if_ssh=false )
POWERLINE_COMMAND=( $POWERLINE_COMMAND -c ext.shell.theme=default_leftonly )
export VIRTUAL_ENV=
cd tests/shell/3rd
cd .git
cd ..
VIRTUAL_ENV="$HOME/.virtenvs/some-virtual-environment"
VIRTUAL_ENV=
bash -c 'echo $$>pid ; while true ; do sleep 0.1s ; done' &
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
POWERLINE_COMMAND=( $POWERLINE_COMMAND[1,4] ${${POWERLINE_COMMAND[5]}/_leftonly} ) ; bindkey -v


echo abc
false
POWERLINE_COMMAND=( $POWERLINE_COMMAND -t default.segment_data.hostname.display=false )
POWERLINE_COMMAND=( $POWERLINE_COMMAND -t default.segment_data.user.display=false )
select abc in def ghi jkl
do
	echo $abc
	break
done
1
true is the last line
exit
