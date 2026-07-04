# Powerline patch: psql extension

## Summary

Add a **psql** extension for rendering PostgreSQL interactive prompts via
`powerline-render`, designed to pair with optional `PROMPT_COMMAND` support in
PostgreSQL psql (separate patch).  See
`docs/source/usage/psql-postgres-integration.rst` and the companion doc
`src/bin/psql/powerline-integration.md` in the postgres patch.

## Backward compatibility

- New files only under `powerline/` config and `psql` ext in `config.json`.
- No change to existing extensions unless the user configures psql.
- PostgreSQL session export is gated there by `PROMPT_SESSION_EXPORT` (off by
  default); this extension is inactive without `PROMPT_COMMAND` in `.psqlrc`.

We can add an `enabled: false` default or distribution packaging split if
reviewers prefer.

## Features

- **Segments** (`powerline/segments/psql.py`): user (PG superuser highlight via
  `PSQL_SUPERUSER`), database, host, port, transaction, row count, txid,
  `shell.last_status`
- **Renderer** (`powerline/renderers/psql.py`): readline `\x01`/`\x02` markers
- **Theme / colorscheme** under `config_files/themes/psql/` and
  `colorschemes/psql/`
- **Bindings** (`powerline/bindings/psql/`), docs, lint registration

## Example

![psql with powerline prompt](source/images/psql-powerline-example.png)

PostgreSQL superuser role → red user segment; database name after `\c` → green
segment; failed query → red exit-status segment.  See postgres
`src/bin/psql/powerline-integration.md` for details.

## Usage

```sql
\set PROMPT_SESSION_EXPORT on
\set PROMPT_COMMAND 'powerline-render psql left --last-exit-code ${PSQL_SHELL_EXIT:-0} -w ${COLUMNS:-120} 2>/dev/null'
\set PROMPT1 '%D %x%# '
```

## Testing

- `python3 scripts/powerline-lint` passes
- Manual: `PGDATABASE=... PSQL_SUPERUSER=1 powerline-render psql left`
- End-to-end with patched psql binary and `.psqlrc`

## Companion patch

PostgreSQL psql `PROMPT_COMMAND` / `%D` / `PROMPT_SESSION_EXPORT` — separate
submission to postgres/postgres.