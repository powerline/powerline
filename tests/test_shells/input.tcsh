setenv POWERLINE_COMMAND $PWD:q/scripts/powerline" -p "$PWD:q/powerline/config_files" -t default_leftonly.segment_data.hostname.args.only_if_ssh=false -c ext.shell.theme=default_leftonly"
unsetenv VIRTUAL_ENV
source powerline/bindings/tcsh/powerline.tcsh ; cd tests/shell/3rd
cd .git
cd ..
setenv VIRTUAL_ENV $HOME:q"/.virtenvs/some-virtual-environment"
unsetenv VIRTUAL_ENV
bash -c 'echo $$>pid ; while true ; do sleep 0.1s ; done' &
false # Warning: currently tcsh bindings do not support job count
kill `cat pid` ; sleep 1s
cd $DIR1:q
cd ../$DIR2:q
cd ../'\[\]'
cd ../'%%'
cd ../'#[bold]'
cd ../'(echo)'
cd ../'$(echo)'
cd ../'`echo`'
false
true is the last line
exit
