.. _psql-postgres-integration:

psql / PostgreSQL integration
=============================

This **psql extension** is designed to work with optional prompt hooks added
to PostgreSQL's psql client.  The two patches are independent at build time;
full functionality requires both to be deployed and configured in
:file:`~/.psqlrc`.

PostgreSQL side (companion patch)
---------------------------------

Repository: https://github.com/postgres/postgres

Documentation in that patch:
:file:`src/bin/psql/powerline-integration.md`

Features used by this extension:

- :varname:`PROMPT_COMMAND` — run ``powerline-render`` before each prompt
- ``%D`` — insert renderer output into :varname:`PROMPT1`
- :varname:`PROMPT_SESSION_EXPORT` — **off by default**; set ``on`` to export
  :envvar:`PG*` / :envvar:`PSQL_*` session variables for the renderer
- :varname:`SHELL_EXIT` / :envvar:`PSQL_SHELL_EXIT` — last command status
- :envvar:`PSQL_SUPERUSER` — PostgreSQL superuser flag (``user`` segment color)

Powerline side (this patch)
---------------------------

- Extension name: ``psql``
- Entry point: ``powerline-render psql left``
- Module: :py:mod:`powerline.psql`, segments in
  :py:mod:`powerline.segments.psql`
- Renderer: :py:mod:`powerline.renderers.psql` (readline markers)

Example screenshot
------------------

End-to-end session with both patches configured (built psql, this extension,
sample :file:`~/.psqlrc`):

.. image:: /images/psql-powerline-example.png
   :alt: psql interactive session with powerline prompt segments

The red **user** segment indicates a PostgreSQL superuser role
(:envvar:`PSQL_SUPERUSER=1`).  The green **database** segment appears after
``\\c`` when the database name differs from the user.  The red status segment
after ``SELECT 1/0`` reflects :varname:`SHELL_EXIT`.

Backward compatibility
----------------------

The psql extension is inert until referenced from :varname:`PROMPT_COMMAND`.
Existing powerline installations are unaffected.  The PostgreSQL patch is inert
until :varname:`PROMPT_COMMAND` / :varname:`PROMPT_SESSION_EXPORT` are set.

Example :file:`~/.psqlrc` (both patches)
----------------------------------------

.. code-block:: sql

   \\set PROMPT_SESSION_EXPORT on
   \\set PROMPT_COMMAND 'powerline-render psql left --last-exit-code ${PSQL_SHELL_EXIT:-0} -w ${COLUMNS:-120} 2>/dev/null'
   \\set PROMPT1 '%D %x%# '
   \\set PROMPT2 '%w%R%x%# '

Optional transaction id segment at connect:

.. code-block:: sql

   SELECT txid_current() AS txid \\gset

Readline note: use ``%D`` without an extra ``%[`` … ``%]`` wrapper; the psql
renderer already emits non-printing markers.

Maintainers
-----------

We can add an explicit ``enabled`` flag or packaging split if preferred.  The
current design keeps both sides opt-in via psql variables and the ``psql`` ext
entry in :file:`config.json`.