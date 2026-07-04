# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.theme import requires_segment_info


def _environ(segment_info, name):
	return segment_info.get('environ', {}).get(name)


def _is_pg_superuser(segment_info):
	'''True when the PostgreSQL session role has superuser privileges.'''
	su = _environ(segment_info, 'PSQL_SUPERUSER')
	return su in ('1', 'on', 'true', 'yes')


@requires_segment_info
def user(pl, segment_info, highlight_superuser=True):
	'''Connected PostgreSQL user (:envvar:`PGUSER`).

	:param bool highlight_superuser:
		If True (default), use the ``superuser`` highlight group when
		:envvar:`PSQL_SUPERUSER` is ``1`` (same test psql uses for the ``%#``
		prompt escape).

	Highlight groups used: ``superuser``, ``user``.
	'''
	val = _environ(segment_info, 'PGUSER')
	if not val:
		return None
	if highlight_superuser and _is_pg_superuser(segment_info):
		return [{
			'contents': val,
			'highlight_groups': ['superuser', 'user'],
		}]
	return val


@requires_segment_info
def database(pl, segment_info, hide_same_as_user=True):
	'''Current database name (:envvar:`PGDATABASE`).

	:param bool hide_same_as_user:
		If True (default), omit the segment when the database name equals
		:envvar:`PGUSER` (like psql's ``%~`` prompt escape).
	'''
	val = _environ(segment_info, 'PGDATABASE')
	if not val:
		return None
	if hide_same_as_user and val == _environ(segment_info, 'PGUSER'):
		return None
	return val


_LOCAL_HOSTNAMES = frozenset(('localhost', '127.0.0.1', '::1'))


@requires_segment_info
def host(pl, segment_info, short=True, localhost_is_local=True):
	'''Server host (:envvar:`PGHOST`), or ``[local]`` for Unix sockets.

	:param bool localhost_is_local:
		If True (default), treat ``localhost`` and loopback addresses as
		``[local]`` (matching typical local psql connections).
	'''
	val = _environ(segment_info, 'PGHOST')
	if not val:
		return '[local]'
	if val[0] == '/' or val[0] == '@':
		return '[local]' if short else val
	if short:
		val = val.split('.')[0]
	if localhost_is_local and val in _LOCAL_HOSTNAMES:
		return '[local]'
	return val


@requires_segment_info
def port(pl, segment_info, show_default=True):
	'''Server port (:envvar:`PGPORT`).

	:param bool show_default:
		If False (default), omit the standard PostgreSQL port (5432).
	'''
	val = _environ(segment_info, 'PGPORT')
	if not val or (not show_default and val == '5432'):
		return None
	return val


@requires_segment_info
def transaction(pl, segment_info):
	'''Transaction state from :envvar:`PSQL_TXN` (idle, active, error).

	Highlight groups used: ``transaction``, ``transaction:active``,
	``transaction:error``.
	'''
	txn = _environ(segment_info, 'PSQL_TXN')
	if not txn or txn == 'idle':
		return None
	if txn == 'active':
		return [{
			'contents': '*',
			'highlight_groups': ['transaction:active', 'transaction'],
		}]
	if txn == 'error':
		return [{
			'contents': '!',
			'highlight_groups': ['transaction:error', 'transaction'],
		}]
	return [{
		'contents': '?',
		'highlight_groups': ['transaction'],
	}]


@requires_segment_info
def row_count(pl, segment_info, show_zero=False, label=True):
	'''Rows from the last query (:envvar:`PSQL_ROW_COUNT`).

	:param bool label:
		If True (default), format as ``N row`` / ``N rows`` instead of a bare
		number.
	'''
	val = _environ(segment_info, 'PSQL_ROW_COUNT')
	if not val or (not show_zero and val == '0'):
		return None
	if not label:
		return val
	try:
		n = int(val)
	except (TypeError, ValueError):
		return val
	if n == 1:
		return '1 row'
	return '{0} rows'.format(n)


@requires_segment_info
def txid(pl, segment_info):
	'''Transaction id from :envvar:`PSQL_TXID` (e.g. set at connect via ``\\gset``).'''
	val = _environ(segment_info, 'PSQL_TXID')
	return val if val else None