#!/bin/bash
git clone --depth=1 git://github.com/powerline/bot-ci tests/bot-ci
git clone --depth=1 git://github.com/powerline/deps tests/bot-ci/deps

. tests/bot-ci/scripts/common/main.sh

sudo apt-get install -qq libssl1.0.0
sudo apt-get install -qq screen zsh tcsh mksh busybox socat realpath bc rc tmux

if test -n "$USE_UCS2_PYTHON" ; then
	pip install virtualenvwrapper
	set +e
	. virtualenvwrapper.sh
	set -e
	archive="${PWD:-$(pwd)}/tests/bot-ci/deps/cpython-ucs2/cpython-ucs2-${UCS2_PYTHON_VARIANT}.tar.gz"
	sudo sh -c "cd /opt && tar xzf $archive"
	PYTHON="/opt/cpython-ucs2-$UCS2_PYTHON_VARIANT/bin/python$UCS2_PYTHON_VARIANT"
	export LD_LIBRARY_PATH="/opt/cpython-ucs2-$UCS2_PYTHON_VARIANT/lib${LD_LIBRARY_PATH:+:}${LD_LIBRARY_PATH}"
	set +e
	mkvirtualenv -p "$PYTHON" cpython-ucs2-$UCS2_PYTHON_VARIANT
	set -e
	. tests/bot-ci/scripts/common/main.sh
	pip install .
	if test "$UCS2_PYTHON_VARIANT" = "2.6" ; then
		rm tests/bot-ci/deps/wheels/ucs2-CPython-${UCS2_PYTHON_VARIANT}*/pyuv*.whl
	fi
	pip install --no-deps tests/bot-ci/deps/wheels/ucs2-CPython-${UCS2_PYTHON_VARIANT}*/*.whl
else
	pip install .
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
	sudo sh -c "cd /opt && tar xzf $archive"
fi

archive="${PWD:-$(pwd)}/tests/bot-ci/deps/fish/fish.tar.gz"
sudo sh -c "cd /opt && tar xzf $archive"

mkdir tests/vim-plugins

for archive in "$ROOT"/tests/bot-ci/deps/vim-plugins/*.tar.gz ; do
	(
		cd tests/vim-plugins
		tar -xzvf "$archive"
	)
done

# Travis has too outdated fish. It cannot be used for tests.
# sudo apt-get install fish
true
