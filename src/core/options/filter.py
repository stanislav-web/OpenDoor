# -*- coding: utf-8 -*-

"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Development Team: Brain Storm Team
"""

import os
import re
import sys

from urllib.parse import unquote

from src.core import helper
from .exceptions import FilterError


class Filter(object):

    """Filter class"""

    URL_REGEX = r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|(?:[-A-Za-z0-9]+\.)+([-A-Za-z]|\w){2,8})$"
    STATUS_RANGE_REGEX = re.compile(r'^\d{3}(?:-\d{3})?$')
    INTEGER_RANGE_REGEX = re.compile(r'^\d+(?:-\d+)?$')

    @staticmethod
    def filter(args):
        """
        Filter options
        :param dict args:
        :return: dict
        """

        filtered = {}

        if args.get('session_load') is not None:
            if args.get('raw_request') is not None:
                raise FilterError('--session-load cannot be used together with --raw-request')

            if args.get('host') or args.get('hostlist') or args.get('stdin') is True:
                raise FilterError('--session-load cannot be used together with target source options')

            filtered = {
                'session_load': Filter.session_file(args.get('session_load'), key='--session-load')
            }

            if args.get('session_autosave_sec') is not None:
                filtered['session_autosave_sec'] = Filter.positive_int(
                    args.get('session_autosave_sec'),
                    key='--session-autosave-sec'
                )

            if args.get('session_autosave_items') is not None:
                filtered['session_autosave_items'] = Filter.positive_int(
                    args.get('session_autosave_items'),
                    key='--session-autosave-items'
                )

            return filtered
        raw_request = Filter.raw_request(args.get('raw_request'), scheme=args.get('scheme'))
        targets = Filter.targets(args, raw_request=raw_request)

        for key, value in args.items():
            if 'scan' == key:
                filtered['scan'] = Filter.scan(value)
            elif key in ['host', 'hostlist', 'stdin', 'raw_request']:
                continue
            elif key in ['session_save']:
                filtered[key] = Filter.session_file(value, key='--{0}'.format(key.replace('_', '-')))
            elif key in ['session_autosave_sec', 'session_autosave_items']:
                filtered[key] = Filter.positive_int(value, key='--{0}'.format(key.replace('_', '-')))
            elif 'proxy' == key:
                filtered[key] = Filter.proxy(value)
            elif 'scheme' == key:
                filtered[key] = Filter.explicit_scheme(value, key='--scheme')
            elif key in ['include_status', 'exclude_status']:
                filtered[key] = Filter.status_ranges(value, key='--{0}'.format(key.replace('_', '-')))
            elif key in ['exclude_size']:
                filtered[key] = Filter.integer_values(value, key='--{0}'.format(key.replace('_', '-')))
            elif key in ['exclude_size_range']:
                filtered[key] = Filter.integer_ranges(value, key='--{0}'.format(key.replace('_', '-')))
            elif key in ['match_regex', 'exclude_regex']:
                filtered[key] = Filter.regex_values(value, key='--{0}'.format(key.replace('_', '-')))
            elif key in ['match_text', 'exclude_text']:
                filtered[key] = Filter.text_values(value)
            elif key in ['min_response_length', 'max_response_length']:
                filtered[key] = Filter.non_negative_int(value, key='--{0}'.format(key.replace('_', '-')))
            else:
                filtered[key] = value

        if raw_request is not None:
            if 'method' not in filtered and raw_request.get('method'):
                filtered['method'] = raw_request.get('method')

            raw_headers = raw_request.get('headers') or []
            cli_headers = filtered.get('header') or []
            merged_headers = list(raw_headers) + list(cli_headers)
            if merged_headers:
                filtered['header'] = merged_headers

            raw_cookies = raw_request.get('cookies') or []
            cli_cookies = filtered.get('cookie') or []
            merged_cookies = list(raw_cookies) + list(cli_cookies)
            if merged_cookies:
                filtered['cookie'] = merged_cookies

            if 'prefix' not in filtered and raw_request.get('prefix'):
                filtered['prefix'] = raw_request.get('prefix')

            if raw_request.get('body') not in [None, '']:
                filtered['request_body'] = raw_request.get('body')

            filtered['raw_request'] = raw_request.get('source')

        if filtered.get('min_response_length') is not None and filtered.get('max_response_length') is not None:
            if filtered.get('min_response_length') > filtered.get('max_response_length'):
                raise FilterError('--min-response-length cannot be greater than --max-response-length')

        if len(targets) == 1:
            filtered['host'] = targets[0]['host']
            filtered['scheme'] = targets[0]['scheme']
            filtered['ssl'] = targets[0]['ssl']
            if targets[0].get('port') is not None and 'port' not in filtered:
                filtered['port'] = targets[0]['port']

        if len(targets) > 0:
            filtered['targets'] = targets

        if raw_request is not None and len(targets) <= 0:
            raise FilterError('Unable to resolve target from --raw-request. Provide a Host header or use --host/--hostlist/--stdin')

        return filtered

    @staticmethod
    def scheme(hostname):
        """
        Get the scheme of the input hostname.

        :param hostname: A string representing the input hostname.
        :type hostname: str
        :return: A string representing the scheme of the input hostname.
        :rtype: str
        """

        scheme = helper.parse_url(hostname).scheme
        if not scheme:
            scheme = 'http'
        return scheme + "://"

    @staticmethod
    def ssl(scheme):
        """
        If `ssl` in action
        :param str scheme: scheme protocol
        :return: bool
        """

        return 'https://' == scheme

    @staticmethod
    def targets(args, raw_request=None):
        """
        Build normalized targets from a single host, host file, STDIN or raw request.

        :param dict args:
        :param dict raw_request:
        :raise FilterError:
        :return: list[dict]
        """

        raw_targets = []

        if args.get('host'):
            raw_targets = [args.get('host')]
        elif args.get('hostlist'):
            raw_targets = Filter._read_target_lines(args.get('hostlist'))
        elif args.get('stdin') is True:
            raw_targets = Filter._read_target_stream(sys.stdin)

        targets = []
        seen = set()

        for raw_target in raw_targets:
            cleaned = Filter._clean_target(raw_target)
            if not cleaned:
                continue
            if cleaned in seen:
                continue

            host = Filter.host(cleaned)
            scheme = Filter.scheme(cleaned)
            targets.append({
                'host': host,
                'scheme': scheme,
                'ssl': Filter.ssl(scheme),
                'source': cleaned,
            })
            seen.add(cleaned)

        if len(targets) <= 0 and raw_request is not None and raw_request.get('host'):
            scheme = raw_request.get('scheme')
            if scheme is None:
                raise FilterError('--scheme is required when --raw-request uses a relative request line')

            target = {
                'host': raw_request.get('host'),
                'scheme': scheme,
                'ssl': Filter.ssl(scheme),
                'source': raw_request.get('target_source') or raw_request.get('host'),
            }

            if raw_request.get('port') is not None:
                target['port'] = raw_request.get('port')

            targets.append(target)

        return targets

    @staticmethod
    def _read_target_lines(filepath):
        """
        Read targets from a file.

        :param str filepath:
        :raise FilterError:
        :return: list[str]
        """

        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                return Filter._read_target_stream(file)
        except OSError as error:
            raise FilterError("Unable to read targets from --hostlist `{0}`. {1}".format(filepath, error))

    @staticmethod
    def _read_target_stream(stream):
        """
        Read targets from a stream-like object.

        :param stream:
        :return: list[str]
        """

        return [line for line in stream.readlines()]

    @staticmethod
    def _clean_target(value):
        """
        Normalize a raw target line.

        :param str value:
        :return: str
        """

        if value is None:
            return ''
        value = str(value).strip()
        if not value or value.startswith('#'):
            return ''
        return value

    @staticmethod
    def explicit_scheme(value, key='--scheme'):
        """
        Normalize explicit scheme values.

        :param str value:
        :param str key:
        :return: str | None
        """

        if value is None:
            return None

        scheme = str(value).strip().lower()
        if not scheme:
            return None

        scheme = scheme.replace('://', '')
        if scheme not in ['http', 'https']:
            raise FilterError('{0} accepts only http or https'.format(key))

        return scheme + '://'

    @staticmethod
    def raw_request(filepath, scheme=None):
        """
        Read and parse a raw HTTP request file.

        :param str filepath:
        :param str scheme:
        :return: dict | None
        """

        if filepath is None:
            return None

        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
        except OSError as error:
            raise FilterError('Unable to read raw request from --raw-request `{0}`. {1}'.format(filepath, error))

        parsed = Filter._parse_raw_request(content, scheme=scheme)
        parsed['source'] = filepath
        return parsed

    @staticmethod
    def _parse_raw_request(content, scheme=None):
        """
        Parse a raw HTTP request payload.

        :param str content:
        :param str scheme:
        :return: dict
        """

        content = '' if content is None else str(content)
        parts = re.split(r'\r?\n\r?\n', content, maxsplit=1)
        head = parts[0] if len(parts) > 0 else ''
        body = parts[1] if len(parts) > 1 else ''
        lines = [line.rstrip('\r') for line in head.splitlines() if line.strip()]

        if len(lines) <= 0:
            raise FilterError('--raw-request file is empty')

        request_line = lines[0].strip()
        request_line_parts = request_line.split()
        if len(request_line_parts) < 2:
            raise FilterError('Invalid request line in --raw-request')

        method = request_line_parts[0].upper()
        request_target = request_line_parts[1].strip()
        explicit_scheme = Filter.explicit_scheme(scheme, key='--scheme')

        headers = []
        cookies = []
        host_header = None

        for line in lines[1:]:
            if ':' not in line:
                raise FilterError('Invalid header in --raw-request: `{0}`'.format(line))

            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()

            if not key:
                raise FilterError('Invalid header in --raw-request: `{0}`'.format(line))

            lower_key = key.lower()
            if lower_key == 'host':
                host_header = value
                continue
            if lower_key == 'cookie':
                cookies.extend([item.strip() for item in value.split(';') if item.strip()])
                continue
            if lower_key == 'content-length':
                continue

            headers.append('{0}: {1}'.format(key, value))

        resolved_scheme = explicit_scheme
        resolved_host = None
        resolved_port = None
        request_path = request_target

        if re.match(r'^https?://', request_target, re.IGNORECASE):
            parsed_url = helper.parse_url(request_target)
            resolved_scheme = parsed_url.scheme + '://'
            resolved_host, resolved_port = Filter._split_host_and_port(parsed_url.netloc)
            request_path = parsed_url.path or '/'
            if parsed_url.query:
                request_path += '?' + parsed_url.query
        elif host_header is not None:
            resolved_host, resolved_port = Filter._split_host_and_port(host_header)
        elif explicit_scheme is None:
            resolved_host = None

        normalized_host = None
        if resolved_host:
            host_for_validation = resolved_host
            if re.match(r'^https?://', host_for_validation, re.IGNORECASE) is None and resolved_scheme is not None:
                host_for_validation = resolved_scheme + resolved_host
            normalized_host = Filter.host(host_for_validation)

        return {
            'method': method,
            'headers': headers,
            'cookies': cookies,
            'body': body,
            'host': normalized_host,
            'port': resolved_port,
            'scheme': resolved_scheme,
            'path': request_path,
            'prefix': Filter._raw_request_prefix(request_path),
            'target_source': Filter._raw_request_target_source(normalized_host, resolved_scheme, resolved_port),
        }

    @staticmethod
    def _split_host_and_port(value):
        """Split host header into host and port parts."""

        raw = str(value).strip()
        if ':' in raw:
            host, port = raw.rsplit(':', 1)
            if port.isdigit():
                return host.strip(), int(port)
        return raw, None

    @staticmethod
    def _raw_request_prefix(path):
        """Derive scan prefix from request path."""

        parsed_path = helper.parse_url('http://raw.local' + (path if str(path).startswith('/') else '/' + str(path))).path
        if not parsed_path or parsed_path == '/':
            return ''

        if parsed_path.endswith('/'):
            prefix = parsed_path
        else:
            prefix = parsed_path.rsplit('/', 1)[0] + '/'

        return unquote(prefix.lstrip('/'))

    @staticmethod
    def _raw_request_target_source(host, scheme, port):
        """Build readable target source string for raw requests."""

        if host is None or scheme is None:
            return None

        source = '{0}{1}'.format(scheme, host)
        if port is not None:
            source += ':{0}'.format(port)
        return source

    @staticmethod
    def host(hostname):
        """
        Input `host` param filter
        :param str hostname: input hostname
        :raise FilterError
        :return: str
        """

        if not re.search('http', hostname, re.IGNORECASE):
            if re.search('https', hostname, re.IGNORECASE):
                hostname = "https://" + hostname
            else:
                hostname = "http://" + hostname

        hostname = helper.parse_url(hostname).netloc
        regex = re.compile(Filter.URL_REGEX, re.UNICODE)

        if not regex.match(hostname):
            try:
                hostname = helper.decode_hostname(hostname)
            except UnicodeError as error:
                raise FilterError("\"{0}\" is invalid host. {1}".format(hostname, str(error)))
            if not regex.match(hostname):
                raise FilterError("\"{0}\" is invalid host. Use ip, http(s) or just hostname".format(hostname))
        return hostname

    @staticmethod
    def proxy(proxyaddress):
        """
        Input `proxy` param filter
        :param str proxyaddress: input proxy server address
        :raise FilterError
        :return: str
        """

        proxy = helper.parse_url(proxyaddress)

        if proxy.scheme not in ['http', 'https', 'socks4', 'socks5'] or None is proxy.port:
            raise FilterError("\"{0}\" is invalid proxy in --proxy. Use scheme:ip:port format".format(proxyaddress))
        return proxyaddress

    @staticmethod
    def scan(choose):
        """
        Input `scan` type filter
        :param str choose: preferred scan type
        :return: str
        """

        if choose not in ['directories', 'subdomains']:
            choose = 'directories'
        return choose

    @staticmethod
    def status_ranges(value, key='--status'):
        """Validate status filters supporting exact codes and ranges."""

        items = []
        for item in Filter._split_csv(value):
            if not Filter.STATUS_RANGE_REGEX.match(item):
                raise FilterError('"{0}" is invalid value in {1}. Use 200,403 or 200-299 format'.format(item, key))

            if '-' in item:
                start, end = [int(chunk) for chunk in item.split('-', 1)]
                if start > end:
                    raise FilterError('"{0}" is invalid range in {1}. Start must be less than or equal to end'.format(item, key))
                if start < 100 or end > 599:
                    raise FilterError('"{0}" is invalid range in {1}. Use HTTP status codes from 100 to 599'.format(item, key))
            else:
                code = int(item)
                if code < 100 or code > 599:
                    raise FilterError('"{0}" is invalid value in {1}. Use HTTP status codes from 100 to 599'.format(item, key))

            items.append(item)

        return items

    @staticmethod
    def integer_values(value, key='--size'):
        """Validate a CSV list of non-negative integers."""

        items = []
        for item in Filter._split_csv(value):
            if not item.isdigit():
                raise FilterError('"{0}" is invalid value in {1}. Use non-negative integer bytes'.format(item, key))
            items.append(str(int(item)))
        return items

    @staticmethod
    def integer_ranges(value, key='--size-range'):
        """Validate a CSV list of non-negative integer ranges."""

        items = []
        for item in Filter._split_csv(value):
            if not Filter.INTEGER_RANGE_REGEX.match(item) or '-' not in item:
                raise FilterError('"{0}" is invalid value in {1}. Use 0-256,1024-2048 format'.format(item, key))
            start, end = [int(chunk) for chunk in item.split('-', 1)]
            if start > end:
                raise FilterError('"{0}" is invalid range in {1}. Start must be less than or equal to end'.format(item, key))
            items.append('{0}-{1}'.format(start, end))
        return items

    @staticmethod
    def regex_values(value, key='--regex'):
        """Validate regex patterns without mutating their original text."""

        items = Filter.text_values(value)

        for item in items:
            try:
                re.compile(item)
            except re.error as error:
                raise FilterError('"{0}" is invalid regex in {1}. {2}'.format(item, key, error))

        return items

    @staticmethod
    def text_values(value):
        """Normalize text filters passed via append or direct strings."""

        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]

        text = str(value).strip()
        if not text:
            return []
        return [text]

    @staticmethod
    def non_negative_int(value, key='--value'):
        """Validate a non-negative integer option."""

        try:
            value = int(value)
        except (TypeError, ValueError):
            raise FilterError('{0} must be a non-negative integer'.format(key))

        if value < 0:
            raise FilterError('{0} must be a non-negative integer'.format(key))

        return value

    @staticmethod
    def _split_csv(value):
        """Normalize comma-separated input into a clean list."""

        if value is None:
            return []

        if isinstance(value, list):
            items = []
            for entry in value:
                items.extend([item.strip() for item in str(entry).split(',') if item.strip()])
            return items

        return [item.strip() for item in str(value).split(',') if item.strip()]

    @staticmethod
    def session_file(value, key='--session-file'):
        """
        Normalize session file path.

        :param str value:
        :param str key:
        :return: str
        """

        if value is None:
            raise FilterError('{0} requires a file path'.format(key))

        filepath = str(value).strip()
        if not filepath:
            raise FilterError('{0} requires a non-empty file path'.format(key))

        return os.path.abspath(filepath)

    @staticmethod
    def positive_int(value, key='--value'):
        """
        Validate a positive integer option.

        :param value:
        :param str key:
        :return: int
        """

        try:
            value = int(value)
        except (TypeError, ValueError):
            raise FilterError('{0} must be a positive integer'.format(key))

        if value <= 0:
            raise FilterError('{0} must be a positive integer'.format(key))

        return value