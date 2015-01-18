#!/bin/sh
. tests/bot-ci/scripts/common/main.sh
FAILED=0

if test -z "$VIM" ; then
	if test -n "$USE_UCS2_PYTHON" ; then
		NEW_VIM="$ROOT/tests/bot-ci/deps/vim/tip-$UCS2_PYTHON_VARIANT-ucs2-double/vim"
		OLD_VIM="$ROOT/tests/bot-ci/deps/vim/v7-0-112-$UCS2_PYTHON_VARIANT-ucs2/vim"
		opt_dir="/opt/cpython-ucs2-$UCS2_PYTHON_VARIANT"
		main_path="$opt_dir/lib/python$UCS2_PYTHON_VARIANT"
		site_path="$main_path/site-packages"
		venv_main_path="$VIRTUAL_ENV/lib/python$UCS2_PYTHON_VARIANT"
		venv_site_path="$venv_main_path/site-packages"
		new_paths="${main_path}:${site_path}:${venv_main_path}:${venv_site_path}"
		export PYTHONPATH="$new_paths${PYTHONPATH:+:}$PYTHONPATH"
	else
		if test "$PYTHON_IMPLEMENTATION" != "CPython" ; then
			exit 0
		fi
		NEW_VIM="$ROOT/tests/bot-ci/deps/vim/tip-$PYTHON_MM/vim"
		OLD_VIM="$ROOT/tests/bot-ci/deps/vim/v7-0-112-$PYTHON_MM/vim"
		if test -e "$OLD_VIM" ; then
			VIMS="NEW_VIM OLD_VIM"
		else
			VIMS="NEW_VIM"
		fi
	fi
else
	NEW_VIM="$VIM"
	OLD_VIM="$VIM"
fi

# Define some overrides. These ones must be ignored and do not affect Vim 
# status/tab lines.
export POWERLINE_CONFIG_OVERRIDES='common.default_top_theme=ascii'
export POWERLINE_THEME_OVERRIDES='default.segments.left=[]'

test_script() {
	local vim="$1"
	local script="$2"
	echo "Running script $script with $vim"
	if ! "$vim" -u NONE -S $script || test -f message.fail ; then
		echo "Failed script $script run with $VIM" >&2
		cat message.fail >&2
		rm message.fail
		FAILED=1
	fi
}

for script in tests/test_*.vim ; do
	if test "${script%.old.vim}" = "${script}" ; then
		test_script "$NEW_VIM" "$script"
	fi
done

if test -e "$OLD_VIM" ; then
	for script in tests/test_*.old.vim ; do
		test_script "$OLD_VIM" "$script"
	done
fi

exit $FAILED
