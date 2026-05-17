# -*- coding: utf-8 -*-

import unittest

from src.lib.diff import DiffReport, DiffReportComparator, DiffReportFinding


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


class TestDiffReportComparator(unittest.TestCase):
    """Differential comparison engine coverage."""

    def compare(self, previous_findings, current_findings):
        """Compare finding lists."""

        return DiffReportComparator().compare(
            report('old', previous_findings),
            report('new', current_findings),
        )

    def test_compare_reports_added_removed_and_unchanged(self):
        """Comparator should classify basic added/removed/unchanged findings."""

        unchanged = finding('success', 'https://example.com/admin')
        old_only = finding('forbidden', 'https://example.com/old', status='403')
        new_only = finding('secret', 'https://example.com/config.json')

        result = self.compare([unchanged, old_only], [unchanged, new_only])

        self.assertEqual(result.unchanged_count, 1)
        self.assertEqual(result.added, (new_only,))
        self.assertEqual(result.removed, (old_only,))
        self.assertEqual(result.changed, ())
        self.assertEqual(result.summary['added'], 1)
        self.assertEqual(result.summary['removed'], 1)
        self.assertEqual(result.summary['unchanged'], 1)

    def test_compare_reports_forbidden_to_success_is_changed_not_added_removed(self):
        """Same endpoint changing bucket/status should be a changed finding."""

        previous = finding('forbidden', 'https://example.com/admin', status='403')
        current = finding('success', 'https://example.com/admin', status='200')

        result = self.compare([previous], [current])

        self.assertEqual(result.added, ())
        self.assertEqual(result.removed, ())
        self.assertEqual(len(result.changed), 1)
        self.assertEqual(result.changed[0].fields, {
            'bucket': ('forbidden', 'success'),
            'status': ('403', '200'),
        })

    def test_compare_reports_size_and_redirect_changes(self):
        """Comparator should track size and redirect location changes."""

        previous = finding(
            'redirect',
            'https://example.com/login',
            status='301',
            size='100B',
            location='/old-login',
        )
        current = finding(
            'redirect',
            'https://example.com/login',
            status='302',
            size='120B',
            location='/new-login',
        )

        result = self.compare([previous], [current])

        self.assertEqual(len(result.changed), 1)
        self.assertEqual(result.changed[0].fields, {
            'location': ('/old-login', '/new-login'),
            'size': ('100B', '120B'),
            'status': ('301', '302'),
        })

    def test_compare_reports_additive_security_bucket_on_same_url_is_added(self):
        """A new additive security finding on an existing URL should remain added."""

        success = finding('success', 'https://example.com/upload.php')
        malware = finding('malware', 'https://example.com/upload.php')

        result = self.compare([success], [success, malware])

        self.assertEqual(result.unchanged_count, 1)
        self.assertEqual(result.added, (malware,))
        self.assertEqual(result.removed, ())
        self.assertEqual(result.changed, ())

    def test_compare_reports_removed_additive_security_bucket_on_same_url_is_removed(self):
        """A removed additive finding should not become an endpoint state change."""

        success = finding('success', 'https://example.com/upload.php')
        malware = finding('malware', 'https://example.com/upload.php')

        result = self.compare([success, malware], [success])

        self.assertEqual(result.unchanged_count, 1)
        self.assertEqual(result.added, ())
        self.assertEqual(result.removed, (malware,))
        self.assertEqual(result.changed, ())

    def test_compare_reports_bucket_change_when_one_unmatched_pair_remains(self):
        """One old/new leftover pair for the same endpoint should become changed."""

        old_stacktrace = finding('stacktrace', 'https://example.com/debug', status='500')
        new_success = finding('success', 'https://example.com/debug', status='200')

        result = self.compare([old_stacktrace], [new_success])

        self.assertEqual(len(result.changed), 1)
        self.assertEqual(result.changed[0].fields['bucket'], ('stacktrace', 'success'))
        self.assertEqual(result.changed[0].fields['status'], ('500', '200'))

    def test_compare_reports_multiple_unmatched_items_are_added_and_removed(self):
        """Ambiguous multi-bucket changes should stay explicit added/removed records."""

        old_secret = finding('secret', 'https://example.com/config')
        old_shadow = finding('shadow', 'https://example.com/config')
        new_malware = finding('malware', 'https://example.com/config')
        new_success = finding('success', 'https://example.com/config')

        result = self.compare([old_secret, old_shadow], [new_malware, new_success])

        self.assertEqual(result.changed, ())
        self.assertEqual(result.added, (new_malware, new_success))
        self.assertEqual(result.removed, (old_secret, old_shadow))

    def test_compare_reports_uses_method_in_identity(self):
        """Same URL with different methods should be compared independently."""

        old_get = finding('success', 'https://example.com/api', method='GET')
        old_post = finding('forbidden', 'https://example.com/api', method='POST', status='403')
        new_get = finding('success', 'https://example.com/api', method='GET')
        new_post = finding('success', 'https://example.com/api', method='POST', status='200')

        result = self.compare([old_get, old_post], [new_get, new_post])

        self.assertEqual(result.unchanged_count, 1)
        self.assertEqual(len(result.changed), 1)
        self.assertEqual(result.changed[0].identity, ('POST', 'https://example.com/api'))

    def test_compare_reports_outputs_deterministic_order(self):
        """Added and removed records should be sorted deterministically."""

        result = self.compare(
            [
                finding('success', 'https://example.com/z'),
                finding('success', 'https://example.com/a'),
            ],
            [
                finding('success', 'https://example.com/c'),
                finding('success', 'https://example.com/b'),
            ],
        )

        self.assertEqual([item.url for item in result.added], [
            'https://example.com/b',
            'https://example.com/c',
        ])
        self.assertEqual([item.url for item in result.removed], [
            'https://example.com/a',
            'https://example.com/z',
        ])


if __name__ == '__main__':
    unittest.main()
