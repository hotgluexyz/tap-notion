# AGENTS.md — AI agent guide for tap-notion

This document guides AI agents and developers working on this Singer tap.

## Project overview

- **Project type**: Singer tap
- **Source**: Notion (Notion API)
- **Stream type**: REST (`RESTStream` base in `tap_notion/client.py`)
- **Authentication**: Bearer token — `access_token` in config, `BearerTokenAuthenticator` in `NotionStream.authenticator`
- **Framework**: [Meltano Singer SDK](https://github.com/meltano/sdk) (`hotglue_singer_sdk`)

## Architecture

The tap follows the Singer spec and uses `hotglue_singer_sdk` to extract from Notion.

### Key components

1. **Tap** (`tap_notion/tap.py`): Entry point, `STREAM_TYPES`, `config_jsonschema`
1. **Client** (`tap_notion/client.py`): `NotionStream` base — `url_base`, headers (`Notion-Version`), `records_jsonpath`, pagination (`get_next_page_token`), `authenticator`
1. **Streams** (`tap_notion/streams.py`): Concrete streams (e.g. `SearchPagesStream`, `BlocksSteam`), schemas, `path`, `rest_method`, `prepare_request_payload` where needed, parent/child context for nested resources

## Development guidelines

### Singer concepts

- **Streams**: Endpoints or logical datasets (pages, blocks, etc.)
- **State**: Bookmarks for incremental sync
- **Catalog**: Stream metadata and JSON Schema
- **Records**: Rows emitted to stdout
- **Schemas**: `th.PropertiesList` / `th.Property` definitions

### REST notes (this tap)

- Set **`path`** under `url_base` (`https://api.notion.com/v1`), **`records_jsonpath`**, and pagination in **`get_next_page_token()`** (Notion uses `next_cursor` in the JSON body; see `next_page_token_jsonpath` on `NotionStream`)
- POST search uses **`prepare_request_payload`** and **`rest_method = "POST"`** on `SearchPagesStream`
- Child streams use **`parent_stream_type`** and **`get_child_context`** (e.g. blocks under pages)

### Adding a new stream

1. Add a class in `tap_notion/streams.py` (PascalCase + `Stream`; Singer `name` in snake_case)
1. Set **`primary_keys`** and **`replication_key`** (or `None` if not incremental)
1. Set **`name`** and **`path`** (and **`rest_method`**, **`prepare_request_payload`** if not GET)
1. Define **`schema`** with `th.PropertiesList` like existing streams
1. Register in **`STREAM_TYPES`** and the **`from tap_notion.streams import (...)`** line in `tap.py`

Example shape:

```python
from hotglue_singer_sdk import typing as th

from tap_notion.client import NotionStream


class MyNewStream(NotionStream):
    name = "my_new_stream"
    path = "/v1/your/resource"
    primary_keys = ["id"]
    replication_key = "last_edited_time"

    schema = th.PropertiesList(
        th.Property("id", th.StringType, description="Primary key"),
        th.Property("last_edited_time", th.DateTimeType),
    ).to_dict()
```

### Briefing with HTTP details

To update `streams.py` / `client.py` / `tap.py` efficiently, include:

1. **Goal** (e.g. new stream or fix pagination/schema)
1. **Request**: method, path, query/body (redact secrets)
1. **Sample JSON** response (trimmed), with where the record list lives
1. **Pagination**: cursor, header, offset, or none
1. **Incremental**: replication key and primary keys, or full-table
1. **Auth/header quirks** if relevant (e.g. `Notion-Version`)

### Modifying authentication

- Token is **`access_token`** in config (see `tap.py` `config_jsonschema`)
- **`BearerTokenAuthenticator.create_for_stream`** in `NotionStream.authenticator`
- Add `secret=True` on the property in the schema for sensitive settings; keep `README` / `.secrets` examples aligned

### Pagination

The base stream uses **`get_next_page_token()`** with **`extract_jsonpath`** on the response JSON. Return the next token the API expects (e.g. Notion `next_cursor` passed as `start_cursor` in the search payload); return **`None`** when done.

Wire tokens in **`get_url_params`**, **`prepare_request_payload`**, or overrides as your endpoint requires.

### State and incremental sync

- Set **`replication_key`** for incremental streams
- Override **`get_starting_timestamp()`** if you need a custom start
- Prefer SDK state APIs over mutating state by hand

### Schema evolution

- Prefer optional properties when the API is volatile
- Use `th.ObjectType` / `th.CustomType` for nested or variable shapes (see existing `properties`, `cover`, etc.)

### Testing

```bash
pip install -e .
pip install pytest
pytest

pytest tap_notion/tests/test_core.py -k test_name
```

### Configuration

Authoritative settings are **`config_jsonschema`** on `TapNotion` in `tap_notion/tap.py`.

Example CLI:

```bash
tap-notion --config config.json --discover
tap-notion --config config.json --catalog catalog.json
```

Example schema fragment (this tap uses `access_token`):

```python
from hotglue_singer_sdk import typing as th

config_jsonschema = th.PropertiesList(
    th.Property(
        "access_token",
        th.StringType,
        required=True,
        secret=True,
        description="Notion integration token",
    ),
).to_dict()
```

### Keeping config, docs, and secrets in sync

When you change config:

1. Update `config_jsonschema` in `tap_notion/tap.py`
1. Update **`README.md`** and any example **`config.json`**
1. Update **`.env.example`** if you use env-based config (`tap-notion --about` lists env keys)

| `th.*` in schema | Typical JSON in `config.json` |
|------------------|--------------------------------|
| `StringType`     | string                         |
| `IntegerType`    | integer                        |
| `BooleanType`    | boolean                        |
| `NumberType`     | number                         |
| `DateTimeType`   | string (ISO-8601)              |
| `ArrayType`      | array                          |
| `ObjectType`     | object                         |

### Common pitfalls

1. **Rate limits**: rely on SDK retries/backoff where configured
1. **Large responses**: pagination; avoid loading full datasets in memory
1. **Schema drift**: nullable/optional fields; validate samples against real API payloads
1. **State**: use SDK helpers, not ad-hoc state edits
1. **Timezones**: prefer UTC / ISO-8601
1. **Notion-Version header**: required for the API — keep `http_headers` in sync with [Notion versioning](https://developers.notion.com/reference/versioning)

### SDK resources

- [Meltano Singer SDK](https://github.com/meltano/sdk)
- [Singer spec](https://github.com/singer-io/getting-started/blob/master/docs/SPEC.md)
- [Notion API reference](https://developers.notion.com/reference)

### Best practices

1. Use **`self.logger`** for diagnostics
1. Document new streams and config in **`README.md`**
1. Add tests for non-trivial stream or auth behavior
1. Run **ruff** (see `ruff.toml`) and **mypy** (`mypy.ini`) before merging when applicable

## File structure

```
tap-notion/
├── tap_notion/
│   ├── __init__.py
│   ├── tap.py
│   ├── client.py
│   ├── streams.py
│   └── tests/
│       ├── __init__.py
│       └── test_core.py
├── .secrets/           # local config (gitignored); launch.json cwd
├── .vscode/
│   └── launch.json
├── meltano.yml
├── pyproject.toml
├── ruff.toml
├── mypy.ini
├── tox.ini
└── README.md
```

## Bumping `singer-sdk`

1. Read [meltano/sdk releases](https://github.com/meltano/sdk/releases) and upgrade notes for each jump
1. Bump **`singer-sdk`** in **`pyproject.toml`** (`[tool.poetry.dependencies]`)
1. `poetry update singer-sdk` (or reinstall in your venv), then **`pytest`**
1. Optionally: `pytest -W error::DeprecationWarning`

## Reporting SDK issues

For bugs or gaps in **`hotglue_singer_sdk`** itself, use the [meltano/sdk issue tracker](https://github.com/meltano/sdk/issues). Include SDK version (`tap-notion --version`), Python version, and a minimal repro.
