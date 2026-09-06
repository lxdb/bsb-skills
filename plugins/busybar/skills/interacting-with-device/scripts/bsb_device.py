#!/usr/bin/env python3
"""Small BUSY Bar HTTP CLI. Only `events` imports optional packages."""

import argparse
import base64
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import uuid
import zlib


API_VERSION = '27.5.0'
THEMES_PATH = '/ext/apps_assets/busy/themes'
KEYS = ('up', 'down', 'ok', 'back', 'start', 'busy', 'custom', 'off', 'apps', 'settings')
EVENT_SETUP = 'Events require websockets and protobuf. Use the bundled script with a virtual environment, or: uv run --python python3 --with "websockets>=15,<17" --with "protobuf>=6,<8" python /path/to/skill/scripts/bsb_device.py events'


class DeviceError(Exception):
    def __init__(self, message, status=None, **details):
        super().__init__(message)
        self.status = status
        self.details = details


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise DeviceError(message, exit_code=2)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def app_name(value):
    if not re.fullmatch(r'[a-zA-Z0-9._-]{1,32}', value) or value in ('.', '..'):
        raise DeviceError('Application/theme name must be 1-32 letters, digits, dots, underscores or hyphens')
    return value


def asset_path(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-zA-Z0-9._/-]{1,64}', value) or any(p in ('', '.', '..') for p in value.split('/')):
        raise DeviceError('Asset path must be relative, at most 64 characters, without empty, dot or parent segments')
    return value


def duration(value):
    match = re.fullmatch(r'(\d+(?:\.\d+)?)(ms|s|m|h)?', value)
    if not match:
        raise argparse.ArgumentTypeError('Use a positive duration such as 30s, 25m or 1h')
    result = float(match[1]) * {'ms': .001, 's': 1, 'm': 60, 'h': 3600, None: 1}[match[2]]
    if not math.isfinite(result) or result < .001:
        raise argparse.ArgumentTypeError('Duration must be finite and at least 1ms')
    return result


def read_json(filename):
    data = json.loads(sys.stdin.read() if filename == '-' else Path(filename).read_text())
    if not isinstance(data, dict):
        raise DeviceError('JSON body must be an object')
    return data


def redacted(message, token):
    if token:
        for secret in (token, quote(token, safe='')):
            message = message.replace(secret, '[redacted]')
    return message


def resolve_token(reference, timeout):
    token = os.environ.get('BUSYBAR_TOKEN', '')
    if token:
        return token, 'env'
    automatic = not reference
    if automatic and sys.platform != 'darwin':
        return '', 'none'
    reference = reference or 'keychain://bsbctl/device/access-token'
    parsed = urlsplit(reference)
    account = unquote(parsed.path[1:])
    if parsed.scheme != 'keychain' or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}', parsed.netloc) or parsed.query or parsed.fragment or not account or any(ord(c) < 32 for c in account):
        raise DeviceError('Use a Keychain reference such as keychain://bsbctl/device/access-token')
    try:
        result = subprocess.run(['/usr/bin/security', 'find-generic-password', '-w', '-s', parsed.netloc, '-a', account], capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        raise DeviceError('Could not read macOS Keychain; check access and the selected reference') from None
    if automatic and result.returncode == 44:
        return '', 'none'
    if result.returncode != 0:
        raise DeviceError(f'Could not read macOS Keychain item (security exit {result.returncode})')
    token = result.stdout.rstrip('\r\n')
    if not token:
        raise DeviceError('Selected macOS Keychain item is empty')
    return token, 'keychain'


class Client:
    def __init__(self, url, token='', timeout=10):
        parsed = urlsplit(url or '')
        if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('', '/'):
            raise DeviceError('Set --url or BUSYBAR_URL to an HTTP(S) device origin, such as http://10.0.4.20')
        self.url = url.rstrip('/')
        self.token = token
        self.timeout = timeout
        self.opener = build_opener(NoRedirect())

    def request(self, method, path, query=None, body=None, content_type='application/json', binary=False):
        parsed = urlsplit(path)
        if not path.startswith('/api/') or parsed.netloc or parsed.scheme or parsed.fragment or '\\' in path:
            raise DeviceError('Request path must start with /api/ on the configured device')
        target = self.url + path
        if query:
            target += ('&' if parsed.query else '?') + urlencode(query)
        if isinstance(body, dict):
            body = json.dumps(body).encode()
        headers = {'X-API-Sem-Ver': API_VERSION}
        if self.token:
            headers['X-API-Token'] = self.token
        if body is not None:
            headers['Content-Type'] = content_type
        try:
            with self.opener.open(Request(target, data=body, headers=headers, method=method), timeout=self.timeout) as response:
                payload = response.read()
        except HTTPError as error:
            detail = error.read(4096).decode('utf-8', errors='replace')
            raise DeviceError(redacted(f'{method} {path}: HTTP {error.code}: {detail}', self.token), status=error.code) from None
        except (URLError, TimeoutError, OSError) as error:
            raise DeviceError(redacted(f'{method} {path}: {error}', self.token)) from None
        if binary:
            return payload
        if not payload:
            return {'success': True}
        try:
            return json.loads(payload)
        except (ValueError, UnicodeError):
            raise DeviceError(f'{method} {path}: expected JSON; use request --out for binary/text responses') from None

    def upload(self, application, path, data):
        return self.request('POST', '/api/assets/upload', {'application_name': app_name(application), 'file': asset_path(path)}, data, 'application/octet-stream')


def screenshot_png(display, encoded):
    width, height = (72, 16) if display == 'front' else (160, 80)
    try:
        raw = base64.b64decode(encoded.strip(), validate=True)
    except ValueError:
        raise DeviceError('Screen response is not valid base64') from None
    expected = width * height * 3 if display == 'front' else width * height // 2
    if len(raw) != expected:
        raise DeviceError(f'Invalid {display} framebuffer: got {len(raw)} bytes, expected {expected}')
    if display == 'front':
        rgb = bytearray(len(raw))
        rgb[0::3], rgb[1::3], rgb[2::3] = raw[2::3], raw[1::3], raw[0::3]
    else:
        rgb = bytearray()
        for packed in raw:
            rgb.extend(bytes([17 * (packed & 15)]) * 3)
            rgb.extend(bytes([17 * (packed >> 4)]) * 3)
    rows = b''.join(b'\0' + rgb[y * width * 3:(y + 1) * width * 3] for y in range(height))

    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))

    header = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', header) + chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b'')
    return png, width, height


def save_file(filename, data, **metadata):
    path = Path(filename).expanduser().resolve()
    # A failed request/decoding operation never truncates an existing capture.
    with path.open('xb') as output:
        output.write(data)
    return {'path': str(path), 'bytes': len(data), **metadata}


def event_dependencies():
    missing = []
    for package in ('websockets', 'google.protobuf'):
        try:
            found = importlib.util.find_spec(package)
        except ModuleNotFoundError:
            found = None
        if found is None:
            missing.append(package)
    return {'available': not missing, 'missing': missing, 'setup': EVENT_SETUP if missing else None}


def upload_theme(client, args):
    folder = Path(args.directory).resolve()
    name = app_name(args.name or folder.name)
    if name == 'busy':
        raise DeviceError('The built-in busy theme name is reserved; choose another name')
    metadata = read_json(str(folder / 'theme.json'))
    background = asset_path(metadata.get('bg_path'))
    source = (folder / background).resolve()
    if folder not in source.parents or source.suffix not in ('.png', '.bin', '.anim'):
        raise DeviceError('Theme bg_path must point to a PNG, BIN or ANIM file inside its directory')
    data = source.read_bytes()
    remote = asset_path(f'themes/{name}/{background}')
    config_path = asset_path(f'themes/{name}/theme.json')
    if 'order' in metadata and (type(metadata['order']) is not int or metadata['order'] < 0):
        raise DeviceError('Theme order must be a nonnegative integer')
    existing = client.request('GET', '/api/storage/list', {'path': THEMES_PATH})
    if not args.replace and any(item['name'] == name for item in existing['list']):
        raise DeviceError(f'Theme {name} already exists; use --replace to overwrite it')
    metadata['bg_path'] = f'/ext/apps_assets/busy/{remote}'
    uploaded = []
    try:
        client.upload('busy', remote, data)
        uploaded.append(remote)
        client.upload('busy', config_path, json.dumps(metadata).encode())
        uploaded.append(config_path)
    except DeviceError as error:
        error.details['uploaded'] = uploaded
        raise
    return {'theme': name, 'uploaded': uploaded}


def parser():
    root = Parser(description=__doc__, epilog='Global options precede the command. JSON body files accept - for stdin. Downloads require a new output path.')
    root.add_argument('--url', default=os.environ.get('BUSYBAR_URL'), help='Device origin; defaults to BUSYBAR_URL')
    root.add_argument('--app', default='bsb-agent', help='Application asset/drawing namespace (default: bsb-agent)')
    root.add_argument('--token-keychain', help='Override automatic macOS bsbctl Keychain lookup; BUSYBAR_TOKEN takes precedence')
    root.add_argument('--timeout', type=duration, default=10, help='HTTP/connect timeout (default: 10s)')
    root.add_argument('--json', action='store_true', help='Compact JSON results and JSON errors')
    commands = root.add_subparsers(dest='command', required=True)
    commands.add_parser('doctor', help='Check access, API version and optional event packages')
    commands.add_parser('status', help='Read device status')
    screen = commands.add_parser('screen', help='Save a native-resolution PNG screenshot')
    screen.add_argument('--display', choices=('front', 'back'), default='front')
    screen.add_argument('--out', required=True)
    key = commands.add_parser('input', help='Send one button, switch or rotary key over HTTP')
    key.add_argument('key', choices=KEYS)
    upload = commands.add_parser('upload', help='Upload raw file bytes into application assets')
    upload.add_argument('file')
    upload.add_argument('--path', help='Remote relative path; defaults to local basename')
    draw = commands.add_parser('draw', help='Draw brief text or native display JSON')
    content = draw.add_mutually_exclusive_group(required=True)
    content.add_argument('--text')
    content.add_argument('--file', help='Native JSON body or elements; - reads stdin')
    draw.add_argument('--seconds', type=duration, default=10, help='Text lifetime (default: 10 seconds)')
    draw.add_argument('--priority', type=int, choices=range(1, 101), metavar='1..100', help='Text default: 50; overrides a JSON body priority when supplied')
    commands.add_parser('clear', help='Clear this application drawing')
    audio = commands.add_parser('audio', help='Play or stop device audio').add_subparsers(dest='action', required=True)
    play = audio.add_parser('play', help='Play an uploaded .snd file, or --stock shared/...')
    play.add_argument('path')
    play.add_argument('--stock', action='store_true')
    audio.add_parser('stop', help='Stop current audio playback (device-wide)')
    themes = commands.add_parser('themes', help='List themes or upload a theme directory').add_subparsers(dest='action', required=True)
    themes.add_parser('list')
    theme = themes.add_parser('upload')
    theme.add_argument('directory')
    theme.add_argument('--name')
    theme.add_argument('--replace', action='store_true')
    busy = commands.add_parser('busy', help='Read, start or stop a BUSY session').add_subparsers(dest='action', required=True)
    busy.add_parser('status')
    busy.add_parser('stop')
    start = busy.add_parser('start')
    clock = start.add_mutually_exclusive_group(required=True)
    clock.add_argument('--duration', type=duration)
    clock.add_argument('--infinite', action='store_true')
    start.add_argument('--theme', default='busy')
    events = commands.add_parser('events', help='Capture decoded WebSocket updates as JSON Lines')
    capture = events.add_mutually_exclusive_group()
    capture.add_argument('--duration', type=duration, default=30, help='Capture duration (default: 30s)')
    capture.add_argument('--follow', action='store_true', help='Continue until interrupted')
    events.add_argument('--type', help='Filter by protobuf update field, e.g. input, timer or frame')
    raw = commands.add_parser('request', help='Call an explicit HTTP method on /api/...')
    raw.add_argument('method', choices=('GET', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE'))
    raw.add_argument('path')
    raw.add_argument('--body', help='JSON object file; - reads stdin')
    raw.add_argument('--out', help='Save raw response bytes instead of parsing JSON')
    return root


def run(args):
    if args.command == 'doctor':
        result = {'url': args.url, 'token_available': False, 'auth_source': 'none', 'reachable': False, 'events': event_dependencies()}
        try:
            token, source = resolve_token(args.token_keychain, args.timeout)
            result.update(token_available=bool(token), auth_source=source)
            client = Client(args.url, token, args.timeout)
            result['version'] = client.request('GET', '/api/version')
            client.request('GET', '/api/status/system')
            result['reachable'] = True
        except DeviceError as error:
            result['error'] = {'message': str(error), 'status': error.status}
        return result
    app_name(args.app)
    if args.command == 'events' and not event_dependencies()['available']:
        raise DeviceError(EVENT_SETUP)
    token, _ = resolve_token(args.token_keychain, args.timeout)
    client = Client(args.url, token, args.timeout)
    if args.command == 'status':
        return client.request('GET', '/api/status')
    if args.command == 'screen':
        encoded = client.request('GET', '/api/screen', {'display': 0 if args.display == 'front' else 1}, binary=True)
        png, width, height = screenshot_png(args.display, encoded)
        return save_file(args.out, png, display=args.display, width=width, height=height)
    if args.command == 'input':
        return client.request('POST', '/api/input', {'key': args.key})
    if args.command == 'upload':
        path = asset_path(args.path or Path(args.file).name)
        result = client.upload(args.app, path, Path(args.file).read_bytes())
        return {'application_name': args.app, 'path': path, 'result': result}
    if args.command == 'draw':
        if args.text is not None:
            if not re.fullmatch(r'[\x20-\x7e]+', args.text):
                raise DeviceError('Drawing text must contain printable ASCII characters')
            if args.seconds != int(args.seconds):
                raise DeviceError('Text expiry must be a whole positive number of seconds')
            body = {'priority': args.priority or 50, 'elements': [{'id': 'message', 'type': 'text', 'display': 'front', 'x': 36, 'y': 8, 'align': 'center', 'font': 'small', 'color': '#FFFFFFFF', 'width': 72, 'scroll_rate': 600, 'timeout': int(args.seconds), 'text': args.text}]}
        else:
            body = read_json(args.file)
            if body.get('application_name', args.app) != args.app:
                raise DeviceError('Drawing application_name differs from --app; select the matching --app')
            if not isinstance(body.get('elements'), list) or not body['elements']:
                raise DeviceError('Drawing JSON must contain a nonempty elements array')
            if args.priority is not None:
                body['priority'] = args.priority
        body['application_name'] = args.app
        return client.request('POST', '/api/display/draw', body=body)
    if args.command == 'clear':
        return client.request('DELETE', '/api/display/draw', {'application_name': args.app})
    if args.command == 'audio':
        if args.action == 'stop':
            return client.request('DELETE', '/api/audio/play')
        path = args.path
        if args.stock:
            if not re.fullmatch(r'shared/[a-zA-Z0-9._/-]+', path) or len(path) > 256 or any(p in ('', '.', '..') for p in path.split('/')):
                raise DeviceError('Stock path must start with shared/ and contain no parent segments')
        else:
            asset_path(path)
        return client.request('POST', '/api/audio/play', body={'application_name': args.app, 'stock_path' if args.stock else 'path': path})
    if args.command == 'themes':
        if args.action == 'list':
            return client.request('GET', '/api/storage/list', {'path': THEMES_PATH})
        return upload_theme(client, args)
    if args.command == 'busy':
        if args.action == 'status':
            return client.request('GET', '/api/busy/snapshot')
        if args.action == 'stop':
            current = client.request('GET', '/api/busy/snapshot')
            snapshot = {'type': 'NOT_STARTED', 'busy_bar_settings': current['snapshot']['busy_bar_settings']}
        else:
            snapshot = {'type': 'INFINITE' if args.infinite else 'SIMPLE', 'card_id': str(uuid.uuid4()), 'is_paused': False, 'busy_bar_settings': {'theme': app_name(args.theme), 'show_work_phase_only': False, 'trigger_smart_home': False}}
            if not args.infinite:
                snapshot['time_left_ms'] = int(args.duration * 1000)
        return client.request('PUT', '/api/busy/snapshot', body={'snapshot': snapshot, 'snapshot_timestamp_ms': time.time_ns() // 1000000})
    if args.command == 'events':
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from bsb_events import capture
        try:
            capture(client, args)
        except (ValueError, OSError) as error:
            raise DeviceError(redacted(str(error), token)) from None
        return None
    if args.command == 'request':
        body = read_json(args.body) if args.body else None
        if args.method in ('GET', 'HEAD') and body is not None:
            raise DeviceError('GET/HEAD requests do not accept --body')
        payload = client.request(args.method, args.path, body=body, binary=bool(args.out))
        return save_file(args.out, payload) if args.out else payload
    raise DeviceError('Unknown command')


def main():
    argv = sys.argv[1:]
    as_json = '--json' in argv
    # Permit --json after any subcommand without duplicating every parser option.
    if as_json:
        argv = ['--json', *(value for value in argv if value != '--json')]
    try:
        args = parser().parse_args(argv)
        result = run(args)
        if result is not None:
            print(json.dumps(result, indent=None if as_json else 2))
        return 1 if args.command == 'doctor' and not result['reachable'] else 0
    except KeyboardInterrupt:
        return 130
    except (DeviceError, OSError, ValueError, KeyError) as error:
        message = redacted(str(error), os.environ.get('BUSYBAR_TOKEN', ''))
        details = dict(getattr(error, 'details', {}))
        code = details.pop('exit_code', 1)
        record = {'error': {'message': message, 'status': getattr(error, 'status', None), **details}}
        if as_json:
            print(json.dumps(record))
        else:
            print(json.dumps(record), file=sys.stderr)
        return code


if __name__ == '__main__':
    sys.exit(main())
