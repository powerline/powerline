#!/bin/sh
. tests/shlib/common.sh

enter_suite shell final

if test $# -eq 0 ; then
	FAST=1
fi
ONLY_SHELL="$1"
ONLY_TEST_TYPE="$2"
ONLY_TEST_CLIENT="$3"

export PYTHON

if test "$ONLY_SHELL" = "--help" ; then
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
	if test -e "$ROOT/tests/test_shells/outputs/${SH}.${TEST_TYPE}.ok" ; then
		diff -a -u "$ROOT/tests/test_shells/outputs/${SH}.${TEST_TYPE}.ok" \
		           "$TEST_ROOT/${SH}.${TEST_TYPE}.${TEST_CLIENT}.log"
		return $?
	elif test -e "$ROOT/tests/test_shells/outputs/${SH}.ok" ; then
		diff -a -u "$ROOT/tests/test_shells/outputs/${SH}.ok" \
		           "$TEST_ROOT/${SH}.${TEST_TYPE}.${TEST_CLIENT}.log"
		return $?
	else
		cat "$TEST_ROOT/${SH}.${TEST_TYPE}.${TEST_CLIENT}.log"
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
	cat "$TEST_ROOT/${SH}.${TEST_TYPE}.${TEST_CLIENT}.full.log"
	echo
	echo '____________________________________________________________'
	if test "$POWERLINE_TEST_NO_CAT_V" != "1" ; then
		echo "Full output (cat -v):"
		echo '============================================================'
		cat -v "$TEST_ROOT/${SH}.${TEST_TYPE}.${TEST_CLIENT}.full.log"
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
		test "${SH}" = "dash" \
		|| ( \
			test "${SH}" = "pdb" \
			&& ( \
				( \
					test "$PYTHON_VERSION_MAJOR" -eq 3 \
					&& test "$PYTHON_VERSION_MINOR" -eq 2 \
					&& test "$PYTHON_IMPLEMENTATION" = "CPython" \
				) \
				|| test "$PYTHON_IMPLEMENTATION" = "PyPy" \
			) \
		) \
		|| ( \
			test "${SH}" = "ipython" \
			&& test "$("${PYTHON}" -mIPython --version | head -n1 | cut -d. -f1)" -ge 5 \
		) \
	) ; then
		wait_for_echo_arg="--wait-for-echo"
	fi
	"${PYTHON}" tests/test_shells/run_script.py \
		$wait_for_echo_arg --type=${TEST_TYPE} --client=${TEST_CLIENT} --shell=${SH} \
		"$@"
	if ! check_screen_log ${TEST_TYPE} ${TEST_CLIENT} ${SH} ; then
		echo '____________________________________________________________'
		if test "$POWERLINE_TEST_NO_CAT_V" != "1" ; then
			# Repeat the diff to make it better viewable in travis output
			echo "Diff (cat -v):"
			echo '============================================================'
			check_screen_log  ${TEST_TYPE} ${TEST_CLIENT} ${SH} | cat -v
			echo '____________________________________________________________'
		fi
		echo -n "Failed ${SH}. "
		print_full_output ${TEST_TYPE} ${TEST_CLIENT} ${SH}
		case "${SH}" in
			*ksh)
				"$TEST_ROOT/path/${SH}" -c 'echo ${KSH_VERSION}'
				;;
			dash)
				# ?
				;;
			busybox)
				busybox --help
				;;
			*)
				"$TEST_ROOT/path/${SH}" --version
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
		rm -f "$TEST_ROOT/${SH}.${TEST_TYPE}.${TEST_CLIENT}.log"
		rm -f "$TEST_ROOT/${SH}.${TEST_TYPE}.${TEST_CLIENT}.full.log"
		do_run_test "$@" && return 0
		attempts=$(( attempts - 1 ))
	done
	return 1
}

make_test_root

git init "$TEST_ROOT/3rd"
git --git-dir="$TEST_ROOT/3rd/.git" checkout -b BRANCH
export DIR1="[32m"
export DIR2=""
mkdir "$TEST_ROOT/3rd/$DIR1"
mkdir "$TEST_ROOT/3rd/$DIR2"
mkdir "$TEST_ROOT"/3rd/'\[\]'
mkdir "$TEST_ROOT"/3rd/'%%'
mkdir "$TEST_ROOT"/3rd/'#[bold]'
mkdir "$TEST_ROOT"/3rd/'(echo)'
mkdir "$TEST_ROOT"/3rd/'$(echo)'
mkdir "$TEST_ROOT"/3rd/'`echo`'
mkdir "$TEST_ROOT"/3rd/'«Unicode!»'

mkdir "$TEST_ROOT/fish_home"
mkdir "$TEST_ROOT/fish_home/fish"
mkdir "$TEST_ROOT/fish_home/fish/generated_completions"
cp -r "$ROOT/tests/test_shells/ipython_home" "$TEST_ROOT"

mkdir "$TEST_ROOT/path"
ln -s "$(which "${PYTHON}")" "$TEST_ROOT/path/python"
ln -s "$(which env)" "$TEST_ROOT/path"
ln -s "$(which git)" "$TEST_ROOT/path"
ln -s "$(which sleep)" "$TEST_ROOT/path"
ln -s "$(which cat)" "$TEST_ROOT/path"
ln -s "$(which false)" "$TEST_ROOT/path"
ln -s "$(which true)" "$TEST_ROOT/path"
ln -s "$(which kill)" "$TEST_ROOT/path"
ln -s "$(which echo)" "$TEST_ROOT/path"
ln -s "$(which which)" "$TEST_ROOT/path"
ln -s "$(which dirname)" "$TEST_ROOT/path"
ln -s "$(which wc)" "$TEST_ROOT/path"
ln -s "$(which stty)" "$TEST_ROOT/path"
ln -s "$(which cut)" "$TEST_ROOT/path"
ln -s "$(which bc)" "$TEST_ROOT/path"
ln -s "$(which expr)" "$TEST_ROOT/path"
ln -s "$(which mktemp)" "$TEST_ROOT/path"
ln -s "$(which grep)" "$TEST_ROOT/path"
ln -s "$(which sed)" "$TEST_ROOT/path"
ln -s "$(which rm)" "$TEST_ROOT/path"
ln -s "$(which tr)" "$TEST_ROOT/path"
ln -s "$(which uname)" "$TEST_ROOT/path"
ln -s "$(which test)" "$TEST_ROOT/path"
ln -s "$(which pwd)" "$TEST_ROOT/path"
ln -s "$(which hostname)" "$TEST_ROOT/path"
ln -s "$ROOT/tests/test_shells/bgscript.sh" "$TEST_ROOT/path"
ln -s "$ROOT/tests/test_shells/waitpid.sh" "$TEST_ROOT/path"
if which socat ; then
	ln -s "$(which socat)" "$TEST_ROOT/path"
fi
for pexe in powerline powerline-config powerline-render powerline.sh powerline.py ; do
	if test -e "$ROOT/scripts/$pexe" ; then
		ln -s "$ROOT/scripts/$pexe" "$TEST_ROOT/path"
	elif test -e client/$pexe ; then
		ln -s "$ROOT/client/$pexe" "$TEST_ROOT/path"
	elif which $pexe ; then
		ln -s "$(which $pexe)" "$TEST_ROOT/path"
	else
		echo "Executable $pexe was not found"
		exit 1
	fi
done

ln -s python "$TEST_ROOT/path/pdb"
PDB_PYTHON=pdb
ln -s python "$TEST_ROOT/path/ipython"
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
	ln -s "$(which $POWERLINE_RC_EXE)" "$TEST_ROOT/path/rc"
fi

exes="bash zsh busybox tcsh mksh"

if test "$TRAVIS" != "true" ; then
	# For some reason fish does not work on travis
	exes="$exes fish"
fi

# dash has some problems with job control
#exes="$exes dash"

for exe in $exes ; do
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
		ln -s "$(which $exe)" "$TEST_ROOT/path"
	fi
done

mkdir "$TEST_ROOT/home"
export HOME="$TEST_ROOT/home"

unset ENV

export ADDRESS="powerline-ipc-test-$$"
export PYTHON
echo "Powerline address: $ADDRESS"

check_test_client() {
	local executable="$1"
	local client_type="$2"
	local actual_mime_type="$(
		file --mime-type --brief --dereference "$TEST_ROOT/path/$executable" \
		| cut -d/ -f1
	)"
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

if ( \
	test -z "${ONLY_SHELL}" \
	|| test "${ONLY_SHELL%sh}" != "${ONLY_SHELL}" \
	|| test "${ONLY_SHELL}" = "busybox" \
	|| test "${ONLY_SHELL}" = "rc" \
) ; then
	scripts/powerline-config shell command

	for TEST_TYPE in "daemon" "nodaemon" ; do
		if test -n "$ONLY_TEST_TYPE" && test "$ONLY_TEST_TYPE" != "$TEST_TYPE"
		then
			continue
		fi
		if test "$FAST" = 1 ; then
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
				echo $$ > "$TEST_ROOT/daemon_pid"
				exec "$PYTHON" ./scripts/powerline-daemon -s"$ADDRESS" -f >"$TEST_ROOT/daemon_log" 2>&1
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
			if test "$TEST_CLIENT" = "C" && ! test -x "$ROOT/scripts/powerline"
			then
				if which powerline >/dev/null ; then
					POWERLINE_COMMAND=powerline
				else
					continue
				fi
			fi
			if ( \
				test "$TEST_CLIENT" = "shell" \
				&& ! test -x "$TEST_ROOT/path/socat" \
			) ; then
				continue
			fi
			if ( \
				test -n "$ONLY_TEST_CLIENT" \
				&& test "$TEST_CLIENT" != "$ONLY_TEST_CLIENT" \
			) ; then
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
				if test "$FAST" = 1 ; then
					if test $(( (I + J) % $VARIANTS )) -ne $EXETEST ; then
						continue
					fi
				fi
				SH="${TEST_COMMAND%% *}"
				if test -n "$ONLY_SHELL" && test "$ONLY_SHELL" != "$SH" ; then
					continue
				fi
				if ! test -x "$TEST_ROOT/path/$SH" ; then
					continue
				fi
				echo ">>> $(readlink "$TEST_ROOT/path/$SH")"
				if ! run_test $TEST_TYPE $TEST_CLIENT $TEST_COMMAND ; then
					fail "$SH-$TEST_TYPE-$TEST_CLIENT:test" F \
						"Failed checking $TEST_COMMAND"
				fi
			done
		done
		if test $TEST_TYPE = daemon ; then
			"$PYTHON" ./scripts/powerline-daemon -s"$ADDRESS" -k
			wait $(cat "$TEST_ROOT/daemon_pid")
			if ! test -z "$(cat "$TEST_ROOT/daemon_log")" ; then
				echo '____________________________________________________________'
				echo "Daemon log:"
				echo '============================================================'
				cat "$TEST_ROOT/daemon_log"
				fail "$SH-$TEST_TYPE-$TEST_CLIENT:log" E \
					"Non-empty daemon log for ${TEST_COMMAND}"
			fi
		fi
	done
fi

if "$PYTHON" scripts/powerline-daemon -s"$ADDRESS" \
	> "$TEST_ROOT/daemon_log_2" 2>&1
then
	sleep 1
	"$PYTHON" scripts/powerline-daemon -s"$ADDRESS" -k
else
	fail "daemon:run" F "Daemon exited with status $?"
fi

if ! test -z "$(cat "$TEST_ROOT/daemon_log_2")" ; then
	echo '____________________________________________________________'
	echo "Daemon log (2nd):"
	echo '============================================================'
	cat "$TEST_ROOT/daemon_log_2"
	fail "daemon:log" E "Daemon run with non-empty log"
fi

if ( test -z "${ONLY_SHELL}" || test "${ONLY_SHELL}" = "zsh" ) \
	&& ( test -z "${ONLY_TEST_TYPE}" || test "${ONLY_TEST_TYPE}" = "zpython" ) \
	&& "$TEST_ROOT/path/zsh" "$ROOT/tests/test_shells/zsh_test_script.zsh"
then
	echo "> zpython"
	if ! run_test zpython zpython zsh -f -i ; then
		fail "zsh-zpython:test" F "Failed checking zsh -f -i"
	fi
fi

if  test -z "${ONLY_SHELL}" || test "${ONLY_SHELL}" = "pdb" ; then
	if test "$PYTHON_IMPLEMENTATION" != "PyPy" ; then
		if test -z "${ONLY_TEST_TYPE}" || test "${ONLY_TEST_TYPE}" = "subclass"
		then
			echo "> pdb subclass"
			if ! run_test subclass python $PDB_PYTHON \
				"$ROOT/tests/test_shells/pdb-main.py"
			then
				fail --allow-failure "pdb-subclass:test" F \
					"Failed checking $PDB_PYTHON $ROOT/tests/test_shells/pdb-main.py"
			fi
		fi
		if test -z "${ONLY_TEST_TYPE}" || test "${ONLY_TEST_TYPE}" = "module" ; then
			echo "> pdb module"
			MODULE="powerline.bindings.pdb"
			if test "$PYTHON_MM" = "2.6" ; then
				MODULE="powerline.bindings.pdb.__main__"
			fi
			if ! run_test module python "$PDB_PYTHON" -m"$MODULE" \
				"$ROOT/tests/test_shells/pdb-script.py"
			then
				fail --allow-failure "pdb-module:test" F \
					"Failed checking $PDB_PYTHON -m$MODULE $ROOT/tests/test_shells/pdb-script"
			fi
		fi
	fi
fi

if test -z "${ONLY_SHELL}" || test "${ONLY_SHELL}" = "ipython" ; then
	if "${PYTHON}" -c "try: import IPython${NL}except ImportError: raise SystemExit(1)" ; then
		# Define some overrides which should be ignored by IPython.
		export POWERLINE_CONFIG_OVERRIDES='common.term_escape_style=fbterm'
		export POWERLINE_THEME_OVERRIDES='in.segments.left=[]'
		echo "> ipython"
		if ! run_test ipython ipython ${IPYTHON_PYTHON} -mIPython ; then
			# Do not allow ipython tests to spoil the build
			fail --allow-failure "ipython:test" F "Failed checking ${IPYTHON_PYTHON} -mIPython"
		fi
		unset POWERLINE_THEME_OVERRIDES
		unset POWERLINE_CONFIG_OVERRIDES
	fi
fi

exit_suite
