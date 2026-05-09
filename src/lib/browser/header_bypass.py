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

    Development Team: Stanislav WEB
"""

from urllib.parse import quote, urlparse, urlunparse


class HeaderBypassProbe(object):
    """Build and score controlled header-injection bypass probes."""

    SAFE_PROFILE = 'safe'
    OFFENSIVE_PROFILE = 'offensive'
    PROFILES = (SAFE_PROFILE, OFFENSIVE_PROFILE)

    KNOWN_HEADERS = (
        'CF-Connecting-IP',
        'CF-Connecting_IP',
        'Client-IP',
        'Fastly-Client-IP',
        'Forwarded',
        'Front-End-Https',
        'Host',
        'Origin',
        'Proxy',
        'Proxy-Host',
        'Proxy-Url',
        'Real-Ip',
        'Referer',
        'Referrer',
        'Request-Uri',
        'True-Client-IP',
        'X-Appengine-User-IP',
        'X-Azure-ClientIP',
        'X-Client-IP',
        'X-Cluster-Client-IP',
        'X-Custom-IP-Authorization',
        'X-Envoy-External-Address',
        'X-Forwarded',
        'X-Forwarded-By',
        'X-Forwarded-For',
        'X-Forwarded-For-Original',
        'X-Forwarded-Host',
        'X-Forwarded-Proto',
        'X-Forwarded-Scheme',
        'X-Forwarded-Server',
        'X-Forwarded-SSL',
        'X-Host',
        'X-HTTP-DestinationURL',
        'X-HTTP-Host-Override',
        'X-HTTP-Method',
        'X-HTTP-Method-Override',
        'X-Method-Override',
        'X-Original-Forwarded-For',
        'X-Original-Remote-Addr',
        'X-Original-URL',
        'X-Originating-IP',
        'X-Proxy-Url',
        'X-ProxyUser-IP',
        'X-Real-IP',
        'X-Real-Ip',
        'X-Referrer',
        'X-Remote-Addr',
        'X-Remote-IP',
        'X-Rewrite-URL',
        'X-True-IP',
        'X-Url-Scheme',
        'X-WAP-Profile',
    )

    DEFAULT_HEADERS = (
        'X-Original-URL',
        'X-Rewrite-URL',
        'Request-Uri',
        'X-Custom-IP-Authorization',
        'X-Forwarded-For',
        'X-Forwarded-Host',
        'X-Forwarded-Proto',
        'X-Host',
        'X-HTTP-Host-Override',
        'X-Originating-IP',
        'X-Real-IP',
        'X-Remote-Addr',
        'X-Remote-IP',
        'X-Client-IP',
        'X-True-IP',
        'True-Client-IP',
        'Client-IP',
        'CF-Connecting-IP',
        'Real-Ip',
        'Forwarded',
        'Referer',
        'Referrer',
        'Origin',
    )

    OFFENSIVE_HEADERS = (
        'X-Original-Forwarded-For',
        'X-Forwarded-For-Original',
        'X-Forwarded-By',
        'X-ProxyUser-IP',
        'X-Cluster-Client-IP',
        'Fastly-Client-IP',
        'X-Azure-ClientIP',
        'X-Appengine-User-IP',
        'X-Envoy-External-Address',
        'X-Forwarded-Scheme',
        'X-Forwarded-SSL',
        'Front-End-Https',
        'X-Url-Scheme',
        'X-HTTP-Method',
        'X-HTTP-Method-Override',
        'X-Method-Override',
    )

    PATH_HEADERS = (
        'X-Original-URL',
        'X-Rewrite-URL',
        'X-HTTP-DestinationURL',
        'Request-Uri',
    )

    HOST_HEADERS = (
        'Host',
        'X-Forwarded-Host',
        'X-Forwarded-Server',
        'X-Host',
        'X-HTTP-Host-Override',
        'Forwarded',
        'Origin',
        'Referer',
        'Referrer',
        'X-Referrer',
    )

    TRUSTED_IP_HEADERS = (
        'CF-Connecting-IP',
        'CF-Connecting_IP',
        'Client-IP',
        'Fastly-Client-IP',
        'Real-Ip',
        'True-Client-IP',
        'X-Appengine-User-IP',
        'X-Azure-ClientIP',
        'X-Client-IP',
        'X-Cluster-Client-IP',
        'X-Custom-IP-Authorization',
        'X-Envoy-External-Address',
        'X-Forwarded',
        'X-Forwarded-For',
        'X-Forwarded-For-Original',
        'X-Original-Forwarded-For',
        'X-Original-Remote-Addr',
        'X-Originating-IP',
        'X-ProxyUser-IP',
        'X-Real-IP',
        'X-Real-Ip',
        'X-Remote-Addr',
        'X-Remote-IP',
        'X-True-IP',
    )

    METHOD_OVERRIDE_HEADERS = (
        'X-HTTP-Method',
        'X-HTTP-Method-Override',
        'X-Method-Override',
    )

    SCHEME_HEADERS = (
        'X-Forwarded-Proto',
        'X-Forwarded-Scheme',
        'X-Url-Scheme',
    )

    HTTPS_HEADERS = (
        'Front-End-Https',
        'X-Forwarded-SSL',
    )

    URL_HEADERS = (
        'Proxy',
        'Proxy-Host',
        'Proxy-Url',
        'X-Proxy-Url',
        'X-HTTP-DestinationURL',
        'X-WAP-Profile',
    )

    DEFAULT_IP_VALUES = (
        '127.0.0.1',
        'localhost',
        '10.0.0.1',
        '192.168.1.1',
    )

    OFFENSIVE_IP_VALUES = (
        '0.0.0.0', # nosec B104 - header-bypass payload value, not a bind/listen address
        '127.0.0.1',
        'localhost',
        '::1',
        '10.0.0.1',
        '10.0.0.2',
        '172.16.0.1',
        '192.168.1.1',
    )

    DEFAULT_STATUS_CODES = (401, 403)

    def __init__(self, config):
        """
        HeaderBypassProbe constructor.

        :param object config: browser configuration
        """

        self.__config = config

    @property
    def profile(self):
        """
        Return the active header-bypass profile.

        :return: safe or offensive profile name
        :rtype: str
        """

        profile = str(getattr(self.__config, 'header_bypass_profile', self.SAFE_PROFILE)).strip().lower()

        if profile not in self.PROFILES:
            return self.SAFE_PROFILE

        return profile

    @staticmethod
    def response_code(response_data):
        """
        Resolve HTTP status code from handled response data.

        :param tuple response_data: handled response data
        :return: int | None
        """

        try:
            return int(response_data[3])
        except (IndexError, TypeError, ValueError):
            return None

    @staticmethod
    def response_status(response_data):
        """
        Resolve normalized response status from handled response data.

        :param tuple response_data: handled response data
        :return: str
        """

        try:
            return str(response_data[0])
        except (IndexError, TypeError):
            return ''

    def is_waf_blocked_probe_candidate(self, response_data):
        """
        Check whether WAF detection should unlock bypass probes for this response.

        This covers WAF/challenge responses that do not use classic 401/403 codes,
        for example 301/302 challenge redirects.

        :param tuple response_data: handled response data
        :return: bool
        """

        if self.response_status(response_data) != 'blocked':
            return False

        return (
            getattr(self.__config, 'is_waf_safe_mode', False) is True
            or getattr(self.__config, 'is_waf_detect', False) is True
        )

    def should_probe(self, response_data):
        """
        Decide whether header bypass probes should run for the response.

        :param tuple response_data: handled response data
        :return: bool
        """

        if True is not getattr(self.__config, 'is_header_bypass', False):
            return False

        if self.response_code(response_data) in self.__config.header_bypass_status:
            return True

        return self.is_waf_blocked_probe_candidate(response_data)

    @staticmethod
    def __append_query(path, query):
        """
        Append an existing query string to a path value.

        :param str path: request path
        :param str query: request query
        :return: str
        """

        if query:
            return '{0}?{1}'.format(path, query)

        return path

    @staticmethod
    def __replace_path(parsed_url, path):
        """
        Rebuild URL with a mutated request path.

        :param urllib.parse.ParseResult parsed_url: parsed URL
        :param str path: mutated URL path
        :return: str
        """

        return urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            path,
            parsed_url.params,
            parsed_url.query,
            parsed_url.fragment,
        ))

    @staticmethod
    def __case_variant(path):
        """
        Build a conservative case-manipulation variant.

        :param str path: original request path
        :return: str | None
        """

        if path in ('', '/'):
            return None

        head, sep, tail = path.rpartition('/')
        if not tail:
            return None

        mutated_tail = tail[:1].upper() + tail[1:]
        if mutated_tail == tail:
            mutated_tail = tail.upper()

        if mutated_tail == tail:
            return None

        return '{0}{1}{2}'.format(head, sep, mutated_tail)

    @staticmethod
    def __encoded_segment_variant(path):
        """
        Build a conservative URL-encoded last-segment variant.

        :param str path: original request path
        :return: str | None
        """

        if path in ('', '/'):
            return None

        head, sep, tail = path.rpartition('/')
        if not tail:
            return None

        encoded_tail = quote(tail, safe='')
        if encoded_tail == tail:
            return None

        return '{0}{1}{2}'.format(head, sep, encoded_tail)

    @staticmethod
    def __encoded_first_character_variant(path):
        """
        Build a URL-encoded first-character variant for the last path segment.

        :param str path: original request path
        :return: str | None
        """

        if path in ('', '/'):
            return None

        head, sep, tail = path.rpartition('/')
        if not tail:
            return None

        encoded_tail = '%{0:02x}{1}'.format(ord(tail[:1]), tail[1:])

        return '{0}{1}{2}'.format(head, sep, encoded_tail)

    @staticmethod
    def __matrix_parameter_variant(path):
        """
        Build a matrix-parameter variant for the last path segment.

        :param str path: original request path
        :return: str | None
        """

        if path in ('', '/') or path.endswith(';'):
            return None

        return path.rstrip('/') + ';'

    def build_header_variants(self, url):
        """
        Build deterministic header variants for one blocked URL.

        :param str url: blocked target URL
        :return: list[dict]
        """

        variants = []
        seen = set()
        parsed = urlparse(url)
        path = parsed.path or '/'
        path_with_query = self.__append_query(path, parsed.query)

        origin = '{0}://{1}'.format(parsed.scheme, parsed.netloc)
        full_url = parsed.geturl()
        headers = self.__config.header_bypass_headers
        ip_values = self.__config.header_bypass_ips
        profile = self.profile

        def add(name, value):
            """
            Add unique header variant.

            :param str name: header name
            :param str value: header value
            :return: None
            """

            key = (str(name).lower(), str(value))
            if key in seen:  # pragma: no cover - defensive duplicate guard.
                return

            seen.add(key)
            item = {'header': str(name), 'value': str(value)}
            if profile != self.SAFE_PROFILE:
                item['profile'] = profile
            variants.append(item)

        for header in headers:
            if header in self.PATH_HEADERS:
                add(header, path_with_query)
                add(header, '/')
                continue

            if header == 'Forwarded':
                for ip in ip_values:
                    add(header, 'for={0};host={1};proto={2}'.format(ip, parsed.netloc, parsed.scheme))
                continue

            if header in self.METHOD_OVERRIDE_HEADERS:
                add(header, 'GET')
                add(header, 'HEAD')
                continue

            if header in self.SCHEME_HEADERS:
                add(header, parsed.scheme or 'https')
                add(header, 'https')
                continue

            if header in self.HTTPS_HEADERS:
                add(header, 'on')
                add(header, '1')
                continue

            if header in self.TRUSTED_IP_HEADERS:
                for ip in ip_values:
                    add(header, ip)
                continue

            if header in ('Origin',):
                add(header, origin)
                continue

            if header in ('Referer', 'Referrer', 'X-Referrer'):
                add(header, full_url)
                add(header, origin)
                continue

            if header in self.HOST_HEADERS:
                add(header, parsed.netloc)
                add(header, 'localhost')
                continue

            if header in self.URL_HEADERS:
                add(header, full_url)
                add(header, origin)
                continue

            add(header, path_with_query)

        return variants

    def build_path_variants(self, url):
        """
        Build deterministic path-manipulation variants for one blocked URL.

        :param str url: blocked target URL
        :return: list[dict]
        """

        variants = []
        seen = set()
        parsed = urlparse(url)
        path = parsed.path or '/'

        def add(name, mutated_path):
            """
            Add unique path variant.

            :param str name: variant name
            :param str mutated_path: mutated request path
            :return: None
            """

            if not mutated_path or mutated_path == path:
                return

            mutated_url = self.__replace_path(parsed, mutated_path)
            key = (name, mutated_url)
            if key in seen:  # pragma: no cover - defensive duplicate guard.
                return

            seen.add(key)
            item = {
                'type': 'path',
                'variant': name,
                'url': mutated_url,
                'value': self.__append_query(mutated_path, parsed.query),
            }
            if self.profile != self.SAFE_PROFILE:
                item['profile'] = self.profile
            variants.append(item)

        if path != '/' and not path.endswith('/'):
            add('trailing-slash', path + '/')

        if path.startswith('/') and not path.startswith('//'):
            add('double-leading-slash', '/' + path)

        if path != '/' and not path.endswith('/.'):
            add('dot-segment', path.rstrip('/') + '/.')

        if path != '/' and not path.endswith('/%2e'):
            add('encoded-dot-segment', path.rstrip('/') + '/%2e')

        if path != '/' and not path.endswith(';/'):
            add('semicolon-suffix', path.rstrip('/') + ';/')

        matrix_variant = self.__matrix_parameter_variant(path)
        if matrix_variant is not None:
            add('matrix-parameter', matrix_variant)

        if path != '/' and not path.endswith('//'):
            add('duplicate-trailing-slash', path.rstrip('/') + '//')

        if path != '/' and not path.lower().endswith('%2f'):
            add('encoded-trailing-slash', path.rstrip('/') + '%2f')

        if path != '/' and not path.lower().endswith('%252f'):
            add('double-encoded-trailing-slash', path.rstrip('/') + '%252f')

        case_variant = self.__case_variant(path)
        if case_variant is not None:
            add('case-variation', case_variant)

        encoded_variant = self.__encoded_segment_variant(path)
        if encoded_variant is not None:
            add('url-encoded-segment', encoded_variant)

        encoded_first_character_variant = self.__encoded_first_character_variant(path)
        if encoded_first_character_variant is not None:
            add('url-encoded-first-character', encoded_first_character_variant)

        return variants

    def build_variants(self, url):
        """
        Build deterministic header and path variants for one blocked URL.

        :param str url: blocked target URL
        :return: list[dict]
        """

        variants = self.build_header_variants(url)
        variants.extend(self.build_path_variants(url))

        limit = self.__config.header_bypass_limit
        if limit > 0:
            return variants[:limit]

        return variants

    @staticmethod
    def is_promising(base_response_data, probe_response_data):
        """
        Check if a probe response is worth reporting.

        :param tuple base_response_data: original blocked response data
        :param tuple probe_response_data: probe response data
        :return: bool
        """

        base_code = HeaderBypassProbe.response_code(base_response_data)
        probe_code = HeaderBypassProbe.response_code(probe_response_data)

        if probe_code is None or probe_code == base_code:
            return False

        if 200 <= probe_code <= 399:
            return True

        if base_code in HeaderBypassProbe.DEFAULT_STATUS_CODES and probe_code not in HeaderBypassProbe.DEFAULT_STATUS_CODES:
            return True

        return False

    @staticmethod
    def evidence(base_response_data, probe_response_data):
        """
        Build a deterministic evidence score and reason list.

        :param tuple base_response_data: original response data
        :param tuple probe_response_data: probe response data
        :return: score and reason list
        :rtype: tuple[int, list[str]]
        """

        base_status = HeaderBypassProbe.response_status(base_response_data)
        probe_status = HeaderBypassProbe.response_status(probe_response_data)
        base_code = HeaderBypassProbe.response_code(base_response_data)
        probe_code = HeaderBypassProbe.response_code(probe_response_data)
        reasons = []
        score = 0

        if base_code is not None and probe_code is not None and base_code != probe_code:
            reasons.append('status-code-changed')
            score += 25

        if base_status and probe_status and base_status != probe_status:
            reasons.append('bucket-changed')
            score += 20

        if probe_code is not None and 200 <= probe_code <= 399:
            reasons.append('probe-returned-success-or-redirect')
            score += 35

        if base_code in HeaderBypassProbe.DEFAULT_STATUS_CODES and probe_code not in HeaderBypassProbe.DEFAULT_STATUS_CODES:
            reasons.append('blocked-status-cleared')
            score += 25

        if base_status == 'blocked' and probe_status != 'blocked':
            reasons.append('waf-block-cleared')
            score += 25

        if score > 100:
            score = 100

        return score, reasons

    @staticmethod
    def metadata(variant, base_response_data, probe_response_data):
        """
        Build report metadata for a bypass probe.

        :param dict variant: header variant
        :param tuple base_response_data: original response data
        :param tuple probe_response_data: probe response data
        :return: dict
        """

        score, reasons = HeaderBypassProbe.evidence(base_response_data, probe_response_data)
        metadata = {
            'bypass': variant.get('type') or 'header',
            'bypass_profile': variant.get('profile') or HeaderBypassProbe.SAFE_PROFILE,
            'bypass_from_status': HeaderBypassProbe.response_status(base_response_data),
            'bypass_to_status': HeaderBypassProbe.response_status(probe_response_data),
            'bypass_from_code': HeaderBypassProbe.response_code(base_response_data),
            'bypass_to_code': HeaderBypassProbe.response_code(probe_response_data),
            'bypass_score': score,
            'bypass_reasons': reasons,
        }

        if metadata['bypass'] == 'path':
            metadata.update({
                'bypass_variant': variant.get('variant'),
                'bypass_value': variant.get('value'),
                'bypass_url': variant.get('url'),
            })
            return metadata

        metadata.update({
            'bypass_header': variant.get('header'),
            'bypass_value': variant.get('value'),
        })
        return metadata
