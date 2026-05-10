# Runtime Commands

## Pipeline

```bash
python scripts/phase3_pipeline.py
python scripts/phase3_pipeline.py --sequential
```

## Core rebuild

```bash
python scripts/build_context_cache.py
python scripts/build_triggers.py
```

## Notifier

```bash
python scripts/run_phase3_notifier.py
```

## Dashboard

```bash
python dashboard/server.py --host 127.0.0.1 --port 8765
```

Use `127.0.0.1` as the safe default. Only switch to `0.0.0.0` when you intentionally expose the dashboard behind your own access controls.

## Semantic Compass

```bash
python scripts/refresh_semantic_compass.py --brief "补充霍尔木兹海峡关闭 / 恢复通航 / 稳定币脱锚 / 交易所宕机等常见表述"
python scripts/refresh_semantic_compass.py --print-prompt
```

## Testing

```bash
pytest -q
pytest tests/test_context_cache_builder.py -q
pytest tests/test_dashboard_server.py -q
pytest tests/test_semantic_compass.py -q
```

## Common operator checks

### Is dashboard listening?
```bash
ss -ltnp | grep 8765 || true
```

### Can dashboard API answer locally?
```bash
python - <<'PY'
import urllib.request
for url in ['http://127.0.0.1:8765/api/config','http://127.0.0.1:8765/api/dashboard']:
    print(url)
    print(urllib.request.urlopen(url, timeout=5).read().decode()[:300])
PY
```

### Refresh pipeline artifacts before inspecting dashboard state
```bash
python scripts/phase3_pipeline.py --sequential
```
