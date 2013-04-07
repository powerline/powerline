#!/usr/bin/env python
# vim:fileencoding=utf-8:noet

from powerline import Powerline
import sys
from time import sleep
from powerline.lib.monotonic import monotonic
from subprocess import Popen, PIPE

powerline = Powerline('wm', renderer_module='pango_markup')
powerline.update_renderer()

try:
	interval = float(sys.argv[1])
except IndexError:
	interval = 2


def read_to_log(pl, client):
	for line in client.stdout:
		if line:
			pl.info(line, prefix='awesome-client')
	for line in client.stderr:
		if line:
			pl.error(line, prefix='awesome-client')
	if client.wait():
		pl.error('Client exited with {0}', client.returncode, prefix='awesome')


while True:
	start_time = monotonic()
	s = powerline.render(side='right')
	request = "powerline_widget:set_markup('" + s.replace('\\', '\\\\').replace("'", "\\'") + "')\n"
	client = Popen(['awesome-client'], shell=False, stdout=PIPE, stderr=PIPE, stdin=PIPE)
	client.stdin.write(request.encode('utf-8'))
	client.stdin.close()
	read_to_log(powerline.pl, client)
	sleep(max(interval - (monotonic() - start_time), 0.1))
