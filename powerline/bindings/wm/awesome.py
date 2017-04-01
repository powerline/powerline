# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys

from threading import Thread, Event
from time import sleep
from subprocess import Popen, PIPE

from powerline import Powerline
from powerline.lib.monotonic import monotonic


def read_to_log(pl, client):
	for line in client.stdout:
		if line:
			pl.info(line, prefix='awesome-client')
	for line in client.stderr:
		if line:
			pl.error(line, prefix='awesome-client')
	if client.wait():
		pl.error('Client exited with {0}', client.returncode, prefix='awesome')


def run(thread_shutdown_event=None, pl_shutdown_event=None, pl_config_loader=None,
        interval=None):
	powerline = Powerline(
		'wm',
		renderer_module='pango_markup',
		shutdown_event=pl_shutdown_event,
		config_loader=pl_config_loader,
	)
	powerline.update_renderer()

	if not thread_shutdown_event:
		thread_shutdown_event = powerline.shutdown_event

	while not thread_shutdown_event.is_set():
		# powerline.update_interval may change over time
		used_interval = interval or powerline.update_interval
		start_time = monotonic()
		s = powerline.render(side='right')
		request = 'powerline_widget:set_markup(\'' + s.translate({'\'': '\\\'', '\\': '\\\\'}) + '\')\n'
		client = Popen(['awesome-client'], shell=False, stdout=PIPE, stderr=PIPE, stdin=PIPE)
		client.stdin.write(request.encode('utf-8'))
		client.stdin.close()
		read_to_log(powerline.pl, client)
		thread_shutdown_event.wait(max(used_interval - (monotonic() - start_time), 0.1))


class AwesomeThread(Thread):
	__slots__ = ('powerline_shutdown_event',)

	def __init__(self, **kwargs):
		super(AwesomeThread, self).__init__()
		self.powerline_run_kwargs = kwargs

	def run(self):
		run(**self.powerline_run_kwargs)
