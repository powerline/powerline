#!/bin/sh
. tests/shlib/common.sh
. tests/shlib/vterm.sh
. tests/shlib/vim.sh

enter_suite vim final

vterm_setup vim

# Define some overrides. These ones must be ignored and do not affect Vim 
# status/tab lines.
export POWERLINE_CONFIG_OVERRIDES='common.default_top_theme=ascii'
export POWERLINE_THEME_OVERRIDES='default.segments.left=[]'

test_script() {
	local vim="$1" ; shift
	local script="$1" ; shift
	local allow_failure_arg="$1" ; shift
	echo "Running script $script with $vim"
	if ! test -e "$vim" ; then
		return 0
	fi
	if ! script="$script" "$vim" -u NONE -c 'source $script' \
	   || test -f message.fail
	then
		local test_name="${script##*/}"
		fail $allow_failure_arg "${test_name%.vim}" \
			F "Failed script $script run with $vim"
		if test -e message.fail ; then
			cat message.fail >&2
			rm message.fail
		fi
	fi
}

TEST_SCRIPT_ROOT="$ROOT/tests/test_vim/tests"

cd "$TEST_ROOT"

for script in "$TEST_SCRIPT_ROOT"/*.vim ; do
	if test "${script%.old.vim}" = "${script}" ; then
		test_script "$NEW_VIM" "$script" ""
	fi
done

if test "$PYTHON_VERSION_MAJOR.$PYTHON_VERSION_MINOR" = "2.7" ; then
	ALLOW_FAILURE_ARG=--allow-failure
else
	ALLOW_FAILURE_ARG=
fi

if test -e "$OLD_VIM" ; then
	for script in "$TEST_SCRIPT_ROOT"/*.old.vim ; do
		test_script "$OLD_VIM" "$script" "$ALLOW_FAILURE_ARG"
	done
fi

vterm_shutdown

exit_suite
