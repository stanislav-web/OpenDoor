# -*- coding: utf-8 -*-

"""Controlled open redirect verification helper."""

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from src.core.http.redirect_classifier import RedirectClassifier


class OpenRedirectProbe(object):
    """Verify redirect-like parameters with safe external marker payloads."""

    RESPONSE_INDEX = 'openredirect'
    MARKER_HOST = 'redirect.invalid'
    REDIRECT_STATUSES = (301, 302, 303, 307, 308)
    REDIRECT_PARAMS = (
        'next',
        'url',
        'redirect',
        'redirect_url',
        'redirect_uri',
        'return',
        'returnurl',
        'return_url',
        'continue',
        'callback',
        'callback_url',
        'target',
        'dest',
        'destination',
        'goto',
        'to',
        'r',
        'u',
        'relaystate',
    )
    PAYLOADS = (
        ('absolute-external-url', 'https://redirect.invalid/'),
        ('protocol-relative-url', '//redirect.invalid/'),
    )
    PAYLOAD_FAMILIES = {
        'absolute-external-url': 'external_url',
        'protocol-relative-url': 'protocol_relative_external',
    }
    CLASSIFICATION_BASE_URL = 'https://opendoor.invalid/'

    def __init__(self):
        """Create open redirect probe instance."""

        self.__seen_probe_urls = set()

    @classmethod
    def is_enabled(cls, config):
        """Return True when --sniff openredirect is selected.

        :param object config: browser config
        :return: whether active open redirect verification is enabled
        :rtype: bool
        """

        return getattr(config, 'is_sniff', False) is True and 'openredirect' in (getattr(config, 'sniffers', []) or [])

    @classmethod
    def is_redirect_parameter(cls, name):
        """Return True for redirect-like parameter names.

        :param str name: query parameter name
        :return: whether parameter can control redirect target
        :rtype: bool
        """

        return str(name or '').strip().lower() in cls.REDIRECT_PARAMS

    @classmethod
    def build_variants(cls, url):
        """Build safe verification requests for redirect-like query parameters.

        :param str url: source URL
        :return: list of probe variant dictionaries
        :rtype: list[dict]
        """

        parsed = urlparse(str(url or ''))
        query_items = parse_qsl(parsed.query, keep_blank_values=True)

        if len(query_items) <= 0:
            return []

        variants = []
        seen = set()

        for index, (name, _value) in enumerate(query_items):
            if cls.is_redirect_parameter(name) is not True:
                continue

            for variant_name, payload in cls.PAYLOADS:
                mutated_items = list(query_items)
                mutated_items[index] = (name, payload)
                probe_url = urlunparse((
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    urlencode(mutated_items, doseq=True),
                    parsed.fragment,
                ))

                key = (probe_url, name, variant_name)
                if key in seen:
                    continue
                seen.add(key)

                variants.append({
                    'url': probe_url,
                    'param': name,
                    'payload': payload,
                    'variant': variant_name,
                    'payload_family': cls.payload_family(variant_name),
                })

        return variants

    def filter_new_variants(self, url):
        """Return variants not already sent in this scan process.

        :param str url: source URL
        :return: unique probe variants
        :rtype: list[dict]
        """

        variants = []
        for variant in self.build_variants(url):
            probe_url = variant.get('url')
            if not probe_url or probe_url in self.__seen_probe_urls:
                continue
            self.__seen_probe_urls.add(probe_url)
            variants.append(variant)
        return variants

    @classmethod
    def get_redirect_location(cls, response):
        """Return response Location header in a case-insensitive way.

        :param object response: HTTP response-like object
        :return: redirect location or empty string
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
            if str(name).lower() == 'location':
                return str(value or '').strip()

        return ''

    @classmethod
    def location_host(cls, location):
        """Resolve host from absolute or protocol-relative Location value.

        :param str location: Location header value
        :return: normalized host
        :rtype: str
        """

        location = str(location or '').strip()
        if location.startswith('//'):
            location = 'https:{0}'.format(location)

        parsed = urlparse(location)
        return str(parsed.hostname or '').strip().lower()

    @classmethod
    def payload_family(cls, variant_name):
        """Return stable payload-family metadata for a variant.

        :param str variant_name: payload variant name
        :return: payload family name
        :rtype: str
        """

        return cls.PAYLOAD_FAMILIES.get(str(variant_name or ''), 'external_url')

    @classmethod
    def classify_response(cls, response, source_url=None):
        """Classify the probe redirect target with the shared redirect classifier.

        :param object response: HTTP response-like object
        :param str|None source_url: probe URL used as the redirect source
        :return: redirect classification metadata
        :rtype: dict
        """

        status = getattr(response, 'status', 0)
        location = cls.get_redirect_location(response)
        return RedirectClassifier.classify(
            source_url or cls.CLASSIFICATION_BASE_URL,
            status,
            location,
        )

    @classmethod
    def is_confirmed(cls, response, source_url=None):
        """Return True when response redirects to the controlled marker host.

        :param object response: HTTP response-like object
        :param str|None source_url: probe URL used as the redirect source
        :return: whether this response confirms open redirect
        :rtype: bool
        """

        classification = cls.classify_response(response, source_url=source_url)
        if classification.get('type') != 'external':
            return False

        return str(classification.get('target_host') or '').lower() == cls.MARKER_HOST

    @classmethod
    def metadata(cls, source_url, variant, response):
        """Build normalized open redirect finding metadata.

        :param str source_url: original scan URL
        :param dict variant: probe variant
        :param object response: matching response object
        :return: detection metadata
        :rtype: dict
        """

        return {
            'openredirect_detection': {
                'type': 'open_redirect',
                'confidence': 100,
                'source_url': str(source_url),
                'probe_url': str(variant.get('url') or ''),
                'parameter': str(variant.get('param') or ''),
                'payload': str(variant.get('payload') or ''),
                'variant': str(variant.get('variant') or ''),
                'payload_family': str(variant.get('payload_family') or cls.payload_family(variant.get('variant'))),
                'location': cls.get_redirect_location(response),
                'marker_host': cls.MARKER_HOST,
            }
        }
