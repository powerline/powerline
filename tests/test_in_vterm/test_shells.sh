#!/bin/sh
. tests/common.sh
# set -x

enter_suite shells

TEST_ROOT="$ROOT/tests/vterm_shell"
TEST_PATH="$TEST_ROOT/path"

rm -rf "$TEST_ROOT"
mkdir "$TEST_ROOT"
mkdir "$TEST_PATH"
mkdir "$TEST_ROOT/empty_dir"
git init "$TEST_ROOT"/3rd
git --git-dir="$TEST_ROOT"/3rd/.git checkout -b BRANCH

export DIR1="[32m"
export DIR2=""
export DIR3="«Unicode!»"
mkdir "$TEST_ROOT"/3rd/"$DIR1"
mkdir "$TEST_ROOT"/3rd/"$DIR2"
mkdir "$TEST_ROOT"/3rd/"$DIR3"
mkdir "$TEST_ROOT"/3rd/'\[\]'
mkdir "$TEST_ROOT"/3rd/'%%'
mkdir "$TEST_ROOT"/3rd/'#[bold]'
mkdir "$TEST_ROOT"/3rd/'(echo)'
mkdir "$TEST_ROOT"/3rd/'$(echo)'
mkdir "$TEST_ROOT"/3rd/'`echo`'

ln -s "$(which "${PYTHON}")" "$TEST_PATH"/python
ln -s "$(which sh)" "$TEST_PATH"
ln -s "$(which cut)" "$TEST_PATH"
ln -s "$(which git)" "$TEST_PATH"
ln -s "$(which sleep)" "$TEST_PATH"
ln -s "$(which cat)" "$TEST_PATH"
ln -s "$(which false)" "$TEST_PATH"
ln -s "$(which true)" "$TEST_PATH"
ln -s "$(which kill)" "$TEST_PATH"
ln -s "$(which echo)" "$TEST_PATH"
ln -s "$(which which)" "$TEST_PATH"
ln -s "$(which dirname)" "$TEST_PATH"
ln -s "$(which wc)" "$TEST_PATH"
ln -s "$(which stty)" "$TEST_PATH"
ln -s "$(which bc)" "$TEST_PATH"
ln -s "$(which expr)" "$TEST_PATH"
ln -s "$(which mktemp)" "$TEST_PATH"
ln -s "$(which grep)" "$TEST_PATH"
ln -s "$(which sed)" "$TEST_PATH"
ln -s "$(which rm)" "$TEST_PATH"
ln -s "$(which tr)" "$TEST_PATH"
ln -s "$(which uname)" "$TEST_PATH"
ln -s "$(which test)" "$TEST_PATH"
ln -s "$(which pwd)" "$TEST_PATH"
ln -s "$(which hostname)" "$TEST_PATH"
ln -s "$(which clear)" "$TEST_PATH"
ln -s "$(which env)" "$TEST_PATH"

if which socat >/dev/null ; then
	ln -s "$(which socat)" "$TEST_PATH"
fi

ln -s ../../test_in_vterm/bgscript.sh "$TEST_PATH"
ln -s ../../test_in_vterm/waitpid.sh "$TEST_PATH"

ln -s ../../../scripts/powerline-config "$TEST_PATH"
ln -s ../../../scripts/powerline-daemon "$TEST_PATH"
ln -s ../../../scripts/powerline-render "$TEST_PATH"

# Busybox ash does not accept `-` in function names. This symlink serves as 
# a fallback for all shells that have no powerline-reload-config function 
# (basically, every shell except zsh with bindings based on zpython module).
ln -s true "$TEST_PATH/powerline-reload-config"

cp -r tests/terminfo "$TEST_ROOT"

FAIL_SUMMARY=""

add_client() {
	local test_client="$1"
	local tgt_exe="$TEST_PATH/powerline-client-$test_client"
	local mime
	local exe

	if test -x "$tgt_exe" ; then
		return 0
	fi

	case "$test_client" in
		C)      mime="application/x-executable" ; exe="client/powerline" ;;
		python) mime="text/x-python"      ; exe="client/powerline.py" ;;
		shell)  mime="text/x-shellscript" ; exe="client/powerline.sh" ;;
		render) mime="text/x-python"      ; exe="scripts/powerline-render" ;;
		internal) return 0 ;;
	esac

	if ! test -x "$exe" ; then
		fail "$test_client:path" E "Client $test_client is not available"
		return 1
	fi

	if test "$test_client" = shell && ! test -x "$TEST_PATH/socat" ; then
		skip "$test_client:socat" "socat is not available"
		return 1
	fi

	local actual_mime="$(file --mime-type --brief --dereference "$exe")"

	# Note: for some reason travis `file` thinks that Python files are 
	# text/x-java.
	if ( test "${actual_mime}" != "${mime}" \
	     && ! ( test "${mime}" = "text/x-python" \
	            && test "${actual_mime}" = "text/x-java" ) ); then
		fail "$test_client:mime" E \
			"Client $test_client has invalid mime type: expected $mime, but got $actual_mime"
		return 1
	fi

	ln -s "../../../$exe" "$tgt_exe"
	return 0
}

add_shell() {
	local sh="$1"
	local whicharg="$sh"
	local tgt_exe="$TEST_PATH/${sh##*/}"

	if test -x "$tgt_exe" ; then
		return 0
	fi

	if test "x$sh" = "xrc" ; then
		if test -n "$POWERLINE_RC_EXE" ; then
			whicharg="$POWERLINE_RC_EXE"
		elif which rc-status >/dev/null ; then
			# On Gentoo `rc` executable is from OpenRC. Thus app-shells/rc 
			# instals `rcsh` executable.
			whicharg="rcsh"
		fi
	elif test "x$sh" = "xipython" ; then
		whicharg="${PYTHON}"
		if ! "${PYTHON}" -c "try: import IPython${NL}except ImportError: raise SystemExit(1)" ; then
			skip "$sh:module" "IPython is not available"
		fi
	elif test "x$sh" = "xpdb_module" || test "x$sh" = "xpdb_subclass" ; then
		whicharg="${PYTHON}"
	fi

	if ! which "$whicharg" > /dev/null ; then
		skip "$sh:path" "Executable $whicharg is not available"
		return 1
	fi
	if test "x$sh" = "xfish" ; then
		local fish_version="$(fish --version 2>&1)"
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
				test $fish_version_major -eq 2 && ( \
					test $fish_version_minor -lt 1 || ( \
						test $fish_version_minor -eq 1 &&
						test $fish_version_patch -lt 2 && \
						test -z "$fish_version_dev"
					) \
				) \
			) ; then
				skip "$sh:version" \
					"Fish is too outdated to run mode switching tests"
				return 2
			fi
		fi
	fi
	ln -s "$(which "$whicharg")" "$tgt_exe"
	return 0
}

run_in_cleansed_env() {
	env -i \
		LANG="en_US.UTF-8" \
		PATH="$TEST_PATH" \
		TERM="screen-256color" \
		XDG_CONFIG_HOME="$TEST_ROOT/empty_dir" \
		PYTHONPATH="$PYTHONPATH" \
		POWERLINE_CONFIG_OVERRIDES="$POWERLINE_CONFIG_OVERRIDES" \
		POWERLINE_THEME_OVERRIDES="$POWERLINE_THEME_OVERRIDES" \
		POWERLINE_CONFIG_PATHS="$ROOT/powerline/config_files" \
		POWERLINE_COMMAND_ARGS="$POWERLINE_COMMAND_ARGS" \
		POWERLINE_COMMAND="$POWERLINE_COMMAND" \
		LD_LIBRARY_PATH="$LD_LIBRARY_PATH" \
		DIR1="$DIR1" \
		DIR2="$DIR2" \
		DIR3="$DIR3" \
		"$@"
}

test_shell() {
	local sh="$1"
	local test_type="$2"
	local test_client="$3"
	shift ; shift ; shift

	add_shell "$sh" || return 0
	add_client "$test_client" || return 0

	local address="powerline-ipc-test-$$"

	local POWERLINE_COMMAND="powerline-client-$test_client"
	local POWERLINE_COMMAND_ARGS="--socket $address"

	if test "$test_type" = "daemon" ; then
		run_in_cleansed_env \
			env \
				address="$address" \
				TEST_ROOT="$TEST_ROOT" \
				sh -c '
					echo $$ > $TEST_ROOT/daemon_pid
					powerline-daemon --socket=$address --foreground \
						>$TEST_ROOT/daemon_log 2>&1
				' &
	fi

	local ret=0

	if ! run_in_cleansed_env \
		env POWERLINE_COMMAND_ARGS="$POWERLINE_COMMAND_ARGS" \
			python ./tests/test_in_vterm/test_shells.py \
				$sh $test_type $test_client
	then
		fail "$sh-$test_type-$test_client:test" F "Failed test"
		ret=1
	fi

	if test "$test_type" = "daemon" ; then
		run_in_cleansed_env powerline-daemon --socket="$address" --kill
		wait $(cat "$TEST_ROOT/daemon_pid")
		if ! test -z "$(cat "$TEST_ROOT/daemon_log")" ; then
			fail "$sh-$test_type-$test_client:log" E "Non-empty daemon log"
			echo '_____________________________________________________________'
			echo "Daemon log:"
			echo '============================================================='
			cat "$TEST_ROOT/daemon_log"
			return 1
		fi
	fi

	return $ret
}

run_tests() {
	local random_skip=
	if test "x$1$2$3" = "x" ; then
		random_skip=1
	fi
	local sh_re="${1:-.*}"
	local test_type_re="${2:-.*}"
	local test_client_re="${3:-.*}"
	local all_tests=
	local ret=0
	for test_type in daemon render internal ; do
		if ! echo $test_type | grep --silent --perl-regexp "$test_type_re"
		then
			continue
		fi
		local test_shs="bash zsh fish tcsh busybox mksh dash rc"
		local test_clients="C python shell render"
		case $test_type in
			(daemon)   test_clients="C python shell" ;;
			(internal) test_shs="zsh ipython pdb_module pdb_subclass"
			           test_clients="internal" ;;
		esac
		for test_client in $test_clients ; do
			if ! echo $test_client | grep --silent --perl-regexp "$test_client_re"
			then
				continue
			fi
			for sh in $test_shs ; do
				if ! echo $sh | grep --silent --perl-regexp "$sh_re"
				then
					continue
				fi
				echo "Testing $sh-$test_type-$test_client"
				if ! test_shell $sh $test_type $test_client ; then
					ret=1
				fi
			done
		done
	done
	return $ret
}

if ! run_tests "$@" ; then
	fail "shells:test" F "Failed shell tests ($@)"
fi

exit_suite
