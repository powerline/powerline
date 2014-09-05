source powerline/bindings/tcsh/powerline.tcsh
set POWERLINE_COMMAND=$POWERLINE_COMMAND:q" -t default_leftonly.segment_data.hostname.args.only_if_ssh=false -c ext.shell.theme=default_leftonly"
unsetenv VIRTUAL_ENV
cd tests/shell/3rd
cd .git
cd ..
setenv VIRTUAL_ENV "/home/foo/.virtenvs/some-virtual-environment"
unsetenv VIRTUAL_ENV
bgscript.sh & waitpid.sh
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
