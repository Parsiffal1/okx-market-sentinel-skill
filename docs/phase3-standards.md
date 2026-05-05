# Phase3 Standards

## Goal
Phase3 must follow a single, repeatable project standard so that source fetchers, builders, trigger logic, tests, and output artifacts all use the same conventions.

## Canonical workflow
Always use the canonical entrypoint:

```bash
python scripts/phase3_pipeline.py
```

The standard execution sequence is:
1. Run all source fetchers under `scripts/sources/`
2. Run `scripts/build_context_cache.py`
3. Run `scripts/build_triggers.py`
4. Write a markdown report under `reports/`
5. Emit machine-readable JSON to stdout

Current canonical source order:
1. `okx_positions_fetch.py`
2. `blockbeats_fetch.py`
3. `cmc_fetch.py`
4. `moss_xsignal_fetch.py`
5. `okx_news_fetch.py`
6. `opennews_fetch.py`
7. `opentwitter_fetch.py`
8. `jin10_fetch.py`

## Directory layout
- `scripts/sources/` — source fetchers only
- `scripts/build_context_cache.py` — context aggregation only
- `scripts/build_triggers.py` — trigger construction only
- `scripts/phase3_pipeline.py` — orchestration only
- `tests/` — test files mirroring the Phase3 modules they validate
- `docs/` — workflow and standards documentation
- `context/raw/` — per-source raw cache files
- `context/context_cache.json` — normalized Phase3 cache
- `context/trigger_candidates.json` — normalized trigger output

## Python style baseline
- UTF-8, LF line endings, 4-space indentation
- Each core Phase3 module must have a module docstring
- Prefer explicit type hints for public helpers and orchestrator functions
- Keep constants at top-level and grouped near imports
- Keep a single `main()` entrypoint guarded by `if __name__ == '__main__':`
- Source fetchers should use shared helpers from `scripts/sources/_common.py` when writing raw cache and stdout results

## Source fetcher template
Each source fetcher should follow this shape:
1. module docstring
2. imports
3. top-level constants
4. pure helper functions
5. `main()`
6. `if __name__ == '__main__': main()`

## Builder / trigger template
Builder and trigger scripts should follow this shape:
1. module docstring
2. imports
3. path/schema constants
4. pure helpers for parsing/normalization/classification
5. `build_*()` function returning normalized payload
6. `main()` to write artifact and print stdout JSON summary

## Stdout JSON summary schema
Each runnable Phase3 script should emit JSON to stdout.

### Source fetchers — minimum fields
```json
{
  "ok": true,
  "source": "source_id",
  "path": "/absolute/path/to/raw_cache.json"
}
```
Additional source-specific summary fields are allowed, but the three fields above must remain stable.

### Builder — minimum fields
```json
{
  "ok": true,
  "generated_at": "ISO-8601 timestamp",
  "context_cache": "/absolute/path/to/context_cache.json"
}
```

### Trigger builder — minimum fields
```json
{
  "ok": true,
  "trigger_file": "/absolute/path/to/trigger_candidates.json"
}
```

## Raw cache schema
Every source raw cache written via `_common.write_raw_cache()` must follow:

```json
{
  "updated_at": "ISO-8601 timestamp",
  "source": "source_id",
  "status": "ok|partial|error|unknown",
  "data": {}
}
```

Optional:
```json
{
  "error": "human-readable message"
}
```

## Test naming standard
- `tests/test_<module_name>.py`
- One module-level `load_module()` helper for direct script testing when needed
- Prefer behavior-driven test names describing observable outcomes
- For Phase3 changes, update targeted tests first, then run full `pytest -q`

## Documentation standard
- `docs/phase3-overview.md` explains workflow and source responsibilities
- `docs/phase3-standards.md` defines formatting, structure, and output contracts
- When behavior changes, update docs in the same change set
