#!/bin/sh
. tests/bot-ci/scripts/common/main.sh
set +x

: ${PYTHON:=python}
FAIL_SUMMARY=""
FAILED=0
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

run() {
	TEST_TYPE="$1"
	shift
	TEST_CLIENT="$1"
	shift
	SH="$1"
	shift
	local local_path="$PWD/tests/shell/path:$PWD/scripts"
	if test "x$SH" = "xfish" ; then
		local_path="${local_path}:/usr/bin:/bin"
	fi
	if test $TEST_TYPE = daemon ; then
		local additional_prompts=1
	else
		local additional_prompts=
	fi
	env -i \
		LANG=en_US.UTF-8 \
		PATH="$local_path" \
		TERM="screen-256color" \
		COLUMNS="${COLUMNS}" \
		LINES="${LINES}" \
		TEST_TYPE="${TEST_TYPE}" \
		TEST_CLIENT="${TEST_CLIENT}" \
		SH="${SH}" \
		DIR1="${DIR1}" \
		POWERLINE_NO_ZSH_ZPYTHON="$(test $TEST_TYPE = zpython || echo 1)" \
		DIR2="${DIR2}" \
		XDG_CONFIG_HOME="$PWD/tests/shell/fish_home" \
		IPYTHONDIR="$PWD/tests/shell/ipython_home" \
		PYTHONPATH="${PWD}${PYTHONPATH:+:}$PYTHONPATH" \
		POWERLINE_CONFIG_OVERRIDES="${POWERLINE_CONFIG_OVERRIDES}" \
		POWERLINE_THEME_OVERRIDES="${POWERLINE_THEME_OVERRIDES}" \
		POWERLINE_SHELL_CONTINUATION=$additional_prompts \
		POWERLINE_SHELL_SELECT=$additional_prompts \
		POWERLINE_CONFIG_PATHS="$PWD/powerline/config_files" \
		POWERLINE_COMMAND_ARGS="${POWERLINE_COMMAND_ARGS}" \
		POWERLINE_COMMAND="${POWERLINE_COMMAND}" \
		"$@"
}

# HACK: get newline for use in strings given that "\n" and $'' do not work.
NL="$(printf '\nE')"
NL="${NL%E}"

do_run_test() {
	TEST_TYPE="$1"
	shift
	TEST_CLIENT="$1"
	shift
	SH="$1"
	SESNAME="powerline-shell-test-${SH}-$$"

	# Note: when running screen with setuid libc unsets LD_LIBRARY_PATH, so it 
	# cannot be added to the `env -i` call above.
	run "${TEST_TYPE}" "${TEST_CLIENT}" "${SH}" \
		screen -L -c tests/test_shells/screenrc -d -m -S "$SESNAME" \
			env LD_LIBRARY_PATH="${LD_LIBRARY_PATH}" \
			"$@"
	while ! screen -S "$SESNAME" -X readreg a tests/test_shells/input.$SH ; do
		sleep 0.1s
	done
	# Wait for screen to initialize
	sleep 1
	local attempts=100
	while ! screen -S "$SESNAME" -p 0 -X width 300 1 >/dev/null ; do
		sleep 0.1s
		attempts=$(( attempts - 1 ))
		if test $attempts -eq 0 ; then
			echo "Waiting for too long: assuming test failed"
			echo "Failed ${SH}. Full output:"
			echo '============================================================'
			cat tests/shell/${SH}.${TEST_TYPE}.${TEST_CLIENT}.full.log
			echo '____________________________________________________________'
			if test "x$POWERLINE_TEST_NO_CAT_V" != "x1" ; then
				echo "Full output (cat -v):"
				echo '============================================================'
				cat -v tests/shell/${SH}.${TEST_TYPE}.${TEST_CLIENT}.full.log
				echo '____________________________________________________________'
			fi
			return 1
		fi
	done
	if ( \
		test "x${SH}" = "xdash" \
		|| ( \
			test "x${SH}" = "xipython" \
			&& test "$PYTHON_IMPLEMENTATION" = "PyPy" \
		) \
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
		# If I do not use this hack for dash then output will look like
		#
		#     command1
		#     command2
		#     …
		#     prompt1> prompt2> …
		while read -r line ; do
			if test "$(screen -S "$SESNAME" -p 0 -X stuff "$line$NL")" = "No screen session found." ; then
				break
			fi
			sleep 1
		done < tests/test_shells/input.$SH
	else
		screen -S "$SESNAME" -p 0 -X paste a
	fi
	# Wait for screen to exit (sending command to non-existing screen session 
	# fails; when launched instance exits corresponding session is deleted)
	while screen -S "$SESNAME" -X blankerprg "" > /dev/null ; do
		sleep 0.1s
	done
	${PYTHON} ./tests/test_shells/postproc.py ${TEST_TYPE} ${TEST_CLIENT} ${SH}
	rm -f tests/shell/3rd/pid
	if ! check_screen_log ${TEST_TYPE} ${TEST_CLIENT} ${SH} ; then
		echo '____________________________________________________________'
		if test "x$POWERLINE_TEST_NO_CAT_V" != "x1" ; then
			# Repeat the diff to make it better viewable in travis output
			echo "Diff (cat -v):"
			echo '============================================================'
			check_screen_log  ${TEST_TYPE} ${TEST_CLIENT} ${SH} | cat -v
			echo '____________________________________________________________'
		fi
		echo "Failed ${SH}. Full output:"
		echo '============================================================'
		cat tests/shell/${SH}.${TEST_TYPE}.${TEST_CLIENT}.full.log
		echo '____________________________________________________________'
		if test "x$POWERLINE_TEST_NO_CAT_V" != "x1" ; then
			echo "Full output (cat -v):"
			echo '============================================================'
			cat -v tests/shell/${SH}.${TEST_TYPE}.${TEST_CLIENT}.full.log
			echo '____________________________________________________________'
		fi
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
ln -s "$(which screen)" tests/shell/path
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
ln -s "$(which uname)" tests/shell/path
ln -s "$(which test)" tests/shell/path
ln -s "$(which pwd)" tests/shell/path
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

for exe in bash zsh busybox fish tcsh mksh dash ipython ; do
	if which $exe >/dev/null ; then
		ln -s "$(which $exe)" tests/shell/path
	fi
done

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
		echo "Expected $executable to have MIME type $expected_mime_type, but got $actual_mime_type"
		FAILED=1
		FAIL_SUMMARY="${FAIL_SUMMARY}${NL}M ${executable}"
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
			if test "$TEST_CLIENT" = "shell" && ! which socat >/dev/null ; then
				continue
			fi
			if test "x$ONLY_TEST_CLIENT" != "x" && test "x$TEST_CLIENT" != "x$ONLY_TEST_CLIENT" ; then
				continue
			fi
			POWERLINE_COMMAND_ARGS="--socket $ADDRESS"
			POWERLINE_COMMAND="$POWERLINE_COMMAND"
			export POWERLINE_COMMAND
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
				if test "x$ONLY_SHELL" != "x" && test "x$ONLY_SHELL" != "x$SH" ; then
					continue
				fi
				if ! test -x tests/shell/path/$SH ; then
					continue
				fi
				echo ">>> $(readlink "tests/shell/path/$SH")"
				if ! run_test $TEST_TYPE $TEST_CLIENT $TEST_COMMAND ; then
					FAILED=1
					FAIL_SUMMARY="${FAIL_SUMMARY}${NL}T ${TEST_TYPE} ${TEST_CLIENT} ${TEST_COMMAND}"
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
				FAILED=1
				FAIL_SUMMARY="${FAIL_SUMMARY}${NL}L ${TEST_TYPE} ${TEST_CLIENT} ${TEST_COMMAND}"
			fi
		fi
	done
fi

if $PYTHON scripts/powerline-daemon -s$ADDRESS > tests/shell/daemon_log_2 2>&1 ; then
	sleep 1
	$PYTHON scripts/powerline-daemon -s$ADDRESS -k
else
	echo "Daemon exited with status $?"
	FAILED=1
	FAIL_SUMMARY="${FAIL_SUMMARY}${NL}D"
fi

if ! test -z "$(cat tests/shell/daemon_log_2)" ; then
	echo '____________________________________________________________'
	echo "Daemon log (2nd):"
	echo '============================================================'
	cat tests/shell/daemon_log_2
	FAILED=1
	FAIL_SUMMARY="${FAIL_SUMMARY}${NL}L"
fi

if ( test "x${ONLY_SHELL}" = "x" || test "x${ONLY_SHELL}" = "xzsh" ) \
	&& ( test "x${ONLY_TEST_TYPE}" = "x" || test "x${ONLY_TEST_TYPE}" = "xzpython" ) \
	&& zsh -f -c 'zmodload libzpython' 2>/dev/null; then
	echo "> zpython"
	if ! run_test zpython zpython zsh -f -i ; then
		FAILED=1
		FAIL_SUMMARY="${FAIL_SUMMARY}${NL}T zpython zsh -f -i"
	fi
fi

if  test "x${ONLY_SHELL}" = "x" || test "x${ONLY_SHELL}" = "xpdb" ; then
	if ! ( test "$PYTHON_IMPLEMENTATION" = "PyPy" && test "$PYTHON_VERSION_MAJOR" = 2 ) ; then
		if test "x${ONLY_TEST_TYPE}" = "x" || test "x${ONLY_TEST_TYPE}" = "xsubclass" ; then
			echo "> pdb subclass"
			if ! run_test subclass python $PDB_PYTHON "$PWD/tests/test_shells/pdb-main.py" ; then
				FAILED=1
				FAIL_SUMMARY="${FAIL_SUMMARY}${NL}T pdb $PDB_PYTHON $PWD/tests/test_shells/pdb-main.py"
			fi
		fi
		if test "x${ONLY_TEST_TYPE}" = "x" || test "x${ONLY_TEST_TYPE}" = "xmodule" ; then
			echo "> pdb module"
			MODULE="powerline.bindings.pdb"
			if test "$PYTHON_MM" = "2.6" ; then
				MODULE="powerline.bindings.pdb.__main__"
			fi
			if ! run_test module python $PDB_PYTHON -m$MODULE "$PWD/tests/test_shells/pdb-script.py" ; then
				FAILED=1
				FAIL_SUMMARY="${FAIL_SUMMARY}${NL}T pdb $PDB_PYTHON -m$MODULE $PWD/tests/test_shells/pdb-script"
			fi
		fi
	fi
fi

if test "x${ONLY_SHELL}" = "x" || test "x${ONLY_SHELL}" = "xipython" ; then
	if which ipython >/dev/null ; then
		# Define some overrides which should be ignored by IPython.
		POWERLINE_CONFIG_OVERRIDES='common.term_escape_style=fbterm'
		POWERLINE_THEME_OVERRIDES='in.segments.left=[]'
		echo "> $(which ipython)"
		if ! run_test ipython ipython ipython ; then
			FAILED=1
			FAIL_SUMMARY="${FAIL_SUMMARY}${NL}T ipython"
		fi
		unset POWERLINE_THEME_OVERRIDES
		unset POWERLINE_CONFIG_OVERRIDES
	fi
fi

if test $FAILED -eq 0 ; then
	rm -r tests/shell
else
	echo "${FAIL_SUMMARY}"
fi
exit $FAILED
