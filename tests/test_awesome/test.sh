#!/bin/sh
. tests/shlib/common.sh

enter_suite awesome

make_test_root

TEST_PATH="$TEST_ROOT/path"
TEST_STATIC_ROOT="$ROOT/tests/test_awesome"

cp -r "$TEST_STATIC_ROOT/path" "$TEST_ROOT"
cp -r "$TEST_STATIC_ROOT/powerline" "$TEST_ROOT"

export PYTHONPATH="$ROOT${PYTHONPATH:+:}$PYTHONPATH"

ln -s "$(which "${PYTHON}")" "$TEST_PATH"/python
ln -s "$(which cat)" "$TEST_PATH"
ln -s "$(which sh)" "$TEST_PATH"
ln -s "$(which env)" "$TEST_PATH"
if which socat ; then
	ln -s "$(which socat)" "$TEST_PATH"
fi
for pexe in powerline powerline.sh powerline.py ; do
	if test -e scripts/$pexe ; then
		ln -s "$PWD/scripts/$pexe" $TEST_ROOT/path
	elif test -e client/$pexe ; then
		ln -s "$PWD/client/$pexe" $TEST_ROOT/path
	elif which $pexe ; then
		ln -s "$(which $pexe)" $TEST_ROOT/path
	else
		continue
	fi
	if test "$pexe" != 'powerline.sh' || test -e "$TEST_PATH/socat" ; then
		POWERLINE_COMMAND="$pexe"
		break
	fi
done

DEPRECATED_SCRIPT="$ROOT/powerline/bindings/awesome/powerline-awesome.py"
POWERLINE_DAEMON="scripts/powerline-daemon"

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
	local args_file="$TEST_ROOT/results/args"
	local log_file="$TEST_ROOT/results/requests"
	local line="$(head -n1 "$log_file")"
	local linenum="$(cat "$log_file" | wc -l)"
	echo "Number of runs: $linenum (expected approx 5 / 0.5 = 10 runs)"
	if test $linenum -lt 5 ; then
		fail "log:lt" F "Script was run not enough times: $linenum < 5"
		return 1
	elif test $linenum -gt 15 ; then
		fail "log:gt" E "Script was run too many times: $linenum > 15"
		return 1
	fi
	local expline="powerline_widget:set_markup('<span foreground=\"#303030\"> </span><span foreground=\"#d0d0d0\" background=\"#303030\" font_weight=\"bold\"> default-right </span>')"
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
	for args in "" "0.5"; do
		rm -rf "$TEST_ROOT/results"
		mkdir "$TEST_ROOT/results"
		DEPRECATED_LOG="$TEST_ROOT/deprecated.log"
		run env \
			DEPRECATED_SCRIPT="$DEPRECATED_SCRIPT" \
			args="$args" \
			DEPRECATED_LOG="$DEPRECATED_LOG" \
			TEST_ROOT="$TEST_ROOT" \
			sh -c '
				echo $$ > "$TEST_ROOT/$args-pid"
				exec "$DEPRECATED_SCRIPT" $args > "$DEPRECATED_LOG" 2>&1
			' &
		sleep 5
		killscript "$(cat "$TEST_ROOT/$args-pid")"
		rm "$TEST_ROOT/$args-pid"
		if test -n "$(cat "$DEPRECATED_LOG")" ; then
			display_log "$DEPRECATED_LOG"
			fail "output" E "Nonempty $DEPRECATED_SCRIPT output"
		fi
		rm "$DEPRECATED_LOG"
		if ! check_log ; then
			display_log "$TEST_ROOT/results/args"
			fail "log" F "Checking log failed"
		fi
	done
	exit_suite --continue
fi

enter_suite "awesome" final
ADDRESS="powerline-ipc-test-$$"
echo "Powerline address: $ADDRESS"
rm -rf "$TEST_ROOT/results"
mkdir "$TEST_ROOT/results"
run env \
	POWERLINE_DAEMON="$POWERLINE_DAEMON" \
	TEST_ROOT="$TEST_ROOT" \
	ADDRESS="$ADDRESS" \
	sh -c '
		echo $$ > "$TEST_ROOT/dpid"
		exec python "$POWERLINE_DAEMON" --socket $ADDRESS --foreground > "$TEST_ROOT/daemon.log" 2>&1
	' &
DPID=$!
sleep 2
run "$POWERLINE_COMMAND" --socket $ADDRESS wm.awesome > "$TEST_ROOT/output.log.1" 2>&1
run "$POWERLINE_COMMAND" --socket $ADDRESS wm.awesome > "$TEST_ROOT/output.log.2" 2>&1
run "$POWERLINE_COMMAND" --socket $ADDRESS wm.awesome > "$TEST_ROOT/output.log.3" 2>&1
run "$POWERLINE_COMMAND" --socket $ADDRESS wm.awesome > "$TEST_ROOT/output.log.4" 2>&1
run "$POWERLINE_COMMAND" --socket $ADDRESS wm.awesome > "$TEST_ROOT/output.log.5" 2>&1
for log_file in "$TEST_ROOT"/output.log.* ; do
	if test -n "$(cat "$log_file")" ; then
		display_log "$log_file"
		fail "output" E "Nonempty $POWERLINE_COMMAND output at run ${log_file#*.}"
	fi
	rm "$log_file"
done
sleep 5
run python "$POWERLINE_DAEMON" --socket $ADDRESS --quiet --kill > "$TEST_ROOT/kill.log" 2>&1
if test -n "$(cat "$TEST_ROOT/kill.log")" ; then
	display_log "$TEST_ROOT/kill.log"
	fail "daemonlog" E "Nonempty kill log"
fi
rm "$TEST_ROOT/kill.log"
wait $DPID
if test -n "$(cat "$TEST_ROOT/daemon.log")" ; then
	display_log "$TEST_ROOT/daemon.log"
	fail "daemonlog" E "Nonempty daemon log"
fi
rm "$TEST_ROOT/daemon.log"
if ! check_log ; then
	display_log "$TEST_ROOT/results/args"
	fail "log" F "Checking log failed"
fi
exit_suite --continue

if ! powerline-lint \
	-p "$ROOT/powerline/config_files" \
	-p "$TEST_STATIC_ROOT/powerline"
then
	fail "lint" F "Checking test config failed"
fi

exit_suite
