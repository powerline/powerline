# vim:fileencoding=utf-8:noet
'''
psql prompt integration for Powerline.

Requires a companion patch to PostgreSQL psql (``PROMPT_COMMAND``, ``%D``,
``PROMPT_SESSION_EXPORT``).  See ``docs/source/usage/psql-postgres-integration.rst``
and ``src/bin/psql/powerline-integration.md`` in the postgres tree.  Both patches
are opt-in and can be merged independently.

Configure in :file:`~/.psqlrc`::

    \\set PROMPT_SESSION_EXPORT on
    \\set PROMPT_COMMAND 'powerline-render psql left --last-exit-code ${PSQL_SHELL_EXIT:-0} -w ${COLUMNS:-120} 2>/dev/null'
    \\set PROMPT1 '%D %x%# '
    \\set PROMPT2 '%w%R%x%# '

Requires a recent psql that exports standard :envvar:`PG*` connection
variables and :envvar:`PSQL_SHELL_EXIT` before each :varname:`PROMPT_COMMAND`
run.

The ``user`` segment uses the ``superuser`` highlight group (red, like the
shell prompt) when the connected PostgreSQL role has superuser privileges
(:envvar:`PSQL_SUPERUSER=1`, same test as psql's ``%#`` escape).

.. note::

   Do **not** wrap ``%D`` in ``%[`` … ``%]``.  The psql renderer already
   marks ANSI sequences with readline non-printing characters (``\\x01`` /
   ``\\x02``).  An extra ``%[`` … ``%]`` wrapper hides the entire powerline
   bar from readline's width calculation and breaks editing (e.g. ``\\c
   postgres`` is received as ``\\cpostgres``).
'''
from __future__ import (unicode_literals, division, absolute_import, print_function)