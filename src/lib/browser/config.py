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


class Config(object):

    """Config class"""

    BODY_REQUIRED_SNIFFERS = ('indexof', 'collation', 'stacktrace', 'secret', 'malware', 'shadow')
    DEFAULT_SOCKET_TIMEOUT = 10
    DEFAULT_MIN_THREADS = 1
    DEFAULT_MAX_THREADS = 25
    DEFAULT_DEBUG_LEVEL = 1
    DEFAULT_REPORT = 'std'
    DEFAULT_SCAN = 'directories'
    SUBDOMAINS_SCAN = 'subdomains'
    DEFAULT_SCHEME = 'http://'
    DEFAULT_HTTP_PORT = 80
    DEFAULT_SSL_PORT = 443
    DEFAULT_HTTP_METHOD = 'HEAD'
    DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36'

    def __init__(self, params):
        """
        Read filtered input params.

        :param dict params: input cli arguments
        """

        self._scan = params.get('scan')
        self._scheme = self._normalize_scheme(params.get('scheme'), params.get('ssl'))
        self._ssl = self._scheme == 'https://'
        self._host = params.get('host')
        self._session_save = params.get('session_save')
        self._session_load = params.get('session_load')
        self._session_autosave_sec = 20 if params.get('session_autosave_sec') is None else int(params.get('session_autosave_sec'))
        self._session_autosave_items = 200 if params.get('session_autosave_items') is None else int(params.get('session_autosave_items'))
        self._proxy = '' if params.get('proxy') is None else params.get('proxy')
        self._transport = 'direct' if params.get('transport') is None else params.get('transport')
        self._transport_profile = params.get('transport_profile')
        self._transport_profiles = params.get('transport_profiles')
        self._transport_rotate = 'none' if params.get('transport_rotate') is None else params.get('transport_rotate')
        self._transport_timeout = 30 if params.get('transport_timeout') is None else int(
            params.get('transport_timeout'))
        self._transport_healthcheck_url = params.get('transport_healthcheck_url')
        self._transport_bin = params.get('transport_bin')
        self._openvpn_auth = params.get('openvpn_auth')
        self._headers = params.get('header')
        self._cookies = params.get('cookie')
        self._raw_request = params.get('raw_request')
        self._request_body = params.get('request_body')
        self._accept_cookies = params.get('accept_cookies') is not None
        self._keep_alive = params.get('keep_alive') is True
        self._port = params.get('port')
        self._wordlist = params.get('wordlist')
        self._reports_dir = params.get('reports_dir')
        self._prefix = '' if params.get('prefix') is None else params.get('prefix')
        self._reports = self._normalize_csv(params.get('reports'))
        self._is_fingerprint = params.get('fingerprint') is True
        self._is_waf_safe_mode = params.get('waf_safe_mode') is True
        self._is_waf_detect = params.get('waf_detect') is True or self._is_waf_safe_mode is True
        self._is_header_bypass = params.get('header_bypass') is True
        self._header_bypass_profile = str(params.get('header_bypass_profile') or 'safe').strip().lower()
        self._header_bypass_headers = self._normalize_csv(params.get('header_bypass_headers'))
        self._header_bypass_ips = self._normalize_csv(params.get('header_bypass_ips'))
        self._header_bypass_status = self._normalize_csv(params.get('header_bypass_status'))
        self._header_bypass_limit = 32 if params.get('header_bypass_limit') is None else int(
            params.get('header_bypass_limit'))
        self._is_auto_calibrate = params.get('auto_calibrate') is True
        self._calibration_samples = 5 if params.get('calibration_samples') is None else int(
            params.get('calibration_samples'))
        self._calibration_threshold = 0.92 if params.get('calibration_threshold') is None else float(
            params.get('calibration_threshold'))
        self._extensions = self._normalize_csv(params.get('extensions'))
        self._ignore_extensions = self._normalize_csv(params.get('ignore_extensions'))
        self._is_recursive = params.get('recursive') is True
        self._recursive_depth = 1 if params.get('recursive_depth') is None else int(params.get('recursive_depth'))
        self._recursive_status = self._normalize_csv(params.get('recursive_status'))
        self._recursive_exclude = self._normalize_csv(params.get('recursive_exclude'))
        self._retries = self._normalize_retries(params.get('retries'))
        self._method = params.get('method')
        self._delay = params.get('delay')
        self._timeout = self.DEFAULT_SOCKET_TIMEOUT if params.get('timeout') is None else float(params.get('timeout'))
        self._debug = self.DEFAULT_DEBUG_LEVEL if params.get('debug') is None else params.get('debug')
        self._is_proxy_pool = params.get('proxy_pool') is True
        self._proxy_list = '' if 'proxy_list' not in params or params.get('proxy_list') is None else params.get('proxy_list')
        self._is_random_user_agent = params.get('random_agent')
        self._sniff = self._normalize_csv(params.get('sniff'))
        self._is_random_list = params.get('random_list') is True
        self._is_extension_filter = len(self._extensions or []) > 0
        self._is_ignore_extension_filter = len(self._ignore_extensions or []) > 0
        self._user_agent = self.DEFAULT_USER_AGENT
        self._threads = self.DEFAULT_MIN_THREADS if params.get('threads') is None else params.get('threads')
        self._include_status = self._normalize_csv(params.get('include_status'))
        self._exclude_status = self._normalize_csv(params.get('exclude_status'))
        self._exclude_size = self._normalize_csv(params.get('exclude_size'))
        self._exclude_size_range = self._normalize_csv(params.get('exclude_size_range'))
        self._match_text = self._normalize_csv(params.get('match_text'))
        self._exclude_text = self._normalize_csv(params.get('exclude_text'))
        self._match_regex = self._normalize_csv(params.get('match_regex'))
        self._exclude_regex = self._normalize_csv(params.get('exclude_regex'))
        self._min_response_length = params.get('min_response_length')
        self._max_response_length = params.get('max_response_length')

    @classmethod
    def _normalize_scheme(cls, scheme, ssl=False):
        """
        Normalize the target scheme and keep legacy ssl=True configs compatible.

        The public target protocol is the scheme. The ssl value is kept as a
        backward-compatible wizard/session input only and must not diverge from
        the effective request provider.

        :param str | None scheme: Configured URL scheme.
        :param bool ssl: Legacy SSL toggle from old wizard configs.
        :return: Normalized URL scheme.
        """

        normalized = cls.DEFAULT_SCHEME if scheme is None else str(scheme).strip().lower()

        if normalized in ['http', 'https']:
            normalized = normalized + '://'

        if ssl is True and normalized == cls.DEFAULT_SCHEME:
            return 'https://'

        return normalized

    @staticmethod
    def _normalize_retries(value):
        """Normalize urllib3 retry count.

        ``None`` keeps the historical disabled value used by direct unit-level
        config construction. CLI and wizard defaults still pass an explicit
        non-negative integer.

        :param int|str|bool|None value: Retry count value.
        :return: Non-negative retry count or False when unset.
        """

        if value is None:
            return False

        if value is False:
            return False

        retries = int(value)
        if retries < 0:
            raise ValueError('retries must be a non-negative integer')

        return retries

    @staticmethod
    def _normalize_csv(value):
        """
        Normalize comma separated values into a list.

        :param value:
        :return: list | None
        """

        if value is None:
            return None
        if isinstance(value, list):
            return list(value)
        return [item.strip() for item in str(value).split(',') if item.strip()]

    @staticmethod
    def _expand_numeric_tokens(values):
        """
        Expand response status tokens so ranges become flat string lists.

        :param list values:
        :return: list[str]
        """

        if values is None:
            return []

        expanded = []
        for item in values:
            item = str(item).strip()
            if not item:
                continue

            if '-' in item:
                start, end = [int(chunk) for chunk in item.split('-', 1)]
                expanded.extend([str(code) for code in range(start, end + 1)])
            else:
                expanded.append(str(int(item)))

        return expanded

    @staticmethod
    def _expand_integer_values(values):
        """
        Normalize exact integer filter values.

        :param list values:
        :return: list[int]
        """

        if values is None:
            return []

        return [int(str(item).strip()) for item in values if str(item).strip()]

    @staticmethod
    def _expand_integer_ranges(values):
        """
        Normalize inclusive integer range filters.

        :param list values:
        :return: list[tuple[int, int]]
        """

        if values is None:
            return []

        ranges = []
        for item in values:
            token = str(item).strip()
            if not token:
                continue

            start, end = [int(chunk) for chunk in token.split('-', 1)]
            ranges.append((start, end))

        return ranges

    @property
    def scan(self):
        """Scan property."""

        return self.DEFAULT_SCAN if self._scan is None else self._scan

    @scan.setter
    def scan(self, value):
        """scan param setter."""

        self._scan = value

    @property
    def scheme(self):
        """Protocol property."""

        return self._scheme

    @property
    def is_ssl(self):
        """If using ssl."""

        return self._ssl

    @property
    def prefix(self):
        """Paths prefix."""

        return self._prefix.lstrip('/')

    @property
    def host(self):
        """Hostname property."""

        return self._host

    @property
    def port(self):
        """Port property."""

        if self._ssl is True and self._port == self.DEFAULT_HTTP_PORT:
            self._port = self.DEFAULT_SSL_PORT
        return self._port

    @property
    def requested_method(self):
        """Requested scan method property."""

        return self.DEFAULT_HTTP_METHOD if self._method is None else str(self._method).upper()

    @property
    def selected_body_required_sniffers(self):
        """Selected sniffers that require response body."""

        if self.is_sniff is not True:
            return []

        return [sniffer for sniffer in self.sniffers if sniffer in self.BODY_REQUIRED_SNIFFERS]

    @property
    def selected_body_required_filters(self):
        """Selected response filters that require response body access."""

        selected = []
        mapping = {
            'match_text': '--match-text',
            'exclude_text': '--exclude-text',
            'match_regex': '--match-regex',
            'exclude_regex': '--exclude-regex',
        }

        for attr, label in mapping.items():
            values = getattr(self, attr)
            if len(values) > 0 and label not in selected:
                selected.append(label)

        return selected

    @property
    def method_override_items(self):
        """List body-dependent sniffers and filters that force GET."""

        items = list(self.selected_body_required_sniffers)

        for item in self.selected_body_required_filters:
            if item not in items:
                items.append(item)

        if self.is_auto_calibrate is True and '--auto-calibrate' not in items:
            items.append('--auto-calibrate')

        return items

    @property
    def method_override_warning(self):
        """Warn when requested HEAD must be overridden to GET."""

        items = self.method_override_items

        if self.requested_method != 'HEAD' or len(items) <= 0:
            return ''

        return 'HEAD overridden to GET because selected sniffers/filters require response body: {0}'.format(
            ', '.join(items)
        )

    @property
    def is_body_required_response_filtering(self):
        """If any selected response filter requires body content."""

        return len(self.selected_body_required_filters) > 0

    @property
    def method(self):
        """Scan method property."""

        if self.requested_method != 'HEAD':
            return self.requested_method

        if self.is_auto_calibrate is True:
            return 'GET'

        if self.is_body_required_response_filtering is True:
            return 'GET'

        if self.is_sniff is True:
            if len(self.sniffers) == 1 and self.sniffers[0] == 'file':
                return 'HEAD'
            return 'GET'

        return self.requested_method

    @property
    def delay(self):
        """Delay property."""

        if self._delay is None:
            self._delay = 0
        elif self._delay >= 1:
            self._delay = int(self._delay)
        return self._delay

    @property
    def timeout(self):
        """Timeout property."""

        return self._timeout

    @timeout.setter
    def timeout(self, value):
        """Timeout param setter."""

        self._timeout = float(value)
        return self._timeout

    @property
    def retries(self):
        """Retries property."""

        return self._retries

    @property
    def debug(self):
        """Debug level property."""

        return self._debug

    @property
    def proxy(self):
        """Standalone proxy property."""

        return self._proxy

    @property
    def is_proxy(self):
        """If proxy is available."""

        if self._is_proxy_pool is True:
            return True
        if self._proxy_list is not None and len(self._proxy_list) > 0:
            return True
        if self._proxy is not None and len(self._proxy) > 0:
            return True
        return False

    @property
    def is_fingerprint(self):
        """If heuristic fingerprinting is enabled."""

        return self._is_fingerprint

    @property
    def is_waf_detect(self):
        """If passive WAF / anti-bot detection is enabled."""

        return self._is_waf_detect

    @property
    def is_waf_safe_mode(self):
        """If WAF-aware safe mode is enabled."""

        return self._is_waf_safe_mode

    @property
    def is_auto_calibrate(self):
        """If smart auto-calibration is enabled."""

        return self._is_auto_calibrate

    @property
    def is_header_bypass(self):
        """If controlled header-injection bypass probes are enabled."""

        return self._is_header_bypass

    @property
    def header_bypass_profile(self):
        """Header-bypass probe profile."""

        from .header_bypass import HeaderBypassProbe

        if self._header_bypass_profile not in HeaderBypassProbe.PROFILES:
            return HeaderBypassProbe.SAFE_PROFILE

        return self._header_bypass_profile

    @property
    def header_bypass_headers(self):
        """Header names used by header-injection bypass probes."""

        if self._header_bypass_headers is None:
            from .header_bypass import HeaderBypassProbe
            headers = list(HeaderBypassProbe.DEFAULT_HEADERS)

            if self.header_bypass_profile == HeaderBypassProbe.OFFENSIVE_PROFILE:
                headers.extend([
                    header for header in HeaderBypassProbe.OFFENSIVE_HEADERS
                    if header.lower() not in {item.lower() for item in headers}
                ])

            return headers

        return [str(item).strip() for item in self._header_bypass_headers if str(item).strip()]

    @property
    def header_bypass_ips(self):
        """Trusted IP values used by header-injection bypass probes."""

        if self._header_bypass_ips is None:
            from .header_bypass import HeaderBypassProbe

            if self.header_bypass_profile == HeaderBypassProbe.OFFENSIVE_PROFILE:
                return list(HeaderBypassProbe.OFFENSIVE_IP_VALUES)

            return list(HeaderBypassProbe.DEFAULT_IP_VALUES)

        return [str(item).strip() for item in self._header_bypass_ips if str(item).strip()]

    @property
    def header_bypass_status(self):
        """HTTP status codes that trigger header-injection bypass probes."""

        if self._header_bypass_status is None:
            from .header_bypass import HeaderBypassProbe
            return list(HeaderBypassProbe.DEFAULT_STATUS_CODES)

        return [int(item) for item in self._expand_numeric_tokens(self._header_bypass_status)]

    @property
    def header_bypass_limit(self):
        """Maximum header-injection bypass variants per blocked URL."""

        return self._header_bypass_limit

    @property
    def calibration_samples(self):
        """Number of calibration probes."""

        return self._calibration_samples

    @property
    def calibration_threshold(self):
        """Auto-calibration match threshold."""

        return self._calibration_threshold

    @property
    def is_random_user_agent(self):
        """If ua randomizing is available."""

        return self._is_random_user_agent

    @property
    def is_sniff(self):
        """If sniffers are available."""

        return self._sniff is not None and len(self._sniff) > 0

    @property
    def is_shadow_sniff(self):
        """If active shadow-copy probing is enabled."""

        return self.is_sniff is True and 'shadow' in self.sniffers

    @property
    def sniffers(self):
        """Get sniffers."""

        return None if self._sniff is None else list(self._sniff)

    @property
    def is_response_filtering(self):
        """If any response filter is enabled."""

        return any([
            len(self.include_status) > 0,
            len(self.exclude_status) > 0,
            len(self.exclude_size) > 0,
            len(self.exclude_size_range) > 0,
            len(self.match_text) > 0,
            len(self.exclude_text) > 0,
            len(self.match_regex) > 0,
            len(self.exclude_regex) > 0,
            self.min_response_length is not None,
            self.max_response_length is not None,
        ])

    @property
    def is_random_list(self):
        """If scan lists randomize and are available."""

        return self._is_random_list

    @property
    def is_extension_filter(self):
        """If scan list filtered by extensions."""

        return self._is_extension_filter

    @property
    def is_ignore_extension_filter(self):
        """If a scan list filtered by ignore extensions."""

        return self._is_ignore_extension_filter

    @property
    def is_standalone_proxy(self):
        """If standalone proxy is available."""

        if self.is_proxy is True and len(self._proxy) > 0:
            self._proxy_list = ''
            return True
        return False

    @property
    def is_builtin_proxy_pool(self):
        """If built-in proxy pool is available."""

        return self._is_proxy_pool is True and len(self._proxy_list) <= 0

    @property
    def is_external_proxy_list(self):
        """If external proxy list is available."""

        return self._proxy_list is not None and len(self._proxy_list) > 0

    @property
    def proxy_list(self):
        """Proxy list property."""

        return self._proxy_list

    @property
    def is_external_wordlist(self):
        """If external word list is available."""

        return self._wordlist is not None

    @property
    def is_external_reports_dir(self):
        """If external reports directory selected."""

        return self._reports_dir is not None

    @property
    def reports_dir(self):
        """Get reports dir."""

        return self._reports_dir

    @property
    def wordlist(self):
        """Get external wordlist."""

        return self._wordlist

    @property
    def extensions(self):
        """Extensions resolver."""

        return [] if self._extensions is None else list(self._extensions)

    @property
    def ignore_extensions(self):
        """Ignore extensions resolver."""

        return [] if self._ignore_extensions is None else list(self._ignore_extensions)

    @property
    def is_recursive(self):
        """If recursive scan is enabled."""

        return self._is_recursive

    @property
    def recursive_depth(self):
        """Maximum recursive scan depth."""

        return self._recursive_depth

    @property
    def recursive_status(self):
        """Statuses allowed for recursive expansion."""

        return [] if self._recursive_status is None else [str(item).strip() for item in self._recursive_status if str(item).strip()]

    @property
    def recursive_exclude(self):
        """Extensions excluded from recursive expansion."""

        if self._recursive_exclude is None:
            return []

        return [
            str(item).strip().lstrip('.').lower()
            for item in self._recursive_exclude
            if str(item).strip()
        ]

    @property
    def transport(self):
        """Network transport mode."""

        return self._transport

    @property
    def transport_profile(self):
        """Single transport profile path."""

        return self._transport_profile

    @property
    def transport_profiles(self):
        """Transport profiles list path."""

        return self._transport_profiles

    @property
    def transport_rotate(self):
        """Transport rotation mode."""

        return self._transport_rotate

    @property
    def transport_timeout(self):
        """Transport command timeout."""

        return self._transport_timeout

    @property
    def transport_healthcheck_url(self):
        """Transport healthcheck URL."""

        return self._transport_healthcheck_url

    @property
    def transport_bin(self):
        """Transport executable path or command name."""

        return self._transport_bin

    @property
    def openvpn_auth(self):
        """OpenVPN auth-user-pass file path."""

        return self._openvpn_auth

    @property
    def reports(self):
        """Reports resolver."""

        reports = [] if self._reports is None else list(self._reports)
        if self.DEFAULT_REPORT not in reports:
            reports.append(self.DEFAULT_REPORT)
        return reports

    @property
    def user_agent(self):
        """User agent property."""

        return self._user_agent

    def set_threads(self, threads):
        """Threads setter."""

        self._threads = threads

    @property
    def threads(self):
        """Threads property."""

        return self._threads

    @property
    def headers(self):
        """Custom request headers."""

        return [] if self._headers is None else [str(item).strip() for item in self._headers if str(item).strip()]

    @property
    def include_status(self):
        """Expanded include-status filter values."""

        return self._expand_numeric_tokens(self._include_status)

    @property
    def exclude_status(self):
        """Expanded exclude-status filter values."""

        return self._expand_numeric_tokens(self._exclude_status)

    @property
    def exclude_size(self):
        """Exact response sizes excluded in bytes."""

        return self._expand_integer_values(self._exclude_size)

    @property
    def exclude_size_range(self):
        """Response size ranges excluded in bytes."""

        return self._expand_integer_ranges(self._exclude_size_range)

    @property
    def match_text(self):
        """Body text fragments required for a response match."""

        return [] if self._match_text is None else [str(item).strip() for item in self._match_text if str(item).strip()]

    @property
    def exclude_text(self):
        """Body text fragments excluded from matching responses."""

        return [] if self._exclude_text is None else [str(item).strip() for item in self._exclude_text if str(item).strip()]

    @property
    def match_regex(self):
        """Regex patterns required for a response match."""

        return [] if self._match_regex is None else [str(item).strip() for item in self._match_regex if str(item).strip()]

    @property
    def exclude_regex(self):
        """Regex patterns excluded from matching responses."""

        return [] if self._exclude_regex is None else [str(item).strip() for item in self._exclude_regex if str(item).strip()]

    @property
    def min_response_length(self):
        """Minimum accepted response length in bytes."""

        return self._min_response_length

    @property
    def max_response_length(self):
        """Maximum accepted response length in bytes."""

        return self._max_response_length

    @property
    def cookies(self):
        """Custom request cookies."""

        return [] if self._cookies is None else [str(item).strip() for item in self._cookies if str(item).strip()]

    @property
    def accept_cookies(self):
        """Accept cookies property."""

        return self._accept_cookies

    @property
    def keep_alive(self):
        """If connection keep-alive."""

        return self._keep_alive

    @property
    def raw_request(self):
        """Raw request file source path."""

        return self._raw_request

    @property
    def is_raw_request(self):
        """If raw-request mode is enabled."""

        return self._raw_request is not None and len(str(self._raw_request).strip()) > 0

    @property
    def request_body(self):
        """Optional request body loaded from raw-request template."""

        return self._request_body

    @property
    def session_save(self):
        """Checkpoint file path for persistent sessions."""
        return self._session_save

    @property
    def session_load(self):
        """Loaded checkpoint file path."""
        return self._session_load

    @property
    def session_autosave_sec(self):
        """Autosave interval in seconds."""
        return self._session_autosave_sec

    @property
    def session_autosave_items(self):
        """Autosave processed-items threshold."""
        return self._session_autosave_items

    @property
    def is_session_enabled(self):
        """If persistent session checkpoints are enabled."""
        return self._session_save is not None and len(str(self._session_save).strip()) > 0
