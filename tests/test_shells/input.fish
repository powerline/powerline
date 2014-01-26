set POWERLINE_COMMAND "$PWD/scripts/powerline -p $PWD/powerline/config_files"
set POWERLINE_COMMAND "$POWERLINE_COMMAND -t default_leftonly.segment_data.hostname.args.only_if_ssh=false"
set POWERLINE_COMMAND "$POWERLINE_COMMAND -c ext.shell.theme=default_leftonly"
set VIRTUAL_ENV
set fish_function_path $fish_function_path "$PWD/powerline/bindings/fish"
powerline-setup ; cd tests/shell/3rd
cd .git
cd ..
set VIRTUAL_ENV "$HOME/.virtenvs/some-virtual-environment"
set VIRTUAL_ENV
bash -c 'echo $$>pid ; while true ; do sleep 0.1s ; done' &
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
false
true is the last line
exit
