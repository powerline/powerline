. tests/bot-ci/scripts/common/main.sh

if test -z "$POWERLINE_VIM_EXE" ; then
	if test -n "$USE_UCS2_PYTHON" ; then
		NEW_VIM="$ROOT/tests/bot-ci/deps/vim/master-$UCS2_PYTHON_VARIANT-ucs2-double/vim"
		OLD_VIM="$ROOT/tests/bot-ci/deps/vim/v7.0.112-$UCS2_PYTHON_VARIANT-ucs2/vim"
		opt_dir="$HOME/opt/cpython-ucs2-$UCS2_PYTHON_VARIANT"
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
		if test -d "$ROOT/tests/bot-ci/deps" ; then
			NEW_VIM="$ROOT/tests/bot-ci/deps/vim/master-$PYTHON_MM/vim"
			OLD_VIM="$ROOT/tests/bot-ci/deps/vim/v7.0.112-$PYTHON_MM/vim"
		else
			NEW_VIM="vim"
		fi
		if test -e "$OLD_VIM" ; then
			VIMS="NEW_VIM OLD_VIM"
		else
			VIMS="NEW_VIM"
		fi
	fi
else
	NEW_VIM="$POWERLINE_VIM_EXE"
	OLD_VIM="$POWERLINE_VIM_EXE"
fi
