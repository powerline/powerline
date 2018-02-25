#!/bin/sh
. tests/shlib/common.sh

enter_suite bar

make_test_root
TEST_PATH="$TEST_ROOT/path"
TEST_STATIC_ROOT="$ROOT/tests/test_bar"

cp -r "$TEST_STATIC_ROOT/path" "$TEST_ROOT"
cp -r "$TEST_STATIC_ROOT/powerline" "$TEST_ROOT"

export PYTHONPATH="$ROOT${PYTHONPATH:+:}$PYTHONPATH"

ln -s "$(which "${PYTHON}")" "$TEST_PATH"/python
ln -s "$(which sed)" "$TEST_PATH"
ln -s "$(which cat)" "$TEST_PATH"
ln -s "$(which mkdir)" "$TEST_PATH"
ln -s "$(which basename)" "$TEST_PATH"
ln -s "$TEST_PATH/lemonbar" "$TEST_PATH/bar-aint-recursive"

DEPRECATED_SCRIPT="$ROOT/powerline/bindings/bar/powerline-bar.py"

run() {
	env -i \
		LANG=C \
		PATH="$TEST_PATH" \
		XDG_CONFIG_HOME="$TEST_ROOT" \
		XDG_CONFIG_DIRS="$TEST_ROOT/dummy" \
		PYTHONPATH="$PYTHONPATH" \
		TEST_ROOT="$TEST_ROOT" \
		LD_LIBRARY_PATH="$LD_LIBRARY_PATH" \
		"$@" || true
}

display_log() {
	local log_file="$1"
	echo "$log_file:"
	echo '============================================================'
	cat -v "$log_file"
	echo
	echo '____________________________________________________________'
}

check_log() {
	local log_file="$1"
	local text="$2"
	local warns="$3"
	if test "$warns" = "warns" ; then
		local warning="$(head -n1 "$log_file" | sed 's/.*://')"
		local expwarning="The 'bar' bindings are deprecated, please switch to 'lemonbar'"
		if test "$warning" != "$expwarning" ; then
			echo "Got: $warning"
			echo "Exp: $expwarning"
			fail "warn" F "Expected warning"
		fi
		sed -r -i -e '1d' "$log_file"
	fi
	local line="$(head -n1 "$log_file")"
	local linenum="$(cat "$log_file" | wc -l)"
	if test $linenum -lt 5 ; then
		fail "log:lt" F "Script was run not enough times"
		return 1
	elif test $linenum -gt 15 ; then
		fail "log:gt" E "Script was run too many times"
		return 1
	fi
	local expline="%{l}%{F#ffd0d0d0}%{B#ff303030} $text-left %{F-B--u}%{F#ff303030} %{F-B--u}%{r}%{F#ff303030} %{F-B--u}%{F#ffd0d0d0}%{B#ff303030} $text-right %{F-B--u}"
	if test "$expline" != "$line" ; then
		echo "Line:     '$line'"
		echo "Expected: '$expline'"
		fail "log:line" F "Unexpected line"
		return 1
	fi
	local ret=0
	while test $linenum -gt 0 ; do
		echo "$line" >> "$TEST_ROOT/ok"
		linenum=$(( linenum - 1 ))
	done
	if ! diff "$TEST_ROOT/ok" "$log_file" ; then
		fail "log:diff" F "Unexpected output"
		ret=1
	fi
	rm "$TEST_ROOT/ok"
	return $ret
}

killscript() {
	kill -KILL $1 || true
}

if ! test -e "$DEPRECATED_SCRIPT" ; then
	# TODO: uncomment when skip is available
	# skip "deprecated" "Missing deprecated bar bindings script"
	:
else
	enter_suite "deprecated" final
	run python "$DEPRECATED_SCRIPT" $args > "$TEST_ROOT/deprecated.log" 2>&1 &
	SPID=$!
	sleep 5
	killscript $SPID
	if ! check_log "$TEST_ROOT/deprecated.log" "default" warns ; then
		display_log "$TEST_ROOT/deprecated.log"
		fail "log" F "Checking log failed"
	fi
	rm "$TEST_ROOT/deprecated.log"
	exit_suite --continue
fi

LEMONBAR_SCRIPT="$ROOT/powerline/bindings/lemonbar/powerline-lemonbar.py"

if ! test -e "$LEMONBAR_SCRIPT" ; then
	# TODO: uncomment when skip is available
	# skip "lemonbar" "Missing lemonbar bindings script"
	:
else
	enter_suite "lemonbar"
	for args in "" "-i0.5" "--interval=0.5" "-- test args" "--bar-command bar-aint-recursive" "--height=10"; do
		rm -rf "$TEST_ROOT/results"
		run python "$LEMONBAR_SCRIPT" $args > "$TEST_ROOT/lemonbar.log" 2>&1 &
		SPID=$!
		sleep 5
		killscript $SPID
		sleep 0.5
		enter_suite "args($args)" final
		fnum=0
		for file in "$TEST_ROOT/results"/*.log ; do
			if ! test -e "$file" ; then
				fail "log" E "Log file is missing"
				break
			fi
			fnum=$(( fnum + 1 ))
			args_file="${file%.log}.args"
			if ! test -e "$args_file" ; then
				fail "args" E "$args_file is missing"
			else
				cat "$args_file" >> "$TEST_ROOT/args.log"
			fi
			text="dvi"
			if cat "$args_file" | grep -q +1 ; then
				text="default"
			fi
			if ! check_log "$file" "$text" ; then
				display_log "$file"
				fail "log" F "Checking log failed"
			fi
			rm "$file"
		done
		if test "$fnum" -ne 2 ; then
			fail "fnum" F "Expected two output files"
		fi
		if test "${args#--height}" != "$args" ; then
			height="${args#--height}"
			height="${height# }"
			height="${height#=}"
			height="${height%% *}"
		fi
		command="lemonbar"
		if test "${args#--bar-command}" != "$args" ; then
			command="${args#--bar-command}"
			command="${command# }"
			command="${command#=}"
			command="${command%% *}"
		fi
		received_args="$(cat "$TEST_ROOT/args.log" | sort)"
		rm "$TEST_ROOT/args.log"
		script_args="${args#*-- }"
		script_args="${script_args# }"
		if test "${script_args}" = "$args" ; then
			script_args=
		fi
		expected_args="$command -g 1920x$height+0${script_args:+ }$script_args${NL}$command -g 1920x$height+1${script_args:+ }$script_args"
		if test "$expected_args" != "$received_args" ; then
			echo "args:${NL}<$received_args>"
			echo "expected:${NL}<$expected_args>"
			fail "args" F "Expected different args"
		fi
		if ! test -z "$(cat "$TEST_ROOT/lemonbar.log")" ; then
			display_log "$TEST_ROOT/lemonbar.log"
			fail "stderr" E "Unexpected script output"
		fi
		rm "$TEST_ROOT/lemonbar.log"
		exit_suite --continue
	done
	exit_suite --continue
fi

if ! powerline-lint \
	-p "$ROOT/powerline/config_files" \
	-p "$TEST_STATIC_ROOT/powerline"
then
	fail "lint" F "Checking test config failed"
fi

exit_suite
