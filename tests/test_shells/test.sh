#!/bin/sh
. tests/common.sh

enter_suite shells

if test "x$1" = "x--fast" ; then
	FAST=1
	shift
fi
ONLY_SHELL="$1"
ONLY_TEST_TYPE="$2"
ONLY_TEST_CLIENT="$3"

if ! test -z "$ONLY_SHELL$ONLY_TEST_TYPE$ONLY_TEST_CLIENT" ; then
	FAST=
fi

export PYTHON

if test "x$ONLY_SHELL" = "x--help" ; then
cat << EOF
Usage:
	$0 [[[ONLY_SHELL | ""] (ONLY_TEST_TYPE | "")] (ONLY_TEST_CLIENT | "")]

ONLY_SHELL: execute only tests for given shell
ONLY_TEST_TYPE: execute only "daemon" or "nodaemon" tests
ONLY_TEST_CLIENT: use only given test client (one of C, python, render, shell)
EOF
exit 0
fi

check_screen_log() {
	TEST_TYPE="$1"
	TEST_CLIENT="$2"
	SH="$3"
	if test -e tests/test_shells/${SH}.${TEST_TYPE}.ok ; then
		diff -a -u tests/test_shells/${SH}.${TEST_TYPE}.ok tests/shell/${SH}.${TEST_TYPE}.${TEST_CLIENT}.log
		return $?
	elif test -e tests/test_shells/${SH}.ok ; then
		diff -a -u tests/test_shells/${SH}.ok tests/shell/${SH}.${TEST_TYPE}.${TEST_CLIENT}.log
		return $?
	else
		cat tests/shell/${SH}.${TEST_TYPE}.${TEST_CLIENT}.log
		return 1
	fi
}

# HACK: get newline for use in strings given that "\n" and $'' do not work.
NL="$(printf '\nE')"
NL="${NL%E}"

print_full_output() {
	TEST_TYPE="$1"
	TEST_CLIENT="$2"
	SH="$3"
	echo "Full output:"
	echo '============================================================'
	cat tests/shell/${SH}.${TEST_TYPE}.${TEST_CLIENT}.full.log
	echo
	echo '____________________________________________________________'
	if test "x$POWERLINE_TEST_NO_CAT_V" != "x1" ; then
		echo "Full output (cat -v):"
		echo '============================================================'
		cat -v tests/shell/${SH}.${TEST_TYPE}.${TEST_CLIENT}.full.log
		echo
		echo '____________________________________________________________'
	fi
}

do_run_test() {
	TEST_TYPE="$1"
	shift
	TEST_CLIENT="$1"
	shift
	SH="$1"

	local wait_for_echo_arg=
	if ( \
		test "x${SH}" = "xdash" \
		|| ( \
			test "x${SH}" = "xpdb" \
			&& ( \
				( \
					test "$PYTHON_VERSION_MAJOR" -eq 3 \
					&& test "$PYTHON_VERSION_MINOR" -eq 2 \
					&& test "$PYTHON_IMPLEMENTATION" = "CPython" \
				) \
				|| test "$PYTHON_IMPLEMENTATION" = "PyPy" \
			) \
		) \
	) ; then
		wait_for_echo_arg="--wait-for-echo"
	fi
	"${PYTHON}" tests/test_shells/run_script.py \
		$wait_for_echo_arg --type=${TEST_TYPE} --client=${TEST_CLIENT} --shell=${SH} \
		"$@"
	if ! check_screen_log ${TEST_TYPE} ${TEST_CLIENT} ${SH} ; then
		echo '____________________________________________________________'
		if test "x$POWERLINE_TEST_NO_CAT_V" != "x1" ; then
			# Repeat the diff to make it better viewable in travis output
			echo "Diff (cat -v):"
			echo '============================================================'
			check_screen_log  ${TEST_TYPE} ${TEST_CLIENT} ${SH} | cat -v
			echo '____________________________________________________________'
		fi
		echo -n "Failed ${SH}. "
		print_full_output ${TEST_TYPE} ${TEST_CLIENT} ${SH}
		case ${SH} in
			*ksh)
				${SH} -c 'echo ${KSH_VERSION}'
				;;
			dash)
				# ?
				;;
			busybox)
				busybox --help
				;;
			*)
				${SH} --version
				;;
		esac
		if which dpkg >/dev/null ; then
			dpkg -s ${SH}
		fi
		return 1
	fi
	return 0
}

run_test() {
	TEST_TYPE="$1"
	TEST_CLIENT="$2"
	SH="$3"
	local attempts=3
	if test -n "$ONLY_SHELL$ONLY_TEST_TYPE$ONLY_TEST_CLIENT" ; then
		attempts=1
	fi
	while test $attempts -gt 0 ; do
		rm -f tests/shell/${SH}.${TEST_TYPE}.${TEST_CLIENT}.log
		rm -f tests/shell/${SH}.${TEST_TYPE}.${TEST_CLIENT}.full.log
		do_run_test "$@" && return 0
		attempts=$(( attempts - 1 ))
	done
	return 1
}

test -d tests/shell && rm -r tests/shell
mkdir tests/shell
git init tests/shell/3rd
git --git-dir=tests/shell/3rd/.git checkout -b BRANCH
export DIR1="[32m"
export DIR2=""
mkdir tests/shell/3rd/"$DIR1"
mkdir tests/shell/3rd/"$DIR2"
mkdir tests/shell/3rd/'\[\]'
mkdir tests/shell/3rd/'%%'
mkdir tests/shell/3rd/'#[bold]'
mkdir tests/shell/3rd/'(echo)'
mkdir tests/shell/3rd/'$(echo)'
mkdir tests/shell/3rd/'`echo`'
mkdir tests/shell/3rd/'«Unicode!»'

mkdir tests/shell/fish_home
mkdir tests/shell/fish_home/fish
mkdir tests/shell/fish_home/fish/generated_completions
cp -r tests/test_shells/ipython_home tests/shell

mkdir tests/shell/path
ln -s "$(which "${PYTHON}")" tests/shell/path/python
ln -s "$(which env)" tests/shell/path
ln -s "$(which git)" tests/shell/path
ln -s "$(which sleep)" tests/shell/path
ln -s "$(which cat)" tests/shell/path
ln -s "$(which false)" tests/shell/path
ln -s "$(which true)" tests/shell/path
ln -s "$(which kill)" tests/shell/path
ln -s "$(which echo)" tests/shell/path
ln -s "$(which which)" tests/shell/path
ln -s "$(which dirname)" tests/shell/path
ln -s "$(which wc)" tests/shell/path
ln -s "$(which stty)" tests/shell/path
ln -s "$(which cut)" tests/shell/path
ln -s "$(which bc)" tests/shell/path
ln -s "$(which expr)" tests/shell/path
ln -s "$(which mktemp)" tests/shell/path
ln -s "$(which grep)" tests/shell/path
ln -s "$(which sed)" tests/shell/path
ln -s "$(which rm)" tests/shell/path
ln -s "$(which tr)" tests/shell/path
ln -s "$(which uname)" tests/shell/path
ln -s "$(which test)" tests/shell/path
ln -s "$(which pwd)" tests/shell/path
ln -s "$(which hostname)" tests/shell/path
ln -s ../../test_shells/bgscript.sh tests/shell/path
ln -s ../../test_shells/waitpid.sh tests/shell/path
if which socat ; then
	ln -s "$(which socat)" tests/shell/path
fi
for pexe in powerline powerline-config powerline-render powerline.sh powerline.py ; do
	if test -e scripts/$pexe ; then
		ln -s "$PWD/scripts/$pexe" tests/shell/path
	elif test -e client/$pexe ; then
		ln -s "$PWD/client/$pexe" tests/shell/path
	elif which $pexe ; then
		ln -s "$(which $pexe)" tests/shell/path
	else
		echo "Executable $pexe was not found"
		exit 1
	fi
done

ln -s python tests/shell/path/pdb
PDB_PYTHON=pdb
ln -s python tests/shell/path/ipython
IPYTHON_PYTHON=ipython

if test -z "$POWERLINE_RC_EXE" ; then
	if which rc-status >/dev/null ; then
		# On Gentoo `rc` executable is from OpenRC. Thus app-shells/rc instals 
		# `rcsh` executable.
		POWERLINE_RC_EXE=rcsh
	else
		POWERLINE_RC_EXE=rc
	fi
fi

if which "$POWERLINE_RC_EXE" >/dev/null ; then
	ln -s "$(which $POWERLINE_RC_EXE)" tests/shell/path/rc
fi

for exe in bash zsh busybox fish tcsh mksh dash ; do
	if which $exe >/dev/null ; then
		if test "$exe" = "fish" ; then
			fish_version="$(fish --version 2>&1)"
			fish_version="${fish_version##* }"
			fish_version_major="${fish_version%%.*}"
			if test "$fish_version_major" != "$fish_version" ; then
				# No dot is in development version compiled by bot-ci
				fish_version_minor="${fish_version#*.}"
				fish_version_patch="${fish_version_minor#*.}"
				fish_version_dev="${fish_version_patch#*-}"
				if test "$fish_version_dev" = "$fish_version_patch" ; then
					fish_version_dev=""
				fi
				fish_version_minor="${fish_version_minor%%.*}"
				fish_version_patch="${fish_version_patch%%-*}"
				if test $fish_version_major -lt 2 || ( \
					test $fish_version_major -eq 2 && (\
						test $fish_version_minor -lt 1 || (\
							test $fish_version_minor -eq 1 &&
							test $fish_version_patch -lt 2 && \
							test -z "$fish_version_dev"
						) \
					) \
				) ; then
					continue
				fi
			fi
		fi
		ln -s "$(which $exe)" tests/shell/path
	fi
done

mkdir tests/shell/home
export HOME="$PWD/tests/shell/home"

unset ENV

export ADDRESS="powerline-ipc-test-$$"
export PYTHON
echo "Powerline address: $ADDRESS"

check_test_client() {
	local executable="$1"
	local client_type="$2"
	local actual_mime_type="$(file --mime-type --brief --dereference "tests/shell/path/$executable" | cut -d/ -f1)"
	local expected_mime_type
	case "$client_type" in
		C)      expected_mime_type="application/x-executable" ;;
		python) expected_mime_type="text/x-python" ;;
		render) expected_mime_type="text/x-python" ;;
		shell)  expected_mime_type="text/x-shellscript" ;;
	esac
	expected_mime_type="${expected_mime_type%/*}"
	if test "$expected_mime_type" != "$actual_mime_type" ; then
		fail "MIME-$executable" "M" "Expected $executable to have MIME type $expected_mime_type, but got $actual_mime_type"
	fi
}

if test -z "${ONLY_SHELL}" || test "x${ONLY_SHELL%sh}" != "x${ONLY_SHELL}" || test "x${ONLY_SHELL}" = xbusybox || test "x${ONLY_SHELL}" = xrc ; then
	scripts/powerline-config shell command

	for TEST_TYPE in "daemon" "nodaemon" ; do
		if test "x$ONLY_TEST_TYPE" != "x" && test "x$ONLY_TEST_TYPE" != "x$TEST_TYPE" ; then
			continue
		fi
		if test x$FAST = x1 ; then
			if test $TEST_TYPE = daemon ; then
				VARIANTS=3
			else
				VARIANTS=4
			fi
			EXETEST="$(( ${RANDOM:-`date +%N | sed s/^0*//`} % $VARIANTS ))"
			echo "Execute tests: $EXETEST"
		fi

		if test $TEST_TYPE = daemon ; then
			sh -c '
				echo $$ > tests/shell/daemon_pid
				$PYTHON ./scripts/powerline-daemon -s$ADDRESS -f >tests/shell/daemon_log 2>&1
			' &
		fi
		echo "> Testing $TEST_TYPE"
		I=-1
		for POWERLINE_COMMAND in \
			powerline \
			powerline-render \
			powerline.py \
			powerline.sh
		do
			case "$POWERLINE_COMMAND" in
				powerline)        TEST_CLIENT=C ;;
				powerline-render) TEST_CLIENT=render ;;
				powerline.py)     TEST_CLIENT=python ;;
				powerline.sh)     TEST_CLIENT=shell ;;
			esac
			check_test_client "$POWERLINE_COMMAND" $TEST_CLIENT
			if test "$TEST_CLIENT" = render && test "$TEST_TYPE" = daemon ; then
				continue
			fi
			I="$(( I + 1 ))"
			if test "$TEST_CLIENT" = "C" && ! test -x scripts/powerline ; then
				if which powerline >/dev/null ; then
					POWERLINE_COMMAND=powerline
				else
					continue
				fi
			fi
			if test "$TEST_CLIENT" = "shell" && ! test -x tests/shell/path/socat ; then
				continue
			fi
			if test "x$ONLY_TEST_CLIENT" != "x" && test "x$TEST_CLIENT" != "x$ONLY_TEST_CLIENT" ; then
				continue
			fi
			export POWERLINE_COMMAND_ARGS="--socket $ADDRESS"
			export POWERLINE_COMMAND="$POWERLINE_COMMAND"
			echo ">> powerline command is ${POWERLINE_COMMAND:-empty}"
			J=-1
			for TEST_COMMAND in \
				"bash --norc --noprofile -i" \
				"zsh -f -i" \
				"fish -i" \
				"tcsh -f -i" \
				"busybox ash -i" \
				"mksh -i" \
				"dash -i" \
				"rc -i -p"
			do
				J="$(( J + 1 ))"
				if test x$FAST = x1 ; then
					if test $(( (I + J) % $VARIANTS )) -ne $EXETEST ; then
						continue
					fi
				fi
				SH="${TEST_COMMAND%% *}"
				# dash tests are not stable, see #931
				if test x$FAST$SH = x1dash ; then
					continue
				fi
				if test x$FAST$SH = x1fish ; then
					continue
				fi
				if test "x$ONLY_SHELL" != "x" && test "x$ONLY_SHELL" != "x$SH" ; then
					continue
				fi
				if ! test -x tests/shell/path/$SH ; then
					continue
				fi
				echo ">>> $(readlink "tests/shell/path/$SH")"
				if ! run_test $TEST_TYPE $TEST_CLIENT $TEST_COMMAND ; then
					fail "$SH-$TEST_TYPE-$TEST_CLIENT:test" F "Failed checking $TEST_COMMAND"
				fi
			done
		done
		if test $TEST_TYPE = daemon ; then
			$PYTHON ./scripts/powerline-daemon -s$ADDRESS -k
			wait $(cat tests/shell/daemon_pid)
			if ! test -z "$(cat tests/shell/daemon_log)" ; then
				echo '____________________________________________________________'
				echo "Daemon log:"
				echo '============================================================'
				cat tests/shell/daemon_log
				fail "$SH-$TEST_TYPE-$TEST_CLIENT:log" E "Non-empty daemon log for ${TEST_COMMAND}"
			fi
		fi
	done
fi

if $PYTHON scripts/powerline-daemon -s$ADDRESS > tests/shell/daemon_log_2 2>&1 ; then
	sleep 1
	$PYTHON scripts/powerline-daemon -s$ADDRESS -k
else
	fail "daemon:run" F "Daemon exited with status $?"
fi

if ! test -z "$(cat tests/shell/daemon_log_2)" ; then
	echo '____________________________________________________________'
	echo "Daemon log (2nd):"
	echo '============================================================'
	cat tests/shell/daemon_log_2
	fail "daemon:log" E "Daemon run with non-empty log"
fi

if ( test "x${ONLY_SHELL}" = "x" || test "x${ONLY_SHELL}" = "xzsh" ) \
	&& ( test "x${ONLY_TEST_TYPE}" = "x" || test "x${ONLY_TEST_TYPE}" = "xzpython" ) \
	&& zsh tests/test_shells/zsh_test_script.zsh 2>/dev/null; then
	echo "> zpython"
	if ! run_test zpython zpython zsh -f -i ; then
		fail "zsh-zpython:test" F "Failed checking zsh -f -i"
	fi
fi

if  test "x${ONLY_SHELL}" = "x" || test "x${ONLY_SHELL}" = "xpdb" ; then
	if test "$PYTHON_IMPLEMENTATION" != "PyPy" ; then
		if test "x${ONLY_TEST_TYPE}" = "x" || test "x${ONLY_TEST_TYPE}" = "xsubclass" ; then
			echo "> pdb subclass"
			if ! run_test subclass python $PDB_PYTHON "$PWD/tests/test_shells/pdb-main.py" ; then
				fail "pdb-subclass:test" F "Failed checking $PDB_PYTHON $PWD/tests/test_shells/pdb-main.py"
			fi
		fi
		if test "x${ONLY_TEST_TYPE}" = "x" || test "x${ONLY_TEST_TYPE}" = "xmodule" ; then
			echo "> pdb module"
			MODULE="powerline.bindings.pdb"
			if test "$PYTHON_MM" = "2.6" ; then
				MODULE="powerline.bindings.pdb.__main__"
			fi
			if ! run_test module python $PDB_PYTHON -m$MODULE "$PWD/tests/test_shells/pdb-script.py" ; then
				fail "pdb-module:test" F "Failed checking $PDB_PYTHON -m$MODULE $PWD/tests/test_shells/pdb-script"
			fi
		fi
	fi
fi

if test "x${ONLY_SHELL}" = "x" || test "x${ONLY_SHELL}" = "xipython" ; then
	if "${PYTHON}" -c "try: import IPython${NL}except ImportError: raise SystemExit(1)" ; then
		# Define some overrides which should be ignored by IPython.
		export POWERLINE_CONFIG_OVERRIDES='common.term_escape_style=fbterm'
		export POWERLINE_THEME_OVERRIDES='in.segments.left=[]'
		echo "> ipython"
		if ! run_test ipython ipython ${IPYTHON_PYTHON} -mIPython ; then
			fail "ipython:test" F "Failed checking ${IPYTHON_PYTHON} -mIPython"
		fi
		unset POWERLINE_THEME_OVERRIDES
		unset POWERLINE_CONFIG_OVERRIDES
	fi
fi

if test $FAILED -eq 0 ; then
	rm -r tests/shell
fi

exit_suite
