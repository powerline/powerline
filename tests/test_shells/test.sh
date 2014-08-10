#!/bin/bash
FAILED=0
ONLY_SHELL="$1"

check_screen_log() {
	TEST_TYPE="$1"
	SH="$2"
	if test -e tests/test_shells/${SH}.${TEST_TYPE}.ok ; then
		diff -a -u tests/test_shells/${SH}.${TEST_TYPE}.ok tests/shell/${SH}.${TEST_TYPE}.log
		return $?
	elif test -e tests/test_shells/${SH}.ok ; then
		diff -a -u tests/test_shells/${SH}.ok tests/shell/${SH}.${TEST_TYPE}.log
		return $?
	else
		cat tests/shell/${SH}.${TEST_TYPE}.log
		return 1
	fi
}

run_test() {
	TEST_TYPE="$1"
	shift
	SH="$1"
	SESNAME="powerline-shell-test-${SH}-$$"
	ARGS=( "$@" )

	test "x$ONLY_SHELL" = "x" || test "x$ONLY_SHELL" = "x$SH" || return 0

	if ! which "${SH}" ; then
		if test "x${SH}" = "xbb" ; then
			if ! which busybox ; then
				return 0
			fi
			shift
			ARGS=( busybox ash "$@" )
		else
			return 0
		fi
	fi

	export TEST_TYPE
	export SH

	screen -L -c tests/test_shells/screenrc -d -m -S "$SESNAME" \
		env LANG=en_US.UTF-8 BINDFILE="$BINDFILE" "${ARGS[@]}"
	screen -S "$SESNAME" -X readreg a tests/test_shells/input.$SH
	# Wait for screen to initialize
	sleep 1
	screen -S "$SESNAME" -p 0 -X width 300 1
	if test "x${SH}" = "xdash" ; then
		# If I do not use this hack for dash then output will look like
		#
		#     command1
		#     command2
		#     …
		#     prompt1> prompt2> …
		while read -r line ; do
			screen -S "$SESNAME" -p 0 -X stuff "$line"$'\n'
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
	./tests/test_shells/postproc.py ${TEST_TYPE} ${SH}
	if ! check_screen_log ${TEST_TYPE} ${SH} ; then
		echo '____________________________________________________________'
		# Repeat the diff to make it better viewable in travis output
		echo "Diff (cat -v):"
		echo '============================================================'
		check_screen_log  ${TEST_TYPE} ${SH} | cat -v
		echo '____________________________________________________________'
		echo "Failed ${SH}. Full output:"
		echo '============================================================'
		cat tests/shell/${SH}.${TEST_TYPE}.full.log
		echo '____________________________________________________________'
		echo "Full output (cat -v):"
		echo '============================================================'
		cat -v tests/shell/${SH}.${TEST_TYPE}.full.log
		echo '____________________________________________________________'
		case ${SH} in
			*ksh)
				${SH} -c 'echo ${KSH_VERSION}'
				;;
			dash)
				# ?
				;;
			bb)
				bb --help
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

mkdir tests/shell/fish_home
cp -r tests/test_shells/ipython_home tests/shell
export XDG_CONFIG_HOME="$PWD/tests/shell/fish_home"
export IPYTHONDIR="$PWD/tests/shell/ipython_home"

unset ENV

if test -z "${ONLY_SHELL}" || test "x${ONLY_SHELL%sh}" != "x${ONLY_SHELL}" || test "x${ONLY_SHELL}" = xbb ; then
	powerline-daemon -k || true
	sleep 1s

	scripts/powerline-config shell command

	for TEST_TYPE in "daemon" "nodaemon" ; do
		if test $TEST_TYPE == daemon ; then
			sh -c 'echo $$ > tests/shell/daemon_pid; ./scripts/powerline-daemon -f &>tests/shell/daemon_log' &
		fi
		if ! run_test $TEST_TYPE bash --norc --noprofile -i ; then
			FAILED=1
		fi

		if ! run_test $TEST_TYPE zsh -f -i ; then
			FAILED=1
		fi

		if ! run_test $TEST_TYPE fish -i ; then
			FAILED=1
		fi

		if ! run_test $TEST_TYPE tcsh -f -i ; then
			FAILED=1
		fi

		if ! run_test $TEST_TYPE bb -i ; then
			FAILED=1
		fi

		if ! run_test $TEST_TYPE mksh -i ; then
			FAILED=1
		fi

		if ! run_test $TEST_TYPE dash -i ; then
			# dash tests are not stable, see #931
			# FAILED=1
			true
		fi
		if test $TEST_TYPE == daemon ; then
			./scripts/powerline-daemon -k
			wait $(cat tests/shell/daemon_pid)
			if ! test -z "$(cat tests/shell/daemon_log)" ; then
				echo '____________________________________________________________'
				echo "Daemon log:"
				echo '============================================================'
				cat tests/shell/daemon_log
				FAILED=1
			fi
		fi
	done
fi

if ! run_test ipython ipython ; then
	FAILED=1
fi

test "x$ONLY_SHELL" = "x" && rm -r tests/shell
exit $FAILED
