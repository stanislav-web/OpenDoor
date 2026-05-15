# -*- coding: utf-8 -*-

import unittest

from urllib3.response import HTTPResponse

from src.core.http.plugins.response import stacktrace
from src.core.http.plugins.response.stacktrace import StacktraceResponsePlugin


class TestStacktraceResponsePlugin(unittest.TestCase):
    """StacktraceResponsePlugin test cases."""

    def make_response(self, status=500, body=b'', headers=None):
        """
        Build a urllib3 response for plugin tests.

        :param int status: HTTP status code
        :param bytes body: response body
        :param dict|None headers: response headers
        :return: HTTP response
        """

        return HTTPResponse(status=status, body=body, headers=headers or {})

    def assert_detection(self, body, runtime, signal, confidence=80, headers=None):
        """
        Assert that a response body is classified as stacktrace.

        :param str body: response body
        :param str runtime: expected runtime family
        :param str signal: expected signal name
        :param int confidence: minimum expected confidence
        :param dict|None headers: optional response headers
        :return: debug detection metadata
        """

        plugin = StacktraceResponsePlugin(None)
        response = self.make_response(
            body=body.encode('utf-8'),
            headers=headers or {'Content-Type': 'text/plain; charset=utf-8'},
        )

        self.assertEqual(plugin.process(response), 'stacktrace')
        detection = getattr(response, 'opendoor_stacktrace_detection')
        self.assertEqual(detection['type'], 'stacktrace')
        self.assertEqual(detection['runtime'], runtime)
        self.assertEqual(detection['signal'], signal)
        self.assertGreaterEqual(detection['confidence'], confidence)
        return detection

    def test_response_package_exports_stacktrace_plugin_alias(self):
        """Response plugin loader should be able to resolve the stacktrace alias."""

        self.assertIs(stacktrace, StacktraceResponsePlugin)

    def test_detects_python_traceback(self):
        """Should detect Python traceback exposure."""

        self.assert_detection(
            'Traceback (most recent call last):\n  File "app.py", line 10, in <module>',
            'python',
            'python-traceback',
            95,
        )

    def test_detects_node_stack_frame(self):
        """Should detect Node.js stack frames."""

        self.assert_detection(
            'Error: boom\n    at Object.<anonymous> (/app/dist/main.js:12:34)',
            'node',
            'node-anonymous-stack-frame',
            90,
        )

    def test_detects_nestjs_error(self):
        """Should detect NestJS verbose errors."""

        self.assert_detection('[Nest] 12345 - ERROR Exception: forbidden', 'nestjs', 'nestjs-error', 85)

    def test_detects_php_error(self):
        """Should detect PHP fatal/warning style errors."""

        self.assert_detection('PHP Fatal error: Uncaught Error in /var/www/index.php:10', 'php', 'php-error', 90)

    def test_detects_java_exception(self):
        """Should detect Java exception exposures."""

        self.assert_detection('java.lang.NullPointerException: Cannot invoke service', 'java', 'java-exception', 90)

    def test_detects_sqlstate_and_oracle_errors(self):
        """Should detect SQLSTATE and Oracle error disclosures."""

        self.assert_detection('SQLSTATE[42S02]: Base table or view not found', 'sql', 'sqlstate-error', 85)
        self.assert_detection('ORA-00942: table or view does not exist', 'oracle', 'oracle-error', 85)

    def test_accepts_json_problem_content_type(self):
        """Should inspect structured textual error content types."""

        self.assert_detection(
            '{"error":"SQLSTATE[HY000]: driver error"}',
            'sql',
            'sqlstate-error',
            headers={'Content-Type': 'application/problem+json'},
        )


    def test_ignores_standard_404_body_with_notice_like_path(self):
        """Should not classify a normal nginx/apache-style 404 page as a PHP notice."""

        plugin = StacktraceResponsePlugin(None)
        body = (
            '<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">\n'
            '<html><head><title>404 Not Found</title></head><body>\n'
            '<h1>Not Found</h1>\n'
            '<p>The requested URL /noticeware was not found on this server.</p>\n'
            '</body></html>'
        )
        response = self.make_response(
            status=404,
            body=body.encode('utf-8'),
            headers={
                'Content-Type': 'text/html; charset=iso-8859-1',
                'Server': 'nginx/1.12.1',
            },
        )

        self.assertIsNone(plugin.process(response))
        self.assertFalse(hasattr(response, 'opendoor_stacktrace_detection'))

    def test_detects_php_notice_when_formatted_as_runtime_error(self):
        """Should still detect real PHP Notice runtime diagnostics."""

        self.assert_detection(
            'Notice: Undefined index: user_id in /var/www/html/index.php on line 12',
            'php',
            'php-error',
            90,
        )

    def test_ignores_standard_404_body_with_warning_like_path(self):
        """Should not classify ordinary 404 pages whose URL contains warning-like text."""

        plugin = StacktraceResponsePlugin(None)
        body = (
            '<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">'
            '<html><head><title>404 Not Found</title></head><body>'
            '<h1>Not Found</h1>'
            '<p>The requested URL /errorswarnings was not found on this server.</p>'
            '</body></html>'
        )
        response = self.make_response(
            status=404,
            body=body.encode('utf-8'),
            headers={
                'Content-Type': 'text/html; charset=iso-8859-1',
                'Server': 'nginx/1.12.1',
            },
        )

        self.assertIsNone(plugin.process(response))
        self.assertFalse(hasattr(response, 'opendoor_stacktrace_detection'))


    def test_ignores_html_css_warning_and_error_tokens(self):
        """Should not classify ordinary CSS warning/error class names as PHP diagnostics."""

        plugin = StacktraceResponsePlugin(None)
        body = (
            '<!DOCTYPE html><html><head><style>'
            '.btn-warning:active,.alert-warning:hover,.has-error .form-control{background:#fff}'
            '.ion-alert:before{content:"\f101"}'
            '</style></head><body><article>normal page source</article></body></html>'
        )
        response = self.make_response(
            status=200,
            body=body.encode('utf-8'),
            headers={'Content-Type': 'text/html; charset=utf-8'},
        )

        self.assertIsNone(plugin.process(response))
        self.assertFalse(hasattr(response, 'opendoor_stacktrace_detection'))

    def test_ignores_cscart_404_i18n_warning_and_notice_keys(self):
        """Should not classify CS-Cart 404 localization keys as PHP diagnostics."""

        plugin = StacktraceResponsePlugin(None)
        body = (
            '<!DOCTYPE html><html><head><title>Страница не найдена</title></head>'
            '<body><div class="ty-exception"><div class="ty-exception__code">404</div>'
            '<p>Запрашиваемая страница не найдена.</p></div>'
            '<script type="text/javascript">_.tr({'
            "notice: 'Оповещение', warning: 'Предупреждение', error: 'Ошибка', "
            "error_validator_integer: 'Значение поля <b>[field]</b> неправильное.'"
            '});</script></body></html>'
        )
        response = self.make_response(
            status=404,
            body=body.encode('utf-8'),
            headers={'Content-Type': 'text/html; charset=utf-8'},
        )

        self.assertIsNone(plugin.process(response))
        self.assertFalse(hasattr(response, 'opendoor_stacktrace_detection'))

    def test_detects_php_warning_when_formatted_as_runtime_error(self):
        """Should still detect real PHP Warning runtime diagnostics."""

        self.assert_detection(
            'Warning: include(config.php): failed to open stream in /var/www/html/index.php on line 7',
            'php',
            'php-error',
            90,
        )

    def test_detects_html_formatted_php_warning(self):
        """Should still detect HTML-formatted PHP runtime diagnostics."""

        self.assert_detection(
            '<br /><b>Warning</b>: require(config.php): failed to open stream '
            'in <b>/var/www/html/index.php</b> on line <b>7</b><br />',
            'php',
            'php-error',
            90,
            headers={'Content-Type': 'text/html; charset=utf-8'},
        )

    def test_ignores_binary_and_normal_responses(self):
        """Should avoid binary bodies and normal non-debug text."""

        plugin = StacktraceResponsePlugin(None)
        binary = self.make_response(body=b'PHP Fatal error', headers={'Content-Type': 'application/pdf'})
        normal = self.make_response(body=b'<html><body>Server error</body></html>', headers={'Content-Type': 'text/html'})

        self.assertIsNone(plugin.process(binary))
        self.assertFalse(hasattr(binary, 'opendoor_stacktrace_detection'))
        self.assertIsNone(plugin.process(normal))
        self.assertFalse(hasattr(normal, 'opendoor_stacktrace_detection'))

    def test_ignores_empty_or_statusless_responses(self):
        """Should ignore empty responses and malformed response objects."""

        plugin = StacktraceResponsePlugin(None)

        self.assertIsNone(plugin.process(self.make_response(body=b'')))
        self.assertIsNone(plugin.process(object()))

    def test_get_header_uses_case_insensitive_fallback_and_handles_missing_header(self):
        """Should resolve Content-Type through case-insensitive header iteration."""

        plugin = StacktraceResponsePlugin(None)
        response = type('PlainResponse', (), {
            'status': 500,
            'data': b'Traceback (most recent call last):',
            'headers': {'content-type': 'text/plain; charset=utf-8'},
        })()

        self.assertEqual(plugin.process(response), 'stacktrace')
        self.assertEqual(getattr(response, 'opendoor_stacktrace_detection')['runtime'], 'python')

        plugin = StacktraceResponsePlugin(None)
        response = self.make_response(body=b'Traceback (most recent call last):', headers={})

        self.assertEqual(plugin.process(response), 'stacktrace')
        self.assertEqual(getattr(response, 'opendoor_stacktrace_detection')['runtime'], 'python')

    def test_accepts_vendor_json_and_xml_suffix_content_types(self):
        """Should inspect vendor structured content types ending with +json or +xml."""

        self.assert_detection(
            '{"error":"SQLSTATE[HY000]: driver error"}',
            'sql',
            'sqlstate-error',
            headers={'Content-Type': 'application/vnd.api+json'},
        )
        self.assert_detection(
            '<error>ORA-00942: table or view does not exist</error>',
            'oracle',
            'oracle-error',
            headers={'Content-Type': 'application/vnd.oracle+xml'},
        )

    def test_ignores_unknown_non_textual_content_type(self):
        """Should skip unknown non-textual content types instead of scanning blindly."""

        plugin = StacktraceResponsePlugin(None)
        response = self.make_response(
            body=b'Traceback (most recent call last):',
            headers={'Content-Type': 'application/x-custom-binary'},
        )

        self.assertIsNone(plugin.process(response))
        self.assertFalse(hasattr(response, 'opendoor_stacktrace_detection'))
