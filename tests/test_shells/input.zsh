unsetopt promptsp transientrprompt
POWERLINE_COMMAND=( $PWD/scripts/powerline -p $PWD/powerline/config_files )
POWERLINE_COMMAND=( $POWERLINE_COMMAND -t default_leftonly.segment_data.hostname.args.only_if_ssh=false )
POWERLINE_COMMAND=( $POWERLINE_COMMAND -c ext.shell.theme=default_leftonly )
VIRTUAL_ENV=
source powerline/bindings/zsh/powerline.zsh ; cd tests/shell/3rd
cd .git
cd ..
VIRTUAL_ENV="$HOME/.virtenvs/some-virtual-environment"
VIRTUAL_ENV=
bash -c 'echo $$>pid ; while true ; do sleep 0.1s ; done' &
false
select abc in def ghi jkl
do
	echo $abc
	break
done
1
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
true is the last line
exit
