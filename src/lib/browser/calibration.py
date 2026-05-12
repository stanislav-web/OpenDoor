# -*- coding: utf-8 -*-

"""
    Smart auto-calibration for soft-404 / wildcard / catch-all responses.
"""

import hashlib
import html
import re

from src.core import helper


class Calibration(object):

    """Calibration baseline matcher."""

    DEFAULT_THRESHOLD = 0.92
    STABLE_HEADERS = ('content-type', 'server', 'x-powered-by')
    DYNAMIC_PATTERNS = (
        r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b',
        r'\b[0-9a-f]{24,}\b',
        r'\b\d{4}-\d{2}-\d{2}(?:[t\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?)?\b',
        r'\b\d{2}:\d{2}:\d{2}\b',
        r'\b\d{5,}\b',
        r'csrf[_-]?token=["\'][^"\']+["\']',
        r'nonce=["\'][^"\']+["\']',
        r'([?&][a-z0-9_-]+)=([^&#\s"\']+)',
        r'\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b',
        r'/(?:[a-z0-9._~%+-]+/)*[a-z0-9._~%+-]+',
        r'\b[a-z0-9+/]{32,}={0,2}\b',
    )
    SEMANTIC_STOPWORDS = frozenset((
        'a', 'about', 'after', 'all', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'can',
        'could', 'did', 'do', 'does', 'for', 'from', 'go', 'has', 'have', 'if', 'in',
        'is', 'it', 'its', 'may', 'not', 'of', 'on', 'or', 'our', 'page', 'please',
        'request', 'requested', 'site', 'that', 'the', 'this', 'to', 'try', 'url',
        'was', 'we', 'were', 'with', 'you', 'your'
    ))
    SOFT_404_PHRASES = (
        '404',
        'not found',
        'page not found',
        'cannot be found',
        'could not be found',
        'does not exist',
        'no longer exists',
        'missing page',
        'resource missing',
        'resource not found',
        'requested page',
        'requested resource',
        'unavailable',
        'unknown page',
    )

    def __init__(self, signatures=None, threshold=None, dns_wildcard_addresses=None):
        """
        Constructor.

        :param list[dict]|None signatures:
        :param float|None threshold:
        :param list[str]|None dns_wildcard_addresses:
        """

        self.signatures = signatures or []
        self.threshold = self.DEFAULT_THRESHOLD if threshold is None else float(threshold)
        self.dns_wildcard_addresses = self._normalize_dns_addresses(dns_wildcard_addresses or [])

    @property
    def is_enabled(self):
        """Return True when baseline has at least one usable signature."""

        return len(self.signatures) > 0 or self.has_dns_wildcard is True

    @property
    def has_dns_wildcard(self):
        """Return True when DNS wildcard baseline addresses are available."""

        return len(self.dns_wildcard_addresses) > 0

    def to_dict(self):
        """
        Export calibration state.

        :return: dict
        """

        state = {
            'threshold': self.threshold,
            'signatures': list(self.signatures),
        }

        if self.has_dns_wildcard is True:
            state['dnsWildcardAddresses'] = list(self.dns_wildcard_addresses)

        return state

    @classmethod
    def from_dict(cls, payload):
        """
        Restore calibration state.

        :param dict|None payload:
        :return: Calibration|None
        """

        if not isinstance(payload, dict):
            return None

        signatures = payload.get('signatures') or []
        threshold = payload.get('threshold', cls.DEFAULT_THRESHOLD)
        dns_wildcard_addresses = payload.get('dnsWildcardAddresses') or []

        if not isinstance(signatures, list):
            return None

        if not isinstance(dns_wildcard_addresses, list):
            dns_wildcard_addresses = []

        return cls(
            signatures=signatures,
            threshold=threshold,
            dns_wildcard_addresses=dns_wildcard_addresses
        )

    @classmethod
    def build_signature(cls, response, response_data):
        """
        Build a response signature.

        :param object response:
        :param tuple response_data:
        :return: dict
        """

        body = cls._body(response)
        normalized_body = cls._normalize_body(body)
        visible_text = cls._visible_text(body)
        skeleton = cls._body_skeleton(body)
        dom_tokens = cls._dom_tokens(body)

        return {
            'bucket': str(response_data[0]),
            'url': str(response_data[1]),
            'size': cls._response_size(response),
            'code': cls._response_code(response, response_data),
            'word_count': cls._word_count(body),
            'line_count': cls._line_count(body),
            'title': cls._title(body),
            'redirect_location': cls._redirect_location(response),
            'normalized_body_hash': cls._hash(normalized_body),
            'body_skeleton_hash': cls._hash(skeleton),
            'visible_text_hash': cls._hash(visible_text),
            'content_kind': cls._content_kind(body),
            'semantic_phrases': cls._semantic_phrases(visible_text),
            'semantic_terms': cls._semantic_terms(visible_text),
            'dom_tokens': dom_tokens,
            'dom_token_hash': cls._hash(' '.join(dom_tokens)),
            'text_density': cls._text_density(body),
            'header_fingerprint': cls._header_fingerprint(response),
        }

    def match_dns_wildcard(self, hostname, addresses):
        """
        Match resolved subdomain addresses against DNS wildcard baseline.

        :param str hostname:
        :param list[str] addresses:
        :return: dict|None
        """

        if self.has_dns_wildcard is not True:
            return None

        candidate_addresses = self._normalize_dns_addresses(addresses or [])
        if len(candidate_addresses) <= 0:
            return None

        wildcard_set = set(self.dns_wildcard_addresses)
        candidate_set = set(candidate_addresses)

        if candidate_set and candidate_set.issubset(wildcard_set):
            return {
                'calibration_score': 1.0,
                'calibration_reason': 'dns-wildcard',
                'dns_wildcard_host': str(hostname),
                'dns_wildcard_addresses': candidate_addresses,
            }

        return None

    @classmethod
    def _soft_200_number(cls, value):
        """
        Convert signature numeric value to float.

        :param object value: numeric-like value
        :return: converted value
        :rtype: float
        """

        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0

    @classmethod
    def _soft_200_similarity(cls, left, right):
        """
        Return ratio similarity for two numeric values.

        :param object left: first numeric value
        :param object right: second numeric value
        :return: similarity from 0.0 to 1.0
        :rtype: float
        """

        left_value = cls._soft_200_number(left)
        right_value = cls._soft_200_number(right)

        if left_value <= 0 and right_value <= 0:
            return 1.0
        if left_value <= 0 or right_value <= 0:
            return 0.0

        return 1.0 - (abs(left_value - right_value) / max(left_value, right_value))

    @classmethod
    def _soft_200_signature_value(cls, signature, *names):
        """
        Read first available signature field.

        :param dict signature: calibration signature
        :param tuple names: candidate field names
        :return: field value
        """

        for name in names:
            if name in signature:
                return signature.get(name)

        return None

    @classmethod
    def _soft_200_list_similarity(cls, left, right):
        """
        Return set similarity for token lists.

        :param list left: first token list
        :param list right: second token list
        :return: similarity from 0.0 to 1.0
        :rtype: float
        """

        left_set = set(left or [])
        right_set = set(right or [])

        if not left_set and not right_set:
            return 1.0
        if not left_set or not right_set:
            return 0.0

        return float(len(left_set & right_set)) / float(len(left_set | right_set))

    @classmethod
    def _is_soft_200_shape_match(cls, baseline, candidate):
        """
        Return True when two large 200 HTML responses look like the same catch-all template.

        This intentionally requires much more than just matching size. It targets sites
        that return one large 200 page for arbitrary missing application paths.

        :param dict baseline: baseline calibration signature
        :param dict candidate: candidate response signature
        :return: whether both signatures represent the same soft-200 template
        :rtype: bool
        """

        baseline_code = int(cls._soft_200_signature_value(baseline, 'code', 'status_code', 'response_code') or 0)
        candidate_code = int(cls._soft_200_signature_value(candidate, 'code', 'status_code', 'response_code') or 0)

        if baseline_code != 200 or candidate_code != 200:
            return False

        baseline_bucket = cls._soft_200_signature_value(baseline, 'bucket', 'status', 'result_status')
        candidate_bucket = cls._soft_200_signature_value(candidate, 'bucket', 'status', 'result_status')

        if baseline_bucket and candidate_bucket:
            if baseline_bucket != 'success' or candidate_bucket != 'success':
                return False

        baseline_kind = cls._soft_200_signature_value(baseline, 'content_kind', 'content_type_kind', 'body_kind')
        candidate_kind = cls._soft_200_signature_value(candidate, 'content_kind', 'content_type_kind', 'body_kind')

        if baseline_kind and candidate_kind:
            if baseline_kind != 'html' or candidate_kind != 'html':
                return False

        baseline_size = cls._soft_200_signature_value(baseline, 'size', 'content_size', 'body_size')
        candidate_size = cls._soft_200_signature_value(candidate, 'size', 'content_size', 'body_size')

        if min(cls._soft_200_number(baseline_size), cls._soft_200_number(candidate_size)) < 2048:
            return False

        if cls._soft_200_similarity(baseline_size, candidate_size) < 0.985:
            return False

        baseline_words = cls._soft_200_signature_value(baseline, 'word_count', 'words')
        candidate_words = cls._soft_200_signature_value(candidate, 'word_count', 'words')

        if baseline_words is not None and candidate_words is not None:
            if cls._soft_200_similarity(baseline_words, candidate_words) < 0.97:
                return False

        baseline_lines = cls._soft_200_signature_value(baseline, 'line_count', 'lines')
        candidate_lines = cls._soft_200_signature_value(candidate, 'line_count', 'lines')

        if baseline_lines is not None and candidate_lines is not None:
            if cls._soft_200_similarity(baseline_lines, candidate_lines) < 0.97:
                return False

        baseline_density = cls._soft_200_signature_value(baseline, 'text_density')
        candidate_density = cls._soft_200_signature_value(candidate, 'text_density')

        if baseline_density is not None and candidate_density is not None:
            if abs(cls._soft_200_number(baseline_density) - cls._soft_200_number(candidate_density)) > 0.05:
                return False

        hash_pairs = (
            ('body_skeleton_hash', 'body_skeleton_hash'),
            ('html_skeleton_hash', 'html_skeleton_hash'),
            ('dom_token_hash', 'dom_token_hash'),
            ('visible_text_hash', 'visible_text_hash'),
            ('semantic_terms_hash', 'semantic_terms_hash'),
        )

        for baseline_name, candidate_name in hash_pairs:
            baseline_hash = baseline.get(baseline_name)
            candidate_hash = candidate.get(candidate_name)
            if baseline_hash and candidate_hash and baseline_hash == candidate_hash:
                return True

        baseline_title = baseline.get('title')
        candidate_title = candidate.get('title')

        if baseline_title and candidate_title and baseline_title == candidate_title:
            if cls._soft_200_similarity(baseline_size, candidate_size) >= 0.995:
                return True

        baseline_tokens = baseline.get('dom_tokens') or []
        candidate_tokens = candidate.get('dom_tokens') or []

        if cls._soft_200_list_similarity(baseline_tokens, candidate_tokens) >= 0.98:
            return True

        return False



    def match(self, response, response_data):
        """
        Match a response against calibration baseline.

        :param object response:
        :param tuple response_data:
        :return: dict|None
        """

        if self.is_enabled is not True:
            return None

        candidate = self.build_signature(response, response_data)
        best_score = 0.0
        best_reasons = []

        for baseline in self.signatures:
            score, reasons = self._score(baseline, candidate)
            if score > best_score:
                best_score = score
                best_reasons = reasons

        if best_score >= self.threshold:
            return {
                'calibration_score': round(best_score, 4),
                'calibration_reason': ','.join(best_reasons),
            }

        return None

    @classmethod
    def _score(cls, baseline, candidate):
        """
        Score candidate against one baseline signature.

        :param dict baseline:
        :param dict candidate:
        :return: tuple[float, list[str]]
        """

        reasons = []

        if baseline.get('code') != candidate.get('code'):
            return 0.0, reasons

        score = 0.18
        reasons.append('code')

        if baseline.get('bucket') == candidate.get('bucket'):
            score += 0.08
            reasons.append('bucket')

        if baseline.get('normalized_body_hash') == candidate.get('normalized_body_hash'):
            score += 0.24
            reasons.append('body-hash')

        if baseline.get('body_skeleton_hash') == candidate.get('body_skeleton_hash'):
            score += 0.15
            reasons.append('skeleton-hash')

        if baseline.get('visible_text_hash') and baseline.get('visible_text_hash') == candidate.get('visible_text_hash'):
            score += 0.20
            reasons.append('visible-text')

        phrase_score = cls._jaccard_similarity(
            baseline.get('semantic_phrases') or [],
            candidate.get('semantic_phrases') or []
        )
        if phrase_score >= 0.50:
            score += 0.16 * phrase_score
            reasons.append('semantic-phrases')

        term_score = cls._jaccard_similarity(
            baseline.get('semantic_terms') or [],
            candidate.get('semantic_terms') or []
        )
        if term_score >= 0.55:
            score += 0.12 * term_score
            reasons.append('semantic-terms')

        dom_score = cls._sequence_similarity(
            baseline.get('dom_tokens') or [],
            candidate.get('dom_tokens') or []
        )
        if dom_score >= 0.65:
            score += 0.10 * dom_score
            reasons.append('dom-structure')

        density_score = cls._ratio_similarity(
            baseline.get('text_density'),
            candidate.get('text_density')
        )
        if density_score >= 0.85:
            score += 0.04 * density_score
            reasons.append('text-density')

        if baseline.get('content_kind') and baseline.get('content_kind') == candidate.get('content_kind'):
            score += 0.02
            reasons.append('content-kind')

        if baseline.get('title') and baseline.get('title') == candidate.get('title'):
            score += 0.06
            reasons.append('title')

        if baseline.get('redirect_location') and baseline.get('redirect_location') == candidate.get('redirect_location'):
            score += 0.08
            reasons.append('redirect')

        size_score = cls._numeric_similarity(baseline.get('size'), candidate.get('size'))
        if size_score >= 0.90:
            score += 0.10 * size_score
            reasons.append('size')

        word_score = cls._numeric_similarity(baseline.get('word_count'), candidate.get('word_count'))
        if word_score >= 0.90:
            score += 0.05 * word_score
            reasons.append('words')

        line_score = cls._numeric_similarity(baseline.get('line_count'), candidate.get('line_count'))
        if line_score >= 0.90:
            score += 0.03 * line_score
            reasons.append('lines')

        if cls._is_exact_shape_match(baseline, candidate) is True:
            score += 0.08
            reasons.append('exact-shape')

        if cls._is_soft_200_shape_match(baseline, candidate) is True:
            score += 0.04
            reasons.append('soft-200-shape')

        header_score = cls._header_similarity(
            baseline.get('header_fingerprint') or {},
            candidate.get('header_fingerprint') or {}
        )
        if header_score >= 0.80:
            score += 0.03 * header_score
            reasons.append('headers')

        return min(score, 1.0), reasons

    @staticmethod
    def _hash(value):
        """
        Build a stable sha256 hash.

        :param str value:
        :return: str
        """

        return hashlib.sha256(str(value).encode('utf-8')).hexdigest()

    @staticmethod
    def _body(response):
        """
        Decode response body.

        :param object response:
        :return: str
        """

        try:
            return helper.decode(response.data)
        except (AttributeError, TypeError, UnicodeError):
            return ''

    @classmethod
    def _normalize_body(cls, body):
        """
        Normalize dynamic body fragments.

        :param str body:
        :return: str
        """

        value = html.unescape(str(body or '')).lower()
        value = re.sub(r'<!--.*?(?:-->|--!>)', ' ', value, flags=re.DOTALL)
        value = re.sub(r'<script\b[^>]*>.*?</script\b[^>]*>', ' ', value, flags=re.DOTALL | re.IGNORECASE)
        value = re.sub(r'<style\b[^>]*>.*?</style\b[^>]*>', ' ', value, flags=re.DOTALL | re.IGNORECASE)

        for pattern in cls.DYNAMIC_PATTERNS:
            value = re.sub(pattern, '<dynamic>', value, flags=re.IGNORECASE)

        value = re.sub(r'\s+', ' ', value)
        return value.strip()

    @staticmethod
    def _normalize_dns_addresses(addresses):
        """
        Normalize DNS addresses for stable wildcard matching.

        :param list[str] addresses:
        :return: list[str]
        """

        normalized = []
        for address in addresses or []:
            value = str(address or '').strip().lower()
            if value:
                normalized.append(value)

        return sorted(set(normalized))

    @classmethod
    def _visible_text(cls, body):
        """
        Build normalized visible text without HTML wrappers or dynamic tokens.

        :param str body:
        :return: str
        """

        value = html.unescape(str(body or '')).lower()
        value = re.sub(r'<!--.*?(?:-->|--!>)', ' ', value, flags=re.DOTALL)
        value = re.sub(r'<script\b[^>]*>.*?</script\b[^>]*>', ' ', value, flags=re.DOTALL | re.IGNORECASE)
        value = re.sub(r'<style\b[^>]*>.*?</style\b[^>]*>', ' ', value, flags=re.DOTALL | re.IGNORECASE)
        value = re.sub(r'<[^>]+>', ' ', value)

        for pattern in cls.DYNAMIC_PATTERNS:
            value = re.sub(pattern, '<dynamic>', value, flags=re.IGNORECASE)

        value = re.sub(r'[^a-z0-9<>]+', ' ', value)
        value = re.sub(r'\s+', ' ', value)
        return value.strip()

    @staticmethod
    def _content_kind(body):
        """
        Classify response body kind for calibration scoring.

        :param str body:
        :return: str
        """

        value = str(body or '').lstrip().lower()

        if value.startswith(('{', '[')):
            return 'json'

        if '<html' in value or '<!doctype html' in value or re.search(r'<[a-z][^>]*>', value):
            return 'html'

        if value:
            return 'text'

        return 'empty'

    @staticmethod
    def _dom_tokens(body):
        """
        Build a bounded sequence of HTML tag tokens.

        :param str body:
        :return: list[str]
        """

        tokens = re.findall(r'<\s*/?\s*([a-z0-9:-]+)', str(body or ''), flags=re.IGNORECASE)
        return [token.lower() for token in tokens[:120]]

    @classmethod
    def _semantic_phrases(cls, text):
        """
        Extract known soft-404 semantic phrases from visible text.

        :param str text:
        :return: list[str]
        """

        value = str(text or '').lower()
        phrases = []

        for phrase in cls.SOFT_404_PHRASES:
            if phrase in value:
                phrases.append(phrase)

        return phrases

    @classmethod
    def _semantic_terms(cls, text):
        """
        Extract stable semantic terms from visible response text.

        :param str text:
        :return: list[str]
        """

        terms = []

        for term in re.findall(r'[a-z][a-z0-9_-]{2,}', str(text or '').lower()):
            if term in cls.SEMANTIC_STOPWORDS:
                continue
            if term == 'dynamic':
                continue
            terms.append(term)

        return sorted(set(terms))[:40]

    @classmethod
    def _text_density(cls, body):
        """
        Estimate visible-text density relative to HTML markup volume.

        :param str body:
        :return: float
        """

        raw = str(body or '')
        if len(raw) <= 0:
            return 0.0

        return round(len(cls._visible_text(raw)) / float(max(len(raw), 1)), 4)

    @staticmethod
    def _body_skeleton(body):
        """
        Build a lightweight HTML structure signature.

        :param str body:
        :return: str
        """

        tags = Calibration._dom_tokens(body)

        if len(tags) > 0:
            return ' '.join(tags)

        text = re.sub(r'\w+', 'w', str(body or '').lower())
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    @staticmethod
    def _title(body):
        """
        Extract HTML title.

        :param str body:
        :return: str
        """

        match = re.search(r'<title[^>]*>(.*?)</title>', str(body or ''), flags=re.IGNORECASE | re.DOTALL)
        if match is None:
            return ''

        value = re.sub(r'\s+', ' ', html.unescape(match.group(1)))
        return value.strip().lower()

    @staticmethod
    def _word_count(body):
        """
        Count text words.

        :param str body:
        :return: int
        """

        text = re.sub(r'<[^>]+>', ' ', str(body or ''))
        return len(re.findall(r'\S+', text))

    @staticmethod
    def _line_count(body):
        """
        Count non-empty lines.

        :param str body:
        :return: int
        """

        return len([line for line in str(body or '').splitlines() if line.strip()])

    @staticmethod
    def _response_size(response):
        """
        Resolve response size.

        :param object response:
        :return: int
        """

        try:
            content_length = response.headers.get('Content-Length')
            if content_length is not None:
                return int(content_length)
        except (AttributeError, TypeError, ValueError):
            pass

        try:
            return len(response.data)
        except (AttributeError, TypeError):
            return 0

    @staticmethod
    def _response_code(response, response_data):
        """
        Resolve HTTP status code.

        :param object response:
        :param tuple response_data:
        :return: int|None
        """

        try:
            return int(response.status)
        except (AttributeError, TypeError, ValueError):
            pass

        try:
            return int(response_data[3])
        except (IndexError, TypeError, ValueError):
            return None

    @classmethod
    def _redirect_location(cls, response):
        """
        Resolve normalized redirect target.

        :param object response:
        :return: str
        """

        location = cls._header(response, 'location')

        if location is None:
            return ''

        return str(location).strip().lower()

    @classmethod
    def _header_fingerprint(cls, response):
        """
        Build stable header fingerprint.

        :param object response:
        :return: dict
        """

        fingerprint = {}

        for header_name in cls.STABLE_HEADERS:
            value = cls._header(response, header_name)
            if value is not None:
                fingerprint[header_name] = str(value).strip().lower()

        return fingerprint

    @staticmethod
    def _header(response, header_name):
        """
        Read response header case-insensitively.

        :param object response:
        :param str header_name:
        :return: str|None
        """

        try:
            headers = response.headers
        except AttributeError:
            return None

        try:
            value = headers.get(header_name)
            if value is not None:
                return value
        except AttributeError:
            pass

        expected = str(header_name).lower()

        try:
            value = headers.get(expected)
            if value is not None:
                return value
        except AttributeError:
            pass

        try:
            for key, value in headers.items():
                if str(key).lower() == expected:
                    return value
        except AttributeError:
            return None

        return None

    @staticmethod
    def _is_exact_shape_match(baseline, candidate):
        """
        Detect exact normalized response shape match.

        :param dict baseline:
        :param dict candidate:
        :return: bool
        """

        return all([
            baseline.get('normalized_body_hash') == candidate.get('normalized_body_hash'),
            baseline.get('body_skeleton_hash') == candidate.get('body_skeleton_hash'),
            baseline.get('size') == candidate.get('size'),
            baseline.get('word_count') == candidate.get('word_count'),
            baseline.get('line_count') == candidate.get('line_count'),
        ])

    @staticmethod
    def _numeric_similarity(left, right):
        """
        Return numeric similarity in range 0..1.

        :param int|None left:
        :param int|None right:
        :return: float
        """

        try:
            left = int(left)
            right = int(right)
        except (TypeError, ValueError):
            return 0.0

        maximum = max(abs(left), abs(right), 1)
        return max(0.0, 1.0 - (abs(left - right) / float(maximum)))

    @staticmethod
    def _ratio_similarity(left, right):
        """
        Return float-ratio similarity in range 0..1.

        :param float|None left:
        :param float|None right:
        :return: float
        """

        try:
            left = float(left)
            right = float(right)
        except (TypeError, ValueError):
            return 0.0

        maximum = max(abs(left), abs(right), 0.0001)
        return max(0.0, 1.0 - (abs(left - right) / maximum))

    @staticmethod
    def _jaccard_similarity(left, right):
        """
        Return set-overlap similarity in range 0..1.

        :param list[str] left:
        :param list[str] right:
        :return: float
        """

        left_set = set(left or [])
        right_set = set(right or [])

        if not left_set and not right_set:
            return 0.0

        union = left_set | right_set
        if len(union) <= 0:
            return 0.0

        return len(left_set & right_set) / float(len(union))

    @staticmethod
    def _sequence_similarity(left, right):
        """
        Return lightweight sequence similarity in range 0..1.

        :param list[str] left:
        :param list[str] right:
        :return: float
        """

        left = list(left or [])
        right = list(right or [])

        if not left and not right:
            return 0.0
        if not left or not right:
            return 0.0

        prefix = 0
        for left_item, right_item in zip(left, right):
            if left_item != right_item:
                break
            prefix += 1

        overlap = len(set(left) & set(right)) / float(len(set(left) | set(right)))
        prefix_score = prefix / float(max(len(left), len(right), 1))

        return max(overlap, prefix_score)

    @staticmethod
    def _header_similarity(left, right):
        """
        Compare stable header fingerprints.

        :param dict left:
        :param dict right:
        :return: float
        """

        if not left and not right:
            return 1.0

        keys = set(left.keys()) | set(right.keys())
        if len(keys) <= 0:
            return 1.0

        matched = 0
        for key in keys:
            if left.get(key) == right.get(key):
                matched += 1

        return matched / float(len(keys))
