"""Optional WebSocket capture; imported only by the events command."""

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
from urllib.parse import urlencode

from google.protobuf import descriptor_pb2, descriptor_pool, message_factory
from google.protobuf.json_format import MessageToDict
from google.protobuf.message import DecodeError
from websockets.exceptions import WebSocketException
from websockets.sync.client import connect


def load_schema():
    descriptor = descriptor_pb2.FileDescriptorSet()
    descriptor.ParseFromString((Path(__file__).resolve().parents[1] / 'assets' / 'state.desc').read_bytes())
    pool = descriptor_pool.DescriptorPool()
    # protoc --include_imports writes dependencies before their consumers.
    for file in descriptor.file:
        pool.Add(file)
    state_type = message_factory.GetMessageClass(pool.FindMessageTypeByName('BSB_State.State'))
    kinds = pool.FindMessageTypeByName('BSB_State.StateUpdate').fields_by_name
    return state_type, kinds


def as_dict(message):
    # Proto3 zero values include OK, PRESS and BUSY: retain them for debugging.
    return MessageToDict(message, preserving_proto_field_name=True, always_print_fields_with_no_presence=True)


def decode_records(payload, state_type, selected, received_at):
    state = state_type()
    try:
        state.ParseFromString(payload)
    except DecodeError as error:
        raise ValueError(f'Invalid protobuf state: {error}') from None
    if state.HasField('error'):
        raise ValueError('Device stream error: ' + json.dumps(as_dict(state.error)))
    records = []
    for update in state.updates:
        kind = update.WhichOneof('state')
        if kind is None:
            raise ValueError('Unknown protobuf update; the bundled schema may need updating')
        if selected is None or selected == kind:
            records.append({'received_at': received_at, 'device_timestamp': str(state.timestamp), 'type': kind, 'data': as_dict(getattr(update, kind))})
    return records


def capture(client, args):
    state_type, kinds = load_schema()
    if args.type is not None and args.type not in kinds:
        raise ValueError('Unknown event type; choose from: ' + ', '.join(kinds))
    query = {'x-api-sem-ver': '27.5.0'}
    if client.token:
        query['x-api-token'] = client.token
    url = ('wss' if client.url.startswith('https:') else 'ws') + client.url[client.url.index(':'):] + '/api/status/ws?' + urlencode(query)
    count = 0
    try:
        with connect(url, compression=None, proxy=None, open_timeout=client.timeout, close_timeout=1, max_size=1048576) as socket:
            socket.send('{"enable":true,"send":"all"}')
            print('Streaming enabled; capture is ready.', file=sys.stderr, flush=True)
            deadline = None if args.follow else time.monotonic() + args.duration
            while True:
                remaining = None if deadline is None else deadline - time.monotonic()
                if remaining is not None and remaining <= 0:
                    break
                try:
                    payload = socket.recv(timeout=remaining)
                except TimeoutError:
                    break
                received_at = datetime.now(timezone.utc).isoformat()
                if isinstance(payload, str):
                    records = [{'received_at': received_at, 'type': 'text', 'data': payload}]
                else:
                    records = decode_records(payload, state_type, args.type, received_at)
                for record in records:
                    print(json.dumps(record), flush=True)
                    count += 1
    except (WebSocketException, OSError, TimeoutError) as error:
        raise ValueError(f'Event capture stopped after {count} records: {error}') from None
    print(f'Capture complete: {count} records.', file=sys.stderr)
