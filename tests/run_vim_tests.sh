#!/bin/sh
. tests/common.sh
. tests/vim.sh

enter_suite vim

# Define some overrides. These ones must be ignored and do not affect Vim 
# status/tab lines.
export POWERLINE_CONFIG_OVERRIDES='common.default_top_theme=ascii'
export POWERLINE_THEME_OVERRIDES='default.segments.left=[]'

test_script() {
	local vim="$1"
	local script="$2"
	local test_name_prefix="$3"
	echo "Running script $script with $vim"
	if ! test -e "$vim" ; then
		return 0
	fi
	if ! "$vim" -u NONE -S "$script" || test -f message.fail ; then
		local test_name="$test_name_prefix-${script##*/}"
		fail "${test_name%.vim}" F "Failed script $script run with $vim"
		cat message.fail >&2
		rm message.fail
	fi
}

for script in tests/test_*.vim ; do
	if test "${script%.old.vim}" = "${script}" ; then
		test_script "$NEW_VIM" "$script" new
	fi
done

if test -e "$OLD_VIM" ; then
	for script in tests/test_*.old.vim ; do
		test_script "$OLD_VIM" "$script" old
	done
fi

exit_suite
