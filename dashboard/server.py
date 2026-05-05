from __future__ import annotations

import argparse
import json
import socket
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

from dashboard_adapter import build_dashboard_payload

BASE_DIR = Path(__file__).resolve().parents[1]
CONTEXT_DIR = BASE_DIR / 'context'
STATIC_DIR = BASE_DIR / 'dashboard' / 'static'
DEFAULT_CONTEXT_PATH = CONTEXT_DIR / 'context_cache.json'
DEFAULT_TRIGGERS_PATH = CONTEXT_DIR / 'trigger_candidates.json'
DEFAULT_SETTINGS_PATH = CONTEXT_DIR / 'dashboard_settings.json'
DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 8765
DEFAULT_SETTINGS = {
    'backend_refresh_minutes': 30,
    'frontend_poll_seconds': 10,
    'theme': 'dark',
    'compact_mode': False,
    'semantic_compass_focus': '',
    'semantic_compass_last_brief': '',
    'semantic_compass_last_updated_at': '',
    'semantic_compass_refresh_status': 'idle',
}

EDITABLE_SETTINGS_FIELDS = {'backend_refresh_minutes', 'frontend_poll_seconds', 'theme', 'compact_mode', 'semantic_compass_focus'}


def sanitize_settings_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
    incoming = payload or {}
    if not isinstance(incoming, dict):
        raise ValueError('settings payload must be a JSON object')
    return {key: incoming[key] for key in EDITABLE_SETTINGS_FIELDS if key in incoming}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding='utf-8'))


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def load_dashboard_settings(path: Path = DEFAULT_SETTINGS_PATH) -> dict[str, Any]:
    current = load_json(path)
    merged = {**DEFAULT_SETTINGS, **current}
    merged['backend_refresh_minutes'] = int(merged.get('backend_refresh_minutes', 30) or 30)
    merged['frontend_poll_seconds'] = int(merged.get('frontend_poll_seconds', 10) or 10)
    merged['theme'] = str(merged.get('theme', 'dark') or 'dark')
    merged['compact_mode'] = bool(merged.get('compact_mode', False))
    merged['semantic_compass_focus'] = str(merged.get('semantic_compass_focus', '') or '')
    merged['semantic_compass_last_brief'] = str(merged.get('semantic_compass_last_brief', '') or '')
    merged['semantic_compass_last_updated_at'] = str(merged.get('semantic_compass_last_updated_at', '') or '')
    merged['semantic_compass_refresh_status'] = str(merged.get('semantic_compass_refresh_status', 'idle') or 'idle')
    return merged




def detect_server_ip() -> str | None:
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        if ip and not ip.startswith('127.'):
            return ip
    except Exception:
        pass
    return None


def build_access_urls(host: str, port: int, server_ip: str | None = None) -> dict[str, str | None]:
    public_candidate = server_ip or detect_server_ip()
    bind = f'{host}:{port}'
    local_url = f'http://127.0.0.1:{port}'
    public_url = None
    if host == '0.0.0.0' and public_candidate:
        public_url = f'http://{public_candidate}:{port}'
    elif host not in {'127.0.0.1', 'localhost', '0.0.0.0'}:
        public_url = f'http://{host}:{port}'
    return {
        'bind': bind,
        'local_url': local_url,
        'public_url': public_url,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run local/cloud dashboard server for crypto-agent')
    parser.add_argument('--host', default=DEFAULT_HOST, help='Bind host, e.g. 127.0.0.1 or 0.0.0.0')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='Bind port')
    return parser.parse_args(argv)

def default_refresh_runner() -> dict[str, Any]:
    proc = subprocess.run(['python', 'scripts/phase3_pipeline.py', '--sequential'], cwd=BASE_DIR, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or 'dashboard refresh failed')
    return json.loads(proc.stdout)


def default_compass_refresh_runner(brief: str) -> dict[str, Any]:
    proc = subprocess.run(
        ['python', 'scripts/refresh_semantic_compass.py', '--brief', brief],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        timeout=900,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or 'semantic compass refresh failed')
    return json.loads(proc.stdout)


class DashboardService:
    def __init__(
        self,
        context_path: Path = DEFAULT_CONTEXT_PATH,
        triggers_path: Path = DEFAULT_TRIGGERS_PATH,
        settings_path: Path = DEFAULT_SETTINGS_PATH,
        refresh_runner: Callable[[], dict[str, Any]] = default_refresh_runner,
        compass_refresh_runner: Callable[[str], dict[str, Any]] = default_compass_refresh_runner,
    ) -> None:
        self.context_path = context_path
        self.triggers_path = triggers_path
        self.settings_path = settings_path
        self.refresh_runner = refresh_runner
        self.compass_refresh_runner = compass_refresh_runner

    def get_context(self) -> dict[str, Any]:
        return load_json(self.context_path)

    def get_triggers(self) -> dict[str, Any]:
        return load_json(self.triggers_path)

    def get_settings(self) -> dict[str, Any]:
        return load_dashboard_settings(self.settings_path)

    def persist_settings(self, payload: dict[str, Any]) -> dict[str, Any]:
        merged = {**self.get_settings(), **(payload or {})}
        try:
            merged['backend_refresh_minutes'] = int(merged.get('backend_refresh_minutes', 30) or 30)
        except (TypeError, ValueError) as exc:
            raise ValueError('backend_refresh_minutes must be an integer') from exc
        try:
            merged['frontend_poll_seconds'] = int(merged.get('frontend_poll_seconds', 10) or 10)
        except (TypeError, ValueError) as exc:
            raise ValueError('frontend_poll_seconds must be an integer') from exc
        merged['theme'] = str(merged.get('theme', 'dark') or 'dark')
        merged['compact_mode'] = bool(merged.get('compact_mode', False))
        merged['semantic_compass_focus'] = str(merged.get('semantic_compass_focus', '') or '')
        merged['semantic_compass_last_brief'] = str(merged.get('semantic_compass_last_brief', '') or '')
        merged['semantic_compass_last_updated_at'] = str(merged.get('semantic_compass_last_updated_at', '') or '')
        merged['semantic_compass_refresh_status'] = str(merged.get('semantic_compass_refresh_status', 'idle') or 'idle')
        save_json(self.settings_path, merged)
        return merged

    def update_settings(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.persist_settings(sanitize_settings_payload(payload))

    def get_dashboard_payload(self) -> dict[str, Any]:
        return build_dashboard_payload(self.get_context(), self.get_triggers(), self.get_settings())

    def run_refresh(self) -> dict[str, Any]:
        return self.refresh_runner()

    def run_semantic_compass_refresh(self, brief: str) -> dict[str, Any]:
        normalized_brief = str(brief or '').strip() or self.get_settings().get('semantic_compass_focus', '')
        result = self.compass_refresh_runner(normalized_brief)
        self.persist_settings({
            'semantic_compass_focus': normalized_brief,
            'semantic_compass_last_brief': result.get('brief', normalized_brief),
            'semantic_compass_last_updated_at': result.get('updated_at', ''),
            'semantic_compass_refresh_status': 'ok' if result.get('ok') else 'error',
        })
        return result


def create_handler(service: DashboardService):
    class DashboardHandler(BaseHTTPRequestHandler):
        def _json(self, payload: dict[str, Any], status: int = 200) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _text(self, payload: str, content_type: str = 'text/html; charset=utf-8', status: int = 200) -> None:
            body = payload.encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path == '/api/dashboard':
                return self._json(service.get_dashboard_payload())
            if parsed.path == '/api/context':
                return self._json(service.get_context())
            if parsed.path == '/api/triggers':
                return self._json(service.get_triggers())
            if parsed.path == '/api/config':
                return self._json(service.get_settings())
            if parsed.path in {'/', '/index.html'}:
                return self._text((STATIC_DIR / 'index.html').read_text(encoding='utf-8'))
            if parsed.path == '/app.js':
                return self._text((STATIC_DIR / 'app.js').read_text(encoding='utf-8'), 'application/javascript; charset=utf-8')
            if parsed.path == '/styles.css':
                return self._text((STATIC_DIR / 'styles.css').read_text(encoding='utf-8'), 'text/css; charset=utf-8')
            return self._json({'ok': False, 'error': 'not_found'}, status=404)

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            length = int(self.headers.get('Content-Length', '0') or 0)
            raw = self.rfile.read(length) if length else b'{}'
            try:
                payload = json.loads(raw.decode('utf-8') or '{}') if raw else {}
            except Exception:
                return self._json({'ok': False, 'error': 'invalid_json'}, status=400)
            try:
                if parsed.path == '/api/config':
                    return self._json(service.update_settings(payload))
                if parsed.path == '/api/refresh':
                    return self._json(service.run_refresh())
                if parsed.path == '/api/semantic-compass/refresh':
                    return self._json(service.run_semantic_compass_refresh(str((payload or {}).get('brief') or '')))
            except ValueError as exc:
                return self._json({'ok': False, 'error': 'invalid_payload', 'message': str(exc)}, status=422)
            except RuntimeError as exc:
                return self._json({'ok': False, 'error': 'runtime_error', 'message': str(exc)}, status=500)
            return self._json({'ok': False, 'error': 'not_found'}, status=404)

        def log_message(self, format: str, *args: Any) -> None:
            return None

    return DashboardHandler


def run_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    service = DashboardService()
    server = ThreadingHTTPServer((host, port), create_handler(service))
    urls = build_access_urls(host=host, port=port)
    print(json.dumps({'ok': True, 'host': host, 'port': port, **urls}, ensure_ascii=False))
    server.serve_forever()


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    run_server(host=args.host, port=args.port)


if __name__ == '__main__':
    main()
