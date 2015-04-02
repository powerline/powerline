#!/bin/sh
for signal in ABRT ALRM BUS CHLD CONT FPE HUP ILL INT PIPE QUIT SEGV TERM TSTP \
              TTIN TTOU USR1 USR2 PROF SYS TRAP URG VTALRM XCPU XFSZ ; do
	trap "echo $$: Got signal $signal >> signal.log" $signal
done
real-powerline-config "$@" > powerline-config.out.log 2>&1
exitcode=$?
echo $$: Returned $exitcode >> returncode.log
exit $exitcode
