# -*- coding: utf-8 -*-

"""Passive HTTP redirect classification helpers."""

from urllib.parse import urljoin, urlparse


class RedirectClassifier(object):
    """Classify already received HTTP redirect Location headers."""

    REDIRECT_STATUSES = (301, 302, 303, 307, 308)
    MAX_LOCATION_LENGTH = 256
    MAX_DISPLAY_LENGTH = 96
    SENSITIVE_QUERY_KEYS = (
        'token',
        'access_token',
        'refresh_token',
        'id_token',
        'code',
        'state',
        'session',
        'sid',
        'ticket',
        'auth',
        'jwt',
        'key',
        'secret',
        'password',
    )
    ASSET_EXTENSIONS = (
        '.css', '.js', '.mjs', '.map', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
        '.webp', '.avif', '.woff', '.woff2', '.ttf', '.eot', '.pdf', '.zip', '.gz',
        '.tar', '.rar', '.7z', '.mp4', '.mp3', '.webm', '.mov', '.avi'
    )
    WAF_PATH_MARKERS = (
        '/cdn-cgi/challenge',
        '/cdn-cgi/l/chk_jschl',
        '/cdn-cgi/bm/cv/',
        '/__cf_chl_',
        '/challenge-platform/',
        '/challenge/',
        '/captcha',
        '/akam/',
        '/_Incapsula_Resource',
        '/.well-known/ddos-guard/',
    )
    LOGIN_PATH_MARKERS = (
        '/login',
        '/signin',
        '/sign-in',
        '/auth',
        '/oauth',
        '/sso',
        '/account/login',
        '/user/login',
        '/users/sign_in',
        '/wp-login.php',
    )
    LOGOUT_PATH_MARKERS = (
        '/logout',
        '/signout',
        '/sign-out',
        '/logoff',
        '/account/logout',
        '/users/sign_out',
    )

    @classmethod
    def get_location(cls, response):
        """Return a best-effort raw Location header value.

        :param object response: response-like object
        :return: Location value or empty string
        :rtype: str
        """

        try:
            location = response.get_redirect_location()
            if location is not False and location is not None:
                return str(location).strip()
        except (AttributeError, TypeError, ValueError):
            pass

        headers = getattr(response, 'headers', {}) or {}
        try:
            iterator = headers.items()
        except AttributeError:
            return ''

        for name, value in iterator:
            if str(name).strip().lower() == 'location':
                return str(value or '').strip()

        return ''

    @classmethod
    def classify(cls, source_url, status, location):
        """Classify one already received redirect response.

        :param str source_url: original request URL
        :param int|str status: response status code
        :param str location: raw Location header value
        :return: bounded redirect classification metadata
        :rtype: dict
        """

        try:
            status_code = int(status)
        except (TypeError, ValueError):
            status_code = 0

        raw_location = str(location or '').strip()
        if status_code not in cls.REDIRECT_STATUSES:
            return {}

        if not raw_location:
            return cls._invalid(raw_location, 'missing_location')

        source = urlparse(str(source_url or ''))
        target_url = urljoin(str(source_url or ''), raw_location)
        target = urlparse(target_url)

        if not target.scheme or not target.netloc:
            return cls._invalid(raw_location, 'invalid_location')

        source_host = cls._host_port(source)
        target_host = cls._host_port(target)
        same_host = bool(source_host and target_host and source_host == target_host)
        same_origin = bool(same_host and source.scheme == target.scheme)
        cross_origin = not same_origin
        target_path = target.path or '/'
        path_lower = target_path.lower()
        location_value = cls.sanitize_location(raw_location)
        target_url_value = cls.sanitize_location(target_url)

        redirect_type = 'unknown'
        reason = 'unclassified_redirect'
        confidence = 'low'

        if cls._is_waf_challenge(path_lower):
            redirect_type = 'waf'
            reason = 'challenge_redirect'
            confidence = 'high'
        elif same_host and source.scheme != target.scheme:
            redirect_type = 'scheme'
            reason = '{0}_to_{1}'.format(source.scheme or 'unknown', target.scheme or 'unknown')
            confidence = 'high'
        elif same_origin and cls._is_logout_path(path_lower):
            redirect_type = 'logout'
            reason = 'logout_redirect'
            confidence = 'high'
        elif same_origin and cls._is_login_path(path_lower):
            redirect_type = 'login'
            reason = 'auth_gate_redirect'
            confidence = 'high'
        elif not same_origin and target.hostname:
            redirect_type = 'external'
            reason = cls._external_reason(target.hostname, path_lower)
            confidence = 'high'
        elif cls._is_asset_path(path_lower):
            redirect_type = 'asset'
            reason = 'static_asset_redirect'
            confidence = 'high'
        elif same_origin and cls._is_canonical_redirect(source.path or '/', target_path):
            redirect_type = 'canonical'
            reason = 'canonical_redirect'
            confidence = 'high'
        elif same_origin:
            redirect_type = 'internal'
            reason = 'same_origin_redirect'
            confidence = 'medium'

        return {
            'type': redirect_type,
            'reason': reason,
            'location': location_value,
            'target_url': target_url_value,
            'target_scheme': str(target.scheme or ''),
            'target_host': str(target.hostname or ''),
            'target_path': cls._truncate(target_path, cls.MAX_LOCATION_LENGTH),
            'same_origin': same_origin,
            'cross_origin': cross_origin,
            'confidence': confidence,
            'display': cls.display_target(redirect_type, location_value, target_url_value, target),
        }

    @classmethod
    def marker(cls, classification):
        """Return the runtime R(...) marker for a classification.

        :param dict classification: classification metadata
        :return: marker
        :rtype: str
        """

        redirect_type = 'unknown'
        if isinstance(classification, dict) and classification.get('type'):
            redirect_type = str(classification.get('type'))
        return 'R({0})'.format(redirect_type)

    @classmethod
    def display_target(cls, redirect_type, location, target_url, target):
        """Return compact target text for runtime output.

        :param str redirect_type: classification type
        :param str location: bounded Location value
        :param str target_url: bounded normalized target URL
        :param urllib.parse.ParseResult target: target URL parts
        :return: display value
        :rtype: str
        """

        if redirect_type == 'external':
            return cls._truncate(target_url or location or str(target.hostname or '-'), cls.MAX_DISPLAY_LENGTH)
        if redirect_type == 'scheme':
            return cls._truncate(target_url or location or '-', cls.MAX_DISPLAY_LENGTH)
        return cls._truncate(location or target_url or '-', cls.MAX_DISPLAY_LENGTH)

    @classmethod
    def sanitize_location(cls, value):
        """Redact sensitive query values and bound Location-like values.

        :param str value: raw location value
        :return: sanitized value
        :rtype: str
        """

        value = str(value or '').strip()
        if '?' not in value:
            return cls._truncate(value, cls.MAX_LOCATION_LENGTH)

        prefix, query = value.split('?', 1)
        fragment = ''
        if '#' in query:
            query, fragment = query.split('#', 1)
            fragment = '#{0}'.format(fragment)

        parts = []
        for part in query.split('&'):
            if '=' not in part:
                parts.append(part)
                continue

            key, part_value = part.split('=', 1)
            key_normalized = key.strip().lower()
            if key_normalized in cls.SENSITIVE_QUERY_KEYS:
                part_value = cls._redact_value(part_value)
            parts.append('{0}={1}'.format(key, part_value))

        return cls._truncate('{0}?{1}{2}'.format(prefix, '&'.join(parts), fragment), cls.MAX_LOCATION_LENGTH)

    @classmethod
    def _invalid(cls, location, reason):
        """Build invalid redirect metadata."""

        return {
            'type': 'invalid',
            'reason': reason,
            'location': cls.sanitize_location(location),
            'target_url': '',
            'target_scheme': '',
            'target_host': '',
            'target_path': '',
            'same_origin': False,
            'cross_origin': False,
            'confidence': 'high',
            'display': '-',
        }

    @staticmethod
    def _host_port(parsed):
        """Return normalized hostname:port for parsed URL parts."""

        hostname = str(parsed.hostname or '').strip().lower()
        if not hostname:
            return ''
        if parsed.port is None:
            return hostname
        return '{0}:{1}'.format(hostname, parsed.port)

    @classmethod
    def _is_waf_challenge(cls, path):
        return any(marker.lower() in path for marker in cls.WAF_PATH_MARKERS)

    @classmethod
    def _is_login_path(cls, path):
        return any(path == marker or path.startswith('{0}/'.format(marker)) for marker in cls.LOGIN_PATH_MARKERS)

    @classmethod
    def _is_logout_path(cls, path):
        return any(path == marker or path.startswith('{0}/'.format(marker)) for marker in cls.LOGOUT_PATH_MARKERS)

    @classmethod
    def _is_asset_path(cls, path):
        if path.endswith(cls.ASSET_EXTENSIONS):
            return True
        return path.startswith(('/static/', '/assets/', '/public/', '/media/', '/img/', '/images/'))

    @staticmethod
    def _is_canonical_redirect(source_path, target_path):
        source_path = source_path or '/'
        target_path = target_path or '/'
        if source_path == target_path:
            return False
        if source_path.rstrip('/') == target_path.rstrip('/'):
            return True
        return False

    @staticmethod
    def _external_reason(hostname, path):
        host = str(hostname or '').lower()
        if 'login.microsoftonline.com' in host or 'okta.com' in host or 'auth0.com' in host:
            return 'sso_redirect'
        if '/oauth' in path or '/sso' in path or '/authorize' in path:
            return 'sso_redirect'
        return 'cross_origin_redirect'

    @staticmethod
    def _redact_value(value):
        value = str(value or '')
        if len(value) <= 4:
            return '****'
        return '{0}****'.format(value[:4])

    @staticmethod
    def _truncate(value, limit):
        value = str(value or '')
        if len(value) <= limit:
            return value
        return '{0}...'.format(value[:max(0, limit - 3)])
