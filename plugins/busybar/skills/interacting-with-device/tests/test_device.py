import base64
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit
import zlib

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'bsb_device.py'
sys.path.insert(0, str(SCRIPT.parent))
import bsb_device


class KeychainTests(unittest.TestCase):
    def test_default_macos_keychain_lookup(self):
        with patch.dict('os.environ', {}, clear=True), patch('bsb_device.sys.platform', 'darwin'), patch('bsb_device.subprocess.run', return_value=SimpleNamespace(returncode=0, stdout='secret\n')) as process:
            self.assertEqual(bsb_device.resolve_token(None, 2), ('secret', 'keychain'))
        self.assertEqual(process.call_args.args[0][-4:], ['-s', 'bsbctl', '-a', 'device/access-token'])

    def test_missing_default_item_allows_unauthenticated_device(self):
        with patch.dict('os.environ', {}, clear=True), patch('bsb_device.sys.platform', 'darwin'), patch('bsb_device.subprocess.run', return_value=SimpleNamespace(returncode=44)):
            self.assertEqual(bsb_device.resolve_token(None, 2), ('', 'none'))

    def test_default_access_denied_is_not_missing_credentials(self):
        with patch.dict('os.environ', {}, clear=True), patch('bsb_device.sys.platform', 'darwin'), patch('bsb_device.subprocess.run', return_value=SimpleNamespace(returncode=36)):
            with self.assertRaises(bsb_device.DeviceError):
                bsb_device.resolve_token(None, 2)

    def test_non_macos_without_override_does_not_read_keychain(self):
        with patch.dict('os.environ', {}, clear=True), patch('bsb_device.sys.platform', 'linux'), patch('bsb_device.subprocess.run', side_effect=AssertionError('No Keychain')):
            self.assertEqual(bsb_device.resolve_token(None, 2), ('', 'none'))

    def test_keychain_reads_requested_bsbctl_item_without_exposing_token(self):
        with patch.dict('os.environ', {}, clear=True), patch('bsb_device.subprocess.run', return_value=SimpleNamespace(returncode=0, stdout='test-secret\n', stderr='')) as process:
            token, source = bsb_device.resolve_token('keychain://bsbctl/device/access-token', 2)
        self.assertEqual((token, source), ('test-secret', 'keychain'))
        self.assertEqual(process.call_args.args[0], ['/usr/bin/security', 'find-generic-password', '-w', '-s', 'bsbctl', '-a', 'device/access-token'])
        self.assertTrue(process.call_args.kwargs['capture_output'])
        self.assertEqual(process.call_args.kwargs['timeout'], 2)

    def test_environment_token_takes_precedence_without_keychain_access(self):
        with patch.dict('os.environ', {'BUSYBAR_TOKEN': 'env-secret'}), patch('bsb_device.subprocess.run', side_effect=AssertionError('Keychain must not be read')):
            self.assertEqual(bsb_device.resolve_token('keychain://bsbctl/device/access-token', 2), ('env-secret', 'env'))

    def test_keychain_failure_does_not_expose_command_output(self):
        with patch.dict('os.environ', {}, clear=True), patch('bsb_device.subprocess.run', return_value=SimpleNamespace(returncode=44, stdout='private-value', stderr='private-diagnostic')):
            with self.assertRaises(bsb_device.DeviceError) as caught:
                bsb_device.resolve_token('keychain://bsbctl/device/access-token', 2)
        self.assertNotIn('private', str(caught.exception))


class DeviceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                path = urlsplit(self.path)
                query = parse_qs(path.query)
                body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
                cls.calls.append((self.command, path.path, query, body))
                code, result = cls.responses.get(path.path, (200, {'success': True}))
                if path.path == '/api/screen':
                    raw = b'\x00\x00\xff' * 1152 if query['display'] == ['0'] else b'\xf1' * 6400
                    result = base64.b64encode(raw)
                if isinstance(result, dict):
                    result = json.dumps(result).encode()
                self.send_response(code)
                self.end_headers()
                self.wfile.write(result)

            do_POST = do_PUT = do_DELETE = do_GET

        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = 'http://127.0.0.1:%s' % cls.server.server_port

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        type(self).calls = []
        type(self).responses = {
            '/api/version': (200, {'api_semver': '27.5.0'}),
            '/api/storage/list': (200, {'list': []}),
            '/api/busy/snapshot': (200, {'snapshot': {'type': 'NOT_STARTED', 'busy_bar_settings': {'theme': 'debug', 'show_work_phase_only': False, 'trigger_smart_home': True}}, 'snapshot_timestamp_ms': 1}),
        }
        temp = tempfile.TemporaryDirectory()
        self.root = Path(temp.name)
        self.addCleanup(temp.cleanup)

    def cli(self, *args, expected=0, isolated=False):
        result = subprocess.run([sys.executable, *(['-S'] if isolated else []), str(SCRIPT), '--url', self.url, '--json', *args], cwd=self.root, env={**os.environ, 'BUSYBAR_TOKEN': 'fixture-token'}, text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, expected, result.stderr + result.stdout)
        return json.loads(result.stdout)

    def test_screen_decodes_colors_without_optional_packages(self):
        for display, width, height, first in [('front', 72, 16, b'\xff\x00\x00'), ('back', 160, 80, b'\x11\x11\x11\xff\xff\xff')]:
            out = self.root / (display + '.png')
            result = self.cli('screen', '--display', display, '--out', str(out), isolated=True)
            self.assertEqual((result['width'], result['height']), (width, height))
            raw = out.read_bytes()
            self.assertEqual(raw[:8], b'\x89PNG\r\n\x1a\n')
            offset, compressed = 8, b''
            while offset < len(raw):
                size = struct.unpack('>I', raw[offset:offset + 4])[0]
                if raw[offset + 4:offset + 8] == b'IDAT':
                    compressed += raw[offset + 8:offset + 8 + size]
                offset += 12 + size
            pixels = zlib.decompress(compressed)
            self.assertEqual(len(pixels), height * (1 + width * 3))
            self.assertEqual(pixels[1:1 + len(first)], first)

    def test_upload_preserves_binary_and_namespace(self):
        asset = self.root / 'ready.png'
        asset.write_bytes(b'\x89PNG\x00\xff\r\n')
        self.cli('--app', 'agent-test', 'upload', str(asset), '--path', 'images/ready.png')
        self.assertEqual(self.calls[-1], ('POST', '/api/assets/upload', {'application_name': ['agent-test'], 'file': ['images/ready.png']}, asset.read_bytes()))

    def test_input_and_expiring_draw_use_correct_http_operations(self):
        self.cli('input', 'ok')
        self.assertEqual(self.calls[-1][:3], ('POST', '/api/input', {'key': ['ok']}))
        self.cli('draw', '--text', 'READY', '--seconds', '4')
        body = json.loads(self.calls[-1][3])
        self.assertEqual(body['application_name'], 'bsb-agent')
        self.assertEqual(body['priority'], 50)
        self.assertEqual(body['elements'][0]['timeout'], 4)
        self.cli('clear')
        self.assertEqual(self.calls[-1][:3], ('DELETE', '/api/display/draw', {'application_name': ['bsb-agent']}))

    def test_conflicts_are_not_retried(self):
        self.responses['/api/display/draw'] = (409, {'error': 'priority conflict'})
        result = self.cli('draw', '--text', 'READY', expected=1)
        self.assertEqual(result['error']['status'], 409)
        self.assertEqual(len([c for c in self.calls if c[1] == '/api/display/draw']), 1)

    def test_text_rejects_fractional_expiry_and_non_ascii_before_writing(self):
        self.cli('draw', '--text', 'READY', '--seconds', '500ms', expected=1)
        self.cli('draw', '--text', '\u2713', expected=1)
        self.assertEqual(self.calls, [])

    def test_reserved_busy_theme_cannot_be_replaced(self):
        self.cli('themes', 'upload', str(self.theme()), '--name', 'busy', '--replace', expected=1)
        self.assertEqual(self.calls, [])

    def test_busy_start_and_stop_snapshot_semantics(self):
        self.cli('busy', 'start', '--duration', '25m', '--theme', 'review')
        body = json.loads(self.calls[-1][3])
        self.assertEqual(body['snapshot']['time_left_ms'], 1500000)
        self.assertEqual(body['snapshot']['type'], 'SIMPLE')
        self.assertFalse(body['snapshot']['busy_bar_settings']['trigger_smart_home'])
        self.assertGreater(body['snapshot_timestamp_ms'], 1)
        self.cli('busy', 'stop')
        body = json.loads(self.calls[-1][3])['snapshot']
        self.assertEqual(body['type'], 'NOT_STARTED')
        self.assertEqual(body['busy_bar_settings']['theme'], 'debug')

    def theme(self):
        folder = self.root / 'ready'
        folder.mkdir()
        (folder / 'theme.json').write_text(json.dumps({'bg_path': 'background.png', 'order': 100}))
        (folder / 'background.png').write_bytes(b'image')
        return folder

    def test_theme_metadata_is_rewritten_and_uploaded_last(self):
        folder = self.theme()
        self.cli('themes', 'upload', str(folder))
        uploads = [c for c in self.calls if c[0] == 'POST']
        self.assertEqual([c[2]['file'][0] for c in uploads], ['themes/ready/background.png', 'themes/ready/theme.json'])
        self.assertTrue(all(c[2]['application_name'] == ['busy'] for c in uploads))
        self.assertEqual(json.loads(uploads[1][3]), {'bg_path': '/ext/apps_assets/busy/themes/ready/background.png', 'order': 100})
        self.assertEqual(json.loads((folder / 'theme.json').read_text())['bg_path'], 'background.png')

    def test_theme_failure_never_publishes_metadata_or_starts_busy(self):
        self.responses['/api/assets/upload'] = (508, {'error': 'full'})
        self.cli('themes', 'upload', str(self.theme()), expected=1)
        writes = [c for c in self.calls if c[0] != 'GET']
        self.assertEqual(len(writes), 1)
        self.assertEqual(writes[0][2]['file'], ['themes/ready/background.png'])

    def test_theme_replacement_is_explicit_and_paths_stay_local(self):
        folder = self.theme()
        self.responses['/api/storage/list'] = (200, {'list': [{'type': 'dir', 'name': 'ready'}]})
        self.cli('themes', 'upload', str(folder), expected=1)
        self.assertFalse(any(c[0] == 'POST' for c in self.calls))
        self.cli('themes', 'upload', str(folder), '--replace')
        self.calls.clear()
        (folder / 'theme.json').write_text('{"bg_path":"../secret.png"}')
        self.cli('themes', 'upload', str(folder), '--replace', expected=1)
        self.assertEqual(self.calls, [])

    def test_raw_request_rejects_other_origins_before_network(self):
        self.cli('request', 'GET', 'http://example.com/api/status', expected=1)
        self.assertEqual(self.calls, [])

    def test_optional_event_packages_do_not_block_http(self):
        result = self.cli('doctor', isolated=True)
        self.assertTrue(result['reachable'])
        self.assertFalse(result['events']['available'])
        result = self.cli('events', isolated=True, expected=1)
        self.assertIn('websockets', result['error']['message'])


if __name__ == '__main__':
    unittest.main()
