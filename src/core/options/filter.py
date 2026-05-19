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

    Development: Stanislav WEB
"""

import ipaddress
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
    IPV4_CIDR_REGEX = re.compile(r'^\d{1,3}(?:\.\d{1,3}){3}/\d{1,3}$')
    IPV4_RANGE_REGEX = re.compile(r'^(\d{1,3}(?:\.\d{1,3}){3})-(\d{1,3}(?:\.\d{1,3}){3})$')
    TARGET_EXPANSION_LIMIT = 65536
    HEADER_NAME_REGEX = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")
    RECURSIVE_EXTENSION_REGEX = re.compile(r'^[A-Za-z0-9][A-Za-z0-9+_-]*$')

    TRANSPORTS = ('direct', 'proxy', 'openvpn', 'wireguard')
    TRANSPORT_ROTATES = ('none', 'per-target')
    PROXY_ROTATIONS = ('random', 'sequential')
    METHODS = ('HEAD', 'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS')
    VPN_TRANSPORTS = ('openvpn', 'wireguard')
    HEADER_BYPASS_PROFILES = ('safe', 'offensive')
    SCAN_REPORTS = ('json', 'std', 'txt', 'csv', 'html', 'sqlite', 'sarif')
    DIFF_REPORTS = ('std', 'json')
    PROXY_SCHEMES = ('http', 'https', 'socks4', 'socks5', 'socks5h')

    @staticmethod
    def filter(args):
        """
        Filter options
        :param dict args:
        :return: dict
        """

        filtered = {}

        if Filter._split_csv(args.get('extensions')) and Filter._split_csv(args.get('ignore_extensions')):
            raise FilterError('--extensions and --ignore-extensions cannot be used together')

        if args.get('diff') is not None:
            if args.get('host') or args.get('hostlist') or args.get('stdin') is True \
                    or args.get('raw_request') or args.get('session_load'):
                raise FilterError('--diff cannot be used together with scan target or session options')

            diff_value = Filter.optional_text(args.get('diff'), key='--diff')
            if diff_value is None:
                raise FilterError('--diff requires old.sqlite:new.sqlite or old.json:new.json')

            filtered = {'diff': diff_value}

            if args.get('reports') is not None:
                filtered['reports'] = Filter.diff_reports(args.get('reports'), key='--reports')

            if args.get('reports_dir') is not None:
                filtered['reports_dir'] = Filter.optional_path(args.get('reports_dir'), key='--reports-dir')

            if args.get('debug') is not None:
                filtered['debug'] = Filter.debug_level(args.get('debug'), key='--debug')

            return filtered

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

            if args.get('waf_detect') is not None:
                filtered['waf_detect'] = Filter.bool_option(args.get('waf_detect'), key='--waf-detect')

            if args.get('waf_safe_mode') is not None:
                filtered['waf_safe_mode'] = Filter.bool_option(args.get('waf_safe_mode'), key='--waf-safe-mode')

            if args.get('waf_guard') is not None:
                filtered['waf_guard'] = Filter.bool_option(args.get('waf_guard'), key='--waf-guard')

            if args.get('waf_guard_after') is not None:
                filtered['waf_guard_after'] = Filter.positive_int(
                    args.get('waf_guard_after'),
                    key='--waf-guard-after'
                )

            if args.get('waf_guard_threshold') is not None:
                filtered['waf_guard_threshold'] = Filter.ratio_float(
                    args.get('waf_guard_threshold'),
                    key='--waf-guard-threshold'
                )

            if args.get('header_bypass') is True:
                filtered['header_bypass'] = True

            if args.get('header_bypass_profile') is not None:
                filtered['header_bypass_profile'] = Filter.header_bypass_profile(
                    args.get('header_bypass_profile'),
                    key='--header-bypass-profile'
                )

            if args.get('header_bypass_headers') is not None:
                filtered['header_bypass_headers'] = Filter.header_names(
                    args.get('header_bypass_headers'),
                    key='--header-bypass-headers'
                )

            if args.get('header_bypass_ips') is not None:
                filtered['header_bypass_ips'] = Filter.header_values(
                    args.get('header_bypass_ips'),
                    key='--header-bypass-ips'
                )

            if args.get('header_bypass_status') is not None:
                filtered['header_bypass_status'] = Filter.status_ranges(
                    args.get('header_bypass_status'),
                    key='--header-bypass-status'
                )

            if args.get('header_bypass_limit') is not None:
                filtered['header_bypass_limit'] = Filter.non_negative_int(
                    args.get('header_bypass_limit'),
                    key='--header-bypass-limit'
                )

            if args.get('fail_on_bucket') is not None:
                filtered['fail_on_bucket'] = Filter.bucket_values(
                    args.get('fail_on_bucket'),
                    key='--fail-on-bucket'
                )

            if args.get('debug') is not None:
                filtered['debug'] = Filter.debug_level(args.get('debug'), key='--debug')

            if args.get('reports') is not None:
                filtered['reports'] = Filter.scan_reports(args.get('reports'), key='--reports')

            if args.get('reports_dir') is not None:
                filtered['reports_dir'] = Filter.optional_path(args.get('reports_dir'), key='--reports-dir')

            if args.get('threads') is not None:
                filtered['threads'] = Filter.positive_int(args.get('threads'), key='--threads')

            if args.get('delay') is not None:
                filtered['delay'] = Filter.non_negative_float(args.get('delay'), key='--delay')

            if args.get('port') is not None:
                filtered['port'] = Filter.port(args.get('port'), key='--port')

            if args.get('header') is not None:
                filtered['header'] = Filter.request_headers(args.get('header'), key='--header')

            if args.get('method') is not None:
                filtered['method'] = Filter.method(args.get('method'), key='--method')

            if args.get('recursive') is True:
                filtered['recursive'] = True

            if args.get('recursive_depth') is not None:
                filtered['recursive_depth'] = Filter.positive_int(
                    args.get('recursive_depth'),
                    key='--recursive-depth'
                )

            if args.get('recursive_status') is not None:
                filtered['recursive_status'] = Filter.recursive_statuses(
                    args.get('recursive_status'),
                    key='--recursive-status'
                )

            if args.get('recursive_exclude') is not None:
                filtered['recursive_exclude'] = Filter.recursive_extensions(
                    args.get('recursive_exclude'),
                    key='--recursive-exclude'
                )

            if args.get('tls_legacy') is True:
                filtered['tls_legacy'] = True

            if args.get('auto_calibrate') is True:
                filtered['auto_calibrate'] = True

            if args.get('calibration_samples') is not None:
                filtered['calibration_samples'] = Filter.positive_int(
                    args.get('calibration_samples'),
                    key='--calibration-samples'
                )

            if args.get('calibration_threshold') is not None:
                filtered['calibration_threshold'] = Filter.ratio_float(
                    args.get('calibration_threshold'),
                    key='--calibration-threshold'
                )

            if args.get('transport') is not None:
                filtered['transport'] = Filter.transport(args.get('transport'), key='--transport')

            if args.get('transport_profile') is not None:
                filtered['transport_profile'] = Filter.optional_path(
                    args.get('transport_profile'),
                    key='--transport-profile'
                )

            if args.get('transport_profiles') is not None:
                filtered['transport_profiles'] = Filter.optional_path(
                    args.get('transport_profiles'),
                    key='--transport-profiles'
                )

            if args.get('transport_rotate') is not None:
                filtered['transport_rotate'] = Filter.transport_rotate(
                    args.get('transport_rotate'),
                    key='--transport-rotate'
                )

            if args.get('transport_timeout') is not None:
                filtered['transport_timeout'] = Filter.positive_int(
                    args.get('transport_timeout'),
                    key='--transport-timeout'
                )

            if args.get('transport_healthcheck_url') is not None:
                filtered['transport_healthcheck_url'] = Filter.optional_text(
                    args.get('transport_healthcheck_url'),
                    key='--transport-healthcheck-url'
                )

            if args.get('transport_bin') is not None:
                filtered['transport_bin'] = Filter.optional_text(
                    args.get('transport_bin'),
                    key='--transport-bin'
                )

            if args.get('openvpn_auth') is not None:
                filtered['openvpn_auth'] = Filter.optional_path(
                    args.get('openvpn_auth'),
                    key='--openvpn-auth'
                )

            if filtered.get('waf_safe_mode') is True or filtered.get('waf_guard') is True:
                filtered['waf_detect'] = True

            Filter.validate_proxy_options(filtered)
            Filter.validate_transport_options(filtered)

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
            elif key in ['reports']:
                filtered[key] = Filter.scan_reports(value, key='--reports')
            elif key in ['reports_dir']:
                filtered[key] = Filter.optional_path(value, key='--reports-dir')
            elif key in ['threads']:
                filtered[key] = Filter.positive_int(value, key='--threads')
            elif key in ['header']:
                filtered[key] = Filter.request_headers(value, key='--header')
            elif key in ['method']:
                filtered[key] = Filter.method(value, key='--method')
            elif key in ['port']:
                filtered[key] = Filter.port(value, key='--port')
            elif key in ['recursive_depth']:
                filtered[key] = Filter.positive_int(value, key='--recursive-depth')
            elif key in ['recursive_status']:
                filtered[key] = Filter.recursive_statuses(value, key='--recursive-status')
            elif key in ['recursive_exclude']:
                filtered[key] = Filter.recursive_extensions(value, key='--recursive-exclude')
            elif key in ['session_autosave_sec', 'session_autosave_items']:
                filtered[key] = Filter.positive_int(value, key='--{0}'.format(key.replace('_', '-')))
            elif 'proxy' == key:
                filtered[key] = Filter.proxy(value)
            elif key in ['proxy_rotation']:
                filtered[key] = Filter.proxy_rotation(value, key='--proxy-rotation')
            elif key in ['tls_legacy']:
                filtered[key] = value is True
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
            elif key in ['fail_on_bucket']:
                filtered[key] = Filter.bucket_values(value, key='--{0}'.format(key.replace('_', '-')))
            elif key in ['debug']:
                filtered[key] = Filter.debug_level(value, key='--debug')
            elif key in ['delay']:
                filtered[key] = Filter.non_negative_float(value, key='--delay')
            elif key in ['waf_detect', 'waf_safe_mode', 'waf_guard']:
                filtered[key] = Filter.bool_option(value, key='--{0}'.format(key.replace('_', '-')))
            elif key in ['waf_guard_after']:
                filtered[key] = Filter.positive_int(value, key='--{0}'.format(key.replace('_', '-')))
            elif key in ['waf_guard_threshold']:
                filtered[key] = Filter.ratio_float(value, key='--{0}'.format(key.replace('_', '-')))
            elif key in ['header_bypass_profile']:
                filtered[key] = Filter.header_bypass_profile(value, key='--{0}'.format(key.replace('_', '-')))
            elif key in ['header_bypass_headers']:
                filtered[key] = Filter.header_names(value, key='--{0}'.format(key.replace('_', '-')))
            elif key in ['header_bypass_ips']:
                filtered[key] = Filter.header_values(value, key='--{0}'.format(key.replace('_', '-')))
            elif key in ['header_bypass_status']:
                filtered[key] = Filter.status_ranges(value, key='--{0}'.format(key.replace('_', '-')))
            elif key in ['header_bypass_limit']:
                filtered[key] = Filter.non_negative_int(value, key='--{0}'.format(key.replace('_', '-')))
            elif key in ['calibration_samples']:
                filtered[key] = Filter.positive_int(value, key='--{0}'.format(key.replace('_', '-')))
            elif key in ['calibration_threshold']:
                filtered[key] = Filter.ratio_float(value, key='--{0}'.format(key.replace('_', '-')))
            elif key in ['retries']:
                filtered[key] = Filter.non_negative_int(value, key='--retries')
            elif key in ['retries_fail_streak']:
                filtered[key] = Filter.positive_int(value, key='--retries-fail-streak')
            elif key in ['transport']:
                filtered[key] = Filter.transport(value, key='--{0}'.format(key.replace('_', '-')))
            elif key in ['transport_rotate']:
                filtered[key] = Filter.transport_rotate(value, key='--{0}'.format(key.replace('_', '-')))
            elif key in ['transport_profile', 'transport_profiles', 'openvpn_auth']:
                filtered[key] = Filter.optional_path(value, key='--{0}'.format(key.replace('_', '-')))
            elif key in ['transport_timeout']:
                filtered[key] = Filter.positive_int(value, key='--{0}'.format(key.replace('_', '-')))
            elif key in ['transport_healthcheck_url', 'transport_bin']:
                filtered[key] = Filter.optional_text(value, key='--{0}'.format(key.replace('_', '-')))
            else:
                filtered[key] = value

        if raw_request is not None:
            if 'method' not in filtered and raw_request.get('method'):
                filtered['method'] = Filter.method(raw_request.get('method'), key='--raw-request method')

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

        if filtered.get('waf_safe_mode') is True or filtered.get('waf_guard') is True:
            filtered['waf_detect'] = True

        Filter.validate_proxy_options(filtered)
        Filter.validate_transport_options(filtered)

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

            for expanded_target in Filter._expand_target(cleaned):
                if expanded_target in seen:
                    continue

                host = Filter.host(expanded_target)
                scheme = Filter.scheme(expanded_target)
                targets.append({
                    'host': host,
                    'scheme': scheme,
                    'ssl': Filter.ssl(scheme),
                    'source': expanded_target,
                })
                seen.add(expanded_target)

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

        return list(stream.readlines())

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
    def _expand_target(value):
        """
        Expand supported batch target expressions.

        IPv4 CIDR and inclusive IPv4 ranges are expanded before normal host
        normalization. Plain URLs, domains and single IPs are returned as-is.

        :param str value:
        :raise FilterError:
        :return: list[str]
        """

        if Filter.IPV4_CIDR_REGEX.match(value):
            return Filter._expand_ipv4_cidr(value)

        range_match = Filter.IPV4_RANGE_REGEX.match(value)
        if range_match:
            return Filter._expand_ipv4_range(range_match.group(1), range_match.group(2))

        return [value]

    @staticmethod
    def _expand_ipv4_cidr(value):
        """
        Expand an IPv4 CIDR expression into host addresses.

        :param str value:
        :raise FilterError:
        :return: list[str]
        """

        try:
            network = ipaddress.ip_network(value, strict=False)
        except ValueError as error:
            raise FilterError('"{0}" is invalid IPv4 CIDR target. {1}'.format(value, error))

        if network.version != 4:
            raise FilterError('"{0}" is invalid target. Only IPv4 CIDR expansion is supported'.format(value))

        hosts_count = Filter._ipv4_network_hosts_count(network)
        Filter._validate_target_expansion_size(value, hosts_count)

        return [str(address) for address in network.hosts()]

    @staticmethod
    def _expand_ipv4_range(start_value, end_value):
        """
        Expand an inclusive IPv4 address range.

        :param str start_value:
        :param str end_value:
        :raise FilterError:
        :return: list[str]
        """

        try:
            start = ipaddress.ip_address(start_value)
            end = ipaddress.ip_address(end_value)
        except ValueError as error:
            raise FilterError('"{0}-{1}" is invalid IPv4 range target. {2}'.format(
                start_value,
                end_value,
                error
            ))

        if start.version != 4 or end.version != 4:
            raise FilterError('"{0}-{1}" is invalid target. Only IPv4 range expansion is supported'.format(
                start_value,
                end_value
            ))

        start_int = int(start)
        end_int = int(end)

        if start_int > end_int:
            raise FilterError('"{0}-{1}" is invalid IPv4 range target. Start must be less than or equal to end'.format(
                start_value,
                end_value
            ))

        count = end_int - start_int + 1
        Filter._validate_target_expansion_size('{0}-{1}'.format(start_value, end_value), count)

        return [str(ipaddress.ip_address(address)) for address in range(start_int, end_int + 1)]

    @staticmethod
    def _ipv4_network_hosts_count(network):
        """
        Return the amount of addresses generated by network.hosts().

        :param ipaddress.IPv4Network network:
        :return: int
        """

        if network.prefixlen == 32:
            return 1

        if network.prefixlen == 31:
            return 2

        return max(int(network.num_addresses) - 2, 0)

    @staticmethod
    def _validate_target_expansion_size(value, count):
        """
        Guard against accidental huge batch expansions.

        :param str value:
        :param int count:
        :raise FilterError:
        :return: None
        """

        if count <= 0:
            raise FilterError('"{0}" produced no scan targets'.format(value))

        if count > Filter.TARGET_EXPANSION_LIMIT:
            raise FilterError(
                '"{0}" expands to {1} targets. Maximum supported expansion is {2}'.format(
                    value,
                    count,
                    Filter.TARGET_EXPANSION_LIMIT
                )
            )

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

        method = Filter.method(request_line_parts[0], key='--raw-request method')
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
                return host.strip(), Filter.port(port, key='raw request Host port')
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
    def port(value, key='--port'):
        """Validate a TCP port value.

        :param value: input port value
        :param str key: CLI option name
        :raise FilterError:
        :return: normalized port
        :rtype: int
        """

        try:
            port = int(value)
        except (TypeError, ValueError):
            raise FilterError('{0} must be an integer from 1 to 65535'.format(key))

        if port < 1 or port > 65535:
            raise FilterError('{0} must be an integer from 1 to 65535'.format(key))

        return port

    @staticmethod
    def method(value, key='--method'):
        """Validate and normalize an HTTP request method.

        :param value: input method value
        :param str key: CLI option name
        :raise FilterError:
        :return: normalized uppercase method
        :rtype: str
        """

        if value is None:
            raise FilterError('{0} must be one of: {1}'.format(key, ', '.join(Filter.METHODS)))

        method = str(value).strip().upper()

        if not method or '\r' in method or '\n' in method or method not in Filter.METHODS:
            raise FilterError('{0} must be one of: {1}'.format(key, ', '.join(Filter.METHODS)))

        return method

    @staticmethod
    def proxy(proxyaddress):
        """
        Input `proxy` param filter
        :param str proxyaddress: input proxy server address
        :raise FilterError
        :return: str
        """

        proxy = helper.parse_url(proxyaddress)

        if proxy.scheme not in Filter.PROXY_SCHEMES or None is proxy.port:
            raise FilterError("\"{0}\" is invalid proxy in --proxy. Use scheme:ip:port format".format(proxyaddress))
        return proxyaddress

    @staticmethod
    def proxy_rotation(value, key='--proxy-rotation'):
        """Validate proxy-list rotation policy.

        :param value: input proxy rotation value
        :param str key: CLI option name
        :raise FilterError:
        :return: normalized proxy rotation policy
        :rtype: str
        """

        value = 'random' if value is None else str(value).strip().lower()

        if value in ['', 'null']:
            value = 'random'

        if value not in Filter.PROXY_ROTATIONS:
            raise FilterError('{0} must be one of: {1}'.format(key, ', '.join(Filter.PROXY_ROTATIONS)))

        return value

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
    def request_headers(value, key='--header'):
        """Validate and normalize one or more custom HTTP request headers.

        :param value: Header value or list of header values in "Name: value" format
        :param str key: CLI option name
        :raise FilterError:
        :return: normalized header list
        :rtype: list[str]
        """

        if value is None:
            return []

        raw_headers = value if isinstance(value, list) else [value]
        headers = []

        for raw_header in raw_headers:
            header = str(raw_header).strip()

            if not header:
                raise FilterError('{0} requires a non-empty HTTP header in "Name: value" format'.format(key))

            if '\r' in header or '\n' in header:
                raise FilterError('"{0}" is invalid value in {1}. Header injection is not allowed'.format(
                    raw_header,
                    key,
                ))

            if ':' not in header:
                raise FilterError('"{0}" is invalid value in {1}. Use "Name: value" format'.format(
                    raw_header,
                    key,
                ))

            header_name, header_value = header.split(':', 1)
            header_name = header_name.strip()
            header_value = header_value.strip()

            if not header_name or not Filter.HEADER_NAME_REGEX.match(header_name):
                raise FilterError('"{0}" is invalid header name in {1}'.format(header_name, key))

            if not header_value:
                raise FilterError('"{0}" is invalid value in {1}. Header value cannot be empty'.format(
                    raw_header,
                    key,
                ))

            headers.append('{0}: {1}'.format(header_name, header_value))

        return headers

    @staticmethod
    def header_bypass_profile(value, key='--header-bypass-profile'):
        """Validate header-bypass profile name."""

        profile = 'safe' if value is None else str(value).strip().lower()

        if profile in ['', 'none', 'null']:
            profile = 'safe'

        if profile not in Filter.HEADER_BYPASS_PROFILES:
            raise FilterError('{0} must be one of: {1}'.format(
                key,
                ', '.join(Filter.HEADER_BYPASS_PROFILES)
            ))

        return profile

    @staticmethod
    def header_names(value, key='--headers'):
        """Validate comma-separated HTTP header names."""

        headers = []
        seen = set()

        for item in Filter._split_csv(value):
            header = str(item).strip()
            header_key = header.lower()

            if not Filter.HEADER_NAME_REGEX.match(header):
                raise FilterError('"{0}" is invalid value in {1}. Use comma-separated HTTP header names'.format(
                    item,
                    key
                ))

            if header_key in seen:
                continue

            headers.append(header)
            seen.add(header_key)

        if len(headers) <= 0:
            raise FilterError('{0} requires at least one HTTP header name'.format(key))

        return headers

    @staticmethod
    def header_values(value, key='--header-values'):
        """Validate comma-separated header values without allowing header injection payloads."""

        values = []
        seen = set()

        for item in Filter._split_csv(value):
            header_value = str(item).strip()

            if not header_value or '\r' in header_value or '\n' in header_value:
                raise FilterError('"{0}" is invalid value in {1}. Use comma-separated safe header values'.format(
                    item,
                    key
                ))

            if header_value in seen:
                continue

            values.append(header_value)
            seen.add(header_value)

        if len(values) <= 0:
            raise FilterError('{0} requires at least one header value'.format(key))

        return values

    @staticmethod
    def bucket_values(value, key='--bucket'):
        """Normalize comma-separated result bucket names."""

        buckets = []
        seen = set()

        for item in Filter._split_csv(value):
            bucket = str(item).strip().lower()

            if not bucket:
                continue

            if not re.match(r'^[a-z][a-z0-9_-]*$', bucket):
                raise FilterError('"{0}" is invalid value in {1}. Use comma-separated bucket names'.format(item, key))

            if bucket in seen:
                continue

            buckets.append(bucket)
            seen.add(bucket)

        if len(buckets) <= 0:
            raise FilterError('{0} requires at least one bucket'.format(key))

        return buckets

    @staticmethod
    def scan_reports(value, key='--reports'):
        """Normalize scan output reports."""

        if value is None:
            return None

        reports = []
        seen = set()

        for item in Filter._split_csv(value):
            report = str(item).strip().lower()

            if report in ['', 'none', 'null']:
                continue

            if report not in Filter.SCAN_REPORTS:
                raise FilterError('{0} supports only: {1}'.format(
                    key,
                    ', '.join(Filter.SCAN_REPORTS),
                ))

            if report in seen:
                continue

            reports.append(report)
            seen.add(report)

        if len(reports) <= 0:
            return None

        return ','.join(reports)

    @staticmethod
    def diff_reports(value, key='--reports'):
        """Normalize diff output reports."""

        reports = []
        seen = set()

        for item in Filter._split_csv(value):
            report = str(item).strip().lower()
            if report not in Filter.DIFF_REPORTS:
                raise FilterError('{0} for --diff supports only: {1}'.format(
                    key,
                    ', '.join(Filter.DIFF_REPORTS),
                ))

            if report in seen:
                continue

            reports.append(report)
            seen.add(report)

        if len(reports) <= 0:
            raise FilterError('{0} requires at least one report: {1}'.format(
                key,
                ', '.join(Filter.DIFF_REPORTS),
            ))

        return ','.join(reports)

    @staticmethod
    def recursive_statuses(value, key='--recursive-status'):
        """Validate exact HTTP status codes allowed for recursive expansion."""

        statuses = []
        seen = set()

        for item in Filter._split_csv(value):
            token = str(item).strip()

            if not token.isdigit():
                raise FilterError(
                    '"{0}" is invalid value in {1}. Use comma-separated HTTP status codes from 100 to 599'.format(
                        item,
                        key
                    )
                )

            code = int(token)
            if code < 100 or code > 599:
                raise FilterError(
                    '"{0}" is invalid value in {1}. Use HTTP status codes from 100 to 599'.format(item, key)
                )

            normalized = str(code)
            if normalized in seen:
                continue

            statuses.append(normalized)
            seen.add(normalized)

        if len(statuses) <= 0:
            raise FilterError('{0} requires at least one HTTP status code'.format(key))

        return statuses

    @staticmethod
    def recursive_extensions(value, key='--recursive-exclude'):
        """Validate and normalize file extensions excluded from recursive expansion."""

        extensions = []
        seen = set()

        for item in Filter._split_csv(value):
            extension = str(item).strip().lstrip('.').lower()

            if not extension or not Filter.RECURSIVE_EXTENSION_REGEX.match(extension):
                raise FilterError(
                    '"{0}" is invalid value in {1}. Use comma-separated file extensions'.format(item, key)
                )

            if extension in seen:
                continue

            extensions.append(extension)
            seen.add(extension)

        return extensions

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
    def bool_option(value, key='--value'):
        """Validate and normalize bool-like CLI, wizard and session values.

        :param value: input value
        :param str key: CLI/config option name
        :raise FilterError:
        :return: normalized boolean
        :rtype: bool
        """

        if isinstance(value, bool):
            return value

        if value is None:
            return False

        token = str(value).strip().lower()
        if token in ['1', 'true', 'yes', 'on']:
            return True
        if token in ['0', 'false', 'no', 'off']:
            return False

        raise FilterError('{0} must be a boolean value'.format(key))

    @staticmethod
    def debug_level(value, key='--debug'):
        """Validate OpenDoor debug level."""

        try:
            value = int(value)
        except (TypeError, ValueError):
            raise FilterError('{0} must be one of: -1, 0, 1, 2, 3'.format(key))

        if value not in [-1, 0, 1, 2, 3]:
            raise FilterError('{0} must be one of: -1, 0, 1, 2, 3'.format(key))

        return value

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
    def non_negative_float(value, key='--value'):
        """Validate a non-negative floating-point option.

        :param value: input value
        :param str key: CLI option name
        :raise FilterError:
        :return: normalized non-negative float
        :rtype: float
        """

        try:
            value = float(value)
        except (TypeError, ValueError):
            raise FilterError('{0} must be a non-negative number'.format(key))

        if value < 0:
            raise FilterError('{0} must be a non-negative number'.format(key))

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
    def ratio_float(value, key='--value'):
        """
        Validate a ratio float option.

        :param value:
        :param str key:
        :return: float
        """

        try:
            value = float(value)
        except (TypeError, ValueError):
            raise FilterError('{0} must be a float from 0.01 to 1.0'.format(key))

        if value <= 0 or value > 1:
            raise FilterError('{0} must be a float from 0.01 to 1.0'.format(key))

        return value

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

    @staticmethod
    def optional_text(value, key='--value'):
        """
        Normalize optional text value.

        :param value:
        :param str key:
        :return: str | None
        """

        if value is None:
            return None

        if isinstance(value, list):
            if len(value) <= 0:
                return None
            value = value[0]

        value = str(value).strip()
        if value.lower() in ['', 'none', 'null']:
            return None

        return value

    @staticmethod
    def optional_path(value, key='--path'):
        """
        Normalize optional file path without reading it.

        :param value:
        :param str key:
        :return: str | None
        """

        value = Filter.optional_text(value, key=key)
        if value is None:
            return None

        return os.path.abspath(value)

    @staticmethod
    def transport(value, key='--transport'):
        """
        Validate network transport mode.

        :param value:
        :param str key:
        :return: str
        """

        value = 'direct' if value is None else str(value).strip().lower()

        if value in ['', 'none', 'null']:
            value = 'direct'

        if value not in Filter.TRANSPORTS:
            raise FilterError('{0} must be one of: {1}'.format(key, ', '.join(Filter.TRANSPORTS)))

        return value

    @staticmethod
    def transport_rotate(value, key='--transport-rotate'):
        """
        Validate transport rotation mode.

        :param value:
        :param str key:
        :return: str
        """

        value = 'none' if value is None else str(value).strip().lower()

        if value in ['', 'null']:
            value = 'none'

        if value not in Filter.TRANSPORT_ROTATES:
            raise FilterError('{0} must be one of: {1}'.format(key, ', '.join(Filter.TRANSPORT_ROTATES)))

        return value


    @staticmethod
    def validate_proxy_options(filtered):
        """Validate that only one proxy routing source is selected.

        :param dict filtered: filtered CLI options
        :raise FilterError:
        :return: None
        """

        selected = []

        if filtered.get('proxy'):
            selected.append('--proxy')

        if filtered.get('proxy_list'):
            selected.append('--proxy-list')

        if filtered.get('proxy_pool') is True:
            selected.append('--proxy-pool')

        if len(selected) > 1:
            raise FilterError('{0} cannot be used together. Select exactly one proxy source.'.format(
                ', '.join(selected)
            ))

        if filtered.get('proxy_rotation') is not None and not filtered.get('proxy_list'):
            raise FilterError('--proxy-rotation can be used only with --proxy-list')

    @staticmethod
    def validate_transport_options(filtered):
        """
        Validate cross-field network transport options.

        :param dict filtered:
        :raise FilterError:
        :return: None
        """

        transport = Filter.transport(filtered.get('transport'), key='--transport')
        rotate = Filter.transport_rotate(filtered.get('transport_rotate'), key='--transport-rotate')
        profile = filtered.get('transport_profile')
        profiles = filtered.get('transport_profiles')
        openvpn_auth = filtered.get('openvpn_auth')
        transport_bin = filtered.get('transport_bin')

        filtered['transport'] = transport
        filtered['transport_rotate'] = rotate

        if transport == 'direct':
            if rotate != 'none':
                raise FilterError('--transport-rotate can be used only with VPN transports')
            if profile is not None:
                raise FilterError('--transport-profile cannot be used with --transport direct')
            if profiles is not None:
                raise FilterError('--transport-profiles cannot be used with --transport direct')
            if openvpn_auth is not None:
                raise FilterError('--openvpn-auth cannot be used with --transport direct')
            if transport_bin is not None:
                raise FilterError('--transport-bin cannot be used with --transport direct')
            return

        if transport == 'proxy':
            if openvpn_auth is not None:
                raise FilterError('--openvpn-auth cannot be used with --transport proxy')
            if transport_bin is not None:
                raise FilterError('--transport-bin cannot be used with --transport proxy')
            if profile is not None:
                raise FilterError('--transport-profile cannot be used with --transport proxy')
            if profiles is not None:
                raise FilterError('--transport-profiles cannot be used with --transport proxy')
            if rotate == 'per-target':
                raise FilterError('--transport-rotate per-target is supported only for VPN transports')
            if not filtered.get('proxy') and not filtered.get('proxy_list') and filtered.get('proxy_pool') is not True:
                raise FilterError('--transport proxy requires --proxy, --proxy-list, or --proxy-pool')
            return

        if transport not in Filter.VPN_TRANSPORTS:
            return

        if openvpn_auth is not None and transport != 'openvpn':
            raise FilterError('--openvpn-auth can be used only with --transport openvpn')

        if rotate == 'per-target':
            if profiles is None:
                raise FilterError('--transport-profiles is required when --transport-rotate per-target is used')
            if profile is not None:
                raise FilterError('--transport-profile cannot be combined with --transport-rotate per-target')
        else:
            if profile is None:
                raise FilterError('--transport-profile is required for --transport {0}'.format(transport))
            if profiles is not None:
                raise FilterError('--transport-profiles requires --transport-rotate per-target')

        if profile is not None:
            Filter.validate_transport_profile_extension(transport, profile, key='--transport-profile')

    @staticmethod
    def validate_transport_profile_extension(transport, profile, key='--transport-profile'):
        """
        Validate profile extension for selected transport.

        :param str transport:
        :param str profile:
        :param str key:
        :raise FilterError:
        :return: None
        """

        lower_profile = str(profile).lower()

        if transport == 'openvpn' and lower_profile.endswith('.ovpn') is False:
            raise FilterError('{0} must point to *.ovpn when --transport openvpn is used'.format(key))

        if transport == 'wireguard' and lower_profile.endswith('.conf') is False:
            raise FilterError('{0} must point to *.conf when --transport wireguard is used'.format(key))
