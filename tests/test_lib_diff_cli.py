# -*- coding: utf-8 -*-

import json
import os
import tempfile
import unittest
from unittest.mock import patch

from src import Controller


class TestDiffCliIntegration(unittest.TestCase):
    """High-level diff command integration coverage without network scans."""

    def setUp(self):
        """Create a temporary workspace."""

        self.tmpdir = tempfile.TemporaryDirectory()

    def tearDown(self):
        """Remove temporary files."""

        self.tmpdir.cleanup()

    def path(self, name):
        """Return a file path inside the temporary workspace."""

        return os.path.join(self.tmpdir.name, name)

    def write_json_report(self, name, report_items):
        """Write a minimal OpenDoor JSON report."""

        path = self.path(name)
        with open(path, 'w', encoding='utf-8') as handler:
            json.dump({
                'target': 'example.com',
                'report_items': report_items,
            }, handler, sort_keys=True)

        return path

    def test_diff_action_compares_two_json_reports_and_writes_json_output(self):
        """Diff command should compare previous/current reports and persist JSON output."""

        old_report = self.write_json_report('old.json', {
            'forbidden': [
                {'url': 'https://example.com/admin', 'code': 403, 'size': '10B'},
            ],
        })
        new_report = self.write_json_report('new.json', {
            'success': [
                {'url': 'https://example.com/admin', 'code': 200, 'size': '12B'},
                {'url': 'https://example.com/debug', 'code': 200, 'size': '1KB'},
            ],
        })

        with patch('src.controller.tpl.message'), patch('src.controller.tpl.info'):
            status = Controller.diff_action({
                'diff': '{0}:{1}'.format(old_report, new_report),
                'reports': 'std,json',
                'reports_dir': self.tmpdir.name,
            })

        self.assertEqual(status, 0)
        output_path = self.path('opendoor-diff.json')
        with open(output_path, encoding='utf-8') as handler:
            payload = json.load(handler)

        self.assertEqual(payload['summary']['added'], 1)
        self.assertEqual(payload['summary']['changed'], 1)
        self.assertEqual(payload['added'][0]['url'], 'https://example.com/debug')
        self.assertEqual(payload['changed'][0]['fields']['status']['previous'], '403')
        self.assertEqual(payload['changed'][0]['fields']['status']['current'], '200')


if __name__ == '__main__':
    unittest.main()
