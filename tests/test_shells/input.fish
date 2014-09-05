set fish_function_path "$PWD/powerline/bindings/fish" $fish_function_path
while jobs | grep fish_update_completions
	sleep 1
end
powerline-setup
set POWERLINE_COMMAND "$POWERLINE_COMMAND -t default_leftonly.segment_data.hostname.args.only_if_ssh=false"
set POWERLINE_COMMAND "$POWERLINE_COMMAND -c ext.shell.theme=default_leftonly"
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
set POWERLINE_COMMAND "$POWERLINE_COMMAND -c ext.shell.theme=default"
set -g fish_key_bindings fish_vi_key_bindings
ii
false
true is the last line
exit
