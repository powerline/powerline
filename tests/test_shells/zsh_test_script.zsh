set -e
set -x
. tests/bot-ci/scripts/common/main.sh
zmodload zpython || zmodload libzpython
zpython 'import zsh'
zpython 'import platform'
zpython 'zsh.setvalue("ZSH_PYTHON_VERSION", platform.python_version())'
zpython 'zsh.setvalue("ZSH_PYTHON_IMPLEMENTATION", platform.python_implementation())'

[[ $ZSH_PYTHON_IMPLEMENTATION = $PYTHON_IMPLEMENTATION ]]
[[ $ZSH_PYTHON_VERSION = $PYTHON_VERSION ]]
