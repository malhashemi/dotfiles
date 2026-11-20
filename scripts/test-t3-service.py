#!/usr/bin/env python3
"""T3 service, update and remote-access behaviour of ai-setup. Every command is mocked."""
import contextlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import types
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1]


def load():
    path = SOURCE / 'dot_local/bin/executable_ai-setup'
    module = types.ModuleType('setup'); module.__file__ = str(path)
    exec(compile(path.read_text(), str(path), 'exec'), module.__dict__)
    return module


class T3ServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.s = load()
        self.s.HOME_DIR = self.home; self.s.BIN = self.home / '.local/bin'
        self.s.INPUTS = self.home / '.config/ai-setup'; self.s.ROOT = self.home / '.config/cli-proxy-api'
        self.s.T3_PREFIX = self.home / '.local/share/t3-cli'
        self.s.T3_BOOT_LOG = self.home / '.t3/userdata/logs/boot-service.log'
        shutil.copytree(SOURCE / 'dot_config/private_ai-setup', self.s.INPUTS)
        shutil.copyfile(self.s.INPUTS / 't3/profiles.json.tmpl', self.s.INPUTS / 't3/profiles.json')
        self.s.t3_running = lambda: False; self.s.t3_desktop_running = lambda: False
        self.calls = []

    def fake_run(self, outputs=None):
        outputs = outputs or {}
        def run(args, **kwargs):
            args = [str(a) for a in args]; self.calls.append(args)
            out = next((v for k, v in outputs.items() if k in ' '.join(args)), '')
            if args[1:3] == ['install', '--prefix']:
                package = Path(args[3]) / 'node_modules/t3/package.json'
                package.parent.mkdir(parents=True, exist_ok=True)
                package.write_text(json.dumps({'version': args[-1].split('@')[1]}))
                (Path(args[3]) / 'node_modules/.bin').mkdir(parents=True, exist_ok=True)
                (Path(args[3]) / 'node_modules/.bin/t3').write_text('')
            return types.SimpleNamespace(stdout=out, returncode=0)
        return run

    def quiet(self, fn, *args, **kwargs):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            fn(*args, **kwargs)
        return out.getvalue()

    def test_no_pin_anywhere(self):
        self.assertNotIn('t3_version', json.loads((SOURCE / 'dot_config/private_ai-setup/bootstrap.json').read_text()))
        self.assertFalse(hasattr(self.s, 't3_install_version'))

    def test_install_uses_npm_latest_on_every_role(self):
        self.s.run = self.fake_run({'view t3 version': '9.9.9\n', '--version': 'v24.11.0\n'})
        with patch.object(self.s.shutil, 'which', side_effect=lambda b: None if b == 't3' else '/usr/bin/' + b):
            self.s.install_t3_server()
        self.assertIn('t3@9.9.9', self.calls[-1])
        self.assertTrue((self.s.BIN / 't3').is_symlink())

    def test_invalid_npm_version_is_refused(self):
        self.s.run = self.fake_run({'view t3 version': 'oops\n'})
        with patch.object(self.s.shutil, 'which', return_value='/usr/bin/npm'):
            with self.assertRaisesRegex(ValueError, 'invalid T3 release'):
                self.s.t3_latest_version()

    def test_update_tools_leaves_t3_alone(self):
        self.s.tool_update_plan = lambda machine: [['yay', '-Syu', '--needed', 't3code-bin']]
        self.s.run = self.fake_run()
        self.s.install_t3_server = lambda **k: self.fail('--update-tools must not touch the T3 CLI')
        text = self.quiet(self.s.update_tools, {'role': 'desktop'})
        self.assertEqual(self.calls, [['yay', '-Syu', '--needed', 't3code-bin']])
        self.assertIn('--update-t3', text)

    def test_update_t3_moves_service_and_protects_on_linux(self):
        unit = self.home / '.config/systemd/user/t3code.service'; unit.parent.mkdir(parents=True); unit.write_text('')
        self.s.sys = types.SimpleNamespace(platform='linux')
        self.s.run = self.fake_run({'view t3 version': '9.9.9\n', '--version': 'v24.11.0\n'})
        self.s.stray_t3_server = lambda: None
        self.s.t3_desktop_running = lambda: True  # the app no longer owns the server
        sudo = types.SimpleNamespace(returncode=0)
        with patch.object(self.s.shutil, 'which', side_effect=lambda b: None if b == 't3' else '/usr/bin/' + b), \
                patch.object(self.s.subprocess, 'run', return_value=sudo):
            text = self.quiet(self.s.update_t3)
        t3 = str(self.s.BIN / 't3')
        self.assertIn([t3, 'update', '9.9.9', '--yes'], self.calls)
        self.assertEqual(self.calls[-1], [t3, 'service', 'protect', '--yes'])
        self.assertIn('restarts', text)

    def test_update_t3_refuses_a_stray_server(self):
        unit = self.home / '.config/systemd/user/t3code.service'; unit.parent.mkdir(parents=True); unit.write_text('')
        self.s.sys = types.SimpleNamespace(platform='linux')
        self.s.run = self.fake_run({'view t3 version': '9.9.9\n'})
        self.s.stray_t3_server = lambda: 4242
        with patch.object(self.s.shutil, 'which', return_value='/usr/bin/npm'):
            with self.assertRaisesRegex(ValueError, 'outside the background service'):
                self.s.update_t3()
        self.assertFalse(any('install' in c for c in self.calls))

    def test_every_desktop_app_uses_the_service(self):
        path = self.home / '.t3/userdata/desktop-settings.json'; path.parent.mkdir(parents=True)
        path.write_text(json.dumps({'mainWindowBounds': {'x': 1}}))
        for machine in ({'role': 'laptop', 'remote_access': True}, {'role': 'desktop', 'autologin': True}):
            planned = {p.name: after for p, _, after in self.s.planned_t3(machine)}
            desktop = planned['desktop-settings.json']
            self.assertIs(desktop['localEnvironmentEnabled'], False)
            self.assertNotIn('serverExposureMode', desktop); self.assertNotIn('tailscaleServeEnabled', desktop)
            self.assertEqual(desktop['mainWindowBounds'], {'x': 1})
        self.assertTrue(self.s.service_host({'role': 'laptop'}))

    def test_macos_service_unit_is_the_launch_agent(self):
        self.s.sys = types.SimpleNamespace(platform='darwin')
        self.assertEqual(self.s.t3_service_unit(),
                         self.home / 'Library/LaunchAgents/com.t3tools.t3code.service.plist')

    def test_existing_macos_service_is_started_not_reinstalled(self):
        self.s.sys = types.SimpleNamespace(platform='darwin')
        unit = self.s.t3_service_unit(); unit.parent.mkdir(parents=True); unit.write_text('')
        self.s.run = self.fake_run(); self.s.t3_service_loaded = lambda: False
        self.s.app_uses_service = lambda: None
        self.quiet(self.s.setup_t3_service, {'role': 'laptop'})
        self.assertEqual(self.calls[-1][1:], ['service', 'restart'])
        self.assertIn('T3CODE_HOST=127.0.0.1', (self.home / '.t3/service.env').read_text())

    def test_fresh_service_install_refuses_a_running_server(self):
        self.s.t3_running = lambda: True; self.s.run = self.fake_run()
        with self.assertRaisesRegex(ValueError, 'not the background service'):
            self.s.setup_t3_service({'role': 'laptop'})
        self.assertEqual(self.calls, [])

    def serve(self, serve_status):
        runtime = self.home / '.t3/userdata/server-runtime.json'; runtime.parent.mkdir(parents=True, exist_ok=True)
        runtime.write_text(json.dumps({'pid': 1, 'origin': 'http://127.0.0.1:3773'}))
        self.s.t3_running = lambda: True
        brew = self.home / 'opt/homebrew/bin/tailscale'; brew.parent.mkdir(parents=True); brew.write_text('')
        self.s.HOMEBREW_TAILSCALE = brew
        self.brew = str(brew)
        def run(args, **kwargs):
            args = [str(a) for a in args]; self.calls.append(args)
            if args[1:3] == ['serve', 'status']:
                return types.SimpleNamespace(stdout=json.dumps(serve_status))
            return types.SimpleNamespace(stdout=json.dumps({'BackendState': 'Running', 'Self': {'DNSName': 'host.example.ts.net.'}}))
        self.s.run = run
        with patch.object(self.s.shutil, 'which', return_value=None):
            self.s.setup_service_https({'remote_access': True})

    def test_serve_uses_homebrew_tailscale_and_keeps_other_ports(self):
        self.serve({'TCP': {'8443': {'HTTPS': True}}, 'Web': {'host.example.ts.net:8443': {'Handlers': {'/': {'Proxy': 'http://127.0.0.1:8777'}}}}})
        self.assertEqual(self.calls[-1], [self.brew, 'serve', '--bg', '--https=443', 'http://127.0.0.1:3773'])

    def test_serve_already_mapped_is_left_alone(self):
        self.serve({'TCP': {'443': {'HTTPS': True}}, 'Web': {'host.example.ts.net:443': {'Handlers': {'/': {'Proxy': 'http://127.0.0.1:3773'}}}}})
        self.assertFalse(any('--bg' in c for c in self.calls))

    def test_serve_root_elsewhere_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'points elsewhere'):
            self.serve({'Web': {'host.example.ts.net:443': {'Handlers': {'/': {'Proxy': 'http://127.0.0.1:9999'}}}}})

    def test_account_mismatch_only_from_the_latest_start(self):
        log = self.s.T3_BOOT_LOG; log.parent.mkdir(parents=True)
        log.write_text('Listening on http://127.0.0.1:3773\nWARN: Failed to reconcile T3 Connect desired link on startup\n'
                       "  { cause: { _tag: 'CloudLinkAccountMismatchError' } }\n")
        self.assertTrue(self.s.connect_account_mismatch())
        log.write_text(log.read_text() + 'Listening on http://127.0.0.1:3773\nT3 Connect desired link reconciled on startup\n')
        self.assertFalse(self.s.connect_account_mismatch())
        self.assertEqual(self.s.connect_log_state(), 'reconciled')

    def forbid_t3_state_commands(self):
        real = self.s.subprocess.run
        def run(args, *a, **k):
            joined = ' '.join(str(x) for x in args)
            if 'connect status' in joined or 'environment list' in joined or 'connect link' in joined:
                self.fail('touches T3 state: ' + joined)
            return real(args, *a, **k)
        return patch.object(self.s.subprocess, 'run', side_effect=run)

    def test_remote_access_guidance_is_passive_and_never_signs_in(self):
        self.s.tunnel_ready = lambda: None
        self.s.run = lambda *a, **k: self.fail('no commands expected')
        with self.forbid_t3_state_commands():
            text = self.quiet(self.s.show_t3_remote_access)
        self.assertIn('T3 Connect: not connected (not linked)', text)
        self.assertIn('t3 connect link --headless && t3 service restart', text)
        self.assertIn('`t3 connect status` (touches T3 state', text)
        self.assertIn('t3 environment link --pairing-code <credential> --url', text)
        self.assertLess(text.index('--access full-access'), text.index('https://<its tailscale name>'))

    def test_connected_from_passive_signals(self):
        secret = self.home / '.t3/userdata/secrets/cloud-linked-user-id.bin'; secret.parent.mkdir(parents=True)
        secret.write_text('')  # existence only; the value is never read
        self.s.tunnel_ready = lambda: 4
        with self.forbid_t3_state_commands():
            text = self.quiet(self.s.show_t3_remote_access)
        self.assertIn('T3 Connect: tunnel ready (4 connections', text)

    def test_stored_links_read_only_with_t3_expiry_rule(self):
        import sqlite3
        path = self.home / '.t3/userdata/statev2.sqlite'; path.parent.mkdir(parents=True)
        with sqlite3.connect(path) as db:
            db.execute('create table peer_environment_links (environment_id text primary key, secret_name text, label text,'
                       ' urls_json text, access text, linked_at text, expires_at text, last_reached_at text,'
                       ' last_error text, fenced integer not null default 0)')
            db.execute("insert into peer_environment_links values ('a','peer-link-x','A','[\"https://a.ts.net\"]','full-access',"
                       "'2026-11-20T00:00:00.000Z','2026-12-20T00:00:00.000Z',null,null,1)")
            db.execute("insert into peer_environment_links values ('b','peer-link-y','B','[\"https://relay\"]','full-access',"
                       "'2026-11-20T00:00:00.000Z','2026-12-20T00:00:00.000Z',null,'boom',0)")
        path.chmod(0o400)
        links = {l['environmentId']: l for l in self.s.stored_environment_links()}
        self.assertEqual(links['a']['expiresAt'], '2026-12-20T00:00:00.000Z')
        self.assertEqual(links['b']['expiresAt'], '2026-11-20T00:00:00.000Z')  # unfenced: T3 treats it as expired
        self.assertNotIn('secret_name', json.dumps(links))

    def test_stray_server_detection(self):
        runtime = self.home / '.t3/userdata/server-runtime.json'; runtime.parent.mkdir(parents=True)
        runtime.write_text(json.dumps({'pid': 4242})); self.s.t3_running = lambda: True
        self.s.sys = types.SimpleNamespace(platform='darwin')
        self.s.t3_service_launcher_pids = lambda: {100}
        for parent, expected in (('100', None), ('1', 4242)):
            with patch.object(self.s.subprocess, 'run', return_value=types.SimpleNamespace(stdout=parent + '\n')):
                self.assertEqual(self.s.stray_t3_server(), expected)


if __name__ == '__main__':
    unittest.main()
