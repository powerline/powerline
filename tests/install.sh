#!/bin/bash
git clone --depth=1 git://github.com/powerline/bot-ci tests/bot-ci
git clone --depth=1 git://github.com/powerline/deps tests/bot-ci/deps

. tests/bot-ci/scripts/common/main.sh

if test -n "$USE_UCS2_PYTHON" ; then
	for variant in $UCS2_PYTHON_VARIANTS ; do
		archive="${PWD:-$(pwd)}/tests/bot-ci/deps/cpython-ucs2/cpython-ucs2-${variant}.tar.gz"
		sudo sh -c "cd /opt && tar xzvf $archive"
	done
fi

pip install .

pip install --no-deps tests/bot-ci/deps/wheels/$PYTHON_SUFFIX/*.whl

sudo apt-get install -qq screen zsh tcsh mksh busybox socat
# Travis has too outdated fish. It cannot be used for tests.
# sudo apt-get install fish
true
