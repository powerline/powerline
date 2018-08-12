#!/bin/bash

set -e
set -x

remote_master_hex() {
	local url="$1"
	git ls-remote "$url" refs/heads/master | cut -f1
}

checkout_cached_dir() {
	local url="$1"
	local target="$2"
	if ! test -e "$target/.version" || \
		test "$(cat "$target/.version")" != "$(remote_master_hex "$url")" ; then
		rm -rf "$target"
	fi
	if ! test -d "$target" ; then
		git clone --depth=1 "$url" "$target"
		git rev-parse HEAD > "$target/.version"
		rm -rf "$target"/.git
	fi
}

checkout_cached_dir git://github.com/powerline/bot-ci tests/bot-ci
checkout_cached_dir git://github.com/powerline/deps tests/bot-ci/deps

. tests/bot-ci/scripts/common/main.sh

mkdir -p "$HOME/opt"

if test -n "$USE_UCS2_PYTHON" ; then
	if test "$UCS2_PYTHON_VARIANT" = "2.6" ; then
		pip install 'virtualenvwrapper==4.6.0'
	else
		pip install virtualenvwrapper
	fi
	set +e
	. virtualenvwrapper.sh
	set -e
	archive="${PWD:-$(pwd)}/tests/bot-ci/deps/cpython-ucs2/cpython-ucs2-${UCS2_PYTHON_VARIANT}.tar.gz"
	sh -c "cd $HOME/opt && tar xzf $archive"
	PYTHON="$HOME/opt/cpython-ucs2-$UCS2_PYTHON_VARIANT/bin/python$UCS2_PYTHON_VARIANT"
	export LD_LIBRARY_PATH="$HOME/opt/cpython-ucs2-$UCS2_PYTHON_VARIANT/lib${LD_LIBRARY_PATH:+:}${LD_LIBRARY_PATH}"
	set +e
	mkvirtualenv -p "$PYTHON" cpython-ucs2-$UCS2_PYTHON_VARIANT
	set -e
	. tests/bot-ci/scripts/common/main.sh
	pip install --verbose --verbose --verbose .
	if test "$UCS2_PYTHON_VARIANT" = "2.6" ; then
		rm tests/bot-ci/deps/wheels/ucs2-CPython-${UCS2_PYTHON_VARIANT}*/pyuv*.whl
	fi
	pip install --no-deps tests/bot-ci/deps/wheels/ucs2-CPython-${UCS2_PYTHON_VARIANT}*/*.whl
else
	pip install --verbose --verbose --verbose .
	# FIXME Uv watcher sometimes misses events and INotify is not available in
	#       Python-2.6, thus pyuv should be removed in order for VCS tests to 
	#       pass.
	if test "$PYTHON_VERSION_MAJOR" -eq 2 && test "$PYTHON_VERSION_MINOR" -lt 7 ; then
		rm tests/bot-ci/deps/wheels/$PYTHON_SUFFIX/pyuv*.whl
	fi
	pip install --no-deps tests/bot-ci/deps/wheels/$PYTHON_SUFFIX/*.whl
fi
if test "$PYTHON_IMPLEMENTATION" = "CPython" ; then
	archive="${PWD:-$(pwd)}/tests/bot-ci/deps/zpython/zsh-${PYTHON_MM}${USE_UCS2_PYTHON:+-ucs2}.tar.gz"
	sh -c "cd $HOME/opt && tar xzf $archive"
fi

archive="${PWD:-$(pwd)}/tests/bot-ci/deps/fish/fish.tar.gz"
sh -c "cd $HOME/opt && tar xzf $archive"

mkdir tests/vim-plugins

for archive in "$ROOT"/tests/bot-ci/deps/vim-plugins/*.tar.gz ; do
	(
		cd tests/vim-plugins
		tar -xzvf "$archive"
	)
done

true
