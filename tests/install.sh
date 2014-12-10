#!/bin/bash
git clone --depth=1 git://github.com/powerline/bot-ci tests/bot-ci
git clone --depth=1 git://github.com/powerline/deps tests/bot-ci/deps

. tests/bot-ci/scripts/common/main.sh

sudo apt-get install -qq screen zsh tcsh mksh busybox socat realpath

if test -n "$USE_UCS2_PYTHON" ; then
	pip install virtualenvwrapper
	set +e
	. virtualenvwrapper.sh
	set -e
	archive="${PWD:-$(pwd)}/tests/bot-ci/deps/cpython-ucs2/cpython-ucs2-${UCS2_PYTHON_VARIANT}.tar.gz"
	sudo sh -c "cd /opt && tar xzf $archive"
	PYTHON="/opt/cpython-ucs2-$UCS2_PYTHON_VARIANT/bin/python$UCS2_PYTHON_VARIANT"
	export LD_LIBRARY_PATH=/opt/cpython-ucs2-$UCS2_PYTHON_VARIANT/lib
	set +e
	mkvirtualenv -p "$PYTHON" cpython-ucs2-$UCS2_PYTHON_VARIANT
	set -e
	pip install .
	pip install --no-deps tests/bot-ci/deps/wheels/ucs2-CPython-${UCS2_PYTHON_VARIANT}*/*.whl
else
	pip install .
	pip install --no-deps tests/bot-ci/deps/wheels/$PYTHON_SUFFIX/*.whl
	if test "$PYTHON_IMPLEMENTATION" = "CPython" ; then
		archive="${PWD:-$(pwd)}/tests/bot-ci/deps/zpython/zsh-${PYTHON_VERSION}.tar.gz"
		sudo sh -c "cd /opt && tar xzf $archive"
	fi
fi

# Travis has too outdated fish. It cannot be used for tests.
# sudo apt-get install fish
true
