#!/usr/bin/env python3
"""Probe an already running owned Mac guest; never start/stop it or post valid input."""
import argparse
import importlib.util
import json
from pathlib import Path
import socket
import sys
import time
import uuid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    if sys.platform != 'darwin':
        parser.error('This probe runs on the Mac that owns the guest.')
    source = Path(__file__).resolve().parents[1] / 'macos' / 'vm_adapter.py'
    # Direct script execution must resolve the adapter's sibling runtime helper.
    sys.path.insert(0, str(source.parent))
    spec = importlib.util.spec_from_file_location('quietwing_vm_boundary', source)
    vm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vm)
    before = vm.request(args.id, {'op': 'status'})
    assert before['ok'] and before['session']['phase'] == 'running', before
    initial = before['session']
    identity = {key: initial[key] for key in ('id', 'pid', 'instance')}
    assert initial['window_offscreen'] and not initial['window_key'] and not initial['window_main']
    # Close the read side before the owner writes. SO_NOSIGPIPE must keep the
    # long-lived owner alive even though these short-lived controllers vanished.
    for _ in range(4):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(3)
            client.connect(str(vm.directory(args.id) / 'control.sock'))
            client.sendall(json.dumps({'op': 'status', 'instance': initial['instance']}).encode())
            client.shutdown(socket.SHUT_RDWR)
        time.sleep(0.1)
    alive = vm.request(args.id, {'op': 'status', 'instance': initial['instance']})
    assert alive['ok'] and alive['session']['pid'] == initial['pid'], alive
    stale = vm.request(args.id, {'op': 'input', 'instance': str(uuid.uuid4()), 'text': 'STALE_REQUEST_MUST_NOT_TYPE'})
    assert not stale['ok'] and stale['error']['code'] == 'instance_changed', stale
    after = vm.request(args.id, {'op': 'status', 'instance': initial['instance']})
    final = after['session']
    assert after['ok'] and final['instance'] == initial['instance']
    assert final.get('last_input_at') == initial.get('last_input_at'), 'Stale request changed input timestamp'
    assert final['window_offscreen'] and not final['window_key'] and not final['window_main']
    assert not final['host_became_frontmost']
    assert final['audio_devices'] == 0
    report = {
        'ok': True, 'checked_at_unix': time.time(), 'identity': identity,
        'disconnected_status_clients': 4, 'owner_survived': True,
        'stale_input_rejected_before_delivery': True,
        'last_input_at_unchanged': True, 'offscreen_nonkey_window': True,
        'audio_devices': final['audio_devices'],
        'host_cursor_before': initial['host_cursor_current'],
        'host_cursor_after': final['host_cursor_current'],
        'host_frontmost_pids_seen': final['host_frontmost_pids_seen'],
        'host_became_frontmost': final['host_became_frontmost'],
        'capture_mode': final.get('capture_mode'),
        'screen_capture_preflight': final.get('screen_capture_preflight'),
    }
    with Path(args.output).open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
