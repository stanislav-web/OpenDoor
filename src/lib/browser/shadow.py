# -*- coding: utf-8 -*-

"""Runtime shadow-copy probing for confirmed 200 OK file hits."""

import difflib
import hashlib
import threading
import time
from queue import Queue
from urllib.parse import urlsplit, urlunsplit

from src.core import CoreConfig
from src.core import helper


class ShadowProbe(object):
    """Bounded active probe worker for backup/shadow postfix copies."""

    BUCKET = 'shadow'
    MAX_CANDIDATES_PER_HIT = 16
    MAX_TOTAL_PROBES = 500
    MAX_BODY_SIZE = 1024 * 1024
    MIN_DIFF_SIMILARITY = 0.90
    MAX_SIZE_DELTA_RATIO = 0.25
    SHADOW_STATUSES = {200}
    QUEUE_TIMEOUT_SEC = 0.25
    MIN_CONTROL_CANDIDATES = 2
    MIN_FALLBACK_CONTROL_SIMILARITY = 0.97
    CONTROL_SUFFIX = '.__healthcheck__'
    CONTROL_STATE_PENDING = 'pending'
    CONTROL_STATE_ALLOWED = 'allowed'
    CONTROL_STATE_SUPPRESSED = 'suppressed'

    SOURCE_EXTENSIONS = {
        'asp', 'aspx', 'bash', 'c', 'cfg', 'cgi', 'conf', 'config', 'cpp', 'cs',
        'css', 'env', 'go', 'h', 'hpp', 'htm', 'html', 'inc', 'ini', 'java',
        'js', 'json', 'jsx', 'jsp', 'kt', 'lua', 'md', 'php', 'phps', 'phtml',
        'pl', 'properties', 'py', 'pyw', 'rb', 'rs', 'sh', 'sql', 'toml', 'ts',
        'tsx', 'txt', 'xml', 'yaml', 'yml', 'zsh',
    }
    SPECIAL_FILENAMES = {
        '.env', '.env.local', '.env.production', '.env.staging', '.htaccess',
        '.htpasswd', 'composer.json', 'composer.lock', 'dockerfile',
        'docker-compose.yml', 'docker-compose.yaml', 'gemfile', 'gemfile.lock',
        'makefile', 'package.json', 'package-lock.json', 'pipfile',
        'pipfile.lock', 'procfile', 'pyproject.toml', 'requirements.txt',
        'settings.py', 'web.config', 'webpack.config.js', 'yarn.lock',
    }
    BINARY_EXTENSIONS = {
        '7z', 'avi', 'bmp', 'bz2', 'eot', 'exe', 'gif', 'gz', 'ico', 'jpeg',
        'jpg', 'mp3', 'mp4', 'otf', 'pdf', 'png', 'rar', 'tar', 'ttf', 'webm',
        'webp', 'woff', 'woff2', 'zip',
    }
    BINARY_CONTENT_TYPES = (
        'application/octet-stream',
        'application/pdf',
        'application/zip',
        'application/gzip',
        'application/x-gzip',
        'application/x-zip-compressed',
        'image/',
        'audio/',
        'video/',
        'font/',
    )

    def __init__(self, request_callback, match_callback, progress_callback=None, delay=0):
        """
        Initialize active shadow probing.

        :param callable request_callback: function used to fetch probe candidates
        :param callable match_callback: function called when a shadow copy is found
        :param callable|None progress_callback: optional progress callback
        :param int|float delay: optional delay before every active probe request
        """

        self.__request_callback = request_callback
        self.__match_callback = match_callback
        self.__progress_callback = progress_callback
        self.__delay = self.normalize_delay(delay)
        self.__suffixes = self.load_suffixes()
        self.__queue = Queue()
        self.__seen = set()
        self.__base_control_states = {}
        self.__lock = threading.RLock()
        self.__submitted = 0
        self.__completed = 0
        self.__findings = 0
        self.__worker = threading.Thread(target=self.__run, name='opendoor-shadow-probe')
        self.__worker.daemon = True
        self.__worker.start()

    @staticmethod
    def normalize_delay(delay):
        """
        Normalize active probe delay to a safe non-negative float.

        :param int|float delay: configured scan delay
        :return: non-negative delay in seconds
        :rtype: float
        """

        try:
            value = float(delay)
        except (TypeError, ValueError):
            return 0.0

        if value <= 0:
            return 0.0

        return value

    @property
    def submitted(self):
        """Return submitted shadow probe count."""

        with self.__lock:
            return int(self.__submitted)

    @property
    def completed(self):
        """Return completed shadow probe count."""

        with self.__lock:
            return int(self.__completed)

    @property
    def findings(self):
        """Return shadow finding count."""

        with self.__lock:
            return int(self.__findings)

    @classmethod
    def is_enabled(cls, config):
        """
        Return True when --sniff shadow is active.

        :param object config: browser config
        :return: whether active shadow probing should be enabled
        :rtype: bool
        """

        return getattr(config, 'is_sniff', False) is True and 'shadow' in (getattr(config, 'sniffers', []) or [])

    @classmethod
    def load_suffixes(cls):
        """
        Load unique suffixes from data/shadow-suffixes.dat.

        :return: normalized suffixes in stable file order
        :rtype: list[str]
        """

        path = CoreConfig.get('data').get('shadow_suffixes')
        suffixes = []
        seen = set()

        try:
            with open(path, 'r', encoding='utf-8') as handler:
                lines = handler.readlines()
        except (OSError, TypeError):
            lines = []

        for line in lines:
            suffix = str(line or '').strip()
            if not suffix or suffix in seen:
                continue
            suffixes.append(suffix)
            seen.add(suffix)

        return suffixes

    @classmethod
    def is_file_like_url(cls, url):
        """
        Decide whether a URL path can safely seed shadow postfix probes.

        :param str url: base URL
        :return: whether the URL points to a source/config-like file
        :rtype: bool
        """

        try:
            path = urlsplit(str(url)).path or ''
        except ValueError:
            return False

        if not path or path.endswith('/'):
            return False

        filename = path.rsplit('/', 1)[-1]
        lowered = filename.lower()

        if not filename or lowered in ('.', '..'):
            return False

        if lowered in cls.SPECIAL_FILENAMES:
            return True

        if '.' not in filename:
            return False

        extension = lowered.rsplit('.', 1)[-1]
        if extension in cls.BINARY_EXTENSIONS:
            return False

        return extension in cls.SOURCE_EXTENSIONS

    @classmethod
    def build_template_path(cls, path, template):
        """
        Render one path-aware shadow template against a file-like URL path.

        :param str path: URL path from the confirmed base response
        :param str template: template body without the tpl: prefix
        :return: rendered candidate path, or None when unsupported
        :rtype: str|None
        """

        template = str(template or '')
        if '{path}' not in template or '{ext}' not in template:
            return None

        path = str(path or '')
        filename = path.rsplit('/', 1)[-1]
        if not filename or '.' not in filename:
            return None

        if filename.startswith('.'):
            return None

        stem, extension = path.rsplit('.', 1)
        if not stem or not extension:
            return None

        rendered = template.replace('{path}', stem).replace('{ext}', extension)
        if '{' in rendered or '}' in rendered:
            return None

        if not rendered or rendered == path:
            return None

        return rendered

    @classmethod
    def build_candidates(cls, url, suffixes):
        """
        Build bounded suffix/template shadow candidates from one base URL.

        :param str url: base URL
        :param list[str] suffixes: configured suffix/template variants
        :return: candidate URL and variant pairs
        :rtype: list[tuple[str, str]]
        """

        try:
            parsed = urlsplit(str(url))
        except ValueError:
            return []

        path = parsed.path or ''
        if not path or path.endswith('/'):
            return []

        candidates = []
        seen = set()
        for variant in list(suffixes or []):
            variant = str(variant or '').strip()
            if not variant:
                continue

            if variant.startswith('tpl:'):
                new_path = cls.build_template_path(path, variant[4:])
            else:
                new_path = '{0}{1}'.format(path, variant)

            if not new_path:
                continue

            candidate_url = urlunsplit((parsed.scheme, parsed.netloc, new_path, parsed.query, parsed.fragment))
            if candidate_url in seen:
                continue

            candidates.append((candidate_url, variant))
            seen.add(candidate_url)
            if len(candidates) >= cls.MAX_CANDIDATES_PER_HIT:
                break

        return candidates

    @classmethod
    def response_signature(cls, response):
        """
        Build a compact normalized response body signature.

        :param object response: HTTP response-like object
        :return: signature metadata or None
        :rtype: dict|None
        """

        if cls.is_supported_response(response) is not True:
            return None

        data = getattr(response, 'data', b'')
        if data is None:
            return None

        if isinstance(data, bytes):
            raw = data[:cls.MAX_BODY_SIZE]
            text = helper.decode(raw, errors='ignore')
            size = len(data)
        else:
            text = str(data)[:cls.MAX_BODY_SIZE]
            size = len(str(data))

        normalized = cls.normalize_body(text)
        if not normalized:
            return None

        return {
            'hash': hashlib.sha256(normalized.encode('utf-8')).hexdigest(),
            'normalized': normalized,
            'size': int(size),
            'content_type': cls.content_type(response),
        }

    @classmethod
    def normalize_body(cls, text):
        """
        Normalize body text for exact shadow-copy matching.

        :param str text: decoded body
        :return: normalized body
        :rtype: str
        """

        return str(text or '').replace('\r\n', '\n').replace('\r', '\n').strip()

    @classmethod
    def is_supported_response(cls, response):
        """
        Return True when response status/content-type can be compared.

        :param object response: HTTP response-like object
        :return: whether response is eligible
        :rtype: bool
        """

        try:
            if int(getattr(response, 'status', 0)) not in cls.SHADOW_STATUSES:
                return False
        except (TypeError, ValueError):
            return False

        content_type = cls.content_type(response)
        for binary_type in cls.BINARY_CONTENT_TYPES:
            if content_type.startswith(binary_type):
                return False

        return True

    @staticmethod
    def content_type(response):
        """
        Extract normalized Content-Type without parameters.

        :param object response: HTTP response-like object
        :return: normalized content type
        :rtype: str
        """

        headers = getattr(response, 'headers', {}) or {}
        value = ''

        try:
            value = headers.get('Content-Type') or headers.get('content-type') or ''
        except AttributeError:
            try:
                for key, item in dict(headers).items():
                    if str(key).lower() == 'content-type':
                        value = item
                        break
            except (TypeError, ValueError):
                value = ''

        return str(value or '').split(';', 1)[0].strip().lower()

    @classmethod
    def similarity_ratio(cls, base_signature, candidate_signature):
        """
        Calculate normalized body similarity for related shadow candidates.

        :param dict base_signature: base response signature
        :param dict candidate_signature: candidate response signature
        :return: similarity ratio in range 0.0..1.0
        :rtype: float
        """

        base_body = str(base_signature.get('normalized', ''))
        candidate_body = str(candidate_signature.get('normalized', ''))
        if not base_body or not candidate_body:
            return 0.0

        return float(difflib.SequenceMatcher(None, base_body, candidate_body).ratio())

    @classmethod
    def size_delta_ratio(cls, base_signature, candidate_signature):
        """
        Calculate relative body size delta for shadow candidate filtering.

        :param dict base_signature: base response signature
        :param dict candidate_signature: candidate response signature
        :return: relative size delta
        :rtype: float
        """

        base_size = int(base_signature.get('size', 0) or 0)
        candidate_size = int(candidate_signature.get('size', 0) or 0)
        if base_size <= 0 or candidate_size <= 0:
            return 1.0

        return abs(base_size - candidate_size) / float(max(base_size, candidate_size))

    @classmethod
    def build_control_candidate(cls, url):
        """
        Build one deterministic negative-control URL for fallback detection.

        The control keeps the same query string as the original URL so route
        fallbacks that depend on query context are still detected, but appends a
        suffix that should not exist as a real backup artifact.

        :param str url: base URL
        :return: control URL, or None when the base URL cannot be parsed
        :rtype: str|None
        """

        try:
            parsed = urlsplit(str(url))
        except ValueError:
            return None

        path = parsed.path or ''
        if not path or path.endswith('/'):
            return None

        return urlunsplit((parsed.scheme, parsed.netloc, '{0}{1}'.format(path, cls.CONTROL_SUFFIX), parsed.query, ''))

    @classmethod
    def is_fallback_like_control(cls, base_signature, response):
        """
        Return True when a negative-control URL behaves like the base response.

        Unlike real shadow matching, byte-identical responses are suspicious
        here: a definitely-nonexistent suffix that returns the same page is a
        soft-200/fallback signal, not a backup copy.

        :param dict base_signature: base response signature
        :param object response: control response
        :return: whether shadow candidates for this base URL should be suppressed
        :rtype: bool
        """

        control_signature = cls.response_signature(response)
        if not isinstance(base_signature, dict) or control_signature is None:
            return False

        base_content_type = str(base_signature.get('content_type', ''))
        control_content_type = str(control_signature.get('content_type', ''))
        if base_content_type and control_content_type and base_content_type != control_content_type:
            return False

        if cls.size_delta_ratio(base_signature, control_signature) > cls.MAX_SIZE_DELTA_RATIO:
            return False

        if control_signature.get('hash') == base_signature.get('hash'):
            return True

        return cls.similarity_ratio(base_signature, control_signature) >= cls.MIN_FALLBACK_CONTROL_SIMILARITY

    @classmethod
    def is_match(cls, base_signature, response):
        """
        Compare a changed shadow candidate response with its base signature.

        Identical copies are intentionally ignored because they do not add new
        information beyond the original success response. A shadow finding is
        emitted only when the candidate is still strongly related to the base
        response but contains a real content difference.

        :param dict base_signature: base response signature
        :param object response: candidate response
        :return: candidate signature when matched, otherwise None
        :rtype: dict|None
        """

        candidate_signature = cls.response_signature(response)
        if not isinstance(base_signature, dict) or candidate_signature is None:
            return None

        if candidate_signature.get('hash') == base_signature.get('hash'):
            return None

        if cls.size_delta_ratio(base_signature, candidate_signature) > cls.MAX_SIZE_DELTA_RATIO:
            return None

        similarity = cls.similarity_ratio(base_signature, candidate_signature)
        if similarity < cls.MIN_DIFF_SIMILARITY or similarity >= 1.0:
            return None

        candidate_signature['similarity'] = round(similarity, 4)
        return candidate_signature

    @classmethod
    def build_metadata(cls, base_url, candidate_url, suffix, base_signature, candidate_signature):
        """
        Build report metadata for one confirmed shadow copy.

        :param str base_url: original 200 OK file URL
        :param str candidate_url: confirmed shadow copy URL
        :param str suffix: matched suffix
        :param dict base_signature: base response signature
        :param dict candidate_signature: candidate response signature
        :return: report metadata
        :rtype: dict
        """

        variant = str(suffix)
        variant_type = 'template' if variant.startswith('tpl:') else 'suffix'

        return {
            'shadow_detection': {
                'type': 'backup_copy',
                'confidence': 90,
                'reason': 'content_diff',
                'base_url': str(base_url),
                'url': str(candidate_url),
                'variant': variant,
                'variant_type': variant_type,
                'similarity': float(candidate_signature.get('similarity', 0.0)),
                'base_size': int(base_signature.get('size', 0)),
                'shadow_size': int(candidate_signature.get('size', 0)),
                'content_type': str(candidate_signature.get('content_type', '')),
            }
        }

    def enqueue(self, base_url, base_response, bucket):
        """
        Queue active shadow probes for one successful base response.

        :param str base_url: base response URL
        :param object base_response: base response object
        :param str bucket: classified base bucket
        :return: queued candidate count
        :rtype: int
        """

        if bucket != 'success':
            return 0

        if self.is_file_like_url(base_url) is not True:
            return 0

        base_signature = self.response_signature(base_response)
        if base_signature is None:
            return 0

        candidates = self.build_candidates(base_url, self.__suffixes)
        with self.__lock:
            if self.__submitted >= self.MAX_TOTAL_PROBES:
                return 0

        self.__enqueue_control_candidate(base_url, base_signature, candidates)

        queued = 0
        for candidate_url, suffix in candidates:
            with self.__lock:
                if self.__submitted >= self.MAX_TOTAL_PROBES:
                    break
                if candidate_url in self.__seen:
                    continue
                self.__seen.add(candidate_url)
                self.__submitted += 1
                current = self.__submitted

            self.__queue.put(('candidate', base_url, base_signature, candidate_url, suffix, current))
            queued += 1

        return queued

    def __enqueue_control_candidate(self, base_url, base_signature, candidates):
        """
        Queue one internal negative-control probe before candidate probes.

        Controls are intentionally not counted in submitted/completed candidate
        counters. They only decide whether a base URL is a soft-200/fallback
        source that would otherwise create a burst of false shadow findings.

        :param str base_url: original base URL
        :param dict base_signature: normalized base response signature
        :param list[tuple[str, str]] candidates: generated shadow candidates
        :return: None
        """

        if len(candidates) < self.MIN_CONTROL_CANDIDATES:
            return

        control_url = self.build_control_candidate(base_url)
        if not control_url:
            return

        with self.__lock:
            if base_url in self.__base_control_states:
                return
            self.__base_control_states[base_url] = self.CONTROL_STATE_PENDING

        self.__queue.put(('control', base_url, base_signature, control_url, self.CONTROL_SUFFIX, 0))

    def drain(self):
        """
        Wait until all submitted shadow probes have completed.

        :return: None
        """

        self.__queue.join()

    def __run(self):
        """Run the bounded shadow probe worker loop."""

        while True:
            task = self.__queue.get(block=True)
            try:
                self.__process_task(task)
            finally:
                if self.__is_control_task(task) is not True:
                    with self.__lock:
                        self.__completed += 1
                self.__queue.task_done()

    def __process_task(self, task):
        """
        Process one shadow probe candidate.

        :param tuple task: queued shadow probe task
        :return: None
        """

        task_type, base_url, base_signature, candidate_url, suffix, current = self.__normalize_task(task)

        if task_type == 'control':
            self.__process_control_task(base_url, base_signature, candidate_url)
            return

        if self.__is_base_suppressed(base_url) is True:
            return

        if self.__delay > 0:
            time.sleep(self.__delay)

        try:
            candidate_response = self.__request_callback(candidate_url)
        except Exception:
            return

        candidate_signature = self.is_match(base_signature, candidate_response)
        if candidate_signature is None:
            if callable(self.__progress_callback):
                self.__progress_callback(candidate_url, candidate_response, current, self.submitted)
            return

        metadata = self.build_metadata(base_url, candidate_url, suffix, base_signature, candidate_signature)

        with self.__lock:
            self.__findings += 1

        if callable(self.__match_callback):
            self.__match_callback(candidate_url, candidate_response, metadata)

    @classmethod
    def __normalize_task(cls, task):
        """
        Normalize legacy and current shadow task tuples.

        :param tuple task: queued shadow task
        :return: task type, base URL, base signature, candidate URL, suffix and counter
        :rtype: tuple[str, str, dict, str, str, int]
        """

        if len(task) == 6:
            return task

        base_url, base_signature, candidate_url, suffix, current = task
        return 'candidate', base_url, base_signature, candidate_url, suffix, current

    @classmethod
    def __is_control_task(cls, task):
        """
        Return whether a queued task is an internal fallback-control task.

        :param tuple task: queued shadow task
        :return: whether task is a control probe
        :rtype: bool
        """

        try:
            return len(task) == 6 and task[0] == 'control'
        except TypeError:
            return False

    def __process_control_task(self, base_url, base_signature, control_url):
        """
        Process one internal negative-control probe.

        :param str base_url: original base URL
        :param dict base_signature: base response signature
        :param str control_url: generated control URL
        :return: None
        """

        if self.__delay > 0:
            time.sleep(self.__delay)

        try:
            control_response = self.__request_callback(control_url)
        except Exception:
            self.__set_base_control_state(base_url, self.CONTROL_STATE_ALLOWED)
            return

        if self.is_fallback_like_control(base_signature, control_response) is True:
            self.__set_base_control_state(base_url, self.CONTROL_STATE_SUPPRESSED)
            return

        self.__set_base_control_state(base_url, self.CONTROL_STATE_ALLOWED)

    def __set_base_control_state(self, base_url, state):
        """
        Store fallback-control state for one base URL.

        :param str base_url: original base URL
        :param str state: control state
        :return: None
        """

        with self.__lock:
            self.__base_control_states[str(base_url)] = state

    def __is_base_suppressed(self, base_url):
        """
        Return whether shadow candidates for a base URL must be skipped.

        :param str base_url: original base URL
        :return: whether candidates are suppressed as fallback noise
        :rtype: bool
        """

        with self.__lock:
            return self.__base_control_states.get(str(base_url)) == self.CONTROL_STATE_SUPPRESSED
