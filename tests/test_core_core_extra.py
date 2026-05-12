# -*- coding: utf-8 -*-

import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock
from pathlib import Path
from unittest.mock import patch

from src.core.decorators import execution_time

import src.core.core as core_module


class TestCoreExtra(unittest.TestCase):
    """TestCoreExtra class."""

    def test_read_version_prefers_version_file_in_source_checkout(self):
        """read_version() should prefer local VERSION over stale installed package metadata."""

        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            (project_root / 'VERSION').write_text('5.15.0\n', encoding='utf-8')

            with patch('src.core.core.package_version', return_value='5.6.0'), \
                    patch.object(core_module, 'PROJECT_ROOT', project_root):
                self.assertEqual(core_module.read_version(), '5.15.0')

    def test_read_version_falls_back_to_installed_package_metadata(self):
        """read_version() should use installed package metadata when VERSION is absent."""

        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            with patch('src.core.core.package_version', return_value='9.9.9'), \
                    patch.object(core_module, 'PROJECT_ROOT', project_root):
                self.assertEqual(core_module.read_version(), '9.9.9')

    def test_read_version_returns_default_when_nothing_found(self):
        """read_version() should return 0.0.0 when metadata and VERSION are missing."""

        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            with patch('src.core.core.package_version', side_effect=core_module.PackageNotFoundError), \
                    patch.object(core_module, 'PROJECT_ROOT', project_root):
                self.assertEqual(core_module.read_version(), '0.0.0')

    def test_resolve_data_root_prefers_project_root_data(self):
        """resolve_data_root() should prefer project-root data directory first."""

        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            project_root = base / 'repo'
            prefix_root = base / 'prefix'
            base_prefix_root = base / 'base-prefix'

            (project_root / 'data').mkdir(parents=True)
            (prefix_root / 'data').mkdir(parents=True)
            (base_prefix_root / 'data').mkdir(parents=True)

            with patch.object(core_module, 'PROJECT_ROOT', project_root), \
                    patch.object(core_module.py_sys, 'prefix', str(prefix_root)), \
                    patch.object(core_module.py_sys, 'base_prefix', str(base_prefix_root)):
                self.assertEqual(core_module.resolve_data_root(), project_root / 'data')

    def test_resolve_data_root_falls_back_to_prefix_and_base_prefix(self):
        """resolve_data_root() should fall back to sys.prefix and then sys.base_prefix."""

        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            project_root = base / 'repo'
            prefix_root = base / 'prefix'
            base_prefix_root = base / 'base-prefix'

            (prefix_root / 'data').mkdir(parents=True)

            with patch.object(core_module, 'PROJECT_ROOT', project_root), \
                    patch.object(core_module.py_sys, 'prefix', str(prefix_root)), \
                    patch.object(core_module.py_sys, 'base_prefix', str(base_prefix_root)):
                self.assertEqual(core_module.resolve_data_root(), prefix_root / 'data')

            (prefix_root / 'data').rmdir()
            (base_prefix_root / 'data').mkdir(parents=True)

            with patch.object(core_module, 'PROJECT_ROOT', project_root), \
                    patch.object(core_module.py_sys, 'prefix', str(prefix_root)), \
                    patch.object(core_module.py_sys, 'base_prefix', str(base_prefix_root)):
                self.assertEqual(core_module.resolve_data_root(), base_prefix_root / 'data')

    def test_resolve_data_root_returns_project_default_when_no_candidates_exist(self):
        """resolve_data_root() should return project-root data path even if it does not exist."""

        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            project_root = base / 'repo'
            prefix_root = base / 'prefix'
            base_prefix_root = base / 'base-prefix'

            with patch.object(core_module, 'PROJECT_ROOT', project_root), \
                    patch.object(core_module.py_sys, 'prefix', str(prefix_root)), \
                    patch.object(core_module.py_sys, 'base_prefix', str(base_prefix_root)):
                self.assertEqual(core_module.resolve_data_root(), project_root / 'data')

    def test_execution_time_logs_total_time_when_debug_enabled(self):
        """execution_time() should log elapsed time when self.ioargs.debug is enabled."""

        log = MagicMock()
        owner = SimpleNamespace(ioargs={'debug': 1})

        @execution_time(log=log)
        def decorated(self, value):
            return value.upper()

        with patch('src.core.decorators.timer.time.time', side_effect=[10.0, 12.5]):
            self.assertEqual(decorated(owner, 'ok'), 'OK')

        log.debug.assert_called_once_with(key='total_time_lvl3', time='0:00:02.500000')

    def test_execution_time_skips_logging_without_dict_ioargs(self):
        """execution_time() should ignore non-dict ioargs and keep the wrapped return value."""

        log = MagicMock()
        owner = SimpleNamespace(ioargs='debug=1')

        @execution_time(log=log)
        def decorated(self):
            return 'done'

        self.assertEqual(decorated(owner), 'done')
        log.debug.assert_not_called()


if __name__ == '__main__':
    unittest.main()
