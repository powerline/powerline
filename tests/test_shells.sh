#!/bin/sh
FAILED=0

if [ "$(echo '\e')" != '\e' ] ; then
	safe_echo() {
		echo -E "$@"
	}
else
	safe_echo() {
		echo "$@"
	}
fi

mkdir tests/shell
git init tests/shell/3rd
git --git-dir=tests/shell/3rd/.git checkout -b BRANCH

INPUT='
POWERLINE_COMMAND="$PWD/scripts/powerline -p $PWD/powerline/config_files"
VIRTUAL_ENV=
COLUMNS=80
source powerline/bindings/bash/powerline.sh ; cd tests/shell/3rd
POWERLINE_COMMAND="$POWERLINE_COMMAND -c ext.shell.theme=default_leftonly"
cd .git
cd ..
VIRTUAL_ENV="$HOME/.virtenvs/some-virtual-environment"
VIRTUAL_ENV=
bash -c "echo \$\$>pid ; while true ; do sleep 0.1s ; done" &
false
kill `cat pid` ; sleep 1s
false
POWERLINE_COMMAND="$POWERLINE_COMMAND -t default_leftonly.segment_data.hostname.args.only_if_ssh=false"
exit
'

OUTPUT="`safe_echo "$INPUT" | LANG=C bash -i 2>&1 | sed 's/ \+\x08\+//g' | tail -n +6`"
OUTPUT="`safe_echo "$OUTPUT" | sed -e s/$(cat tests/shell/3rd/pid)/PID/g -e 's/\x1b/\\\\e/g'`"

EXPECTED_OUTPUT='\e[0;38;5;231;48;5;31;1m zyx \e[0;38;5;31;48;5;240;22m \e[0;38;5;250;48;5;240m⋯ \e[0;38;5;245;48;5;240;22m \e[0;38;5;250;48;5;240mtests \e[0;38;5;245;48;5;240;22m \e[0;38;5;250;48;5;240mshell \e[0;38;5;245;48;5;240;22m \e[0;38;5;252;48;5;240;1m3rd \e[0;38;5;240;49;22m \e[0mPOWERLINE_COMMAND="$POWERLINE_COMMAND -c ext.shell.theme=default_leftonly"
\e[0;38;5;231;48;5;31;1m zyx \e[0;38;5;31;48;5;236;22m \e[0;38;5;250;48;5;236m BRANCH \e[0;38;5;236;48;5;240;22m \e[0;38;5;250;48;5;240m⋯ \e[0;38;5;245;48;5;240;22m \e[0;38;5;250;48;5;240mtests \e[0;38;5;245;48;5;240;22m \e[0;38;5;250;48;5;240mshell \e[0;38;5;245;48;5;240;22m \e[0;38;5;252;48;5;240;1m3rd \e[0;38;5;240;49;22m \e[0mcd .git
\e[0;38;5;231;48;5;31;1m zyx \e[0;38;5;31;48;5;236;22m \e[0;38;5;250;48;5;236m BRANCH \e[0;38;5;236;48;5;240;22m \e[0;38;5;250;48;5;240m⋯ \e[0;38;5;245;48;5;240;22m \e[0;38;5;250;48;5;240mshell \e[0;38;5;245;48;5;240;22m \e[0;38;5;250;48;5;240m3rd \e[0;38;5;245;48;5;240;22m \e[0;38;5;252;48;5;240;1m.git \e[0;38;5;240;49;22m \e[0mcd ..
\e[0;38;5;231;48;5;31;1m zyx \e[0;38;5;31;48;5;236;22m \e[0;38;5;250;48;5;236m BRANCH \e[0;38;5;236;48;5;240;22m \e[0;38;5;250;48;5;240m⋯ \e[0;38;5;245;48;5;240;22m \e[0;38;5;250;48;5;240mtests \e[0;38;5;245;48;5;240;22m \e[0;38;5;250;48;5;240mshell \e[0;38;5;245;48;5;240;22m \e[0;38;5;252;48;5;240;1m3rd \e[0;38;5;240;49;22m \e[0mVIRTUAL_ENV="$HOME/.virtenvs/some-virtual-environment"
\e[0;38;5;231;48;5;31;1m zyx \e[0;38;5;31;48;5;74;22m \e[0;38;5;231;48;5;74mⓔ  some-virtual-environment \e[0;38;5;74;48;5;236;22m \e[0;38;5;250;48;5;236m BRANCH \e[0;38;5;236;48;5;240;22m \e[0;38;5;250;48;5;240m⋯ \e[0;38;5;245;48;5;240;22m \e[0;38;5;250;48;5;240mtests \e[0;38;5;245;48;5;240;22m \e[0;38;5;250;48;5;240mshell \e[0;38;5;245;48;5;240;22m \e[0;38;5;252;48;5;240;1m3rd \e[0;38;5;240;49;22m \e[0mVIRTUAL_ENV=
\e[0;38;5;231;48;5;31;1m zyx \e[0;38;5;31;48;5;236;22m \e[0;38;5;250;48;5;236m BRANCH \e[0;38;5;236;48;5;240;22m \e[0;38;5;250;48;5;240m⋯ \e[0;38;5;245;48;5;240;22m \e[0;38;5;250;48;5;240mtests \e[0;38;5;245;48;5;240;22m \e[0;38;5;250;48;5;240mshell \e[0;38;5;245;48;5;240;22m \e[0;38;5;252;48;5;240;1m3rd \e[0;38;5;240;49;22m \e[0mbash -c "echo \$\$>pid ; while true ; do sleep 0.1s ; done" &
[1] PID
\e[0;38;5;231;48;5;31;1m zyx \e[0;38;5;31;48;5;236;22m \e[0;38;5;250;48;5;236m BRANCH \e[0;38;5;236;48;5;240;22m \e[0;38;5;250;48;5;240m⋯ \e[0;38;5;245;48;5;240;22m \e[0;38;5;250;48;5;240mtests \e[0;38;5;245;48;5;240;22m \e[0;38;5;250;48;5;240mshell \e[0;38;5;245;48;5;240;22m \e[0;38;5;252;48;5;240;1m3rd \e[0;38;5;240;48;5;166;22m \e[0;38;5;220;48;5;166m1 \e[0;38;5;166;49;22m \e[0mfalse
\e[0;38;5;231;48;5;31;1m zyx \e[0;38;5;31;48;5;236;22m \e[0;38;5;250;48;5;236m BRANCH \e[0;38;5;236;48;5;240;22m \e[0;38;5;250;48;5;240m⋯ \e[0;38;5;245;48;5;240;22m \e[0;38;5;250;48;5;240mtests \e[0;38;5;245;48;5;240;22m \e[0;38;5;250;48;5;240mshell \e[0;38;5;245;48;5;240;22m \e[0;38;5;252;48;5;240;1m3rd \e[0;38;5;240;48;5;166;22m \e[0;38;5;220;48;5;166m1 \e[0;38;5;166;48;5;52;22m \e[0;38;5;231;48;5;52m1 \e[0;38;5;52;49;22m \e[0mkill `cat pid` ; sleep 1s
[1]+  Terminated              bash -c "echo \$\$>pid ; while true ; do sleep 0.1s ; done"
\e[0;38;5;231;48;5;31;1m zyx \e[0;38;5;31;48;5;236;22m \e[0;38;5;250;48;5;236m BRANCH \e[0;38;5;236;48;5;240;22m \e[0;38;5;250;48;5;240m⋯ \e[0;38;5;245;48;5;240;22m \e[0;38;5;250;48;5;240mtests \e[0;38;5;245;48;5;240;22m \e[0;38;5;250;48;5;240mshell \e[0;38;5;245;48;5;240;22m \e[0;38;5;252;48;5;240;1m3rd \e[0;38;5;240;49;22m \e[0mfalse
\e[0;38;5;231;48;5;31;1m zyx \e[0;38;5;31;48;5;236;22m \e[0;38;5;250;48;5;236m BRANCH \e[0;38;5;236;48;5;240;22m \e[0;38;5;250;48;5;240m⋯ \e[0;38;5;245;48;5;240;22m \e[0;38;5;250;48;5;240mtests \e[0;38;5;245;48;5;240;22m \e[0;38;5;250;48;5;240mshell \e[0;38;5;245;48;5;240;22m \e[0;38;5;252;48;5;240;1m3rd \e[0;38;5;240;48;5;52;22m \e[0;38;5;231;48;5;52m1 \e[0;38;5;52;49;22m \e[0mPOWERLINE_COMMAND="$POWERLINE_COMMAND -t default_leftonly.segment_data.hostname.args.only_if_ssh=false"
\e[0;38;5;220;48;5;166m  zyx-desktop \e[0;38;5;166;48;5;31;22m \e[0;38;5;231;48;5;31;1mzyx \e[0;38;5;31;48;5;236;22m \e[0;38;5;250;48;5;236m BRANCH \e[0;38;5;236;48;5;240;22m \e[0;38;5;250;48;5;240m⋯ \e[0;38;5;245;48;5;240;22m \e[0;38;5;250;48;5;240mtests \e[0;38;5;245;48;5;240;22m \e[0;38;5;250;48;5;240mshell \e[0;38;5;245;48;5;240;22m \e[0;38;5;252;48;5;240;1m3rd \e[0;38;5;240;49;22m \e[0mexit
exit'

if [ "b$EXPECTED_OUTPUT" != "b$OUTPUT" ] ; then
	safe_echo "$EXPECTED_OUTPUT" > tests/shell/expected
	safe_echo "$OUTPUT" > tests/shell/actual
	diff -u tests/shell/expected tests/shell/actual
	rm tests/shell/expected tests/shell/actual
	FAILED=1
fi

rm -r tests/shell

exit $FAILED
