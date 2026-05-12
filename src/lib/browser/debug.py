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
from urllib.parse import unquote, urlsplit, urlunsplit

from src.core import helper
from src.core import sys
from src.core.http.providers.debug import DebugProvider
from src.lib.tpl import Tpl as tpl


class Debug(DebugProvider):
    """Debug class"""

    def __init__(self, Config):
        """
        Debug constructor.

        :param Config: Config
        """

        self.__catched = False
        self.__clear = False
        self.__cfg = Config
        self.__level = self.__cfg.debug
        self.__cookie_accept_enabled_logged = False

        if self.is_scan_debug():
            tpl.debug(key='debug', level=self.__cfg.debug, method=self.__cfg.method)

    def is_enabled(self, level):
        """Return True when the current debug level includes the requested level.

        :param int level: required debug level
        :return: whether the level is enabled
        :rtype: bool
        """

        return self.__level >= level

    def is_scan_debug(self):
        """Return True for scanner decision debug output.

        :return: whether level 1 output is enabled
        :rtype: bool
        """

        return self.is_enabled(1)

    def is_request_debug(self):
        """Return True for outgoing request debug output.

        :return: whether level 2 output is enabled
        :rtype: bool
        """

        return self.is_enabled(2)

    def is_response_debug(self):
        """Return True for incoming response debug output.

        :return: whether level 3 output is enabled
        :rtype: bool
        """

        return self.is_enabled(3)

    @classmethod
    def __normalize_debug_headers(cls, headers):
        """Return a serializable copy of request/response headers.

        Debug output intentionally keeps header values visible.

        :param dict|object headers: header mapping or header-like object
        :return: normalized header mapping
        :rtype: dict
        """

        if not isinstance(headers, dict):
            try:
                headers = dict(headers)
            except (TypeError, ValueError):
                headers = getattr(headers, '__dict__', {})

        safe_headers = {}
        for name, value in dict(headers or {}).items():
            safe_headers[name] = value

        return safe_headers

    @property
    def level(self):
        """Get debug level."""

        return self.__level

    def debug_user_agents(self):
        """Debug info for user agent."""

        if self.is_scan_debug():
            if self.__cfg.is_random_user_agent is True:
                tpl.debug(key='random_browser')
            else:
                tpl.debug(key='browser', browser=self.__cfg.user_agent)

        return True

    def debug_list(self, total_lines):
        """Debug scan list."""

        if self.is_scan_debug():
            if self.__cfg.is_random_list is True:
                tpl.debug(key='randomizing')
            if self.__cfg.DEFAULT_SCAN == self.__cfg.scan:
                if self.__cfg.is_extension_filter is True:
                    tpl.debug(key='ext_filter', total=total_lines, ext=', '.join(self.__cfg.extensions))
                elif self.__cfg.is_ignore_extension_filter is True:
                    tpl.debug(key='ext_ignore_filter', total=total_lines, ext=', '.join(self.__cfg.ignore_extensions))
                else:
                    tpl.debug(key='directories', total=total_lines)
            else:
                tpl.debug(key='subdomains', total=total_lines)
            tpl.debug(key='create_queue', threads=self.__cfg.threads)

        return True

    def debug_connection_pool(self, keymsg, pool, connection_type):
        """Debug connection pool message."""

        if not self.is_request_debug():
            return True

        tpl.debug(key=keymsg, type=connection_type)
        if pool:
            tpl.debug(str(pool), type=connection_type)

        return True

    def debug_header_bypass(self):
        """Debug header-bypass configuration."""

        if self.is_scan_debug() and self.__cfg.is_header_bypass is True:
            tpl.debug(
                key='header_bypass_enabled',
                statuses=','.join([str(status) for status in self.__cfg.header_bypass_status]),
                limit=self.__cfg.header_bypass_limit,
                headers=len(self.__cfg.header_bypass_headers)
            )

        return True

    def debug_waf_guard(self):
        """Debug WAF guard configuration."""

        if self.is_scan_debug() and getattr(self.__cfg, 'is_waf_guard', False) is True:
            tpl.debug(
                key='waf_guard_enabled',
                after=self.__cfg.waf_guard_after,
                threshold='{0:.1f}'.format(float(self.__cfg.waf_guard_threshold) * 100.0)
            )

        return True

    @staticmethod
    def __mask_proxy_server(server):
        """Return proxy URL with masked password for debug output."""

        if not server:
            return server

        try:
            parsed = urlsplit(server)
        except (TypeError, ValueError):
            return str(server)

        if not parsed.username and parsed.password is None:
            return server

        host = parsed.hostname or ''
        if ':' in host and not host.startswith('['):
            host = '[{0}]'.format(host)

        netloc = host
        if parsed.port is not None:
            netloc = '{0}:{1}'.format(netloc, parsed.port)

        username = unquote(parsed.username or '')
        if username:
            netloc = '{0}:*****@{1}'.format(username, netloc)
        else:
            netloc = '*****@{0}'.format(netloc)

        return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))

    def debug_proxy_pool(self):
        """Debug proxy pool message."""

        if not self.is_scan_debug():
            return True

        if self.__cfg.is_external_proxy_list is True:
            tpl.debug(key='proxy_pool_external_start')
        elif self.__cfg.is_standalone_proxy is True:
            tpl.debug(key='proxy_pool_standalone', server=self.__mask_proxy_server(self.__cfg.proxy))
        elif self.__cfg.is_builtin_proxy_pool is True:
            tpl.debug(key='proxy_pool_internal_start')

        return True

    def debug_proxy_selected(self, server):
        """Debug selected proxy for rotating proxy modes."""

        if self.is_scan_debug():
            tpl.debug(key='proxy_pool_selected', server=self.__mask_proxy_server(server))

        return True

    def debug_request(self, request_header, url, method):
        """Debug request."""

        if not self.is_request_debug():
            return True

        if not isinstance(request_header, dict):
            request_header = request_header.__dict__

        request_data = self.__normalize_debug_headers(request_header)
        request_data.update({'Request URI': url, 'Request Method': method})

        tpl.debug(key='request_header_dbg', dbg=helper.to_json(request_data))

        return True

    def debug_response(self, response_header):
        """Debug response."""

        if not self.is_response_debug():
            return True

        response_data = self.__normalize_debug_headers(response_header)
        tpl.debug(key='response_header_dbg', dbg=helper.to_json(response_data))

        return True

    def debug_request_uri(self, status, request_uri, **kwargs):
        """Debug request_uri."""

        percentage = tpl.line(msg=helper.percent(kwargs.get('items_size', 0), kwargs.get('total_size', 1)), color='cyan')
        total_len = len(str(abs(kwargs.get('total_size', 1))))

        if self.__cfg.DEFAULT_SCAN == self.__cfg.scan:
            urlpath = helper.parse_url(request_uri).path
        else:
            urlpath = request_uri

        if status in ['success', 'file', 'indexof', 'certificate', 'auth']:
            request_uri = tpl.line(key=status, color='green', url=urlpath)
        elif status in ['malware']:
            request_uri = '{0} ({1}) {2}'.format(
                tpl.line(msg='OK', color='green'),
                tpl.line(msg='Malware', color='red'),
                tpl.line(msg=urlpath, color='green')
            )
        elif status in ['stacktrace']:
            request_uri = '{0} ({1}) {2}'.format(
                tpl.line(msg='OK', color='green'),
                tpl.line(msg='StackTrace', color='red'),
                tpl.line(msg=urlpath, color='green')
            )
        elif status in ['shadow']:
            request_uri = '{0} ({1}) {2}'.format(
                tpl.line(msg='OK', color='green'),
                tpl.line(msg='Shadow', color='red'),
                tpl.line(msg=urlpath, color='green')
            )
        elif status in ['openredirect']:
            openredirect_detection = kwargs.get('openredirect_detection') or {}
            request_uri = '{0} ({1}) {2} -> {3}'.format(
                tpl.line(msg='R', color='blue'),
                tpl.line(msg='OpenRedirect', color='red'),
                tpl.line(msg=urlpath, color='green'),
                tpl.line(msg=openredirect_detection.get('location') or '-', color='blue')
            )
        elif status in ['bad', 'forbidden']:
            request_uri = tpl.line(key='forbidden', color='yellow', url=urlpath)
        elif status in ['redirect']:
            request_uri = tpl.line(key='redirect', color='blue', url=urlpath, rurl=kwargs.get('redirect_uri'))
        elif status in ['blocked']:
            waf_name = kwargs.get('waf_name')
            waf_confidence = kwargs.get('waf_confidence')

            if waf_name:
                request_uri = tpl.line(
                    msg='WAF: {0} ({1}%) {2}'.format(waf_name, waf_confidence, urlpath),
                    color='yellow'
                )
            else:
                request_uri = tpl.line(key=status, color='yellow', url=urlpath)

        self.__clear = True if self.__catched else False

        if status in ['success', 'file', 'bad', 'forbidden', 'redirect', 'blocked', 'indexof', 'certificate', 'auth', 'stacktrace', 'malware', 'shadow', 'openredirect']:
            sys.writels('', flush=True)
            tpl.info(
                key='get_item',
                clear=self.__clear,
                percent=percentage,
                current='{0:0{l}d}'.format(kwargs.get('items_size', 0), l=total_len),
                total=kwargs.get('total_size', 1),
                item=request_uri,
                size=kwargs.get('content_size'),
                code=kwargs.get('response_code', '-'),
            )
            self.__catched = True
        else:
            request_uri = tpl.line(
                msg=urlpath,
                color='white'
            )

            if self.__level != -1:
                tpl.line_log(
                    key='get_item',
                    percent=percentage,
                    current='{0:0{l}d}'.format(kwargs.get('items_size', 0), l=total_len),
                    total=kwargs.get('total_size', 1),
                    item=request_uri,
                    size=kwargs.get('content_size'),
                    code=kwargs.get('response_code', '-'),
                )

            self.__catched = False
            if kwargs.get('items_size', 0) == kwargs.get('total_size', 1):
                sys.writels('', flush=True)

        return True

    def debug_load_sniffer_plugin(self, description):
        """Debug load sniffers plugin."""

        if self.is_scan_debug():
            tpl.debug(key='load_sniffer_plugin', description=description)

        return True

    def debug_cookie_accept_enabled(self):
        """Debug active response cookie routing once per scan."""

        if self.is_request_debug() and self.__cookie_accept_enabled_logged is False:
            tpl.debug(key='accept_cookies_enabled')
            self.__cookie_accept_enabled_logged = True

        return True

    def debug_cookie_accepted(self, cookies):
        """Debug cookies accepted from a response.

        :param str cookies: cookie header value prepared for following requests
        :return: bool
        """

        if self.is_request_debug():
            tpl.debug(key='response_cookies_accepted', cookies=cookies)

        return True

    def debug_cookie_attached(self, headers):
        """Debug Cookie header attached to an outgoing request.

        :param dict headers: outgoing request headers
        :return: bool
        """

        if self.is_request_debug() and isinstance(headers, dict) and headers.get('Cookie'):
            tpl.debug(key='cookie_header_attached', cookies=headers.get('Cookie'))

        return True

    def debug_auto_calibration_enabled(self):
        """Debug auto-calibration configuration."""

        if self.is_scan_debug():
            tpl.debug(
                msg='Auto-calibration enabled: samples={0}, threshold={1}'.format(
                    self.__cfg.calibration_samples,
                    self.__cfg.calibration_threshold
                )
            )

        return True

    def debug_header_bypass_skipped(self, status):
        """Debug skipped header-bypass probe."""

        if self.is_scan_debug():
            tpl.debug(
                key='header_bypass_skipped',
                status=status or '-',
                statuses=','.join([str(status) for status in self.__cfg.header_bypass_status])
            )

        return True

    def debug_header_bypass_probing(self, status, variants):
        """Debug header-bypass probe start."""

        if self.is_scan_debug():
            tpl.debug(key='header_bypass_probing', status=status or '-', variants=variants)

        return True

    def debug_header_bypass_candidate(self, metadata):
        """Debug promising header-bypass candidate."""

        if self.is_scan_debug():
            tpl.debug(
                key='header_bypass_candidate',
                header=metadata.get('bypass_header') or metadata.get('bypass_variant'),
                from_code=metadata.get('bypass_from_code') or '-',
                to_code=metadata.get('bypass_to_code') or '-'
            )

        return True

    def debug_header_bypass_finished(self):
        """Debug header-bypass probe completion."""

        if self.is_scan_debug():
            tpl.debug(key='header_bypass_finished')

        return True

    def debug_recursive_expansion(self, parent_url, child_count, next_depth):
        """Debug recursive queue expansion."""

        if self.is_scan_debug():
            tpl.debug(
                msg='Recursive expansion [{0}] -> +{1} urls (next depth: {2})'.format(
                    parent_url,
                    child_count,
                    next_depth
                )
            )

        return True

    def debug_classification(
            self,
            status,
            code='-',
            size='-',
            waf_name=None,
            waf_confidence=None,
            signals=None,
            redirect_uri=None,
            stacktrace_detection=None,
            secret_detection=None,
            shadow_detection=None,
            openredirect_detection=None,
            malware_detection=None
    ):
        """Debug response classification summary."""

        if not self.is_response_debug():
            return True

        parts = [
            'Classification: {0}'.format(status),
            'code={0}'.format(code),
            'size={0}'.format(size),
        ]

        if redirect_uri:
            parts.append('redirect={0}'.format(redirect_uri))
        if waf_name:
            parts.append('waf={0}'.format(waf_name))
        if waf_confidence is not None:
            parts.append('confidence={0}'.format(waf_confidence))

        tpl.debug(msg='; '.join(parts))

        if signals:
            tpl.debug(msg='WAF signals: {0}'.format(', '.join([str(signal) for signal in signals])))

        if secret_detection:
            tpl.debug(
                msg='Secret detection: type={0}; redacted={1}; confidence={2}; count={3}'.format(
                    secret_detection.get('type') or '-',
                    secret_detection.get('redacted') or '-',
                    secret_detection.get('confidence') or '-',
                    secret_detection.get('count') or '-',
                )
            )

        if malware_detection:
            tpl.debug(
                msg='Malware detection: subtype={0}; family={1}; signal={2}; confidence={3}; count={4}'.format(
                    malware_detection.get('subtype') or '-',
                    malware_detection.get('family') or '-',
                    malware_detection.get('signal') or '-',
                    malware_detection.get('confidence') or '-',
                    malware_detection.get('count') or '-',
                )
            )

        if stacktrace_detection:
            tpl.debug(
                msg='StackTrace detection: runtime={0}; signal={1}; confidence={2}'.format(
                    stacktrace_detection.get('runtime') or '-',
                    stacktrace_detection.get('signal') or '-',
                    stacktrace_detection.get('confidence') or '-'
                )
            )

        if shadow_detection:
            tpl.debug(
                msg='Shadow detection: base={0}; variant={1}; confidence={2}'.format(
                    shadow_detection.get('base_url') or '-',
                    shadow_detection.get('variant') or '-',
                    shadow_detection.get('confidence') or '-'
                )
            )

        if openredirect_detection:
            tpl.debug(
                msg='OpenRedirect detection: param={0}; variant={1}; location={2}; confidence={3}'.format(
                    openredirect_detection.get('parameter') or '-',
                    openredirect_detection.get('variant') or '-',
                    openredirect_detection.get('location') or '-',
                    openredirect_detection.get('confidence') or '-'
                )
            )

        return True
