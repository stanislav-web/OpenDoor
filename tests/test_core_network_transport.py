# -*- coding: utf-8 -*-

import os
import subprocess
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from src.core.network.exceptions import NetworkTransportError
from src.core.network.process import ProcessRunner
from src.core.network.transport import NetworkTransportManager
from src.core.network.adapters.direct import DirectTransport
from src.core.network.adapters.proxy import ProxyTransport
from src.core.network.adapters.openvpn import OpenVpnTransport
from src.core.network.adapters.wireguard import WireGuardTransport


class TestNetworkTransport(unittest.TestCase):

    """TestNetworkTransport class."""

    def setUp(self):
        """Use deterministic transport executable resolution in unit tests."""

        self.which_patcher = patch(
            'src.core.network.adapters.base.shutil.which',
            side_effect=lambda command: command if command in ['openvpn', 'wg-quick'] else None
        )
        self.which_patcher.start()
        self.addCleanup(self.which_patcher.stop)

    def make_file(self, suffix, content=''):
        """Create a temporary file."""

        handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        handle.write(content.encode('utf-8'))
        handle.close()
        self.addCleanup(lambda: os.path.exists(handle.name) and os.unlink(handle.name))
        return handle.name

    def make_dir_with_file(self, filename, content=''):
        """Create a temporary directory with one file."""

        directory = tempfile.mkdtemp()
        self.addCleanup(lambda: os.path.isdir(directory) and os.rmdir(directory))

        filepath = os.path.join(directory, filename)
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(content)

        self.addCleanup(lambda: os.path.exists(filepath) and os.unlink(filepath))
        return directory, filepath

    def test_direct_transport_should_start_and_stop_as_noop(self):
        """DirectTransport should start and stop as no-op."""

        transport = DirectTransport({})

        self.assertIsNone(transport.start())
        self.assertIsNone(transport.stop())
        self.assertEqual(transport.profile_name, '-')

    def test_proxy_transport_should_start_and_stop_as_noop(self):
        """ProxyTransport should start and stop as no-op."""

        transport = ProxyTransport({})

        self.assertIsNone(transport.start())
        self.assertIsNone(transport.stop())

    def test_openvpn_transport_should_build_command_without_auth(self):
        """OpenVpnTransport should build command without auth file."""

        profile = self.make_file('.ovpn')
        transport = OpenVpnTransport({'transport_profile': profile})

        self.assertEqual(transport.build_start_command(), ['openvpn', '--config', profile])
        self.assertEqual(transport.profile_name, os.path.basename(profile))

    def test_openvpn_transport_should_build_command_with_auth(self):
        """OpenVpnTransport should build command with auth file."""

        profile = self.make_file('.ovpn')
        auth = self.make_file('.txt')
        transport = OpenVpnTransport({
            'transport_profile': profile,
            'openvpn_auth': auth,
        })

        self.assertEqual(
            transport.build_start_command(),
            ['openvpn', '--config', profile, '--auth-user-pass', auth]
        )

    def test_openvpn_transport_should_reject_missing_profile(self):
        """OpenVpnTransport should reject missing profile path."""

        transport = OpenVpnTransport({})

        with self.assertRaises(NetworkTransportError):
            transport.build_start_command()

    def test_openvpn_transport_should_reject_non_ovpn_profile(self):
        """OpenVpnTransport should reject non-ovpn profile."""

        profile = self.make_file('.conf')
        transport = OpenVpnTransport({'transport_profile': profile})

        with self.assertRaises(NetworkTransportError):
            transport.build_start_command()

    def test_openvpn_transport_should_reject_missing_auth_file(self):
        """OpenVpnTransport should reject missing auth-user-pass file."""

        profile = self.make_file('.ovpn')
        transport = OpenVpnTransport({
            'transport_profile': profile,
            'openvpn_auth': '/missing/auth.txt',
        })

        with self.assertRaises(NetworkTransportError):
            transport.build_start_command()

    def test_wireguard_transport_should_build_up_and_down_commands(self):
        """WireGuardTransport should build up and down commands."""

        profile = self.make_file('.conf')
        transport = WireGuardTransport({'transport_profile': profile})

        self.assertEqual(transport.build_up_command(), ['wg-quick', 'up', profile])
        self.assertEqual(transport.build_down_command(), ['wg-quick', 'down', profile])

    def test_wireguard_transport_should_reject_non_conf_profile(self):
        """WireGuardTransport should reject non-conf profile."""

        profile = self.make_file('.ovpn')
        transport = WireGuardTransport({'transport_profile': profile})

        with self.assertRaises(NetworkTransportError):
            transport.build_up_command()

    def test_openvpn_transport_should_start_and_stop_with_runner(self):
        """OpenVpnTransport should start and stop using process runner."""

        profile = self.make_file('.ovpn')
        process = MagicMock()
        runner = MagicMock()
        runner.start_persistent.return_value = process

        transport = OpenVpnTransport({'transport_profile': profile}, runner=runner)

        self.assertIs(transport.start(), process)
        runner.start_persistent.assert_called_once_with(['openvpn', '--config', profile])

        transport.stop()
        runner.stop.assert_called_once_with(process, timeout=5)
        self.assertIsNone(transport.process)

    def test_wireguard_transport_should_start_and_stop_with_runner(self):
        """WireGuardTransport should start and stop using process runner."""

        profile = self.make_file('.conf')
        runner = MagicMock()

        transport = WireGuardTransport({
            'transport_profile': profile,
            'transport_timeout': 12,
        }, runner=runner)

        transport.start()
        runner.run.assert_called_with(['wg-quick', 'up', profile], timeout=12)

        transport.stop()
        runner.run.assert_called_with(['wg-quick', 'down', profile], timeout=12)

    def test_manager_should_build_direct_adapter_by_default(self):
        """NetworkTransportManager should use direct transport by default."""

        manager = NetworkTransportManager({})

        self.assertFalse(manager.is_vpn)
        self.assertEqual(manager.current_profile_name, '-')
        self.assertIsNone(manager.start())
        self.assertIsNone(manager.stop())

    def test_manager_should_build_proxy_adapter(self):
        """NetworkTransportManager should build proxy adapter."""

        manager = NetworkTransportManager({'transport': 'proxy'})

        self.assertFalse(manager.is_vpn)
        self.assertEqual(manager.transport, 'proxy')
        self.assertIsNone(manager.start())
        self.assertIsNone(manager.stop())

    def test_manager_should_rotate_profiles_per_target(self):
        """NetworkTransportManager should rotate profiles in per-target mode."""

        first = self.make_file('.conf')
        second = self.make_file('.conf')
        profiles = self.make_file('.txt', '{0}\n# comment\n\n{1}\n'.format(first, second))

        manager = NetworkTransportManager({
            'transport': 'wireguard',
            'transport_profiles': profiles,
            'transport_rotate': 'per-target',
        })

        self.assertTrue(manager.is_vpn)

        manager.rotate()
        self.assertEqual(manager.current_profile_name, os.path.basename(first))

        manager.rotate()
        self.assertEqual(manager.current_profile_name, os.path.basename(second))

        manager.rotate()
        self.assertEqual(manager.current_profile_name, os.path.basename(first))

    def test_manager_should_resolve_relative_profiles_from_profiles_file_directory(self):
        """NetworkTransportManager should resolve relative profile paths from profiles file directory."""

        directory, profile = self.make_dir_with_file('nl.conf')
        profiles = os.path.join(directory, 'profiles.txt')

        with open(profiles, 'w', encoding='utf-8') as file:
            file.write('nl.conf\n')

        self.addCleanup(lambda: os.path.exists(profiles) and os.unlink(profiles))

        manager = NetworkTransportManager({
            'transport': 'wireguard',
            'transport_profiles': profiles,
            'transport_rotate': 'per-target',
        })

        manager.rotate()

        self.assertEqual(manager.adapter.profile, profile)

    def test_manager_start_should_auto_rotate_first_profile_for_per_target_mode(self):
        """NetworkTransportManager.start() should auto-rotate first profile in per-target mode."""

        profile = self.make_file('.conf')
        profiles = self.make_file('.txt', '{0}\n'.format(profile))
        runner = MagicMock()

        manager = NetworkTransportManager({
            'transport': 'wireguard',
            'transport_profiles': profiles,
            'transport_rotate': 'per-target',
        }, runner=runner)

        manager.start()

        runner.run.assert_called_once_with(['wg-quick', 'up', profile], timeout=30)
        self.assertEqual(manager.current_profile_name, os.path.basename(profile))

    def test_manager_should_reject_missing_profiles_file(self):
        """NetworkTransportManager should reject missing transport profiles file."""

        with self.assertRaises(NetworkTransportError):
            NetworkTransportManager({
                'transport': 'wireguard',
                'transport_profiles': '/missing/profiles.txt',
                'transport_rotate': 'per-target',
            })

    def test_manager_should_reject_wrong_profile_extension_in_profiles_file(self):
        """NetworkTransportManager should reject wrong profile extension in profiles list."""

        profile = self.make_file('.ovpn')
        profiles = self.make_file('.txt', '{0}\n'.format(profile))

        with self.assertRaises(NetworkTransportError):
            NetworkTransportManager({
                'transport': 'wireguard',
                'transport_profiles': profiles,
                'transport_rotate': 'per-target',
            })

    def test_manager_should_reject_missing_profile_in_profiles_file(self):
        """NetworkTransportManager should reject missing profile path from profiles list."""

        profiles = self.make_file('.txt', '/missing/nl.conf\n')

        with self.assertRaises(NetworkTransportError):
            NetworkTransportManager({
                'transport': 'wireguard',
                'transport_profiles': profiles,
                'transport_rotate': 'per-target',
            })

    def test_manager_should_reject_unsupported_transport(self):
        """NetworkTransportManager should reject unsupported transport."""

        with self.assertRaises(NetworkTransportError):
            NetworkTransportManager({'transport': 'bad'})

    def test_manager_should_assert_openvpn_process_when_healthcheck_is_disabled(self):
        """NetworkTransportManager.start() should still validate OpenVPN process liveness without healthcheck URL."""

        profile = self.make_file('.ovpn')
        process = MagicMock()
        process.poll.return_value = None
        runner = MagicMock()
        runner.start_persistent.return_value = process

        manager = NetworkTransportManager({
            'transport': 'openvpn',
            'transport_profile': profile,
        }, runner=runner)

        with patch.object(OpenVpnTransport, 'wait_ready') as wait_ready:
            self.assertIs(manager.start(), process)

        wait_ready.assert_called_once_with(timeout=30)

    def test_manager_should_run_healthcheck_after_transport_start(self):
        """NetworkTransportManager.start() should validate configured healthcheck URL."""

        profile = self.make_file('.conf')
        runner = MagicMock()
        runner.healthcheck.return_value = 200

        manager = NetworkTransportManager({
            'transport': 'wireguard',
            'transport_profile': profile,
            'transport_healthcheck_url': 'https://ifconfig.me',
            'transport_timeout': 9,
        }, runner=runner)

        manager.start()

        runner.run.assert_called_once_with(['wg-quick', 'up', profile], timeout=9)
        runner.healthcheck.assert_called_once_with('https://ifconfig.me', timeout=5)

    def test_manager_should_stop_transport_when_healthcheck_fails(self):
        """NetworkTransportManager.start() should cleanup transport after healthcheck failure."""

        profile = self.make_file('.conf')
        runner = MagicMock()
        runner.healthcheck.side_effect = NetworkTransportError('offline')

        manager = NetworkTransportManager({
            'transport': 'wireguard',
            'transport_profile': profile,
            'transport_healthcheck_url': 'https://ifconfig.me',
            'transport_timeout': 1,
        }, runner=runner)

        with patch('src.core.network.transport.time.sleep'), self.assertRaises(NetworkTransportError):
            manager.start()

        runner.run.assert_any_call(['wg-quick', 'up', profile], timeout=1)
        runner.run.assert_any_call(['wg-quick', 'down', profile], timeout=1)

    def test_openvpn_transport_should_reject_exited_process_before_scan(self):
        """OpenVpnTransport.assert_running() should catch immediate OpenVPN failures."""

        process = MagicMock()
        process.poll.return_value = 1
        process.communicate.return_value = ('AUTH_FAILED\n', '')

        transport = OpenVpnTransport({'transport_profile': self.make_file('.ovpn')})
        transport.process = process

        with self.assertRaises(NetworkTransportError) as ctx:
            transport.assert_running()

        self.assertIn('OpenVPN process exited before scan start', str(ctx.exception))
        self.assertIn('AUTH_FAILED', str(ctx.exception))

    def test_openvpn_transport_assert_running_should_ignore_missing_or_live_process(self):
        """OpenVpnTransport.assert_running() should no-op for missing or still-running process."""

        transport = OpenVpnTransport({'transport_profile': self.make_file('.ovpn')})

        self.assertIsNone(transport.assert_running())

        process = MagicMock()
        process.poll.return_value = None
        transport.process = process

        self.assertIsNone(transport.assert_running())
        process.communicate.assert_not_called()

    def test_openvpn_transport_assert_running_should_show_concise_summary_on_debug_one(self):
        """OpenVpnTransport.assert_running() should hide verbose output at debug 1."""

        process = MagicMock()
        process.poll.return_value = 1
        process.communicate.return_value = (
            '2026-05-09 TLS Error: TLS key negotiation failed\n'
            '2026-05-09 Exiting due to fatal error\n',
            '',
        )

        transport = OpenVpnTransport({'transport_profile': self.make_file('.ovpn'), 'debug': 1})
        transport.process = process

        with self.assertRaises(NetworkTransportError) as ctx:
            transport.assert_running()

        message = str(ctx.exception)
        self.assertIn('OpenVPN process exited before scan start with code 1', message)
        self.assertIn('TLS Error: TLS key negotiation failed', message)
        self.assertIn('Re-run with --debug 2 for OpenVPN output tail', message)
        self.assertNotIn('Exiting due to fatal error', message)

    def test_openvpn_transport_assert_running_should_show_output_tail_on_debug_two(self):
        """OpenVpnTransport.assert_running() should expose OpenVPN output tail at debug 2."""

        process = MagicMock()
        process.poll.return_value = 1
        process.communicate.return_value = (
            'line-01\nline-02\nline-03\nline-04\nline-05\nline-06\n'
            'line-07\nline-08\nline-09\nline-10\nline-11\nline-12\nline-13\n'
            '2026-05-09 Exiting due to fatal error\n',
            '',
        )

        transport = OpenVpnTransport({'transport_profile': self.make_file('.ovpn'), 'debug': 2})
        transport.process = process

        with self.assertRaises(NetworkTransportError) as ctx:
            transport.assert_running()

        message = str(ctx.exception)
        self.assertIn('OpenVPN output tail:', message)
        self.assertNotIn('line-01', message)
        self.assertNotIn('line-02', message)
        self.assertIn('line-03', message)
        self.assertIn('line-13', message)
        self.assertIn('Exiting due to fatal error', message)

    def test_openvpn_transport_assert_running_should_handle_invalid_debug_and_empty_output(self):
        """OpenVpnTransport.assert_running() should tolerate invalid debug value and empty output."""

        process = MagicMock()
        process.poll.return_value = 1
        process.communicate.return_value = ('', '')

        transport = OpenVpnTransport({'transport_profile': self.make_file('.ovpn'), 'debug': 'bad'})
        transport.process = process

        with self.assertRaises(NetworkTransportError) as ctx:
            transport.assert_running()

        self.assertEqual(str(ctx.exception), 'OpenVPN process exited before scan start with code 1')

    def test_openvpn_transport_assert_running_should_fallback_when_only_generic_output_exists(self):
        """OpenVpnTransport.assert_running() should still show a generic line when it is the only output."""

        process = MagicMock()
        process.poll.return_value = 1
        process.communicate.return_value = ('2026-05-09 Exiting due to fatal error\n', '')

        transport = OpenVpnTransport({'transport_profile': self.make_file('.ovpn'), 'debug': 1})
        transport.process = process

        with self.assertRaises(NetworkTransportError) as ctx:
            transport.assert_running()

        message = str(ctx.exception)
        self.assertIn('Exiting due to fatal error', message)
        self.assertIn('Re-run with --debug 2 for OpenVPN output tail', message)

    def test_openvpn_transport_assert_running_should_handle_unreadable_output(self):
        """OpenVpnTransport.assert_running() should still fail when process output cannot be read."""

        process = MagicMock()
        process.poll.return_value = 1
        process.communicate.side_effect = RuntimeError('closed pipe')

        transport = OpenVpnTransport({'transport_profile': self.make_file('.ovpn')})
        transport.process = process

        with self.assertRaises(NetworkTransportError) as ctx:
            transport.assert_running()

        self.assertIn('OpenVPN process exited before scan start with code 1', str(ctx.exception))

    def test_process_runner_should_request_healthcheck_url(self):
        """ProcessRunner.healthcheck() should return HTTP status for reachable URL."""

        response = MagicMock()
        response.status = 204
        manager = MagicMock()
        manager.request.return_value = response

        with patch('src.core.network.process.PoolManager', return_value=manager):
            actual = ProcessRunner().healthcheck('https://ifconfig.me', timeout=3)

        self.assertEqual(actual, 204)
        manager.request.assert_called_once_with(
            'GET',
            'https://ifconfig.me',
            preload_content=False,
            retries=False,
            redirect=False,
        )
        response.release_conn.assert_called_once_with()
        manager.clear.assert_called_once_with()

    def test_process_runner_healthcheck_should_wrap_transport_errors(self):
        """ProcessRunner.healthcheck() should wrap low-level healthcheck errors."""

        manager = MagicMock()
        manager.request.side_effect = ValueError('bad healthcheck url')

        with patch('src.core.network.process.PoolManager', return_value=manager):
            with self.assertRaises(NetworkTransportError):
                ProcessRunner().healthcheck('not-a-url', timeout=3)

        manager.clear.assert_called_once_with()

    def test_process_runner_should_start_persistent_process(self):
        """ProcessRunner.start_persistent() should start subprocess with safe defaults."""

        process = MagicMock()

        with patch('src.core.network.process.subprocess.Popen', return_value=process) as popen_mock:
            actual = ProcessRunner().start_persistent(['openvpn', '--config', 'a.ovpn'])

        self.assertIs(actual, process)
        popen_mock.assert_called_once_with(
            ['openvpn', '--config', 'a.ovpn'],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

    def test_process_runner_should_wrap_start_errors(self):
        """ProcessRunner.start_persistent() should wrap OSError."""

        with patch('src.core.network.process.subprocess.Popen', side_effect=OSError('missing')):
            with self.assertRaises(NetworkTransportError):
                ProcessRunner().start_persistent(['openvpn'])

    def test_process_runner_should_run_short_command(self):
        """ProcessRunner.run() should run command with safe defaults."""

        completed = MagicMock()

        with patch('src.core.network.process.subprocess.run', return_value=completed) as run_mock:
            actual = ProcessRunner().run(['wg-quick', 'up', 'a.conf'], timeout=10)

        self.assertIs(actual, completed)
        run_mock.assert_called_once_with(
            ['wg-quick', 'up', 'a.conf'],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            check=True
        )

    def test_process_runner_should_wrap_run_errors(self):
        """ProcessRunner.run() should wrap subprocess errors."""

        with patch('src.core.network.process.subprocess.run', side_effect=subprocess.CalledProcessError(1, ['cmd'])):
            with self.assertRaises(NetworkTransportError):
                ProcessRunner().run(['cmd'])

    def test_process_runner_stop_should_ignore_none_or_finished_process(self):
        """ProcessRunner.stop() should ignore missing or already finished process."""

        runner = ProcessRunner()

        self.assertIsNone(runner.stop(None))

        process = MagicMock()
        process.poll.return_value = 0

        self.assertIsNone(runner.stop(process))
        process.terminate.assert_not_called()

    def test_process_runner_stop_should_terminate_running_process(self):
        """ProcessRunner.stop() should terminate running process."""

        process = MagicMock()
        process.poll.return_value = None

        ProcessRunner().stop(process, timeout=3)

        process.terminate.assert_called_once_with()
        process.wait.assert_called_once_with(timeout=3)

    def test_process_runner_stop_should_kill_after_timeout(self):
        """ProcessRunner.stop() should kill process when terminate wait times out."""

        process = MagicMock()
        process.poll.return_value = None
        process.wait.side_effect = [subprocess.TimeoutExpired('cmd', 3), None]

        ProcessRunner().stop(process, timeout=3)

        process.terminate.assert_called_once_with()
        process.kill.assert_called_once_with()
        self.assertEqual(process.wait.call_count, 2)

    def test_process_runner_stop_should_wrap_stop_errors(self):
        """ProcessRunner.stop() should wrap stop errors."""

        process = MagicMock()
        process.poll.side_effect = OSError('bad process')

        with self.assertRaises(NetworkTransportError):
            ProcessRunner().stop(process)

    def test_manager_start_should_not_cleanup_when_adapter_start_fails(self):
        """NetworkTransportManager.start() should not run cleanup when adapter startup fails before activation."""

        manager = NetworkTransportManager({'transport': 'direct'})
        adapter = MagicMock()
        adapter.start.side_effect = NetworkTransportError('start failed')
        adapter.stop = MagicMock()
        manager.adapter = adapter

        with self.assertRaises(NetworkTransportError):
            manager.start()

        adapter.stop.assert_not_called()

    def test_manager_healthcheck_should_stop_on_deadline_error_without_sleep(self):
        """NetworkTransportManager.start() should stop after a healthcheck error at the deadline."""

        profile = self.make_file('.conf')
        runner = MagicMock()
        runner.healthcheck.side_effect = NetworkTransportError('offline')

        manager = NetworkTransportManager({
            'transport': 'wireguard',
            'transport_profile': profile,
            'transport_healthcheck_url': 'https://ifconfig.me',
            'transport_timeout': 1,
        }, runner=runner)

        with patch('src.core.network.transport.time.monotonic', side_effect=[0, 0, 0, 1]), \
                patch('src.core.network.transport.time.sleep') as sleep_mock, \
                self.assertRaises(NetworkTransportError):
            manager.start()

        sleep_mock.assert_not_called()
        runner.run.assert_any_call(['wg-quick', 'down', profile], timeout=1)

    def test_manager_should_ignore_cleanup_error_after_failed_post_start_validation(self):
        """NetworkTransportManager.start() should preserve original validation error when cleanup fails."""

        profile = self.make_file('.conf')
        runner = MagicMock()
        runner.healthcheck.side_effect = NetworkTransportError('health failed')
        runner.run.side_effect = [None, NetworkTransportError('stop failed')]

        manager = NetworkTransportManager({
            'transport': 'wireguard',
            'transport_profile': profile,
            'transport_healthcheck_url': 'https://ifconfig.me',
            'transport_timeout': 1,
        }, runner=runner)

        with patch('src.core.network.transport.time.monotonic', side_effect=[0, 0, 0, 1]), \
                self.assertRaises(NetworkTransportError) as ctx:
            manager.start()

        self.assertIn('health failed', str(ctx.exception))
        runner.run.assert_any_call(['wg-quick', 'down', profile], timeout=1)

    def test_manager_should_reject_wrong_openvpn_profile_extension_in_profiles_file(self):
        """NetworkTransportManager should reject non-ovpn entries for OpenVPN profile lists."""

        profile = self.make_file('.conf')
        profiles = self.make_file('.txt', '{0}\n'.format(profile))

        with self.assertRaises(NetworkTransportError):
            NetworkTransportManager({
                'transport': 'openvpn',
                'transport_profiles': profiles,
                'transport_rotate': 'per-target',
            })

    def test_manager_rotate_should_return_current_adapter_when_rotation_is_disabled(self):
        """NetworkTransportManager.rotate() should return current adapter when rotation is disabled."""

        manager = NetworkTransportManager({'transport': 'direct'})

        adapter = manager.adapter

        actual = manager.rotate()

        self.assertIs(actual, adapter)
        self.assertIs(manager.adapter, adapter)
        self.assertEqual(manager.profile_index, -1)

    def test_manager_rotate_should_reject_empty_profiles_list(self):
        """NetworkTransportManager.rotate() should reject empty profile list in per-target mode."""

        profiles = self.make_file('.txt', '\n# only comments\n\n')

        manager = NetworkTransportManager({
            'transport': 'wireguard',
            'transport_profiles': profiles,
            'transport_rotate': 'per-target',
        })

        with self.assertRaises(NetworkTransportError):
            manager.rotate()

    def test_manager_should_load_profiles_without_vpn_validation_for_proxy_transport(self):
        """NetworkTransportManager should load profile list without VPN extension checks for proxy transport."""

        profiles = self.make_file('.txt', 'not-a-vpn-profile.custom\n')

        manager = NetworkTransportManager({
            'transport': 'proxy',
            'transport_profiles': profiles,
        })

        self.assertEqual(len(manager.profiles), 1)
        self.assertTrue(manager.profiles[0].endswith('not-a-vpn-profile.custom'))
        self.assertFalse(manager.is_vpn)

    def test_base_transport_should_return_profile_basename(self):
        """BaseTransport.profile_name should return basename when profile is set."""

        transport = DirectTransport({'transport_profile': '/tmp/vpn/nl.conf'})

        self.assertEqual(transport.profile_name, 'nl.conf')

    def test_base_transport_validate_profile_should_noop_without_required_extension(self):
        """BaseTransport.validate_profile() should do nothing when adapter has no profile extension."""

        transport = DirectTransport({})

        self.assertIsNone(transport.validate_profile())

    def test_base_transport_should_reject_missing_profile_file(self):
        """BaseTransport.validate_profile() should reject missing profile file with valid extension."""

        transport = WireGuardTransport({'transport_profile': '/missing/nl.conf'})

        with self.assertRaises(NetworkTransportError):
            transport.validate_profile()

    def test_base_transport_resolve_executable_should_use_candidate_file(self):
        """BaseTransport should resolve executable fallback candidates."""

        executable = self.make_file('.bin')
        os.chmod(executable, 0o700)
        transport = DirectTransport({})

        with patch('src.core.network.adapters.base.shutil.which', return_value=None):
            self.assertEqual(transport.resolve_executable('custom-vpn', [executable]), executable)

    def test_base_transport_resolve_executable_should_use_explicit_command_from_path(self):
        """BaseTransport should resolve explicit command names through PATH."""

        transport = DirectTransport({'transport_bin': 'openvpn'})

        with patch('src.core.network.adapters.base.shutil.which', return_value='/usr/sbin/openvpn'):
            self.assertEqual(transport.resolve_executable('ignored'), '/usr/sbin/openvpn')

    def test_base_transport_resolve_executable_should_reject_invalid_explicit_bin(self):
        """BaseTransport should reject invalid explicit transport binaries."""

        transport = DirectTransport({'transport_bin': '/missing/openvpn'})

        with patch('src.core.network.adapters.base.shutil.which', return_value=None):
            with self.assertRaises(NetworkTransportError) as ctx:
                transport.resolve_executable('ignored')

        self.assertIn('Transport executable does not exist or is not executable', str(ctx.exception))

    def test_base_transport_missing_executable_errors_should_be_platform_specific(self):
        """BaseTransport should return actionable per-platform executable diagnostics."""

        cases = [
            ('openvpn', 'Darwin', 'brew install openvpn'),
            ('openvpn', 'Windows', 'OpenVPN Community client'),
            ('openvpn', 'Linux', 'apt install openvpn'),
            ('wg-quick', 'Windows', 'wg-quick is not a native Windows backend'),
            ('wg-quick', 'Linux', 'wireguard-tools'),
            ('custom-vpn', 'Linux', 'Pass --transport-bin'),
        ]

        for command, system, expected in cases:
            transport = DirectTransport({})

            with self.subTest(command=command, system=system):
                with patch('src.core.network.adapters.base.shutil.which', return_value=None), \
                        patch('src.core.network.adapters.base.platform.system', return_value=system):
                    with self.assertRaises(NetworkTransportError) as ctx:
                        transport.resolve_executable(command, [])

                self.assertIn(expected, str(ctx.exception))

    def test_openvpn_transport_should_use_explicit_transport_bin(self):
        """OpenVpnTransport should use explicit transport executable when configured."""

        profile = self.make_file('.ovpn')
        executable = self.make_file('.bin')
        os.chmod(executable, 0o700)
        transport = OpenVpnTransport({
            'transport_profile': profile,
            'transport_bin': executable,
        })

        self.assertEqual(transport.build_start_command(), [executable, '--config', profile])


    def test_openvpn_transport_should_return_windows_candidates_from_program_files(self):
        transport = OpenVpnTransport({})

        with patch("src.core.network.adapters.openvpn.os.name", "nt"), \
                patch.dict("src.core.network.adapters.openvpn.os.environ", {
                    "ProgramFiles": "C:\\Program Files",
                    "ProgramFiles(x86)": "C:\\Program Files (x86)",
                }, clear=True):
            candidates = transport.executable_candidates()

        self.assertEqual(candidates, [
            os.path.join("C:\\Program Files", "OpenVPN", "bin", "openvpn.exe"),
            os.path.join("C:\\Program Files (x86)", "OpenVPN", "bin", "openvpn.exe"),
        ])

    def test_openvpn_transport_should_report_missing_executable(self):
        """OpenVpnTransport should return actionable error when executable is missing."""

        profile = self.make_file('.ovpn')
        transport = OpenVpnTransport({'transport_profile': profile})

        with patch('src.core.network.adapters.base.shutil.which', return_value=None):
            with patch.object(transport, 'executable_candidates', return_value=[]):
                with self.assertRaises(NetworkTransportError) as ctx:
                    transport.build_start_command()

        self.assertIn('openvpn executable not found in PATH', str(ctx.exception))
        self.assertIn('--transport-bin', str(ctx.exception))


    def test_manager_should_wait_openvpn_ready_without_healthcheck(self):
        """NetworkTransportManager.start() should wait OpenVPN readiness even without healthcheck URL."""

        profile = self.make_file('.ovpn')
        process = MagicMock()
        process.poll.return_value = None
        runner = MagicMock()
        runner.start_persistent.return_value = process

        with patch.object(OpenVpnTransport, 'wait_ready') as wait_ready:
            manager = NetworkTransportManager({
                'transport': 'openvpn',
                'transport_profile': profile,
                'transport_timeout': 9,
            }, runner=runner)

            manager.start()

        wait_ready.assert_called_once_with(timeout=9)
        runner.healthcheck.assert_not_called()

    def test_openvpn_transport_wait_ready_should_keep_process_alive_during_startup_grace(self):
        """OpenVpnTransport.wait_ready() should give the OS route a startup grace window."""

        process = MagicMock()
        process.poll.return_value = None
        transport = OpenVpnTransport({})
        transport.process = process

        with patch('src.core.network.adapters.openvpn.time.monotonic', side_effect=[0.0, 0.0, 0.2, 3.0]),                 patch('src.core.network.adapters.openvpn.time.sleep') as sleep_mock:
            transport.wait_ready(timeout=30)

        process.poll.assert_called()
        sleep_mock.assert_called_with(transport.STARTUP_POLL_SEC)

    def test_wireguard_transport_should_report_windows_backend_limitation(self):
        """WireGuard transport should explain Windows wg-quick limitation."""

        profile = self.make_file('.conf')
        transport = WireGuardTransport({'transport_profile': profile})

        with patch('src.core.network.adapters.base.shutil.which', return_value=None):
            with patch('src.core.network.adapters.base.platform.system', return_value='Windows'):
                with self.assertRaises(NetworkTransportError) as ctx:
                    transport.build_up_command()

        self.assertIn('wg-quick is not a native Windows backend', str(ctx.exception))

if __name__ == '__main__':
    unittest.main()
