# -*- coding: utf-8 -*-

import unittest

from src.lib.diff import (
    DiffReport,
    DiffReportComparator,
    DiffReportFinding,
    DiffResultSerializer,
    DiffStdoutFormatter,
)


def report(name, findings):
    """Create a normalized diff report."""

    return DiffReport(
        path='{0}.sqlite'.format(name),
        format='sqlite',
        target='example.com',
        findings=tuple(findings),
    )


def finding(bucket, url, status='200', size='1KB', method='', location=''):
    """Create a normalized finding."""

    return DiffReportFinding(
        bucket=bucket,
        url=url,
        status=str(status),
        size=size,
        method=method,
        location=location,
    )


def compare(previous_findings, current_findings):
    """Compare two finding lists."""

    return DiffReportComparator().compare(
        report('old', previous_findings),
        report('new', current_findings),
    )


class TestDiffResultSerializer(unittest.TestCase):
    """JSON-compatible diff serialization coverage."""

    def test_serializer_outputs_summary_and_sections(self):
        """Serializer should expose deterministic summary and section arrays."""

        previous = finding('forbidden', 'https://example.com/admin', status='403')
        current = finding('success', 'https://example.com/admin', status='200')
        added = finding('secret', 'https://example.com/config.json', method='GET')

        result = compare([previous], [current, added])
        payload = DiffResultSerializer().serialize(result)

        self.assertEqual(payload['summary'], {
            'old_report': 'old.sqlite',
            'new_report': 'new.sqlite',
            'added': 1,
            'removed': 0,
            'changed': 1,
            'unchanged': 0,
        })
        self.assertEqual(payload['added'][0]['bucket'], 'secret')
        self.assertEqual(payload['added'][0]['method'], 'GET')
        self.assertEqual(payload['removed'], [])
        self.assertEqual(payload['changed'][0]['fields'], {
            'bucket': {'previous': 'forbidden', 'current': 'success'},
            'status': {'previous': '403', 'current': '200'},
        })

    def test_serializer_preserves_location_and_empty_fields(self):
        """Serializer should keep redirect location and empty optional fields stable."""

        redirect = finding(
            'redirect',
            'https://example.com/login',
            status='301',
            location='/login',
        )
        result = compare([], [redirect])
        payload = DiffResultSerializer().serialize(result)

        self.assertEqual(payload['added'][0], {
            'bucket': 'redirect',
            'url': 'https://example.com/login',
            'method': '',
            'status': '301',
            'size': '1KB',
            'location': '/login',
        })


class TestDiffStdoutFormatter(unittest.TestCase):
    """Readable stdout diff output coverage."""

    def test_formatter_outputs_summary_and_all_sections(self):
        """Formatter should render summary, added, removed and changed sections."""

        previous = finding('forbidden', 'https://example.com/admin', status='403')
        current = finding('success', 'https://example.com/admin', status='200')
        removed = finding('stacktrace', 'https://example.com/debug', status='500')
        added = finding('malware', 'https://example.com/upload.php', method='GET')

        result = compare([previous, removed], [current, added])
        output = DiffStdoutFormatter().format(result)

        self.assertIn('Differential scan summary', output)
        self.assertIn('old_report: old.sqlite', output)
        self.assertIn('new_report: new.sqlite', output)
        self.assertIn('added: 1', output)
        self.assertIn('removed: 1', output)
        self.assertIn('changed: 1', output)
        self.assertIn('Added:\n  [malware] 200 1KB GET https://example.com/upload.php', output)
        self.assertIn('Removed:\n  [stacktrace] 500 1KB https://example.com/debug', output)
        self.assertIn('Changed:\n  [success] 200 1KB https://example.com/admin', output)
        self.assertIn('    bucket: forbidden -> success', output)
        self.assertIn('    status: 403 -> 200', output)

    def test_formatter_outputs_empty_section_placeholders(self):
        """Formatter should render explicit placeholders for empty sections."""

        unchanged = finding('success', 'https://example.com/admin')
        output = DiffStdoutFormatter().format(compare([unchanged], [unchanged]))

        self.assertIn('Added:\n  -', output)
        self.assertIn('Removed:\n  -', output)
        self.assertIn('Changed:\n  -', output)
        self.assertIn('unchanged: 1', output)

    def test_formatter_prints_empty_values_as_dashes(self):
        """Formatter should avoid blank visual fields in changed details."""

        previous = finding('redirect', 'https://example.com/login', status='302', location='/login')
        current = finding('redirect', 'https://example.com/login', status='200', location='')
        output = DiffStdoutFormatter().format(compare([previous], [current]))

        self.assertIn('    location: /login -> -', output)

    def test_formatter_includes_redirect_location_on_finding_lines(self):
        """Formatter should append redirect locations when a finding carries one."""

        redirect = finding(
            'redirect',
            'https://example.com/start',
            status='302',
            location='https://example.com/final',
        )
        output = DiffStdoutFormatter().format(compare([], [redirect]))

        self.assertIn(
            'Added:\n  [redirect] 302 1KB https://example.com/start -> https://example.com/final',
            output,
        )


if __name__ == '__main__':
    unittest.main()
