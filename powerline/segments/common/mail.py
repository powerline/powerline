# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import re

from collections import namedtuple

from powerline.lib.threaded import KwThreadedSegment
from powerline.segments import with_docstring


_IMAPKey = namedtuple('Key', 'username password server port folder')


class EmailIMAPSegment(KwThreadedSegment):
	interval = 60

	@staticmethod
	def key(username, password, server='imap.gmail.com', port=993, folder='INBOX', **kwargs):
		return _IMAPKey(username, password, server, port, folder)

	def compute_state(self, key):
		if not key.username or not key.password:
			self.warn('Username and password are not configured')
			return None
		try:
			import imaplib
		except imaplib.IMAP4.error as e:
			unread_count = str(e)
		else:
			mail = imaplib.IMAP4_SSL(key.server, key.port)
			mail.login(key.username, key.password)
			rc, message = mail.status(key.folder, '(UNSEEN)')
			unread_str = message[0].decode('utf-8')
			unread_count = int(re.search('UNSEEN (\d+)', unread_str).group(1))
		return unread_count

	@staticmethod
	def render_one(unread_count, max_msgs=None, **kwargs):
		if not unread_count:
			return None
		elif type(unread_count) != int or not max_msgs:
			return [{
				'contents': str(unread_count),
				'highlight_groups': ['email_alert'],
			}]
		else:
			return [{
				'contents': str(unread_count),
				'highlight_groups': ['email_alert_gradient', 'email_alert'],
				'gradient_level': min(unread_count * 100.0 / max_msgs, 100),
			}]


email_imap_alert = with_docstring(EmailIMAPSegment(),
'''Return unread e-mail count for IMAP servers.

:param str username:
	login username
:param str password:
	login password
:param str server:
	e-mail server
:param int port:
	e-mail server port
:param str folder:
	folder to check for e-mails
:param int max_msgs:
	Maximum number of messages. If there are more messages then max_msgs then it
	will use gradient level equal to 100, otherwise gradient level is equal to
	``100 * msgs_num / max_msgs``. If not present gradient is not computed.

Highlight groups used: ``email_alert_gradient`` (gradient), ``email_alert``.
''')
