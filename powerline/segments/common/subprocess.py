# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from subprocess import check_output

def command(pl, command):
    return check_output(command)
