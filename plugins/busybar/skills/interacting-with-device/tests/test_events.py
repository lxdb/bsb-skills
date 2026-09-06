import json
from pathlib import Path
import struct
import subprocess
import sys
import threading
import time
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
try:
    import google.protobuf
    from websockets.sync.server import serve
    OPTIONAL = True
except ImportError:
    OPTIONAL = False


@unittest.skipUnless(OPTIONAL, 'events need websockets and protobuf')
class EventTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import bsb_events
        cls.events = bsb_events
        cls.state_type, cls.kinds = bsb_events.load_schema()

    def state(self, *updates):
        # Independently specified protobuf wire fixtures: fixed64 timestamp,
        # then repeated StateUpdate messages. OK and PRESS are enum zero.
        return b'\x09' + struct.pack('<Q', 123456) + b''.join(b'\x12' + bytes([len(u)]) + u for u in updates)

    def test_zero_enum_press_release_and_signed_rotary_are_readable_in_order(self):
        payload = self.state(bytes.fromhex('5a020a00'), bytes.fromhex('5a040a021001'), bytes.fromhex('5a041a020801'))
        records = self.events.decode_records(payload, self.state_type, None, 'now')
        self.assertEqual([r['data'] for r in records], [
            {'button_event': {'button': 'OK', 'action': 'PRESS'}},
            {'button_event': {'button': 'OK', 'action': 'RELEASE'}},
            {'encoder_event': {'delta': -1}},
        ])
        self.assertTrue(all(r['device_timestamp'] == '123456' and r['received_at'] == 'now' for r in records))

    def test_filter_keeps_order_and_does_not_hide_device_error(self):
        payload = self.state(bytes.fromhex('0a030a0178'), bytes.fromhex('5a020a00'))
        records = self.events.decode_records(payload, self.state_type, 'input', 'now')
        self.assertEqual([r['type'] for r in records], ['input'])
        with self.assertRaisesRegex(Exception, 'RESOURCE_LIMIT'):
            self.events.decode_records(self.state() + b'\x1a\x00', self.state_type, 'input', 'now')

    def test_bad_protobuf_is_reported(self):
        with self.assertRaisesRegex(Exception, 'protobuf'):
            self.events.decode_records(b'\x12\xff', self.state_type, None, 'now')

    def test_bounded_capture_subscribes_and_closes_even_when_filter_is_idle(self):
        commands = []
        payload = self.state(bytes.fromhex('5a020a00'))
        def handler(socket):
            commands.append(json.loads(socket.recv()))
            socket.send(payload)
            try:
                socket.recv(timeout=3)
            except Exception:
                pass
        with serve(handler, '127.0.0.1', 0) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            started = time.monotonic()
            result = subprocess.run([sys.executable, str(SCRIPTS / 'bsb_device.py'), '--url', 'http://127.0.0.1:%s' % server.socket.getsockname()[1], '--json', 'events', '--duration', '100ms', '--type', 'timer'], capture_output=True, text=True, timeout=5)
            server.shutdown()
            thread.join()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, '')
        self.assertEqual(commands, [{'enable': True, 'send': 'all'}])
        self.assertLess(time.monotonic() - started, 3)


if __name__ == '__main__':
    unittest.main()
